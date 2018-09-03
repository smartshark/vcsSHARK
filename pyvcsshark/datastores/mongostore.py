import sys
import os
from pymongo.errors import DocumentTooLarge, DuplicateKeyError

from pyvcsshark.datastores.basestore import BaseStore
from mongoengine import connect, connection, Document, DoesNotExist, NotUniqueError, OperationError
from pycoshark.mongomodels import VCSSystem, Project, Commit, Tag, File, People, FileAction, Hunk, Branch
from pycoshark.utils import create_mongodb_uri_string

import multiprocessing
import logging
import datetime
import traceback

logger = logging.getLogger("store")


class MongoStore(BaseStore):
    """ Datastore implementation for saving data to the mongodb. Inherits from
    :class:`pyvcsshark.datastores.basestore.BaseStore`.

    :property commit_queue: instance of a :class:`multiprocessing.JoinableQueue`, which  \
    holds objects of :class:`pyvcsshark.dbmodels.models.CommitModel`, that should be put into the mongodb
    :property logger: holds the logging instance, by calling logging.getLogger("store")
    """

    commit_queue = None

    def __init__(self):
        BaseStore.__init__(self)

    def initialize(self, config, repository_url, repository_type):
        """Initializes the mongostore by connecting to the mongodb, creating the project in the project collection \
        and setting up processes (see: :class:`pyvcsshark.datastores.mongostore.CommitStorageProcess`, which
        read commits out of the commitqueue, process them and store them into the mongodb.

        :param config: all configuration
        :param repository_url: url of the repository, which is to be analyzed
        :param repository_type: type of the repository, which is to be analyzed (e.g. "git")
        """

        logger.setLevel(config.debug_level)
        logger.info("Initializing MongoStore...")

        # Create queue for multiprocessing
        self.commit_queue = multiprocessing.Queue()
        self.commit_condition = multiprocessing.Condition()

        # we need an extra queue for branches because all commits need to be finished before we can process branches
        self.branches = []
        self.config = config
        self.cores_per_job = config.cores_per_job

        # We define, that the user we authenticate with is in the admin database
        logger.info("Connecting to MongoDB...")

        uri = create_mongodb_uri_string(config.db_user, config.db_password, config.db_hostname, config.db_port,
                                        config.db_authentication, config.ssl_enabled)
        connect(config.db_database, host=uri, connect=False)

        # Get project_id
        try:
            project_id = Project.objects(name=config.project_name).get().id
        except DoesNotExist:
            logger.error('Project with name "%s" does not exist in database!' % config.project_name)
            sys.exit(1)

        # Check if vcssystem already exist, and use upsert
        self.vcs_system_id = VCSSystem.objects(url=repository_url).upsert_one(url=repository_url,
                                                                              repository_type=repository_type,
                                                                              last_updated=datetime.datetime.today(),
                                                                              project_id=project_id).id

        # Get the last commit by date of the project (if there is any)
        last_commit = Commit.objects(vcs_system_id=self.vcs_system_id)\
            .only('committer_date').order_by('-committer_date').first()

        if last_commit is not None:
            last_commit_date = last_commit.committer_date
        else:
            last_commit_date = None

        # Start worker, they will wait till something comes into the queue and then process it
        worker = multiprocessing.Process(
            target=_commit_pooler,
            args=(self.commit_queue, self.commit_condition, self.cores_per_job,
                self, self.vcs_system_id, last_commit_date, self.config,))
        worker.start()

        logger.info("Starting storage Process...")

    def register_subprocess(self):
        connection._connections = {}
        connection._connection_settings ={}
        connection._dbs = {}
        for document_class in Document.__subclasses__():
            document_class._collection = None
        uri = create_mongodb_uri_string(
            self.config.db_user, self.config.db_password, self.config.db_hostname,
            self.config.db_port, self.config.db_authentication, self.config.ssl_enabled)
        connect(self.config.db_database, host=uri, connect=False)

    @property
    def store_identifier(self):
        """Returns the identifier **mongo** for this datastore"""
        return 'mongo'

    def contains_commit(self, commit_id):
        try:
            Commit.objects(vcs_system_id=self.vcs_system_id, revision_hash=commit_id).only('_id').get()
            return True
        except DoesNotExist:
            return False

    def add_commit(self, commit_model):
        """Adds commits of class :class:`pyvcsshark.dbmodels.models.CommitModel` to the commitqueue"""
        # add to queue
        self.commit_queue.put(commit_model)
        return

    def add_branch(self, branch_model):
        """Add branch to extra queue"""
        self.branches.append(branch_model)
        return

    def finalize(self):
        """As we depend on commits beeing finished with branches (for the references) we must wait first for them to finish before we can start our branch processing."""
        # wait for all commits to be parsed
        self.commit_queue.put(None)
        self.commit_condition.acquire()
        self.commit_condition.wait()
        self.commit_condition.release()

        # after commits are finished, process branches
        pool = multiprocessing.Pool(
            processes=self.cores_per_job,
            initializer=_initialize_branch_storage_process,
            initargs=(self, self.vcs_system_id))
        pool.map(_store_branch, self.branches)
        pool.close()
        pool.join()

        logger.info("Storing Process complete...")
        return

branch_storage = None
def _initialize_branch_storage_process(datastore, vcs_system_id):
    global branch_storage
    branch_storage = BranchStorage(datastore, vcs_system_id)

def _store_branch(branch_model):
    try:
        global branch_storage
        branch_storage.store(branch_model)
    except Exception as e:
        traceback.print_exc()
        raise
    except:
        print('Storing branch failed due to non-Exception exception!')
        raise

class BranchStorage():
    def __init__(self, datastore, vcs_system_id):
        datastore.register_subprocess()
        self.vcs_system_id = vcs_system_id
        self.proc_name = "BranchStorageProcess-" + str(os.getpid())

    def store(self, branch):
        """Endless loop for the processes.

        1. Get a object of class :class:`pyvcsshark.dbmodels.models.BranchModel` from the queue
        2. Check if this branch was stored before and if so: update the branch, if not create branch
        """
        logger.debug("Process {} is processing branch {} -> {}".format(self.proc_name, branch.name, branch.target))

        # get commit OID for Target ref
        mongo_commit = Commit.objects.get(vcs_system_id=self.vcs_system_id, revision_hash=branch.target)

        # Try to get the commit
        try:
            mongo_branch = Branch.objects.get(vcs_system_id=self.vcs_system_id, name=branch.name)
        except DoesNotExist:
            mongo_branch = Branch(
                vcs_system_id=self.vcs_system_id,
                name=branch.name,
                commit_id=mongo_commit.id
            ).save()
        mongo_branch.commit_id = mongo_commit.id
        mongo_branch.is_origin_head = branch.is_origin_head
        mongo_branch.save()

        logger.debug("Process %s saved branch %s." % (self.proc_name, branch.name))

def _commit_pooler(commit_queue, commit_condition, process_count, datastore, vcs_system_id, last_commit_date, config):
    pool = multiprocessing.Pool(
        processes=process_count,
        initializer=_initialize_commit_storage_process,
        initargs=(datastore, vcs_system_id, last_commit_date, config),
        maxtasksperchild=100)
    while True:
        commit = commit_queue.get()
        if commit is None:
            break
        pool.apply_async(_store_commit, [commit])

    # finish all jobs
    pool.close()
    pool.join()

    # notify the main process that all commits have been parsed
    commit_condition.acquire()
    commit_condition.notify_all()
    commit_condition.release()

commit_storage = None
def _initialize_commit_storage_process(datastore, vcs_system_id, last_commit_date, config):
    global commit_storage
    commit_storage = CommitStorage(datastore, vcs_system_id, last_commit_date, config)

def _store_commit(commit_model):
    global commit_storage
    try:
        commit_storage.store(commit_model)
    except Exception as e:
        traceback.print_exc()
        raise
    except:
        print('Storing commit failed due to non-Exception exception!')
        raise

class CommitStorage():
    """Class that inherits from :class:`multiprocessing.Process` for processing instances of class
    :class:`pyvcsshark.dbmodels.models.CommitModel` \
    and writing it into the mongodb

    :param queue: queue, where the :class:`pyvcsshark.dbmodels.models.CommitModel` are stored in
    :param vcs_system_id: object id of class :class:`bson.objectid.ObjectId` from the vcs system
    :param last_commit_date: object of class :class:`datetime.datetime`, which holds the last commit that was parsed
    :param config: object of class :class:`pyvcsshark.config.Config`, which holds configuration information
    """
    def __init__(self, datastore, vcs_system_id, last_commit_date, config):
        datastore.register_subprocess()
        self.vcs_system_id = vcs_system_id
        self.last_commit_date = last_commit_date
        self.config = config
        self.proc_name = "CommitStorageProcess-" + str(os.getpid())

    def store(self, commit):
        """ Endless loop for the processes, which consists of several steps:

        1. Get a object of class :class:`pyvcsshark.dbmodels.models.CommitModel` from the queue
        2. Check if this commit was stored before and if it is so: update branches and tags (if they have changed)
        3. Store author and committer in mongodb
        4. Store Tags in mongodb
        5. Create a list of branches, where the commit belongs to
        6. Save the different file actions, which were done in this commit in the mongodb
        7. Save the commit itself


        .. NOTE:: The committer date is used to check if a commit was already stored before. Meaning: We get the \
        last commit out of the database and check if the committer date of the commits we process are > than the \
        committer date of the last commit.

        .. WARNING:: We only look for changed tags and branches here for already processed commits!
        """
        logger.debug("Process %s is processing commit with hash %s." % (self.proc_name, commit.id))

        # Try to get the commit
        try:
            mongo_commit = Commit.objects(vcs_system_id=self.vcs_system_id, revision_hash=commit.id).get()
        except DoesNotExist:
            mongo_commit = Commit(
                vcs_system_id=self.vcs_system_id,
                revision_hash=commit.id
            ).save()
        self.set_whole_commit(mongo_commit, commit)

        # Save Revision object
        mongo_commit.save()
        logger.debug("Process %s saved commit with hash %s." % (self.proc_name, commit.id))

    def set_whole_commit(self, mongo_commit, commit):
        # Create tags
        logger.debug("Process %s is creating tags for commit with hash %s." % (self.proc_name, commit.id))
        self.create_tags(mongo_commit.id, commit.tags)

        # Create branchlist
        logger.debug("Process %s is creating branches for commit with hash %s." % (self.proc_name, commit.id))
        mongo_commit.branches = self.create_branch_list(commit.branches)

        # Create people
        logger.debug("Process %s is setting author for commit with hash %s." % (self.proc_name, commit.id))
        mongo_commit.author_id = self.create_people(commit.author.name, commit.author.email)
        mongo_commit.author_date = commit.authorDate
        mongo_commit.author_date_offset = commit.authorOffset

        logger.debug("Process %s is setting committer for commit with hash %s." % (self.proc_name, commit.id))
        mongo_commit.committer_id = self.create_people(commit.committer.name, commit.committer.email)
        mongo_commit.committer_date = commit.committerDate
        mongo_commit.committer_date_offset = commit.committerOffset

        # Set parent hashes
        logger.debug("Process %s is setting parents for commit with hash %s." % (self.proc_name, commit.id))
        mongo_commit.parents = commit.parents

        # Set message
        logger.debug("Process %s is setting message for commit with hash %s." % (self.proc_name, commit.id))
        mongo_commit.message = commit.message

        # Create fileActions
        logger.debug("Process %s is setting file actions for commit with hash %s." % (self.proc_name, commit.id))
        self.create_file_actions(commit.changedFiles, mongo_commit.id)

    def create_branch_list(self, branches):
        """Creates a list of the different branch names, where a commit belongs to. We go through the \
        branches property of the class :class:`pyvcsshark.dbmodels.models.CommitModel`, which is a list of \
        different branch objects of class `pyvcsshark.dbmodels.models.CommitModel`

        :param branches: list of objects of class :class:`pyvcsshark.dbmodels.models.BranchModel`
        """
        if branches is None:
            return []

        branch_list = []
        for branch in branches:
            if branch is not None:
                branch_list.append(branch.name)

        if len(branch_list) == 0:
            branch_list = None

        return branch_list

    def create_tags(self, commit_id, tags):
        tag_list = []
        for tag in tags:
            if tag.tagger is not None:
                tagger_id = self.create_people(tag.tagger.name, tag.tagger.email)
                try:
                    logger.debug("Process %s is creating tag %s with tagger." % (self.proc_name, tag.name))
                    mongo_tag = Tag(commit_id=commit_id, name=tag.name, message=tag.message, tagger_id=tagger_id,
                                    date=tag.taggerDate, date_offset=tag.taggerOffset,
                                    vcs_system_id=self.vcs_system_id).save()
                except (DuplicateKeyError, NotUniqueError):
                    logger.debug("Process %s found tag with tagger with name %s." % (self.proc_name, tag.name))
                    mongo_tag = Tag.objects(commit_id=commit_id, name=tag.name) \
                        .only('id', 'name').get()
            else:
                try:
                    logger.debug("Process %s is creating tag %s." % (self.proc_name, tag.name))
                    mongo_tag = Tag(commit_id=commit_id, name=tag.name, date=tag.taggerDate,
                                    date_offset=tag.taggerOffset, vcs_system_id=self.vcs_system_id).save()
                except (DuplicateKeyError, NotUniqueError):
                    logger.debug("Process %s is found tag %s." % (self.proc_name, tag.name))
                    mongo_tag = Tag.objects(commit_id=commit_id, name=tag.name).only('id', 'name').get()

            tag_list.append(mongo_tag)
        return tag_list

    def create_people(self, name, email):
        """ Creates a people object of type People (which can be found in the pycoshark library) and returns a
        object id of the type :class:`bson.objectid.ObjectId` of the stored object

        :param name: name of the contributor
        :param email: email of the contributor

        .. NOTE:: The call to :func:`mongoengine.queryset.QuerySet.upsert_one` is thread/process safe
        """
        try:
            logger.debug("Process %s is creating person with email %s and name %s." % (self.proc_name, email, name))
            people_id = People(name=name, email=email).save().id
        except (DuplicateKeyError, NotUniqueError):
            logger.debug("Process %s found person with email %s and name %s." % (self.proc_name, email, name))
            people_id = People.objects(name=name, email=email).only('id').get().id
        return people_id

    def create_file_actions(self, files, mongo_commit_id):
        """ Creates a list of object ids of type :class:`bson.objectid.ObjectId` for the different file actions of the
        commit by transforming the files into file actions of type FileAction, File, and Hunk (pycoshark library)

        :param files: list of changed files of type :class:`pyvcsshark.dbmodels.models.FileModel`
        :param mongo_commit_id: mongoid of the commit which is processed

        .. NOTE:: Hunks and the file action itself are inserted via bulk insert.
        """

        for file in files:

            # Check if the file was a copy or move action (then the oldPath attribute is not None)
            old_file_id = None
            if file.oldPath is not None:
                logger.debug("Process %s is creating old file with path %s." % (self.proc_name, file.oldPath))
                try:
                    old_file_id = File(vcs_system_id=self.vcs_system_id, path=file.oldPath).save().id
                except (DuplicateKeyError, NotUniqueError):
                    logger.debug("Process %s found old file with path %s." % (self.proc_name, file.oldPath))
                    old_file_id = File.objects(vcs_system_id=self.vcs_system_id, path=file.oldPath).only('id').get().id

            # Create a new file object
            try:
                logger.debug("Process %s is creating file with path %s." % (self.proc_name, file.path))
                new_file_id = File(vcs_system_id=self.vcs_system_id, path=file.path).save().id
            except (DuplicateKeyError, NotUniqueError):
                logger.debug("Process %s found file with path %s." % (self.proc_name, file.path))
                new_file_id = File.objects(vcs_system_id=self.vcs_system_id, path=file.path).only('id').get().id

            # Create the new file action
            try:
                logger.debug("Process %s is creating file action with file_id %s." % (self.proc_name, new_file_id))
                file_action_id = FileAction.objects(file_id=new_file_id, commit_id=mongo_commit_id).get().id

                logger.debug("Process %s is deleting all hunks for file action id %s." % (self.proc_name, file_action_id))
                Hunk.objects(file_action_id=file_action_id).all().delete()
            except DoesNotExist:
                file_action_id = FileAction(file_id=new_file_id,
                                            commit_id=mongo_commit_id,
                                            size_at_commit=file.size,
                                            lines_added=file.linesAdded,
                                            lines_deleted=file.linesDeleted,
                                            is_binary=file.isBinary,
                                            mode=file.mode,
                                            old_file_id=old_file_id).save().id

            if file.hunks is None:
                continue

            # Create hunk objects for bulk insert
            logger.debug("Process %s is creating hunks for bulk insert." % self.proc_name)
            hunks = []
            for hunk in file.hunks:
                mongo_hunk = Hunk(file_action_id=file_action_id, new_start=hunk.new_start, new_lines=hunk.new_lines,
                                  old_start=hunk.old_start, old_lines=hunk.old_lines, content=hunk.content)
                hunks.append(mongo_hunk)

            # Get hunk ids from insert if hunks is not empty
            if hunks:
                try:
                    logger.debug("Process %s is inserting hunks..." % self.proc_name)
                    Hunk.objects.insert(hunks, load_bulk=False)
                except (DocumentTooLarge, OperationError):
                    for hunk in hunks:
                        try:
                            hunk.save()
                        except (DocumentTooLarge, OperationError):
                            logger.info("Document was too large for commit: %s" % mongo_commit_id)

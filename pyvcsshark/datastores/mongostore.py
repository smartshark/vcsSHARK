import os
import sys
import tarfile
import re
import pygit2
from pymongo.errors import DocumentTooLarge, DuplicateKeyError

from pyvcsshark.datastores.basestore import BaseStore
from mongoengine import connect, DoesNotExist, NotUniqueError
from pycoshark.mongomodels import VCSSystem, Project, Commit, Tag, File, People, FileAction, Hunk, Branch
from pycoshark.utils import create_mongodb_uri_string

import multiprocessing
import logging
import datetime


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
        self.commit_queue = multiprocessing.JoinableQueue()

        # we need an extra queue for branches because all commits need to be finished before we can process branches
        self.branch_queue = multiprocessing.JoinableQueue()
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
            logger.error(
                'Project with name "%s" does not exist in database!' % config.project_name)
            sys.exit(1)

        # Check if vcssystem already exist, and use upsert
        vcs_system = VCSSystem.objects(url=repository_url).upsert_one(url=repository_url,
                                                                      repository_type=repository_type,
                                                                      last_updated=datetime.datetime.today(),
                                                                      project_id=project_id)
        self.vcs_system_id = vcs_system.id
        self.vcs_system_last_updated = vcs_system.last_updated

        # Tar.gz name based on project name
        tar_gz_name = '{}.tar.gz'.format(config.project_name)

        # Tar.gz of repository folder
        with tarfile.open(tar_gz_name, "w:gz") as tar:
            tar.add(config.path, arcname=config.project_name)

        # Add repository to gridfs if not existent
        if vcs_system.repository_file.grid_id is None:
            logger.info('Copying project to gridfs...')

            # Store in gridfs
            with open(tar_gz_name, 'rb') as tar_file:
                vcs_system.repository_file.put(tar_file, content_type='application/gzip',
                                               filename=tar_gz_name)
                vcs_system.save()
        else:
            # replace file if not existent
            logger.info('Replacing project file in gridfs...')
            with open(tar_gz_name, 'rb') as tar_file:
                vcs_system.repository_file.replace(tar_file, content_type='application/gzip',
                                                   filename=tar_gz_name)
                vcs_system.save()

        # Delete tar.gz file
        os.remove(tar_gz_name)

        # Get the last commit by date of the project (if there is any)
        last_commit = Commit.objects(vcs_system_id=self.vcs_system_id)\
            .only('committer_date').order_by('-committer_date').first()

        if last_commit is not None:
            last_commit_date = last_commit.committer_date
        else:
            last_commit_date = None

        # Sync commits
        remove_sync_thread = RemovedDataSync(
            self.vcs_system_id, self.config, 'RemovedDataSync',self.vcs_system_last_updated)
        remove_sync_thread.daemon = True
        remove_sync_thread.start()
        remove_sync_thread.join()

        # Start worker, they will wait till something comes into the queue and then process it
        for i in range(self.cores_per_job):
            name = "StorageProcess-%d" % i
            process = CommitStorageProcess(
                self.commit_queue, self.vcs_system_id, last_commit_date, self.config, name,self.vcs_system_last_updated)
            process.daemon = True
            process.start()

        logger.info("Starting storage Process...")

    @property
    def store_identifier(self):
        """Returns the identifier **mongo** for this datastore"""
        return 'mongo'

    def add_commit(self, commit_model):
        """Adds commits of class :class:`pyvcsshark.dbmodels.models.CommitModel` to the commitqueue"""
        # add to queue
        self.commit_queue.put(commit_model)
        return

    def add_branch(self, branch_model):
        """Add branch to extra queue"""
        self.branch_queue.put(branch_model)
        return

    def finalize(self):
        """As we depend on commits beeing finished with branches (for the references) we must wait first for
        them to finish before we can start our branch processing."""
        self.commit_queue.join()

        # after commits are finished, process branches
        for i in range(self.cores_per_job):
            name = "StorageProcessBranch-%d" % i
            process = BranchStorageProcess(
                self.branch_queue, self.vcs_system_id, self.config, name)
            process.daemon = True
            process.start()

        # wait for branches to finish
        self.branch_queue.join()
        logger.info("Storing Process complete...")
        return


class BranchStorageProcess(multiprocessing.Process):

    def __init__(self, queue, vcs_system_id, config, name):
        multiprocessing.Process.__init__(self)
        uri = create_mongodb_uri_string(config.db_user, config.db_password, config.db_hostname, config.db_port,
                                        config.db_authentication, config.ssl_enabled)
        connect(config.db_database, host=uri, connect=False)
        self.queue = queue
        self.vcs_system_id = vcs_system_id
        self.proc_name = name

    def run(self):
        """Endless loop for the processes.

        1. Get a object of class :class:`pyvcsshark.dbmodels.models.BranchModel` from the queue
        2. Check if this branch was stored before and if so: update the branch, if not create branch
        """
        while True:
            branch = self.queue.get()
            logger.debug("Process {} is processing branch {} -> {}".format(
                self.proc_name, branch.name, branch.target))

            # get commit OID for Target ref
            mongo_commit = Commit.objects.get(
                vcs_system_id=self.vcs_system_id, revision_hash=branch.target)

            # Try to get the commit
            try:
                mongo_branch = Branch.objects.get(
                    vcs_system_id=self.vcs_system_id, name=branch.name)
            except DoesNotExist:
                mongo_branch = Branch(
                    vcs_system_id=self.vcs_system_id,
                    name=branch.name,
                    commit_id=mongo_commit.id
                ).save()

            mongo_branch.commit_id = mongo_commit.id
            mongo_branch.is_origin_head = branch.is_origin_head
            mongo_branch.save()

            logger.debug("Process %s saved branch %s. Queue size: %d" %
                         (self.proc_name, branch.name, self.queue.qsize()))

            self.queue.task_done()


class CommitStorageProcess(multiprocessing.Process):
    """Class that inherits from :class:`multiprocessing.Process` for processing instances of class
    :class:`pyvcsshark.dbmodels.models.CommitModel` \
    and writing it into the mongodb

    :param queue: queue, where the :class:`pyvcsshark.dbmodels.models.CommitModel` are stored in
    :param vcs_system_id: object id of class :class:`bson.objectid.ObjectId` from the vcs system
    :param last_commit_date: object of class :class:`datetime.datetime`, which holds the last commit that was parsed
    :param config: object of class :class:`pyvcsshark.config.Config`, which holds configuration information
    """

    def __init__(self, queue, vcs_system_id, last_commit_date, config, name,vcs_system_last_updated):
        multiprocessing.Process.__init__(self)
        uri = create_mongodb_uri_string(config.db_user, config.db_password, config.db_hostname, config.db_port,
                                        config.db_authentication, config.ssl_enabled)
        connect(config.db_database, host=uri, connect=False)
        self.queue = queue
        self.vcs_system_id = vcs_system_id
        self.vcs_system_last_updated = vcs_system_last_updated
        self.last_commit_date = last_commit_date
        self.proc_name = name

    def isUpdated(self, mongo_commit, commit):
        """ Checks if the commit has any update
        Return False if nothing changed
        """
        branch_list = self.create_branch_list(commit.branches)
        if branch_list is not None:
            branch_list.sort()

        mongoBranch = []
        if mongo_commit.branches:
            mongoBranch = list(mongo_commit.branches)
            if mongoBranch:
                mongoBranch.sort()
        if mongoBranch != branch_list:
            return True

        return False

    def run(self):
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
        while True:
            commit = self.queue.get()
            logger.debug("Process %s is processing commit with hash %s." %
                         (self.proc_name, commit.id))

            # Try to get the commit
            isNew = False
            try:
                mongo_commit = Commit.objects(
                    vcs_system_id=self.vcs_system_id, revision_hash=commit.id).get()
            except DoesNotExist:
                mongo_commit = Commit(
                    vcs_system_id=self.vcs_system_id,
                    revision_hash=commit.id
                ).save()
                isNew = True

            logger.debug("Process %s is creating tags for commit with hash %s." % (
                self.proc_name, commit.id))
            self.create_tags(mongo_commit, commit)

            if isNew or self.isUpdated(mongo_commit, commit):
                self.set_whole_commit(mongo_commit, commit)
                # Save Revision object
                mongo_commit.save()
                logger.debug("Process %s saved commit with hash %s. Queue size: %d" % (
                    self.proc_name, commit.id, self.queue.qsize()))

            self.queue.task_done()

    def set_whole_commit(self, mongo_commit, commit):
        # Create branchlist
        logger.debug("Process %s is creating branches for commit with hash %s." % (
            self.proc_name, commit.id))
        branch_list = self.create_branch_list(commit.branches)

        if branch_list is not None:
            branch_list.sort()
        mongoBranch = list(
            mongo_commit.branches) if mongo_commit.branches else None
        if mongoBranch != None:
            mongoBranch.sort()

        if mongoBranch != None and mongoBranch != branch_list:
            stateDict = {'branches': mongo_commit.branches}
            stateDict['date'] = mongo_commit.modified_date or None

            mongo_commit.previous_states.append(stateDict)

        mongo_commit.branches = branch_list

        # Create people
        logger.debug("Process %s is setting author for commit with hash %s." % (
            self.proc_name, commit.id))
        mongo_commit.author_id = self.create_people(
            commit.author.name, commit.author.email)
        mongo_commit.author_date = commit.authorDate
        mongo_commit.author_date_offset = commit.authorOffset

        logger.debug("Process %s is setting committer for commit with hash %s." % (
            self.proc_name, commit.id))
        mongo_commit.committer_id = self.create_people(
            commit.committer.name, commit.committer.email)
        mongo_commit.committer_date = commit.committerDate
        mongo_commit.committer_date_offset = commit.committerOffset

        # Set parent hashes
        logger.debug("Process %s is setting parents for commit with hash %s." % (
            self.proc_name, commit.id))
        mongo_commit.parents = commit.parents

        # Set message
        logger.debug("Process %s is setting message for commit with hash %s." % (
            self.proc_name, commit.id))
        mongo_commit.message = commit.message

        # Create fileActions
        logger.debug("Process %s is setting file actions for commit with hash %s." % (
            self.proc_name, commit.id))
        self.create_file_actions(commit.changedFiles, mongo_commit.id)

        # Set Date
        mongo_commit.modified_date = self.vcs_system_last_updated

    def create_branch_list(self, branches):
        """Creates a list of the different branch names, where a commit belongs to. We go through the \
        branches property of the class :class:`pyvcsshark.dbmodels.models.CommitModel`, which is a list of \
        different branch objects of class `pyvcsshark.dbmodels.models.CommitModel`

        :param branches: list of objects of class :class:`pyvcsshark.dbmodels.models.BranchModel`
        """
        branch_list = []
        for branch in branches:
            if branch is not None:
                branch_list.append(branch.name)

        if len(branch_list) == 0:
            branch_list = None

        return branch_list

    def create_tags(self, mongo_commit, commit):
        tag_list = []
        commit_id = mongo_commit.id
        tags = commit.tags

        for tag in tags:
            if tag.tagger is not None:
                tagger_id = self.create_people(
                    tag.tagger.name, tag.tagger.email)
                try:
                    logger.debug("Process %s is creating tag %s with tagger." % (
                        self.proc_name, tag.name))
                    mongo_tag = Tag(commit_id=commit_id, name=tag.name, message=tag.message, tagger_id=tagger_id,
                                    date=tag.taggerDate, date_offset=tag.taggerOffset,
                                    vcs_system_id=self.vcs_system_id, stored_at=self.vcs_system_last_updated).save()
                except (DuplicateKeyError, NotUniqueError):
                    logger.debug("Process %s found tag with tagger with name %s." % (
                        self.proc_name, tag.name))
                    mongo_tag = Tag.objects(commit_id=commit_id, name=tag.name) \
                        .only('id', 'name', 'stored_at').get()
            else:
                try:
                    logger.debug("Process %s is creating tag %s." %
                                 (self.proc_name, tag.name))
                    mongo_tag = Tag(commit_id=commit_id, name=tag.name, date=tag.taggerDate,
                                    date_offset=tag.taggerOffset, vcs_system_id=self.vcs_system_id, stored_at=self.vcs_system_last_updated).save()
                except (DuplicateKeyError, NotUniqueError):
                    logger.debug("Process %s is found tag %s." %
                                 (self.proc_name, tag.name))
                    mongo_tag = Tag.objects(commit_id=commit_id, name=tag.name).only(
                        'id', 'name', 'stored_at').get()

            # Check stored_at for Older Records
            mongo_tag_obj = Tag.objects(id=mongo_tag.id).get()
            if mongo_tag_obj.message != tag.message:
                mongo_tag_obj.message = tag.message

            mongo_tag_obj.save()

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
            logger.debug("Process %s is creating person with email %s and name %s." % (
                self.proc_name, email, name))
            people_id = People(name=name, email=email).save().id
        except (DuplicateKeyError, NotUniqueError):
            logger.debug("Process %s found person with email %s and name %s." % (
                self.proc_name, email, name))
            people_id = People.objects(
                name=name, email=email).only('id').get().id
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
                logger.debug("Process %s is creating old file with path %s." % (
                    self.proc_name, file.oldPath))
                try:
                    old_file_id = File(
                        vcs_system_id=self.vcs_system_id, path=file.oldPath).save().id
                except (DuplicateKeyError, NotUniqueError):
                    logger.debug("Process %s found old file with path %s." % (
                        self.proc_name, file.oldPath))
                    old_file_id = File.objects(
                        vcs_system_id=self.vcs_system_id, path=file.oldPath).only('id').get().id

            # Create a new file object
            try:
                logger.debug("Process %s is creating file with path %s." %
                             (self.proc_name, file.path))
                new_file_id = File(
                    vcs_system_id=self.vcs_system_id, path=file.path).save().id
            except (DuplicateKeyError, NotUniqueError):
                logger.debug("Process %s found file with path %s." %
                             (self.proc_name, file.path))
                new_file_id = File.objects(
                    vcs_system_id=self.vcs_system_id, path=file.path).only('id').get().id

            # Create the new file action
            try:
                logger.debug("Process %s is creating file action with file_id %s." % (
                    self.proc_name, new_file_id))
                file_action_id = FileAction.objects(file_id=new_file_id, commit_id=mongo_commit_id,
                                                    parent_revision_hash=file.parent_revision_hash).get().id

                logger.debug("Process %s is deleting all hunks for file action id %s." % (
                    self.proc_name, file_action_id))
                Hunk.objects(file_action_id=file_action_id).all().delete()
            except DoesNotExist:
                file_action_id = FileAction(file_id=new_file_id,
                                            commit_id=mongo_commit_id,
                                            size_at_commit=file.size,
                                            lines_added=file.linesAdded,
                                            lines_deleted=file.linesDeleted,
                                            is_binary=file.isBinary,
                                            mode=file.mode,
                                            old_file_id=old_file_id,
                                            parent_revision_hash=file.parent_revision_hash).save().id

            # Create hunk objects for bulk insert
            logger.debug(
                "Process %s is creating hunks for bulk insert." % self.proc_name)
            hunks = []
            for hunk in file.hunks:
                mongo_hunk = Hunk(file_action_id=file_action_id, new_start=hunk.new_start, new_lines=hunk.new_lines,
                                  old_start=hunk.old_start, old_lines=hunk.old_lines, content=hunk.content)
                hunks.append(mongo_hunk)

            # Get hunk ids from insert if hunks is not empty
            if hunks:
                try:
                    logger.debug("Process %s is inserting hunks..." %
                                 self.proc_name)
                    Hunk.objects.insert(hunks, load_bulk=False)
                except DocumentTooLarge:
                    for hunk in hunks:
                        try:
                            hunk.save()
                        except DocumentTooLarge:
                            logger.info(
                                "Document was too large for commit: %s" % mongo_commit_id)


class RemovedDataSync(multiprocessing.Process):
    """
    It will update deleted objects from repository to database 
    """

    def __init__(self, vcs_system_id, config, name,vcs_system_last_updated):
        multiprocessing.Process.__init__(self)
        uri = create_mongodb_uri_string(config.db_user, config.db_password, config.db_hostname, config.db_port,
                                        config.db_authentication, config.ssl_enabled)

        connect(config.db_database, host=uri, connect=False)
        self.vcs_system_id = vcs_system_id
        self.proc_name = name
        self.config = config
        discovered_path = pygit2.discover_repository(self.config.path)
        self.repository = pygit2.Repository(discovered_path)
        self.vcs_system_last_updated = vcs_system_last_updated

    def sync(self):
        # lookup in mongoDB for all commits
        for mongo_commit in Commit.objects(vcs_system_id=self.vcs_system_id, deleted_at=None):
            git_commit_contain = self.repository.__contains__(
                mongo_commit.revision_hash)
            if git_commit_contain == False:
                mongo_commit.deleted_at = self.vcs_system_last_updated
                mongo_commit.save()

        # Tags Update
        # Get all tags
        regex = re.compile('^refs/tags')
        tags = set(filter(lambda r: regex.match(
            r), self.repository.listall_references()))
        current_tags_list = []
        for tag in tags:
            tagged_commit = self.repository.lookup_reference(tag).peel()
            reference=self.repository.lookup_reference(tag)
            tag_object = self.repository[reference.target.hex]

            # Exclude Blob
            if isinstance(tagged_commit, pygit2.Blob):
                continue

            current_tags_list.append(
                {"tag_name": tag.split("/")[-1], "commit_hash": tagged_commit.hex, "message": getattr(tag_object, 'message', None)})

        for mongo_tag in Tag.objects(vcs_system_id=self.vcs_system_id):
            commit_revision_hash = Commit.objects(id=mongo_tag.commit_id).only(
                'revision_hash').get().revision_hash

            is_found = False
            for tags in current_tags_list:
                if tags['commit_hash'] == commit_revision_hash and tags['tag_name'] == mongo_tag.name:
                    # Tag is recreated, marked as deleted previously
                    if mongo_tag.deleted_at != None:
                        state_object = {
                            "deleted_at": mongo_tag.deleted_at,
                            "stored_at": mongo_tag.stored_at
                        }

                        # Message can be update
                        if mongo_tag.message != tags['message']:
                            state_object['message'] = mongo_tag.message

                        mongo_tag.previous_states.append(state_object)
                        mongo_tag.deleted_at = None
                        mongo_tag.stored_at = self.vcs_system_last_updated
                        mongo_tag.save()

                    is_found = True
                    break

            if is_found == False:
                mongo_tag.deleted_at = self.vcs_system_last_updated
                mongo_tag.save()
    def run(self):
        self.sync()

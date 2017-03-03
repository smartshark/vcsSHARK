import sys
from pymongo.errors import DocumentTooLarge, DuplicateKeyError

from pyvcsshark.datastores.basestore import BaseStore
from mongoengine import connect, DoesNotExist, NotUniqueError
from pycoshark.mongomodels import VCSSystem, Project, Commit, Tag, File, People, FileAction, Hunk
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
    :property NUMBER_OF_PROCESSES: holds the number of processes by calling :func:`multiprocessing.cpu_count`
    :property logger: holds the logging instance, by calling logging.getLogger("store")
    """

    commit_queue = None
    NUMBER_OF_PROCESSES = multiprocessing.cpu_count()

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
        vcs_system_id = VCSSystem.objects(url=repository_url).upsert_one(url=repository_url,
                                                                         repository_type=repository_type,
                                                                         last_updated=datetime.datetime.today(),
                                                                         project_id=project_id).id

        # Get the last commit by date of the project (if there is any)
        last_commit = Commit.objects(vcs_system_id=vcs_system_id)\
            .only('committer_date').order_by('-committer_date').first()

        if last_commit is not None:
            last_commit_date = last_commit.committer_date
        else:
            last_commit_date = None

        # Start worker, they will wait till something comes into the queue and then process it
        for i in range(self.NUMBER_OF_PROCESSES):
            process = CommitStorageProcess(self.commit_queue, vcs_system_id, last_commit_date, config)
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

    def finalize(self):
        """Wait till all commits are processed, by calling a join on the queue"""
        self.commit_queue.join()
        logger.info("Storing Process complete...")
        return


class CommitStorageProcess(multiprocessing.Process):
    """Class that inherits from :class:`multiprocessing.Process` for processing instances of class
    :class:`pyvcsshark.dbmodels.models.CommitModel` \
    and writing it into the mongodb

    :param queue: queue, where the :class:`pyvcsshark.dbmodels.models.CommitModel` are stored in
    :param vcs_system_id: object id of class :class:`bson.objectid.ObjectId` from the vcs system
    :param last_commit_date: object of class :class:`datetime.datetime`, which holds the last commit that was parsed
    :param config: object of class :class:`pyvcsshark.config.Config`, which holds configuration information
    """
    def __init__(self, queue, vcs_system_id, last_commit_date, config):
        multiprocessing.Process.__init__(self)
        uri = create_mongodb_uri_string(config.db_user, config.db_password, config.db_hostname, config.db_port,
                                        config.db_authentication, config.ssl_enabled)
        connect(config.db_database, host=uri, connect=False)
        self.queue = queue
        self.vcs_system_id = vcs_system_id
        self.last_commit_date = last_commit_date

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

            # Check if commitdate > lastcommit date
            if self.last_commit_date is not None and commit.committerDate <= self.last_commit_date:
                mongo_commit = Commit.objects(vcs_system_id=self.vcs_system_id, revision_hash=commit.id).first()

                if mongo_commit is not None:
                    # We have parsed that commit before, now we need to check if branches or tags were changed
                    self.check_and_update_branches_and_tags(commit, mongo_commit)

                    # Nothing more than branches or tags can be changed, therefore we only need to update the commit
                    self.queue.task_done()
                    continue

            # Try to get the commit. If it is already existent, then return directly
            try:
                mongo_commit = Commit.objects(vcs_system_id=self.vcs_system_id, revision_hash=commit.id).get()
            except DoesNotExist:
                mongo_commit = Commit(
                    vcs_system_id=self.vcs_system_id,
                    revision_hash=commit.id
                ).save()

            # Create people
            mongo_commit.author_id = self.create_people(commit.author.name, commit.author.email)
            mongo_commit.author_date = commit.authorDate
            mongo_commit.author_date_offset = commit.authorOffset

            mongo_commit.committer_id = self.create_people(commit.committer.name, commit.committer.email)
            mongo_commit.committer_date = commit.committerDate
            mongo_commit.committer_date_offset = commit.committerOffset

            # Create tags
            self.create_tags(mongo_commit.id, commit.tags)

            # Create branchlist
            mongo_commit.branches = self.create_branch_list(commit.branches)

            # Set parent hashes
            mongo_commit.parents = commit.parents

            # Set message
            mongo_commit.message = commit.message

            # Create fileActions
            self.create_file_actions(commit.changedFiles, mongo_commit.id)

            # Save Revision object#
            mongo_commit.save()

            self.queue.task_done()

    def check_and_update_branches_and_tags(self, commit, mongo_commit):
        """ Method that checks if the commit that was stored in the database has the same
        branches and tags as the commit which is processed at the moment.

        :param commit: object of class :class:`pyvcsshark.dbmodels.models.CommitModel`.
        :param mongo_commit: object of the commit class from the pycoshark library (stored in MongoDB)

        .. NOTE:: We use the project id and the revision hash to find the commit in the datastore.
        """

        old_tags = list(Tag.objects(commit_id=mongo_commit.id).all())

        # Directly creates the new tags and associates it with the new commit
        new_tags = self.create_tags(mongo_commit.id, commit.tags)

        # If they are not equal, we need to delete old tags
        if old_tags != new_tags:
            for old_tag in old_tags:
                if old_tag not in new_tags:
                    Tag.objects(id=old_tag.id).delete()

        # If they are not equal we need to update the commit
        old_branches = set(mongo_commit.branches)
        new_branches = set(self.create_branch_list(commit.branches))
        if old_branches != new_branches:
            mongo_commit.update(branches=new_branches)

    def create_branch_list(self, branches):
        """Creates a list of the different branch names, where a commit belongs to. We go through the \
        branches property of the class :class:`pyvcsshark.dbmodels.models.CommitModel`, which is a list of \
        different branch objects of class `pyvcsshark.dbmodels.models.CommitModel`

        :param branches: list of objects of class :class:`pyvcsshark.dbmodels.models.BranchModel`
        """
        branch_list = []
        for branch in branches:
            branch_list.append(branch.name)

        return branch_list

    def create_tags(self, commit_id, tags):
        tag_list = []
        for tag in tags:
            if tag.tagger is not None:
                tagger_id = self.create_people(tag.tagger.name, tag.tagger.email)
                try:
                    mongo_tag = Tag(commit_id=commit_id, name=tag.name, message=tag.message, tagger_id=tagger_id,
                                    date=tag.taggerDate, date_offset=tag.taggerOffset,
                                    vcs_system_id=self.vcs_system_id).save()
                except (DuplicateKeyError, NotUniqueError):
                    mongo_tag = Tag.objects(commit_id=commit_id, name=tag.name) \
                        .only('id', 'name').get()
            else:
                try:
                    mongo_tag = Tag(commit_id=commit_id, name=tag.name, date=tag.taggerDate,
                                    date_offset=tag.taggerOffset, vcs_system_id=self.vcs_system_id).save()
                except (DuplicateKeyError, NotUniqueError):
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
            people_id = People(name=name, email=email).save().id
        except (DuplicateKeyError, NotUniqueError):
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
                try:
                    old_file_id = File(vcs_system_id=self.vcs_system_id, path=file.oldPath).save().id
                except (DuplicateKeyError, NotUniqueError):
                    old_file_id = File.objects(vcs_system_id=self.vcs_system_id, path=file.oldPath).only('id').get().id

            # Create a new file object
            try:
                new_file_id = File(vcs_system_id=self.vcs_system_id, path=file.path).save().id
            except (DuplicateKeyError, NotUniqueError):
                new_file_id = File.objects(vcs_system_id=self.vcs_system_id, path=file.path).only('id').get().id

            # Create the new file action
            file_action = FileAction(file_id=new_file_id,
                                     commit_id=mongo_commit_id,
                                     size_at_commit=file.size,
                                     lines_added=file.linesAdded,
                                     lines_deleted=file.linesDeleted,
                                     is_binary=file.isBinary,
                                     mode=file.mode,
                                     old_file_id=old_file_id).save()

            # Create hunk objects for bulk insert
            hunks = []
            for hunk in file.hunks:
                mongo_hunk = Hunk(file_action_id=file_action.id, new_start=hunk.new_start, new_lines=hunk.new_lines,
                                  old_start=hunk.old_start, old_lines=hunk.old_lines, content=hunk.content)
                hunks.append(mongo_hunk)

            # Get hunk ids from insert if hunks is not empty
            if hunks:
                try:
                    Hunk.objects.insert(hunks, load_bulk=False)
                except DocumentTooLarge:
                    for hunk in hunks:
                        try:
                            hunk.save()
                        except DocumentTooLarge:
                            logger.info("Document was too large for commit: %s" % mongo_commit_id)

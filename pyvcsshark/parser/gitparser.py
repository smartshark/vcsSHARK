import sys

from pyvcsshark.parser.baseparser import BaseParser
import pygit2
import logging
import re
import uuid
import multiprocessing

from pyvcsshark.parser.models import BranchModel, PeopleModel, TagModel, FileModel, CommitModel, Hunk, BranchTipModel


class GitParser(BaseParser):
    """ Parser for git repositories. The general parsing process is described in
    :func:`pyvcsshark.parser.gitparser.GitParser.parse`.
    
    :property SIMILARITY_THRESHOLD: sets the threshold for deciding if a file is similar to another. Default: 50%
    :func:`multiprocessing.cpu_count()`.
    :property repository: object of class :class:`pygit2.Repository`, which represents the repository
    :property commits_to_be_processed: dictionary that is set up the following way: \
    commits_to_be_processed = {'<revisionHash>' : {'branches' : set(), 'tags' : []}}, where <revisionHash> must be\
    replaced with the actual hash. Therefore, this dictionary holds information about every revision and which branches\
     this revision belongs to and which tags it has.
    :property logger: logger, which is acquired via logging.getLogger("parser")
    :property datastore: datastore, where the commits should be saved to
    :property commit_queue: object of class :class:`multiprocessing.JoinableQueue`, where commits are stored in that\
    can be parsed
    
    """
    
    # Includes rename and copy threshold, 50% is the default git threshold
    SIMILARITY_THRESHOLD = 50

    def __init__(self):
        self.repository = None
        self.commits_to_be_processed = {}
        self.logger = logging.getLogger("parser")
        self.datastore = None

        self.commit_queue = multiprocessing.JoinableQueue()

    @property
    def repository_type(self):
        return 'git'

    def get_project_url(self):
        """ Returns the url of the project, which is processed """
        url = "local/"+str(uuid.uuid4())
        try:
            url = self.repository.remotes["origin"].url
        except KeyError:
            # repository is only local
            pass
        
        return url

    def finalize(self):
        """Finalization process for parser"""
        return

    def detect(self, repository_path):
        """Try to detect the repository, if its not there an exception is raised and therfore false can be returned"""
        try:
            discovered_path = pygit2.discover_repository(repository_path)
            self.repository = pygit2.Repository(discovered_path)
            return True
        except Exception:
            return False

    def add_branch(self, commit_hash, branch):
        """ Does two things: First it adds the commitHash to the commitqueue, so that the parsing processes can process this commit. Second it
        creates objects of type :class:`pyvcsshark.parser.models.BranchModel` and stores it in the dictionary.

        :param commit_hash: revision hash of the commit to be processed
        :param branch: branch that should be added for the commit
        """
        string_commit_hash = str(commit_hash)

        if branch is None:
            branch_model = None
        else:
            branch_model = BranchModel(branch)

        # If the commit is already in the dict, we only need to append the branch (because then it was already parsed)
        if string_commit_hash in self.commits_to_be_processed:
            self.commits_to_be_processed[string_commit_hash]['branches'].add(branch_model)
        else:
            self.commit_queue.put(string_commit_hash)
            self.commits_to_be_processed[string_commit_hash] = {'branches': {branch_model}, 'tags': []}

    def add_tag(self, tagged_commit, tag_name, tag_object):
        """
        Creates objects of type :class:`pyvcsshark.parser.models.TagModel` and stores it in the dictionary mentioned above.

        :param tagged_commit: revision hash of the commit to be processed
        :param tag_name: name of the tag that should be added
        :param tag_object: in git it is possible to annotate tags. If a tag is annotated,
         we get a tag object of class :class:`pygit2.Tag`


        .. NOTE:: It can happen, that people committed to a tag and therefore created \
        a "tag-branch" which is normally not possible in git. Therefore, we go through all tags and check \
        if they respond to a commit, which is already in the dictionary. \
        If **yes** -> we **tag** that commit \
        If **no** -> we **ignore** it
        """
        commit_id = str(tagged_commit.id)
        tag_name = tag_name.split("/")[-1]

        # If we have an annotated tag, get all the information we can out of it
        if isinstance(tag_object, pygit2.Tag):

            # in some cases (jspwiki) there are taggers where the name or email contains non utf-8 chars.
            # In these cases we replace them with the utf-8 replacement character
            try:
                name = tag_object.tagger.name
            except UnicodeDecodeError as e:
                name = tag_object.tagger.raw_name.decode('utf-8', 'replace')
            try:
                email = tag_object.tagger.email
            except UnicodeDecodeError as e:
                email = tag_object.tagger.raw_email.decode('utf-8', 'replace')

            people_model = PeopleModel(name, email)
            tag_model = TagModel(tag_name, getattr(tag_object, 'message', None), people_model,
                                 tag_object.tagger.time, tag_object.tagger.offset)
        else:
            tag_model = TagModel(tag_name)

        # As it can happen that we have commits with tags that are not on any branch (e.g. project Zookeeper), we need
        # to take care of that here
        if commit_id in self.commits_to_be_processed:
            self.commits_to_be_processed[commit_id]['tags'].append(tag_model)
        else:
            self.commits_to_be_processed[commit_id] = {'branches': set([]), 'tags': [tag_model]}
            self.commit_queue.put(commit_id)

    def _set_branch_tips(self, branches):
        """This sets the tips (last commits) for all remote branches.

        Normally we would also multiprocess here but as this is a quick operation we do not need
        the additional overhead of defining a new BranchParserProcess.
        """
        self.branches = {}
        for branch_name in list(self.repository.branches.remote):
            if str(branch_name).lower().startswith('origin/'):
                branch = self.repository.branches.remote[branch_name]
                if branch_name != 'origin/HEAD':
                    # print('head: {}'.format(branch.target.replace('refs/remotes/', ''))
                    self.branches[branch_name] = {'target': str(branch.target), 'is_origin_head': False}

        # set origin_head we know its there and that it has a target that we also know
        om = self.repository.branches['origin/HEAD']
        om_target = om.target.replace('refs/remotes/', '')
        self.branches[om_target]['is_origin_head'] = True

    def initialize(self):
        """
        Initializes the parser. It gets all the branch and tag information and puts it into two different
        locations: First the commit id is put into the commitqueue for the processing with the parsing processes.
        Second a dictionary is created, which holds the information of which branches a commit is on and which tags it
        has
        """
        # Get all references (branches, tags)
        references = set(self.repository.listall_references())

        # Get all tags
        regex = re.compile('^refs/tags')
        tags = set(filter(lambda r: regex.match(r), self.repository.listall_references()))

        # Get all branches
        branches = references - tags

        # set all tips for every branch
        self._set_branch_tips(branches)

        self.logger.info("Getting branch information...")
        for branch in branches:
            self.logger.info("Getting information from branch %s" % (branch))
            commit = self.repository.lookup_reference(branch).peel()
            # Walk through every child
            for child in self.repository.walk(commit.id,
                                              pygit2.GIT_SORT_TIME | pygit2.GIT_SORT_TOPOLOGICAL):
                self.add_branch(child.id, branch)

        self.logger.info("Getting tags...")
        # Walk through every tag and put the information in the dictionary via the addtag method
        for tag in tags:
            reference = self.repository.lookup_reference(tag)
            tag_object = self.repository[reference.target.hex]
            tagged_commit = self.repository.lookup_reference(tag).peel()

            # we exclude Blobs
            if isinstance(tagged_commit, pygit2.Blob):
                continue

            self.add_tag(tagged_commit, tag, tag_object)

            # The tagged_commit can have children that are not on any branch, but we may need it anyway --> collect it
            # and add it only if we have not collected it before
            try:
                for child in self.repository.walk(tagged_commit.id, pygit2.GIT_SORT_TIME | pygit2.GIT_SORT_TOPOLOGICAL):
                    if str(child.id) not in self.commits_to_be_processed:
                        self.add_branch(child.id, None)
            except ValueError as e:
                # we may hit a tag that does not point to a commit but to a blob, therefore we can not walk over it until libgit implements this
                # see: https://github.com/libgit2/libgit2/issues/3595
                if str(e) != 'ValueError: object is not a committish':  # we do not bail on this we just ignore tags to blobs
                    raise

    def parse(self, repository_path, datastore, cores_per_job):
        """ Parses the repository, which is located at the repository_path and save the parsed commits in the
        datastore, by calling the :func:`pyvcsshark.datastores.basestore.BaseStore.add_commit` method of the chosen
        datastore. It mostly uses pygit2 (see: http://www.pygit2.org/).
        
        The parsing process is divided into several steps:
        
            1. A list of all branches and tags are created
            2. All branches and tags are parsed. So we create dictionary of all commits with their corresponding tags\
            and branches and add all revision hashes to the commitqueue
            3. Add the poison pills for terminating of the parsing process to the commit_queue
            4. Create processes of class :class:`pyvcsshark.parser.gitparser.CommitParserProcess`, which parse all\
            commits.
        
        :param repository_path: Path to the repository
        :param datastore: Datastore used to save the data to
        """
        self.datastore = datastore
        self.logger.info("Starting parsing process...")

        # first we want the branches queue filled
        for name, val in self.branches.items():
            self.datastore.add_branch(BranchTipModel(name, val['target'], val['is_origin_head']))

        # Set up the poison pills
        for i in range(cores_per_job):
            self.commit_queue.put(None)

        # Parsing all commits of the queue
        self.logger.info("Parsing commits...")
        lock = multiprocessing.Lock()
        for i in range(cores_per_job):
            thread = CommitParserProcess(self.commit_queue, self.commits_to_be_processed, self.repository, self.datastore,
                                         lock)
            thread.daemon = True
            thread.start()

        self.commit_queue.join()
        self.logger.info("Parsing complete...")

        return


class CommitParserProcess(multiprocessing.Process):
    """
    A process, which inherits from :class:`multiprocessing.Process`, that will parse the branches it 
    gets from the queue and call the :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` function to add
    the commits
    
    :property logger: logger acquired by calling logging.getLogger("parser")
    
    :param queue: queue, where the different commithashes are stored in
    :param commits_to_be_processed: dictionary, which contains information about the branches and tags of each commit
    :param repository: repository object of type :class:`pygit2.Repository`
    :param datastore: object, that is a subclass of :class:`pyvcsshark.datastores.basestore.BaseStore`
    :param lock: lock that is used, so that only one process at a time is calling \
    the :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` function
    """
    
    def __init__(self, queue, commits_to_be_processed, repository, datastore, lock):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.commits_to_be_processed = commits_to_be_processed
        self.datastore = datastore
        self.logger = logging.getLogger("parser")
        self.repository = repository
        self.lock = lock
        
    def run(self):
        """
        The process gets a commit out of the queue and processes it.
        We use the poisonous pill technique here. Means, our queue has #Processes times "None" in it in the end.
        If a process encounters that None, he will stop and terminate.
        """
        while True:
            next_task = self.queue.get()
            # If process pulls the poisoned pill, he exits
            if next_task is None:
                self.queue.task_done()
                break
            commitHash = pygit2.Oid(hex=next_task)
            commit = self.repository[commitHash]
            self.parse_commit(commit)
            self.queue.task_done()
        return

    def parse_commit(self, commit):
        """ Function for parsing a commit.

        1. changedFiles are created (type: list of :class:`pyvcsshark.parser.models.FileModel`)
        2. author and commiter are created (type: :class:`pyvcsshark.parser.models.PeopleModel`)
        3. parents are added (list of strings)
        4. commit model is created (type: :class:`pyvcsshark.parser.models.CommitModel`)
        5. :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` is called

        :param commit: commit object of type :class:`pygit2.Commit`

        .. NOTE:: The call to :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` is thread/process safe, as a\
        lock is used to regulate the calls
        """
        # we do not want Blobs (for now)
        if commit.__class__.__name__ == 'Blob':
            del self.commits_to_be_processed[str(commit.id)]
            return

        # If there are parents, we need to get the normal changed files, if not we need to get the files for initial
        # commit
        if commit.parents:
            changed_files = []
            for parent in commit.parents:
                changed_files += self.get_changed_files_with_similiarity(parent, commit)
        else:
            changed_files = self.get_changed_files_for_initial_commit(commit)

        string_commit_hash = str(commit.id)

        # Create the different models
        author_model = PeopleModel(commit.author.name, commit.author.email)
        committer_model = PeopleModel(commit.committer.name, commit.committer.email)
        parent_ids = [str(parentId) for parentId in commit.parent_ids]
        commit_model = CommitModel(string_commit_hash, self.commits_to_be_processed[string_commit_hash]['branches'],
                                   self.commits_to_be_processed[string_commit_hash]['tags'], parent_ids,
                                   author_model, committer_model, commit.message, changed_files, commit.author.time,
                                   commit.author.offset, commit.committer.time, commit.committer.offset)
        
        # Make sure, that addCommit is only called by one process at a time
        self.lock.acquire()
        self.datastore.add_commit(commit_model)
        self.lock.release()
        
        del self.commits_to_be_processed[string_commit_hash]

    def create_hunks(self, hunks, initial_commit=False):
        """
        Creates the diff in the unified format (see: https://en.wikipedia.org/wiki/Diff#Unified_format)

        If we have the initial commit, we need to turn around the hunk.* attributes.

        :param hunks: list of objects of class :class:`pygit2.DiffHunk`
        :param initial_commit: indicates if we have an initial commit
        """

        list_of_hunks = []

        for hunk in hunks:
            output = ""
            if initial_commit:
                for line in hunk.lines:
                    output += "%s%s" % ('+', line.content)
                gen_hunk = Hunk(hunk.old_start, hunk.old_lines, hunk.new_start, hunk.new_lines, output)
            else:
                for line in hunk.lines:
                    output += "%s%s" % (line.origin, line.content)
                gen_hunk = Hunk(hunk.new_start, hunk.new_lines, hunk.old_start, hunk.old_lines, output)
            list_of_hunks.append(gen_hunk)
        return list_of_hunks

    def get_changed_files_for_initial_commit(self, commit):
        """
        Special function for the initial commit, as we need to diff against the empty tree. Creates
        the changed files list, where objects of class :class:`pyvcsshark.parser.models.FileModel` are added.
        For every changed file in the initial commit.

        :param commit: commit of type :class:`pygit2.Commit`
        """
        changed_files = []
        diff = commit.tree.diff_to_tree(context_lines=0, interhunk_lines=1)

        for patch in diff:
            changed_file = FileModel(patch.delta.old_file.path, patch.delta.old_file.size,
                                     patch.line_stats[2], patch.line_stats[1],
                                     patch.delta.is_binary, 'A',
                                     self.create_hunks(patch.hunks, True))
            changed_files.append(changed_file)
        return changed_files

    def get_changed_files_with_similiarity(self, parent, commit):
        """ Creates a list of changed files of the class :class:`pyvcsshark.parser.models.FileModel`. For every
        changed file in the commit such an object is created. Furthermore, hunks are saved an each file is tested for
        similarity to detect copy and move operations
        
        :param parent: Object of class :class:`pygit2.Commit`, that represents the parent commit
        :param commit: Object of class :class:`pygit2.Commit`, that represents the child commit
        """
        
        changed_files = []
        diff = self.repository.diff(parent, commit, context_lines=0, interhunk_lines=1)
                            
        opts = pygit2.GIT_DIFF_FIND_RENAMES | pygit2.GIT_DIFF_FIND_COPIES
        diff.find_similar(opts, GitParser.SIMILARITY_THRESHOLD, GitParser.SIMILARITY_THRESHOLD)

        already_checked_file_paths = set()
        for patch in diff:

            # Only if the filepath was not processed before, add new file
            if patch.delta.new_file.path in already_checked_file_paths:
                continue

            # Check change mode
            mode = 'X'
            if patch.delta.status == 1:
                mode = 'A'
            elif patch.delta.status == 2:
                mode = 'D'
            elif patch.delta.status == 3:
                mode = 'M'
            elif patch.delta.status == 4:
                mode = 'R'
            elif patch.delta.status == 5:
                mode = 'C'
            elif patch.delta.status == 6:
                mode = 'I'
            elif patch.delta.status == 7:
                mode = 'U'
            elif patch.delta.status == 8:
                mode = 'T'

            changed_file = FileModel(patch.delta.new_file.path, patch.delta.new_file.size,
                                     patch.line_stats[1], patch.line_stats[2],
                                     patch.delta.is_binary, mode,
                                     self.create_hunks(patch.hunks), parent_revision_hash=str(parent.id))
            
            # only add oldpath if file was copied/renamed
            if mode in ['C', 'R']:
                changed_file.oldPath = patch.delta.old_file.path
    
            already_checked_file_paths.add(patch.delta.new_file.path)
            changed_files.append(changed_file)
        return changed_files

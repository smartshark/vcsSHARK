import sys

from pyvcsshark.parser.baseparser import BaseParser
import pygit2
import logging
import re
import traceback
import uuid
import multiprocessing

from pyvcsshark.parser.models import BranchModel, PeopleModel, TagModel, FileModel, CommitModel, Hunk, BranchTipModel


class GitParser(BaseParser):
    """ Parser for git repositories. The general parsing process is described in
    :func:`pyvcsshark.parser.gitparser.GitParser.parse`.
    
    :property SIMILARITY_THRESHOLD: sets the threshold for deciding if a file is similar to another. Default: 50%
    :property NUMBER_OF_PROCESSES: number of processes for the parsing process. Calls \
    :func:`multiprocessing.cpu_count()`.
    :property repository: object of class :class:`pygit2.Repository`, which represents the repository
    :property commit_info: dictionary that is set up the following way: \
    commit_info = {'<revisionHash>' : {'branches' : set(), 'tags' : []}}, where <revisionHash> must be\
    replaced with the actual hash. Therefore, this dictionary holds information about every revision and which branches\
     this revision belongs to and which tags it has.
    :property logger: logger, which is acquired via logging.getLogger("parser")
    :property datastore: datastore, where the commits should be saved to
    """
    
    # Includes rename and copy threshold, 50% is the default git threshold
    SIMILARITY_THRESHOLD = 50
    NUMBER_OF_PROCESSES = multiprocessing.cpu_count()

    def __init__(self):
        self.repository = None
        self.commit_info = {}
        self.logger = logging.getLogger("parser")
        self.datastore = None


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
            self.discovered_path = pygit2.discover_repository(repository_path)
            self.repository = pygit2.Repository(self.discovered_path)
            return True
        except Exception:
            return False

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
            people_model = PeopleModel(tag_object.tagger.name, tag_object.tagger.email)
            tag_model = TagModel(tag_name, getattr(tag_object, 'message', None), people_model,
                                 tag_object.tagger.time, tag_object.tagger.offset)
        else:
            tag_model = TagModel(tag_name)

        # As it can happen that we have commits with tags that are not on any branch (e.g. project Zookeeper), we need
        # to take care of that here
        self.commit_info[commit_id]['tags'].append(tag_model)

    def _set_branch_tips(self, branches):
        """This sets the tips (last commits) for all remote branches.

        Normally we would also multiprocess here but as this is a quick operation we do not need
        the additional overhead of defining a new BranchParserProcess.
        """
        self.branches = {}
        regex = re.compile('^refs/remotes/origin/')
        for branch in filter(lambda b: regex.match(b.name), branches):
            branch_name = branch.name.replace('refs/remotes/', '')
            if branch_name != 'origin/HEAD':
                self.branches[branch_name] = {'target': str(branch.target), 'is_origin_head': False}

        # set origin_head we know its there and that it has a target that we also know
        om = self.repository.branches['origin/HEAD']
        om_target = om.target.replace('refs/remotes/', '')
        self.branches[om_target]['is_origin_head'] = True

    def _walk(self, commit, func):
        """
        Calls func for each commit that is encountered by topologically walking
        the repository from the given commit
        """
        for child in self.repository.walk(commit.id,
            pygit2.GIT_SORT_TIME | pygit2.GIT_SORT_TOPOLOGICAL):
            func(str(child.id))

    def initialize(self):
        """
        Collects information for the parser.
        For each branch and tag the repository is walked topologically. Each
        found commit is added to the commit list.
        Additionally for each commit it's tags a branches it belongs to are
        saved to the commit_info dictionary.
        """
        # Get all references (branches, tags)
        references = set(self.repository.listall_reference_objects())
        self.logger.info("Found {} references...".format(len(references)))

        # Get all tags
        regex = re.compile(r'^refs/tags')
        tags = set(filter(lambda r: regex.match(r.name), references))

        # Get all branches
        branches = references - tags

        # Add all commits
        pool = multiprocessing.Pool(
            processes=self.NUMBER_OF_PROCESSES,
            initializer=_initialize_oid_process,
            initargs=[self.discovered_path])
        oids = list(map(lambda oid: str(oid), self.repository))
        commits = pool.map(_process_oid, oids)
        commits = list(filter(lambda obj: obj is not None, commits))
        pool.close()
        pool.join()
        for commit in commits:
            self.commit_info.setdefault(commit, {'branches': set([]), 'tags': []})

        # set all tips for every branch
        self._set_branch_tips(branches)

        if not self.config.no_commit_branch_info:
            self.logger.info("Processing branches...")
            count = len(branches)
            for i, branch in enumerate(branches):
                branch_name = branch.name
                self.logger.info("({}/{}) {}".format(i + 1, count, branch_name))

                commit = branch.peel()
                branch_model = BranchModel(branch_name)
                self._walk(commit, lambda id: self.commit_info[id]['branches'].add(branch_model))

        # Walk through every tag and put the information in the dictionary via the addtag method
        self.logger.info("Getting tags...")
        for tag in tags:
            tag_name = tag.name
            tagged_commit = tag.peel()
            self.add_tag(tagged_commit, tag_name, tag.target)

    def parse(self, repository_path, datastore):
        """ Parses the repository, which is located at the repository_path and save the parsed commits in the
        datastore, by calling the :func:`pyvcsshark.datastores.basestore.BaseStore.add_commit` method of the chosen
        datastore. It mostly uses pygit2 (see: http://www.pygit2.org/).
        
        The parsing process is divided into several steps:

            1. A list of all branches and tags are created (see GitParser.initialize)
            2. All branches and tags are parsed. So we create dictionary of all commits with their corresponding tags\
            and branches and add all revision hashes to the commit list (see GitParser.initialize)
            3. Create processes of class :class:`pyvcsshark.parser.gitparser.CommitParserProcess`, which parse all\
            commits.
        
        :param repository_path: Path to the repository
        :param datastore: Datastore used to save the data to
        """
        self.datastore = datastore
        self.logger.info("Starting parsing process...")

        # first we want the branches queue filled
        for name, val in self.branches.items():
            self.datastore.add_branch(BranchTipModel(name, val['target'], val['is_origin_head']))

        self.logger.info("Parsing {} commits...".format(len(self.commit_info.keys())))

        # Lock for synchronizing the processes access to the datastores
        lock = multiprocessing.Lock()

        # Use a pool.map to parallelize parsing of the commits
        # Map submits chunks of size chunksize to each process as a single task,
        # thus maxtasksperchild is set to 1.
        commits_per_process=100
        pool = multiprocessing.Pool(
            processes=self.NUMBER_OF_PROCESSES,
            initializer=_initialize_commit_parser_process,
            initargs=(self.config, self.discovered_path, self.datastore, lock),
            maxtasksperchild=1)
        pool.map(_parse_commit, self.commit_info.items(), chunksize=commits_per_process)
        pool.close()
        pool.join()

        self.logger.info("Parsing complete...")

        return

crawler_repository = None
def _initialize_oid_process(discovered_path):
    global crawler_repository
    crawler_repository = pygit2.Repository(discovered_path)

def _process_oid(oid):
    global crawler_repository
    if crawler_repository[oid].type == pygit2.GIT_OBJ_COMMIT:
        return str(oid)

commit_parser = None
def _initialize_commit_parser_process(config, discovered_path, datastore, lock):
    global commit_parser
    commit_parser = CommitParser(config, discovered_path, datastore, lock)

def _parse_commit(commit):
    try:
        global commit_parser
        commit_parser.parse(commit[0], commit[1])
    except Exception as e:
        traceback.print_exc()
        raise
    except:
        print('Parsing commit failed due to non-Exception exception!')
        raise

class CommitParser():
    """
    A class that provides an API for parsing commits.
    A single commit can be parsed by calling :fund:`pyvcsshark.parser.gitparser.CommitParser.parse`.
    Each parsed commit is submitted to the given datastore via
    :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit`.

    :property logger: logger acquired by calling logging.getLogger("parser")

    :param config: configuration of type :class:`pyvcsshark.config.Config`
    :param discovered_path: path to the repository
    :param datastore: object, that is a subclass of :class:`pyvcsshark.datastores.basestore.BaseStore`
    :param lock: lock that is used, so that only one process at a time is calling \
    the :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` function
    """

    def __init__(self, config, discovered_path, datastore, lock):
        self.config = config
        self.discovered_path = discovered_path
        self.datastore = datastore
        self.lock = lock

        self.datastore.register_subprocess()
        self.repository = pygit2.Repository(self.discovered_path)
        self.logger = logging.getLogger("parser")

    def parse(self, commit_oid, commit_info):
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
        # if the per commit branch info and hunks are not parsed
        # and the commit exists in the database it can be skipped
        # as commit metadata cannot change without also changing
        # the commit hash
        if self.config.no_commit_branch_info \
            and self.config.no_hunks \
            and self.datastore.contains_commit(commit_oid):
            return

        commit_hash = pygit2.Oid(hex=commit_oid)
        commit = self.repository[commit_hash]

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
        branches = commit_info['branches']
        branches = branches if not len(branches) == 0 else None
        commit_model = CommitModel(string_commit_hash, branches,
                                   commit_info['tags'], parent_ids,
                                   author_model, committer_model, commit.message, changed_files, commit.author.time,
                                   commit.author.offset, commit.committer.time, commit.committer.offset)
        
        # Make sure, that addCommit is only called by one process at a time
        self.lock.acquire()
        self.datastore.add_commit(commit_model)
        self.lock.release()

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
            hunks = self.create_hunks(patch.hunks, True) if not self.config.no_hunks else None
            changed_file = FileModel(patch.delta.old_file.path, patch.delta.old_file.size,
                                     patch.line_stats[2], patch.line_stats[1],
                                     patch.delta.is_binary, 'A', hunks)
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
            if patch.delta.status == pygit2.GIT_DELTA_ADDED:
                mode = 'A'
            elif patch.delta.status == pygit2.GIT_DELTA_DELETED:
                mode = 'D'
            elif patch.delta.status == pygit2.GIT_DELTA_MODIFIED:
                mode = 'M'
            elif patch.delta.status == pygit2.GIT_DELTA_RENAMED:
                mode = 'R'
            elif patch.delta.status == pygit2.GIT_DELTA_COPIED:
                mode = 'C'
            elif patch.delta.status == pygit2.GIT_DELTA_IGNORED:
                mode = 'I'
            elif patch.delta.status == pygit2.GIT_DELTA_UNTRACKED:
                mode = 'U'
            elif patch.delta.status == pygit2.GIT_DELTA_TYPECHANGE:
                mode = 'T'

            hunks = self.create_hunks(patch.hunks) if not self.config.no_hunks else None
            changed_file = FileModel(patch.delta.new_file.path, patch.delta.new_file.size,
                                     patch.line_stats[1], patch.line_stats[2],
                                     patch.delta.is_binary, mode, hunks)

            # only add oldpath if file was copied/renamed
            if mode in ['C', 'R']:
                changed_file.oldPath = patch.delta.old_file.path
    
            already_checked_file_paths.add(patch.delta.new_file.path)
            changed_files.append(changed_file)
        return changed_files

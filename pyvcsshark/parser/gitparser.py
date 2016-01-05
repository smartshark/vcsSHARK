from pyvcsshark.parser.baseparser import BaseParser
import threading
import pygit2
import logging
import re
import math
import queue
import multiprocessing
from collections import Counter
from pprint import pprint
from pyvcsshark.dbmodels.models import BranchModel, PeopleModel, TagModel,\
    FileModel, CommitModel

class GitParser(BaseParser):
    """ Parser for git repositories. The general parsing process is described in :func:`pyvcsshark.parser.gitparser.GitParser.parse`.
    
    :property SIMILARITY_THRESHOLD: sets the threshold for deciding if a file is similar to another. Default: 50%
    :property NUMBER_OF_PROCESSES: number of processes for the parsing process. Calls :func:`multiprocessing.cpu_count()`.
    :property repository: object of class :class:`pygit2.Repository`, which represents the repository
    :property commitsToBeProcessed: dictionary that is set up the following way: \
    commitsToBeProcessed = {'<revisionHash>' : {'branches' : set(), 'tags' : []}}, where <revisionHash> must be replaced with the actual hash. Therefore, \
    this dictionary holds information about every revision and which branches this revision belongs to and which tags it has.
        
    :property logger: logger, which is acquired via logging.getLogger("parser")
    :property datastore: datestore, where the commits should be saved to
    :property commitqueue: object of class :class:`multiprocessing.JoinableQueue`, where commits are stored in that can be parsed
    
    """
    
    # Includes rename and copy threshold, 50% is the default git threshold
    SIMILARITY_THRESHOLD = 50
    NUMBER_OF_PROCESSES = multiprocessing.cpu_count()

    def __init__(self):
        self.repository = None
        self.commitsToBeProcessed = {}
        self.logger = logging.getLogger("parser")
        self.datastore = None
       
        self.commitQueue = multiprocessing.JoinableQueue()
        
    @property   
    def repositoryType(self):
        return 'git'
    
    def getProjectName(self):
        """ Returns the name of the project, which is processed"""
        remoteURL = self.getProjectURL()
        if(remoteURL.endswith(".git")) :
            lastPart = remoteURL.rsplit('/',1)[-1]
            return lastPart.rsplit('.', 1)[0]
        else:
            return remoteURL.rsplit('/',1)[-1]

    def getProjectURL(self):
        """ Returns the url of the project, which is processed """
        return self.repository.remotes["origin"].url
        
        
    #def initialize(self):
    #    """Initialization process for parser"""
    #    return
    
    def finalize(self):
        """Finalization process for paser"""
        return
  
    def detect(self, repositoryPath):
        """Try to detect the repository, if its not there an exception is raised and therfore false can be returned"""
        try:
            pathToRepository = pygit2.discover_repository(repositoryPath)
            self.repository = pygit2.Repository(pathToRepository)
            return True
        except Exception:
            return False


    def addBranch(self, commitHash, branch):
        """ Does two things: First it adds the commitHash to the commitqueue, so that the parsing processes can process this commit. Second it
        creates objects of type :class:`pyvcsshark.dbmodels.models.BranchModel` and stores it in the dictionary.
        
        :param commitHash: revision hash of the commit to be processed
        :param branch: branch that should be added for the commit
        """
        strCommitHash = str(commitHash)
        
        branchModel = BranchModel(branch)
        
        # If the commit is already in the dict, we only need to append the branch (because then it was already parsed)
        if(strCommitHash in self.commitsToBeProcessed):
            self.commitsToBeProcessed[strCommitHash]['branches'].add(branchModel)
        else:
            self.commitQueue.put(strCommitHash)
            self.commitsToBeProcessed[strCommitHash] = {
                                           'branches' : set([branchModel]),
                                           'tags' : []
                                           }

    def addTag(self, taggedCommit, tagName, tagObject):
        """
        Creates objects of type :class:`pyvcsshark.dbmodels.models.TagModel` and stores it in the dictionary mentioned above. 
        
        
        :param taggedCommit: revision hash of the commit to be processed
        :param tagName: name of the tag that should be added
        :param tagObject: in git it is possible to annotate tags. If a tag is annottated, we get a tag object of class :class:`pygit2.Tag`

        
        .. NOTE:: It can happen, that people committed to a tag and therefore created \
        a "tag-branch" which is normally not possible in git. Therefore, we go through all tags and check \
        if they respond to a commit, which is already in the dictionary. \
        If **yes** -> we **tag** that commit \
        If **no** -> we **ignore** it
        """

        
        commitId = str(taggedCommit.id)
        
        tagName = tagName.split("/")[-1]
                
        
        if(commitId in self.commitsToBeProcessed):
            
            # If we have an annotated tag, get all the information we can out of it
            if(isinstance(tagObject, pygit2.Tag)):
                peopleModel = PeopleModel(tagObject.tagger.name, tagObject.tagger.email)
                tagModel = TagModel(tagName, getattr(tagObject, 'message', None), peopleModel,  tagObject.tagger.time, tagObject.tagger.offset)
            else:
                tagModel = TagModel(tagName)
                
            self.commitsToBeProcessed[commitId]['tags'].append(tagModel)

          
    def initialize(self):
        """ Initializes the parser. It gets all the branch and tag information and puts it into two different locations: First the commit id
        is put into the commitqueue for the processing with the parsing processes. Second a dictionary is created, which holds the information of
        which branches a commit is on and which tags it has
        """
        # Get all references (branches, tags)
        references = set(self.repository.listall_references())
        
        # Get all tags
        regex = re.compile('^refs/tags')
        tags = set(filter(lambda r: regex.match(r), self.repository.listall_references()))
        
        # Get all branches
        branches = references-tags

        self.logger.info("Getting branch information...")
        for branch in branches:
            self.logger.info("Getting information from branch %s" % (branch))
            commit = self.repository.lookup_reference(branch).peel()
            # Walk through every child
            for child in self.repository.walk(commit.id, 
                                              pygit2.GIT_SORT_TIME | pygit2.GIT_SORT_TOPOLOGICAL):
                self.addBranch(child.id, branch)
                
        self.logger.info("Getting tags...")
    
        # Walk through every tag and put the information in the dictionary via the addtag method
        for tag in tags:
            reference = self.repository.lookup_reference(tag)
            tagObject = self.repository[reference.target.hex]
            taggedCommit = self.repository.lookup_reference(tag).peel()
    
            self.addTag(taggedCommit, tag, tagObject)


               
        
            
    def parse(self, repositoryPath, datastore):
        """ Parses the repository, which is located at the repositoryPath and save the parsed commits in the
        datastore, by calling the :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` method of the chosen datastore. It
        mostly uses pygit2 (see: http://www.pygit2.org/).
        
        The parsing process is divided into several steps:
        
            1. A list of all branches and tags are created
            2. All branches and tags are parsed. So we create dictionary of all commits with their corresponding tags and branches and add all \
        revision hashes to the commitqueue
            3. Add the poison pills for terminating of the parsing process to the commitqueue
            4. Create processes of class :class:`pyvcsshark.parser.gitparser.CommitParserProcess`, which parse all commits.
        
        
        """
        self.datastore = datastore
        self.logger.info("Starting parsing process...")
        
        # Set up the poison pills
        for i in range(self.NUMBER_OF_PROCESSES):
            self.commitQueue.put(None)
        
        # Parsing all commits of the queue
        self.logger.info("Parsing commits...")
        lock = multiprocessing.Lock()
        for i in range(self.NUMBER_OF_PROCESSES):
            thread = CommitParserProcess(self.commitQueue, self.commitsToBeProcessed, self.repository, self.datastore, lock)
            thread.daemon=True
            thread.start()
        
        
        self.commitQueue.join()
        self.logger.info("Parsing complete...")
     
        # Linux "tests"
        #print(self.commitsToBeProcessed['73796d8bf27372e26c2b79881947304c14c2d353'])        
        #print(self.commitsToBeProcessed['9b29c6962b70f232cde4076b1020191e1be0889d'])    
        #print(self.commitsToBeProcessed['6a13feb9c82803e2b815eca72fa7a9f5561d7861']) # 4.3  
        #print(self.commitsToBeProcessed['b953c0d234bc72e8489d3bf51a276c5c4ec85345']) # 4.1
        #print(len(self.commitsToBeProcessed))  
        
        # Samba "tests"      
        #print(self.commits['5f9d3113d73bf87de16d909273dc6eb8c4cc98de']) # only v4-2-test branch
        #print(self.commits['a6f9a793d8b14b9b77729fdeeea34287dd3bda3b']) # 4-2-test and v4-2-stable
        #print(self.commits['392b2d33f243d1c9e25b7c48a38977cfe9924305']) # v4-3-test
        #print(self.commits['c7207e73b116b76f6dd681e0c5a872ae2e702616']) # v4-3-test, master, v4-3-stable + tag tdb-1.3.7
        #print(self.commits['8c8cbd984f8d1f30c7f2dfe3a4d3b472e3245aee']) # same as above + tag samba-4.3.0rc1
        
        # Checkstyle "tests"
        #print(self.commits['3fb7ae8ee60c30f1ad4a5b4b2ad0325075fef6ac']) # tag: release4_4
        #print(self.commits['e2f1c7db68501d767a12fc5d99a14dd036ce400b']) # branch: build-helper-maven-plugin-1-10 + master
        #print(self.commits['0bf5f793206ca5e219e19b4379f6d46221fe2aea']) # branch: build-helper-maven-plugin-1-10 + master
        #print(self.commits['75989a70bbe0f6f319e7c250b9b10c5b51b8486d']) # branch: i2604-name-checks-format
        #print(self.commits['9817c4fb3c1729772956bb9d37b549e823f4ffba']) # branch: i2604-name-checks-format
        #print(self.commits['f52306ff7799ea2b2e4d99fba7040a11b186d68a']) # branch: i2604-name-checks-format + master + build-helper
        #print(self.commits['753bc06c7aa24cb6be8d23afb6b4dc5cf4b5caea']) # branch: master, tag: checkstyle-6.12.1
        
        #print(len(self.commits))
        return


class CommitParserProcess(multiprocessing.Process):
    """
    A process, which inherits from :class:`multiprocessing.Process`, that will parse the branches it 
    gets from the queue and call the :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` function to add
    the commits
    
    :property logger: logger acquired by calling logging.getLogger("parser")
    
    :param queue: queue, where the different commithashes are stored in
    :param commitsToBeProcessed: dictionary, which contains information about the branches and tags of each commit
    :param repository: repository object of type :class:`pygit2.Repository`
    :param datastore: object, that is a subclass of :class:`pyvcsshark.datastores.basestore.BaseStore`
    :param lock: lock that is used, so that only one process at a time is calling the :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` function
    """
    
    def __init__(self, queue, commitsToBeProcessed, repository, datastore, lock):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.commitsToBeProcessed = commitsToBeProcessed
        self.datastore = datastore
        self.logger = logging.getLogger("parser")
        self.repository = repository
        self.lock = lock
        
    def run(self):
        """
        The process gets a commit out of the queue and processes it.
        We use the poisonous pill technique here. Means, our queue has #Processes times "None" in it in the end.
        If a process encouters that None, he will stop and terminate.
        """
        while True:
            nextTask = self.queue.get()
            # If process pulls the poisoned pill, he exits
            if(nextTask is None):
                self.queue.task_done()
                break
            commitHash = pygit2.Oid(hex=nextTask)
            commit = self.repository[commitHash]
            self.parseCommit(commit)
            self.queue.task_done()

               
            
        return
    
    def parseCommit(self, commit):
        """ Function for parsing a commit.
        
        1. changedFiles are created (type: list of :class:`pyvcsshark.dbmodels.models.FileModel`)
        2. author and commiter are created (type: :class:`pyvcsshark.dbmodels.models.PeopleModel`)
        3. parents are added (list of strings)
        4. commit model is created (type: :class:`pyvcsshark.dbmodels.models.CommitModel`)
        5. :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` is called
        
        :param commit: commit object of type :class:`pygit2.Commit`
        
        .. NOTE:: The call to :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` is thread/process safe, as a lock is used to regulate the calls
        """
        changedFiles = []
        # If there are parents, we need to get the normal changed files, if not we need to get the files for initial commit
        if(commit.parents):
            changedFiles = self.getChangedFilesWithSimiliarity(commit.parents[0], commit)
        else:
            changedFiles = self.getChangedFilesForInitialCommit(commit)
            
        strCommitHash = str(commit.id)

        # Create the different models
        authorModel = PeopleModel(commit.author.name, commit.author.email)
        committerModel = PeopleModel(commit.committer.name, commit.committer.email)
        parentIds = [str(parentId) for parentId in commit.parent_ids]
                 
                 
        
        commitModel = CommitModel(strCommitHash, self.commitsToBeProcessed[strCommitHash]['branches'],
                                  self.commitsToBeProcessed[strCommitHash]['tags'], parentIds,
                                  authorModel, committerModel, commit.message, changedFiles, commit.author.time,
                                  commit.author.offset, commit.committer.time, commit.committer.offset)
        # Make sure, that addCommit is only called by one process at a time
        self.lock.acquire()
        self.datastore.addCommit(commitModel)
        self.lock.release()
        del self.commitsToBeProcessed[strCommitHash]
  
    
    def createDiffInUnifiedFormat(self, hunks, initialCommit=False):
        '''
        Creates the diff in the unified format (see: https://en.wikipedia.org/wiki/Diff#Unified_format)
        
        If we have the initial commit, we need to turn around the hunk.* attributes.
        
        :param hunks: list of objects of class :class:`pygit2.DiffHunk`
        :param initialCommit: indicates if we have an initial commit
        '''
        listOfHunks = []
        output = ""
        for hunk in hunks:
            if(initialCommit):
                output = "@@ -%d,%d +%d,%d @@ \n" % (hunk.new_start, hunk.new_lines, hunk.old_start, hunk.old_lines)     
                for line in hunk.lines:
                    output+= "%s%s" %('+', line.content) 
            else:
                output = "@@ -%d,%d +%d,%d @@ \n" % (hunk.old_start, hunk.old_lines, hunk.new_start, hunk.new_lines)
                for line in hunk.lines:
                    output+= "%s%s" %(line.origin, line.content)     
            
            listOfHunks.append(output)
        
        return listOfHunks
            

    def getModeForFile(self, parentTree, childTree, path, similarity):
        '''
        Gets the mode for a file.
        C = Copied/Moved (if similiarity is greater than threshold)
        A = Added (if file is not in parenttree, but in child tree)
        D = Deleted (if file is in parent tree, but not in child tree)
        M = Modified (otherwise)
        
        :param parentTree: object of type :class:`pygit2.Tree` of the parent commit
        :param childTree: object of type :class:`pygit2.Tree` of the child commit
        :param path: path to the file that is analyzed
        :param similarity: similarity of the two files in both trees
        '''    
        if(similarity >= GitParser.SIMILARITY_THRESHOLD):
            return 'C'
        elif(path not in parentTree and path in childTree):
            return 'A'
        elif(path in parentTree and path not in childTree):
            return 'D'
        else:
            return 'M'
        

    def getChangedFilesForInitialCommit(self, commit):
        '''
        Special function for the initial commit, as we need to diff against the empty tree. Creates
        the changed files list, where objects of class :class:`pyvcsshark.dbmodels.models.FileModel` are added.
        For every changed file in the initial commit.
        
        :param commit: commit of type :class:`pygit2.Commit`
        '''
        changedFiles = []
        diff = commit.tree.diff_to_tree()

        for patch in diff:
            changedFile = FileModel(patch.delta.old_file.path, patch.delta.old_file.size,
                                    patch.line_stats[2], patch.line_stats[1],
                                    patch.delta.is_binary, 'A', 
                                    self.createDiffInUnifiedFormat(patch.hunks, True))
            changedFiles.append(changedFile)
        return changedFiles
        
        
    def getChangedFilesWithSimiliarity(self, parent, child): 
        """ Creates a list of changed files of the class :class:`pyvcsshark.dbmodels.models.FileModel`. For every
        changed file in the commit such an object is created. Furthermore, hunks are saved an each file is tested for similarity to
        detect copy and move operations
        
        :param parent: Object of class :class:`pygit2.Commit`, that represents the parent commit
        :param child:  Object of class :class:`pygit2.Commit`, that represents the child commit
        """
        
        changedFiles = []
        diff = self.repository.diff(parent, child)
                            
        opts = pygit2.GIT_DIFF_FIND_RENAMES | pygit2.GIT_DIFF_FIND_COPIES
        diff.find_similar(opts, GitParser.SIMILARITY_THRESHOLD, GitParser.SIMILARITY_THRESHOLD)
                    
        # We need to check for mode "T" for files. We have this mode, if there are >1 patches, which affect the same file
        # Therefore, we first need to check, which file is there more than once
        filePaths = [patch.delta.new_file.path for patch in diff]
        counts = Counter(filePaths)

        alreadyCheckedFilePaths = set()
        for patch in diff:
            # Only if the filepath was not processed before, add new file
            if(patch.delta.new_file.path in alreadyCheckedFilePaths):
                continue
            
            if(counts[patch.delta.new_file.path] > 1):
                mode = 'T'
            else:
                mode = self.getModeForFile(parent.tree, child.tree, patch.delta.new_file.path, patch.delta.similarity)
                
            
            changedFile = FileModel(patch.delta.new_file.path, patch.delta.new_file.size,
                                    patch.line_stats[1], patch.line_stats[2],
                                    patch.delta.is_binary, mode, 
                                    self.createDiffInUnifiedFormat(patch.hunks))
            
            # only add oldpath if file was copied/renamed
            if('C' in mode):
                changedFile.oldPath = patch.delta.old_file.path
    
            alreadyCheckedFilePaths.add(patch.delta.new_file.path)
            changedFiles.append(changedFile)
            
            
        return changedFiles   















    
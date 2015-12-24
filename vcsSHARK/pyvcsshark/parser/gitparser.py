'''
Created on 09.12.2015

@author: fabian
'''
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
    '''
    classdocs
    '''
    
    # Includes rename and copy threshold, 50% is the default git threshold
    SIMILARITY_THRESHOLD = 50
    NUMBER_OF_PROCESSES = multiprocessing.cpu_count()

    def __init__(self):
        '''
        Constructor
        '''
        self.repository = None
        self.commits = {}
        self.commitsToBeProcessed = {}
        self.logger = logging.getLogger("parser")
        self.datastore = None
       
        self.commitQueue = multiprocessing.JoinableQueue()
        
    @property   
    def repositoryType(self):
        return 'git'
    
    def getProjectName(self):
        remoteURL = self.getProjectURL()
        if(remoteURL.endswith(".git")) :
            lastPart = remoteURL.rsplit('/',1)[-1]
            return lastPart.rsplit('.', 1)[0]
        else:
            return remoteURL.rsplit('/',1)[-1]

    def getProjectURL(self):
        return self.repository.remotes["origin"].url
        
        
    def initialize(self):
        """Initialization process for parser"""
        return
    
    def finalize(self):
        """Finalization process for paser"""
        return
  
    def detect(self, repositoryPath):
        '''Try to detect the repository, if its not there an exception is raised'''
        try:
            pathToRepository = pygit2.discover_repository(repositoryPath)
            self.repository = pygit2.Repository(pathToRepository)
            return True
        except Exception:
            return False


    def addBranch(self, commitHash, branch):
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

    def addTag(self, taggedCommit, tag):
        '''
        Go through all tags: Special thing - It can happen, that people committed to a tag and therefore created
        a "tag-branch" which is normally not possible in git. Therefore, we go through all tags and check
        if they respond to a commit, which is already in the dictionary.
        
        If yes -> we tag that commit
        If no -> we ignore it
        '''

        
        commitId = str(taggedCommit.id)
        
        if(commitId in self.commitsToBeProcessed):
            peopleModel = None
            if(hasattr(tag, 'tagger') and tag.tagger is not None):
                peopleModel = PeopleModel(tag.tagger.name, tag.tagger.email, tag.tagger.time, tag.tagger.offset)
            tagModel = TagModel(tag.name, getattr(tag, 'message', None), peopleModel)
            self.commitsToBeProcessed[commitId]['tags'].append(tagModel)

          
    def intializeParsing(self, branches, tags):
        self.logger.info("Getting branch information...")
        for branch in branches:
            self.logger.info("Getting information from branch %s" % (branch))
            commit = self.repository.lookup_reference(branch).peel()
            # Walk through every child
            for child in self.repository.walk(commit.id, 
                                              pygit2.GIT_SORT_TIME | pygit2.GIT_SORT_TOPOLOGICAL):
                self.addBranch(child.id, branch)
                
        self.logger.info("Getting tags...")
    
        for tag in tags:
            reference = self.repository.lookup_reference(tag)
            tagObject = self.repository[reference.target.hex]
            taggedCommit = self.repository.lookup_reference(tag).peel()
            
            if(isinstance(tagObject, pygit2.Tag)):
                self.addTag(taggedCommit, tagObject)
        
            
        
        
    #TODO: Update function - get lastparsed revision, and actual revision
    # Then parse commits of head, till lastparsed revision found -> break
    # it should be okay, if the rest remains untouched
    def parse(self, repositoryPath, datastore):
        self.datastore = datastore
        self.logger.info("Starting parsing process...")

        # Get all references (branches, tags)
        references = set(self.repository.listall_references())
        
        # Get all tags
        regex = re.compile('^refs/tags')
        tags = set(filter(lambda r: regex.match(r), self.repository.listall_references()))
        
        # Get all branches
        branches = references-tags
        
        # First parse all branches and tags. So that we know which commit belongs to which branch and has which tags
        self.intializeParsing(branches, tags)

        
        
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
    A thread that will parse the branches it gets from the queue and fill a dictionary with
    information about which branches a commit is on
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
        '''
            We use the poisonous pill technique here. Means, our queue has #Processes times "None" in it in the end.
            If a process encouters that None, he will stop and terminate. Other thinks, like catching the exception
            from a get_nowait() was not working here.
        '''
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
        changedFiles = []
        if(commit.parents):
            changedFiles = self.getChangedFilesWithSimiliarity(commit.parents[0], commit)
        else:
            changedFiles = self.getChangedFilesForInitialCommit(commit)
            
        strCommitHash = str(commit.id)

        authorModel = PeopleModel(commit.author.name, commit.author.email, commit.author.time, commit.author.offset)
        committerModel = PeopleModel(commit.committer.name, commit.committer.email, commit.committer.time, commit.committer.offset)
        parentIds = [str(parentId) for parentId in commit.parent_ids]
                 
                 
        
        commitModel = CommitModel(strCommitHash, self.commitsToBeProcessed[strCommitHash]['branches'],
                                  self.commitsToBeProcessed[strCommitHash]['tags'], parentIds,
                                  authorModel, committerModel, commit.message, changedFiles)
        self.lock.acquire()
        self.datastore.addCommit(commitModel)
        self.lock.release()
        del self.commitsToBeProcessed[strCommitHash]
  
    
    def createDiffInUnifiedFormat(self, hunks, initialCommit=False):
        '''
        Creates the diff in the unified format (see: https://en.wikipedia.org/wiki/Diff#Unified_format)
        
        If we have the initial commit, we need to turn around the hunk.* attributes
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
        C = Copied/Moved
        A = Added
        D = Deleted
        M = Modified
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
        Special function for the initial commit, as we need to diff against the empty tree
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















    
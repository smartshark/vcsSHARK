'''
Created on 16.12.2015

@author: fabian
'''
from pyvcsshark.datastores.basestore import BaseStore
from pyvcsshark.dbmodels.mongomodels import *
from pymongo import UpdateOne

from mongoengine import connect, DoesNotExist, register_connection
from bson.objectid import ObjectId

import math
import multiprocessing
import logging
import os
import time
import queue
from mongoengine.errors import NotUniqueError

class MongoStore(BaseStore):
    '''
    classdocs
    '''
    
    commitqueue = None
    #NUMBER_OF_PROCESSES = 1
    NUMBER_OF_PROCESSES = multiprocessing.cpu_count()
    logger = logging.getLogger("store")
    
    def __init__(self):
        BaseStore.__init__(self)
        
        
    def initialize(self, dbname, host, port, user , password, projectname, repositoryURL, type=None):
        self.logger.info("Initializing MongoStore...")
        # Create queue for multiprocessing
        self.commitqueue = multiprocessing.JoinableQueue()
        # We define, that the user we authenticate with is in the admin database
        self.logger.info("Connecting to MongoDB...")
        connect(dbname, username=user, password=password, host=host, port=port, authentication_source='admin', connect=False)

        # Update project if project with the same url is already in the mongodb and add if not
        project = Project.objects(url=repositoryURL).upsert_one(url=repositoryURL, repositoryType=type, name=projectname)

        # Start worker, they will wait till something comes into the queue and then process it
        for i in range(self.NUMBER_OF_PROCESSES):
            process = CommitStorageProcess(self.commitqueue, project.id)
            process.daemon=True
            process.start()
        
            
        self.logger.info("Starting storage Process...")
        

    
    @property
    def storeIdentifier(self):
        '''Must return the identifier for the store. This should match the configuration options'''
        return 'mongo'


    def addCommit(self, commitModel):
        '''Add the commit to the datastore (e.g. mongoDB, mySQL, a model, ...). How this is 
        handled depends on the implementation'''
        # add to queue
        self.commitqueue.put(commitModel)
        return

    def deleteAll(self):
        '''Deletes all data of one project from the datastore'''
        return
    
    def finalize(self):
        self.commitqueue.join()
        self.logger.info("Storing Process complete...")
        return
    

class CommitStorageProcess(multiprocessing.Process):
    def __init__(self, queue, projectId):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.projectId = projectId
        
    def run(self):   
        print (os.getpid(), "working")
        #connect('test', username='root', password='root', host='localhost', port=27017, authentication_source='admin')
        while True:
            commit = self.queue.get()

            
            # we need to be careful here, as we need to split up the commit first 
            # and set all the references
            
             
            
           
            
            # Create people 
            authorId = self.createPeople(commit.author.name, commit.author.email)
            committerId = self.createPeople(commit.committer.name, commit.committer.email)
            
            # Create tag list
            tagIds = self.createTagList(commit.tags)
            
           
            
            
            # Create branchlist
            branches = self.createBranchList(commit.branches)
            
            
            # Create fileActions
            fileActionIds = self.createFileActions(commit.changedFiles, commit.id)
            
            
            # Create Revision object#
            '''
            mongoCommit = Commit.objects(projectId = self.projectId, 
                                         revisionHash = commit.id).upsert_one(projectId = self.projectId,
                                                                              revisionHash = commit.id,
                                                                              branches = branches,
                                                                              tagIds = tagIds ,
                                                                              parents=commit.parents,
                                                                              authorId=authorId,
                                                                              authorDate=commit.author.date,
                                                                              authorOffset=commit.author.dateOffset,
                                                                              committerId=committerId,
                                                                              committerDate=commit.committer.date,
                                                                              committerOffset=commit.committer.dateOffset,
                                                                              message=commit.message,
                                                                              fileActionIds= fileActionIds)
            '''
            mongoCommit = Commit(projectId = self.projectId,
                                 revisionHash = commit.id,
                                 branches = branches,
                                 tagIds = tagIds ,
                                 parents=commit.parents,
                                 authorId=authorId,
                                 authorOffset=commit.author.dateOffset,
                                 committerId=committerId,
                                 committerDate=commit.committer.date,
                                 committerOffset=commit.committer.dateOffset,
                                 message=commit.message,
                                 fileActionIds= fileActionIds).save()      

            
            self.queue.task_done()


    def createBranchList(self, branches):
        branchList = []
        for branch in branches:
            branchList.append(branch.name)
            
        return branchList
        
    def createTagList(self, tags):
        tagList = []
        for tag in tags:
            if tag.tagger is not None:
                taggerId = self.createPeople(tag.tagger.name, tag.tagger.email)
                mongoTag = Tag.objects(projectId = self.projectId, name = tag.name).upsert_one(projectId = self.projectId, name=tag.name, message=tag.message, 
                                                                                               taggerId=taggerId, date=tag.tagger.date, offset = tag.tagger.dateOffset)
            else:
                mongoTag = Tag.objects(projectId = self.projectId, name = tag.name).upsert_one(projectId = self.projectId, name= tag.name)
                
            tagList.append(mongoTag.id)
        return tagList
    
    def createPeople(self, name, email):
        mongoPeople = People.objects(name=name, email=email).upsert_one(name=name, email=email)
        return mongoPeople.id
    
    def createFileActions(self, files, revisionHash):
        fileActionList = []
        for file in files:
            oldFileId = None
            if file.oldPath is not None:
                oldFile = File.objects(projectId=self.projectId, path=file.oldPath, name=os.path.basename(file.oldPath)).upsert_one(projectId=self.projectId, 
                                                                                                                                    path=file.oldPath,
                                                                                                                                    name=os.path.basename(file.oldPath))
                oldFileId = oldFile.id
                
            # Create hunk objects for bulk insert
            hunks = []
            for hunk in file.hunks:
                mongoHunk = Hunk(content=hunk)
                hunks.append(mongoHunk)
            
            # Get hunk ids from insert if hunks is not empty
            hunkIds = [] 
            if(hunks):
                hunkIds = Hunk.objects.insert(hunks, load_bulk=False)
    
            
            newFile = File.objects(projectId=self.projectId, path=file.path, name=os.path.basename(file.path)).upsert_one(projectId=self.projectId, 
                                                                                                                          path=file.path,
                                                                                                                          name=os.path.basename(file.path))
            fileAction = FileAction(projectId=self.projectId,
                                        fileId=newFile.id,
                                        revisionHash=revisionHash,
                                        sizeAtCommit=file.size,
                                        linesAdded = file.linesAdded,
                                        linesDeleted = file.linesDeleted,
                                        isBinary = file.isBinary,
                                        mode = file.mode,
                                        hunkIds = hunkIds) 
            fileActionList.append(fileAction)
            
        fileActionIds = [] 
        if(fileActionList):
            fileActionIds = FileAction.objects.insert(fileActionList, load_bulk=False)   
        return fileActionIds 

    
    
    
    
    
        
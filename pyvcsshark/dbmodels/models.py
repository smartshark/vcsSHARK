'''
Created on 18.12.2015

@author: fabian
'''

import datetime

class CommitModel(object):
    '''
    classdocs
    '''
    def __init__(self, id, branches=[], tags=[], parents=[], 
                 author=None, committer=None, message=None, changedFiles=[]):
        '''
        Constructor
        '''
        self.id = id
        self.branches = branches
        self.tags = tags
        self.parents = parents
        self.author = author
        self.committer = committer
        self.message = message
        self.changedFiles = changedFiles
        
    @property
    def branches(self):
        return self._branches
        
    @branches.setter
    def branches(self, value):
        if(value is not None and type(value) is not set):
            raise Exception("Branches must be a list!")
        
        if(value is not None):
            for branch in value:
                if(not isinstance(branch, BranchModel)):
                    raise Exception("Branch is not a Branch model!")
        
        self._branches = value
    
    @property
    def tags(self):
        return self._tags
    
    @tags.setter
    def tags(self, value):
        if(value is not None and type(value) is not list):
            raise Exception("Hunks must be a list!")
        
        if(value is not None):
            for tag in value:
                if(not isinstance(tag, TagModel)):
                    raise Exception("Hunk is not a Hunk model!")
        
        self._tags = value
    
    @property
    def author(self):
        return self._author
    
    @author.setter
    def author(self, value):
        if(value is not None and not isinstance(value, PeopleModel)):
            raise Exception("Author must be of type PeopleModel!")
        
        self._author = value
    
    @property
    def committer(self):
        return self._committer
    
    @committer.setter
    def committer(self, value):
        if(value is not None and not isinstance(value, PeopleModel)):
            raise Exception("Committer must be of type PeopleModel!")
        
        self._committer = value
        
    @property
    def changedFiles(self):
        return self._changedFiles
    
    @changedFiles.setter
    def changedFiles(self, value):
        if(value is not None and type(value) is not list):
            raise Exception("ChangedFiles must be a list!")
        
        if(value is not None):
            for file in value:
                if(not isinstance(file, FileModel)):
                    raise Exception("File must be of type FileModel!")
        
        self._changedFiles = value
        
        

    def __str__(self):
        files = ""
        for file in self.changedFiles:
            files += file.path
            
        branches = ""
        for branch in self.branches:
            branches+=branch.name
            
        tags = ""
        for tag in self.tags:
            tags+=tag.name
        
        return "<CommitHash: %s>, <Branches: %s>, <Tags: %s>, <Parents: %s>, <AuthorName: %s>,"\
               "<AuthorEmail: %s>, <AuthorTime: %s>, <AuthorOffset: %s>, <CommitterName: %s>, "\
                "<CommitterEmail: %s>, <CommitterTime: %s>, <CommitterOffset: %s>, <Message: %s>"\
                "<ChangedFiles: %s>" % (self.id, branches, tags,
                                        ",".join(self.parents), self.author.name, self.author.email,
                                        self.author.date, self.author.dateOffset, self.committer.name,
                                        self.committer.email, self.committer.date, self.committer.dateOffset,
                                        self.message, files)
        
        
        
class FileModel(object):
    def __init__(self, path, size=None, linesAdded=None, linesDeleted=None,
                 isBinary= None, mode=None, hunks=[], oldPath=None):
        '''
        Constructor
        '''
        self.path = path
        self.size = size
        self.linesAdded = linesAdded
        self.linesDeleted = linesDeleted
        self.isBinary = isBinary
        self.mode = mode
        self.hunks = hunks
        self.oldPath = oldPath
        
    @property
    def hunks(self):
        return self._hunks
        
    @hunks.setter
    def hunks(self, value):
        # Check hunks
        if(value is not None and type(value) is not list):
            raise Exception("Hunks must be a list!")
        
        self._hunks = value
        
class TagModel(object):
    def __init__(self, name, message=None, tagger=None):
        '''
        Constructor
        '''
        self.name = name
        self.message = message
        self.tagger = tagger

           
            
    @property
    def tagger(self):
        return self._tagger
    
    @tagger.setter
    def tagger(self, value):
        if(value is not None and not isinstance(value, PeopleModel)):
            raise Exception("Tagger is not a People model!")
        self._tagger = value
            
    
        

class BranchModel(object):
    def __init__(self, name):
        '''
        Constructor
        '''
        self.name = name
        
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash(repr(self))

class PeopleModel(object):
    def __init__(self, name=None, email=None, date=None, dateOffset=None):
        '''
        Constructor
        '''
        self.name = name
        self.date = date
        self.email = email
        self.dateOffset = dateOffset
        
    @property
    def date(self):
        return self._date
    
    @date.setter
    def date(self, value):
        if(value is not None and not isinstance(value, int)):
            raise Exception("Date must be a UNIX timestamp!")
        self._date = datetime.datetime.utcfromtimestamp(value)
        
        
        
        

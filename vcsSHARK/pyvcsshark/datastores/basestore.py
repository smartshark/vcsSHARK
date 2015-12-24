'''
Created on 09.12.2015

@author: fabian
'''

import abc
import os

class BaseStore(metaclass=abc.ABCMeta):
    '''
    Abstract class for the datastores. One must inherit from this class and implement
    the methods to create a new datastore.
    '''
    projectName = None
    projectURL = None
    repositoryType = None
    
    @abc.abstractmethod
    def initialize(self, dbname=None, host=None, port=None, user=None , 
                   password=None, projectname=None, repositoryURL=None, type=None):
        '''Initializes the datastore'''
        return

    @abc.abstractproperty
    def storeIdentifier(self):
        '''Must return the identifier for the store. This should match the configuration options'''
        return

    @abc.abstractmethod
    def addCommit(self, commitModel):
        '''Add the commit to the datastore (e.g. mongoDB, mySQL, a model, ...). How this is 
        handled depends on the implementation. It MUST BE threadsafe! More than one process 
        can be calling addCommit at a time!'''
        return

    @abc.abstractmethod
    def deleteAll(self):
        '''Deletes all data of one project from the datastore'''
        return
    
    @abc.abstractmethod
    def finalize(self):
        '''Is called in the end of the whole program'''
        return


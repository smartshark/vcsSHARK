'''
Created on 09.12.2015

@author: fabian
'''

import abc
import os

class BaseStore(metaclass=abc.ABCMeta):
    """
    Abstract class for the datastores. One must inherit from this class and implement
    the methods to create a new datastore.
    
    Based on pythons abc: :py:mod:`abc`
    
    :property projectName: name of the project, which should be stored
    :property projectURL: url of the repository of the project, which should be stored
    :property repositoryType: type of the repository of the project, which should be stored
    
    
    
    :param metaclass: name of the abstract metaclass
    
    .. NOTE:: If you want to use a logger for your implementation of a datastore you can write::
    
          logger = logging.getLogger("store") 
      
        to get the logger.

    .. NOTE:: It is possible to include datastores, which are not databases like mongoDB or mysql. But you should make \
    sure, that your datastore implementation handels the values which are given to it correctly. 


    """
    projectName = None
    projectURL = None
    repositoryType = None
    
    @abc.abstractmethod
    def initialize(self, dbname=None, host=None, port=None, user=None , 
                   password=None, projectname=None, repositoryURL=None, type=None):
        """Initializes the datastore
        
        :param dbname: name of the database to use
        :param host: name of the host, where the datastore runs on
        :param port: port, where the datastore is listening to
        :param user: user of the datastore (e.g. for authentication)
        :param password: password for the given user
        :param projectname: name of the project, which is to be analyzed
        :param repositoryURL: url of the repository, which is to be analyzed
        :param type: type of the repository, which is to be analyzed (e.g. "git")"""
        
        return

    @abc.abstractproperty
    def storeIdentifier(self):
        """Must return a string identifier for the datastore (e.g. **mongo**) """
        return

    @abc.abstractmethod
    def addCommit(self, commitModel):
        """Add the commit to the datastore. How this is 
        handled depends on the implementation.
        
        :param commitModel: instance of :class:`~pyvcsshark.dbmodels.models.CommitModel`, which includes all important information about the commit"""
        return

    @abc.abstractmethod
    def deleteAll(self):
        """Deletes all data of one project from the datastore"""
        return
    
    @abc.abstractmethod
    def finalize(self):
        """Is called in the end to finalize the datastore (e.g. closing files or connections)"""
        return


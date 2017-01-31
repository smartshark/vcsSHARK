'''
Created on 09.12.2015

@author: fabian
'''

import abc
import os
import pyvcsshark.utils


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
    sure, that your datastore implementation handles the values which are given to it correctly.


    """
    projectName = None
    projectURL = None
    repositoryType = None
    
    @abc.abstractmethod
    def initialize(self, config, repository_url, repository_type):
        """Initializes the datastore
        
        :param config: all configuration
        :param repository_url: url of the repository, which is to be analyzed
        :param repository_type: type of the repository, which is to be analyzed (e.g. "git")
        """
        return

    @abc.abstractproperty
    def store_identifier(self):
        """Must return a string identifier for the datastore (e.g. **mongo**) """
        return

    @abc.abstractmethod
    def add_commit(self, commit_model):
        """Add the commit to the datastore. How this is handled depends on the implementation.
        
        :param commit_model: instance of :class:`~pyvcsshark.dbmodels.models.CommitModel`, which includes all \
        important information about the commit
        
        .. WARNING:: The commits we get here are not sorted. Furthermore, they need to be processed right away or\
            stored in a :class:`~multiprocessing.SimpleQueue`. Storing it in a normal list or dictionary can not be done,\
            as some parser (e.g. GitParser) use multiprocessing to add the commits.
        """
        return
    
    @abc.abstractmethod
    def finalize(self):
        """Is called in the end to finalize the datastore (e.g. closing files or connections)"""
        return

    @staticmethod
    def find_correct_datastore(datastore_identifier):
        """ Finds the correct datastore by looking at the datastore.storeIdentifier property

        :param datastore_identifier: string that represents the correct datastore (e.g. **mongo**)
        """

        # import datastore plugins
        pyvcsshark.utils.find_plugins(os.path.dirname(os.path.realpath(__file__)))
        for sc in BaseStore.__subclasses__():
            datastore = sc()
            if datastore_identifier and datastore_identifier in datastore.store_identifier:
                return datastore
        return None

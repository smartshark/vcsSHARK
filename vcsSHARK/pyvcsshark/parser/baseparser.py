'''
Created on 09.12.2015

@author: fabian
'''

import abc
import os

class BaseParser(metaclass=abc.ABCMeta):
    '''
    classdocs
    '''
    
    
    @abc.abstractproperty
    def repositoryType(self):
        """Must return the type for the given repository"""
        return
    
    @abc.abstractmethod
    def initialize(self):
        """Initialization process for parser"""
        return
    
    @abc.abstractmethod
    def finalize(self):
        """Finalization process for paser"""
        return
    
    
    @abc.abstractmethod
    def detect(self, repositoryPath):
        """Return true if the parser is applicable to the repository"""
        return

    @abc.abstractmethod
    def parse(self, repositoryPath, datastore):
        """Parses the repository"""
        return
    
    @abc.abstractmethod
    def getProjectName(self):
        """Retrieves the project name from the repository. This need to be
        put here, as only the parser is specific to the repository type"""
    
    @abc.abstractmethod
    def getProjectURL(self):
        """Retrieves the project url from the repository. This need to be
        put here, as only the parser is specific to the repository type"""
    
    
    def getImmediateSubdirectories(self, a_dir):
        return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]
        
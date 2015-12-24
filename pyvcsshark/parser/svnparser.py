'''
Created on 09.12.2015

@author: fabian
'''
import abc
from pyvcsshark.parser.baseparser import BaseParser
import logging

class SVNParser(BaseParser):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.logger = logging.getLogger("parser")
        
    @property   
    def repositoryType(self):
        return 'svn'
    
    def getProjectName(self):
        return

    def getProjectURL(self):
        return 
        
    def detect(self, repositoryPath):
        subdirectories = self.getImmediateSubdirectories(repositoryPath)
        
        if(".svn" in subdirectories):
            return True
        else:
            return False
    
    
    
    def initialize(self):
        """Initialization process for parser"""
        return
    
    def finalize(self):
        """Finalization process for paser"""
        return
    
    def parse(self, repositoryPath, datastore):
        return None
    
    
    
    
    
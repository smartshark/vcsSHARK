from pyvcsshark.utils import get_immediate_subdirectories
from pyvcsshark.parser.baseparser import BaseParser
import logging


logger = logging.getLogger("parser")


class SVNParser(BaseParser):
    def __init__(self):
        pass
        
    @property   
    def repository_type(self):
        return 'svn'

    def get_project_url(self):
        return 
        
    def detect(self, repository_path):
        subdirectories = get_immediate_subdirectories(repository_path)
        
        if ".svn" in subdirectories:
            return True
        else:
            return False

    def initialize(self):
        """Initialization process for parser"""
        return
    
    def finalize(self):
        """Finalization process for parser"""
        return
    
    def parse(self, repository_path, datastore, cores_per_job):
        return None
    
    
    
    
    
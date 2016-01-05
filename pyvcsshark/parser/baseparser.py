import abc
import os

class BaseParser(metaclass=abc.ABCMeta):
    """
    Abstract class for the parsers. One must inherit from this class and implement
    the methods to create a new repository parser.
    
    Based on pythons abc: :py:mod:`abc`
    
    :param metaclass: name of the abstract metaclass
    
    .. NOTE:: If you want to use a logger for your implementation of a datastore you can write::
    
          logger = logging.getLogger("parser") 
      
        to get the logger.

    """
    
    
    @abc.abstractproperty
    def repositoryType(self):
        """Must return the type for the given repository. E.g. **git**"""
        return
    
    @abc.abstractmethod
    def initialize(self):
        """Initialization process for parser"""
        return
    
    @abc.abstractmethod
    def finalize(self):
        """Finalization process for parser"""
        return
    
    
    @abc.abstractmethod
    def detect(self, repositoryPath):
        """Return true if the parser is applicable to the repository
        
        :param repositoryPath: path to the repository
        """
        return

    @abc.abstractmethod
    def parse(self, repositoryPath, datastore):
        """Parses the repository
        
        :param repositoryPath: path to the repository
        :param datastore: subclass of :class:`pyvcsshark.datastores.basestore.BaseStore`.
        
        
        .. NOTE:: We must call the :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` function in the parsing process if we want \
        to add commits to the datastore
        """
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
        """ Helper method, which gets the **immediate** subdirectoriesof a path. Is helpful, if one want to create a 
        parser, which looks if certain folders are there.
        
        :param a_dir: directory from which **immediate** subdirectories should be listed """
        return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]
            
            
            
            
        
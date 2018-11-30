import abc
import os
import pyvcsshark.utils

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
    def repository_type(self):
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
    def detect(self, repository_path):
        """Return true if the parser is applicable to the repository
        
        :param repository_path: path to the repository
        """
        return

    @abc.abstractmethod
    def parse(self, repository_path, datastore, cores_per_job):
        """Parses the repository
        
        :param repository_path: path to the repository
        :param datastore: subclass of :class:`pyvcsshark.datastores.basestore.BaseStore`.
        :param cores_per_job: number of cores used for parsing
        
        
        .. NOTE:: We must call the :func:`pyvcsshark.datastores.basestore.BaseStore.addCommit` function in the parsing process if we want \
        to add commits to the datastore
        """
        return
    
    @abc.abstractmethod
    def get_project_url(self):
        """Retrieves the project url from the repository. This need to be
        put here, as only the parser is specific to the repository type"""

    @staticmethod
    def find_correct_parser(repository_path):
        """ Finds the correct parser by executing the parser.detect() method on
        the given repository path

        :param repository_path: path to the repository
        """

        # Import parser plugins
        pyvcsshark.utils.find_plugins(os.path.dirname(os.path.realpath(__file__)))

        # Trying to find the correct parser by checking if it implements the
        # needed methods and calling the detect method
        correct_parser = None
        for sc in BaseParser.__subclasses__():
            parser = sc()
            if parser.detect(repository_path):
                return parser

        # Check if correct parser was found
        if correct_parser is None:
            raise Exception("No fitting parser found for repository located at %s" % repository_path)
        else:
            return correct_parser

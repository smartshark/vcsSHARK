'''
Created on 09.12.2015

@author: fabian
'''
from pyvcsshark.parser.baseparser import BaseParser

from .utils import findCorrectParser, findCorrectDatastore
import logging
import sys
import traceback
import timeit
class Application(object):
    """ Main application class. Contains the most important process logic.
    The main application consists of different steps: \n
    
    1. The correct datastore is found (inherits from: :class:`pyvcsshark.datastores.basestore.BaseStore`) by looking at which one was chosen by the user and the class is instantiated
    2. The correct parser (inherits from: :class:`pyvcsshark.parser.baseparser.BaseParser`) for the specified repository is instantiated
    3. :func:`pyvcsshark.parser.baseparser.BaseParser.initialize` is called (concreter: the **implemented function** of the **correct parser**)
    4. :func:`pyvcsshark.datastores.basestore.BaseStore.initialize` is called with the different configuration parameters and values from the parser (concreter: the **implemented function** of the **correct datastore**)
    5. :func:`pyvcsshark.baseparser.BaseParser.parse` is called to start the parsing process of the repository (concreter: the **implemented function** of the **correct parser**)
    6. :func:`pyvcsshark.parser.baseparser.BaseParser.finalize` is called to finalize the parsing process (e.g. closing files) (concreter: the **implemented function** of the **correct parser**)
    7. :func:`pyvcsshark.datastores.basestore.BaseStore.finalize` is called to finalize the storing process (e.g. closing connections) (concreter: the **implemented function** of the **correct datastore**)
    
    
    
    :param config: An instance of :class:`~pyvcsshark.Config`, which contains the configuration parameters
    
    """
    
    def __init__(self,config):
        self.config = config
        self.logger = logging.getLogger("main")
        
        # Only find correct parser and parse,
        # Measure excution time
        start_time = timeit.default_timer()
                    
        datastore = findCorrectDatastore(self.config.db_driver)
        self.logger.info("Using %s for storing the results of repository %s" % (datastore.__class__.__name__, self.config.uri))

        try:
            parser = findCorrectParser(self.config.uri)
            self.logger.info("Using %s for parsing directory %s" % (parser.__class__.__name__, self.config.uri))
        except Exception as e:
            traceback.print_exc()
            self.logger.error("Failed to instantiate parser. Original message: %s" % (e))#
            sys.exit(1)
            
        # Set projectName, url and repository type, as they
        # are most likely required for storing into a datastore (e.g. creating a project table)
        parser.initialize()
        datastore.initialize(self.config.db_database, self.config.db_hostname, self.config.db_port,
                             self.config.db_user, self.config.db_password, parser.getProjectName(),
                             parser.getProjectURL(), parser.repositoryType, self.config.db_authentication)
        parser.parse(self.config.uri, datastore)
        parser.finalize()
        datastore.finalize()
            
        elapsed = timeit.default_timer() - start_time
        
        
        self.logger.info("Execution time: %0.5f s" % elapsed)

            
            
            
            
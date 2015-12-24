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
    def __init__(self,config):
        self.config = config
        self.logger = logging.getLogger("main")
        
        # Only find correct parser and parse,
        # if it was not excluded
        if(not self.config.no_parse):
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
                                 parser.getProjectURL(), parser.repositoryType)
            parser.parse(self.config.uri, datastore)
            parser.finalize()
            datastore.finalize()
            
            elapsed = timeit.default_timer() - start_time
        
        
            self.logger.info("Execution time: %0.5f s" % elapsed)

            
            
            
            
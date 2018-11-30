from pyvcsshark.datastores.basestore import BaseStore
from pyvcsshark.parser.baseparser import BaseParser

import logging
import sys
import traceback
import timeit

logger = logging.getLogger("main")

class Application(object):
    """ Main application class. Contains the most important process logic.
    The main application consists of different steps: \n
    
    1. The correct datastore is found (inherits from: :class:`pyvcsshark.datastores.basestore.BaseStore`) by
    looking at which one was chosen by the user and the class is instantiated

    2. The correct parser (inherits from: :class:`pyvcsshark.parser.baseparser.BaseParser`)
    for the specified repository is instantiated

    3. :func:`pyvcsshark.parser.baseparser.BaseParser.initialize` is called (concreter: the **implemented function**
    of the **correct parser**)

    4. :func:`pyvcsshark.datastores.basestore.BaseStore.initialize` is called with the different configuration
    parameters and values from the parser (concreter: the **implemented function** of the **correct datastore**)

    5. :func:`pyvcsshark.baseparser.BaseParser.parse` is called to start the parsing process of the repository
    (concreter: the **implemented function** of the **correct parser**)

    6. :func:`pyvcsshark.parser.baseparser.BaseParser.finalize` is called to finalize the parsing process
    (e.g. closing files) (concreter: the **implemented function** of the **correct parser**)

    7. :func:`pyvcsshark.datastores.basestore.BaseStore.finalize` is called to finalize the storing process
    (e.g. closing connections) (concreter: the **implemented function** of the **correct datastore**)

    :param config: An instance of :class:`~pyvcsshark.Config`, which contains the configuration parameters
    """
    
    def __init__(self,config):
        logger.setLevel(config.debug_level)
        
        # Only find correct parser and parse,
        # Measure execution time
        start_time = timeit.default_timer()
                    
        datastore = BaseStore.find_correct_datastore(config.db_driver)
        logger.info("Using %s for storing the results of repository %s" % (datastore.__class__.__name__, config.path))

        try:
            parser = BaseParser.find_correct_parser(config.path)
            logger.info("Using %s for parsing directory %s" % (parser.__class__.__name__, config.path))
        except Exception as e:
            traceback.print_exc()
            logger.exception("Failed to instantiate parser.")
            sys.exit(1)
            
        # Set projectName, url and repository type, as they
        # are most likely required for storing into a datastore (e.g. creating a project table)
        parser.initialize()
        datastore.initialize(config, parser.get_project_url(), parser.repository_type)
        parser.parse(config.path, datastore, config.cores_per_job)
        parser.finalize()
        datastore.finalize()
            
        elapsed = timeit.default_timer() - start_time
        
        logger.info("Execution time: %0.5f s" % elapsed)
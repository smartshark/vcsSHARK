import argparse
from .config import Config
from .main import Application
from .utils import *
import json
import logging
import logging.config
from pyvcsshark.datastores.basestore import BaseStore
from pycoshark.utils import get_base_argparser


def setup_logging(default_path=os.path.dirname(os.path.realpath(__file__))+"/loggerConfiguration.json", 
                  default_level=logging.INFO):
        """
        Setup logging configuration
        
        :param default_path: path to the logger configuration
        :param default_level: defines the default logging level if configuration file is not found (default: logging.INFO)
        """
        path = default_path
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)


def get_datastore_choices():
    """ Helper function that gets all the available datastore choices, so that
    we can check, if the user chooses an available datastore.
    """
    
    # Helper function, that imports all .py files in the datastores folder
    find_plugins(os.path.dirname(os.path.realpath(__file__))+"/datastores")
    choices = []
    for sc in BaseStore.__subclasses__():
        datastore = sc()
        choices.append(datastore.store_identifier)
    return choices
        
        
def start():
    """ Start method to start the program. It first sets up the logging and then parses all the arguments
    it got from the commandline.
    """
    
    setup_logging()
    logger = logging.getLogger("main")

    try:
        datastore_choices = get_datastore_choices()
    except Exception as e:
        logger.exception("Failed to instantiate datastore")
        sys.exit(1)
        
    if not datastore_choices :
        logger.error("No datastores found! Exiting...")
        sys.exit(1)

    parser = get_base_argparser('Analyze the given URI. An URI can be a checked out directory. If URI is omitted, '
                                'the current working directory will be used as a checked out directory.', '1.0.0')
    parser.add_argument('-D', '--db-driver', help='Output database driver. Currently only mongoDB is supported',
                        default='mongo', choices=datastore_choices)
    parser.add_argument('-d', '--log-level', help='Debug level', choices=['INFO', 'DEBUG', 'WARNING', 'ERROR'],
                        default='INFO')
    parser.add_argument('-n', '--project-name', help='Name of the project, that is analyzed', required=True)
    parser.add_argument('--path', help='Path to the checked out repository directory', default=os.getcwd(),
                        type=readable_dir)
    parser.add_argument('--cores-per-job', help='Number of cores to use', default=4, type=int)

    logger.info("Reading out config from command line")

    try:
        args = parser.parse_args()
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    read_config = Config(args)
    logger.debug('Read the following config: %s' % read_config)

    Application(read_config)

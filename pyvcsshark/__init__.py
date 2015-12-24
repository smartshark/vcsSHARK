'''
Created on 09.12.2015

@author: fabian
'''

import argparse
import os
import sys
from .config import Config
from .main import Application
from .utils import *
import json
import logging
import logging.config
from pyvcsshark.datastores.basestore import BaseStore


def setup_logging(default_path='loggerConfiguration.json', 
                  default_level=logging.INFO,
                  env_key='LOG_CFG'):
        """
        Setup logging configuration
        """
        path = default_path
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)
            
def getDatastoreChoices():
    find_plugins('./pyvcsshark/datastores')
    choices = []
    for sc in BaseStore.__subclasses__():
        datastore = sc()
        choices.append(datastore.storeIdentifier)
    return choices
        
        
def start():
    setup_logging()
    logger = logging.getLogger("main")
    
    datastoreChoices = None
    try:
        datastoreChoices = getDatastoreChoices()
    except Exception as e:
        logger.error("Failed to instantiate datastore. Original message: %s" % (e))
        sys.exit(1)
        
    if(not datastoreChoices):
        logger.error("No datastores found! Exiting...")
        sys.exit(1)
                
    parser = argparse.ArgumentParser(description='Analyze the given URI. An URI can be a checked out directory. \
                                                 If URI is omitted, the current working directory will be used as a checked out directory.')
    parser.add_argument('-d', '--debug', help='Enables debug mode', default=False, action='store_true')
    parser.add_argument('-v', '--version', help='Shows the version', action='version', version='0.0.1')
    parser.add_argument('-q', '--quiet', help='Run silently, only print error messages', default=False, action='store_true')
    parser.add_argument('-f', '--config-file', help='Path to a custom configuration file', default=None)
    parser.add_argument('-n', '--no-parse', help='Skip the parsing process. Only makes sense, if you want to execute extensions only', default=False, action='store_true')
    parser.add_argument('-D', '--db-driver', help='Output database driver. Currently only mongoDB is supported', default='mongo', choices=datastoreChoices)
    parser.add_argument('-U', '--db-user', help='Database user name', default='root')
    parser.add_argument('-P', '--db-password', help='Database user password', default='root')
    parser.add_argument('-DB', '--db-database', help='Database name', default='smartshark')
    parser.add_argument('-H', '--db-hostname', help='Name of the host, where the database server is running', default='localhost')
    parser.add_argument('-p', '--db-port', help='Port, where the database server is listening', default=27017, type=int)
    parser.add_argument('-e', '--list-extensions', help='Show all available extensions')
    parser.add_argument('--extensions', help='List of extensions to run. E.g. ext1 ext2', default=[], nargs='*')
    parser.add_argument('-w', '--writable-path', help='Storage of files (e.g. cache, config) to the given path', default=None, type=readable_dir)
    parser.add_argument('-u', '--uri', help='Path to the checked out repository directory', default=os.getcwd(), type=readable_dir)

    logger.info("Reading out config from command line")

    try:
        args = parser.parse_args()
    except Exception as e:
        logger.error(e)
    
    
   
    config = Config(args.debug, args.quiet, args.writable_path, 
                    args.no_parse, args.db_driver, args.db_user,
                    args.db_password, args.db_database, 
                    args.db_hostname, args.db_port, args.extensions,
                    args.uri)
    
    # If config file was specified, overwrite the values
    if(args.config_file != None):
        try:
            logger.info("Found config file... read configuration file")
            config.load_from_file(args.config_file)
        except Exception as e:
            logger.error(e)
            sys.exit(1)
            
    logger.debug('Read the following config: %s' %(config))
    
        
    if not config.extensions and config.no_parse:
        logger.info("No extensions were given and no parse is true. Exiting...")
        sys.exit(0)

    Application(config)

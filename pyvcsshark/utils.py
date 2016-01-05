import os
import sys
from pyvcsshark.datastores.basestore import BaseStore
from pyvcsshark.parser.baseparser import BaseParser

def readable_dir(prospective_dir):
    """ Function that checks if a path is a directory, if it exists and if it is accessible and only
    returns true if all these three are the case
    
    :param prospective_dir: path to the directory"""
    if(prospective_dir != None):
        if not os.path.isdir(prospective_dir):
            raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            return prospective_dir
        else:
            raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
        
def find_plugins(pluginDir):
    """Finds all python files in the specified path and imports them. This is needed, if we want to
    detect automatically, which datastore and parser we can apply
    
    :param pluginDir: path to the plugin directory"""
    plugin_files = [x[:-3] for x in os.listdir(pluginDir) if x.endswith(".py")]
    sys.path.insert(0, pluginDir)
    for plugin in plugin_files:
        __import__(plugin)
        
            
        
def findCorrectDatastore(datastoreIdentifier):
    """ Finds the correct datastore by looking at the datastore.storeIdentifier property
    
    :param datastoreIdentifier: string that represents the correct datastore (e.g. **mongo**)
    """
    
    # import datastore plugins
    find_plugins(os.path.dirname(os.path.realpath(__file__))+"/datastores")
    correctDatastore = None
    for sc in BaseStore.__subclasses__():
        datastore = sc()
        if(datastoreIdentifier and datastoreIdentifier in datastore.storeIdentifier):
            return datastore


def findCorrectParser(repositoryPath):
    """ Finds the correct parser by executing the parser.detect() method on
    the given repository path
    
    :param repositoryPath: path to the repository 
    """
    
    # Import parser plugins
    find_plugins(os.path.dirname(os.path.realpath(__file__))+"/parser")
        
    # Trying to find the correct parser by checking if it implements the
    # needed methods and calling the detect method
    correctParser = None
    for sc in BaseParser.__subclasses__():
        parser = sc()  
        if(parser.detect(repositoryPath)):
            return parser

    # Check if correct parser was found
    if(correctParser == None):
        raise Exception("No fitting parser found for repository located at %s" % (repositoryPath))
    else:
        return correctParser
            
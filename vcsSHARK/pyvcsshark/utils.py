'''
Created on 09.12.2015

@author: fabian
'''
import os
import sys
from pyvcsshark.datastores.basestore import BaseStore
from pyvcsshark.parser.baseparser import BaseParser

def readable_dir(prospective_dir):
    if(prospective_dir != None):
        if not os.path.isdir(prospective_dir):
            raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            return prospective_dir
        else:
            raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))
        
def find_plugins(pluginDir):
    '''find all files in the plugin directory and imports them'''
    plugin_files = [x[:-3] for x in os.listdir(pluginDir) if x.endswith(".py")]
    sys.path.insert(0, pluginDir)
    for plugin in plugin_files:
        __import__(plugin)
        
            
        
def findCorrectDatastore(datastoreIdentifier):
    # import datastore plugins
    find_plugins('./pyvcsshark/datastores')
    correctDatastore = None
    for sc in BaseStore.__subclasses__():
        datastore = sc()
        if(datastoreIdentifier and datastoreIdentifier in datastore.storeIdentifier):
            return datastore


def findCorrectParser(repositoryPath):
    # Import parser plugins
    find_plugins('./pyvcsshark/parser')
        
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
            
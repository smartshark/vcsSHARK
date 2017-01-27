'''
Created on 21.01.2016

@author: fabian
'''

import multiprocessing

class DatastoreMock(object):

    projectName = None
    projectURL = None
    repositoryType = None
    listTest = list()
    
    
    def __init__(self):
        self.datastore = {}
        self.queue = multiprocessing.SimpleQueue()
        return
    
    def initialize(self, dbname=None, host=None, port=None, user=None , 
                   password=None, projectname=None, repositoryURL=None, type=None):
        return

    def storeIdentifier(self):
        return "datastoremock"

    def add_commit(self, commitModel):
        self.queue.put(commitModel)
    
    def finalize(self): 
        return
    
    def get_commit_queue(self):
        return self.queue
    

    

        
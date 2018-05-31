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
        self.branch_queue = multiprocessing.SimpleQueue()
        return

    def initialize(self, dbname=None, host=None, port=None, user=None , 
                   password=None, projectname=None, repositoryURL=None, type=None):
        return

    def storeIdentifier(self):
        return "datastoremock"

    def add_commit(self, commitModel):
        self.queue.put(commitModel)

    def add_branch(self, branchModel):
        self.branch_queue.put(branchModel)

    def finalize(self): 
        return

    def get_commit_queue(self):
        return self.queue

    def get_branch_queue(self):
        return self.branch_queue

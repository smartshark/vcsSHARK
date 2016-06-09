'''
Created on 16.12.2015

@author: fabian
'''
from pyvcsshark.datastores.basestore import BaseStore

class MySQLStore(BaseStore):
    '''
    classdocs
    '''
        
    def initialize(self, dbname=None, host=None, port=None, user=None , 
                   password=None, projectname=None, repositoryURL=None, type=None, authentication_db=None):
        return
        
    @property
    def storeIdentifier(self):
        '''Must return the identifier for the store. This should match the configuration options'''
        return 'mysql'

    def addCommit(self, commitId=None, branches=set(), tags=set(), parents=[], authorName=None,
                  authorEmail=None, authorTime=None, authorTimeOffset=None, committerName=None,
                  committerEmail=None, committerTime=None, committerTimeOffset=None, message=None,
                  changedFiles=[]):
        '''Add the commit to the datastore (e.g. mongoDB, mySQL, a model, ...). How this is 
        handled depends on the implementation'''
        return

    def deleteAll(self):
        '''Deletes all data of one project from the datastore'''
        return
    
    def finalize(self):
        return
        
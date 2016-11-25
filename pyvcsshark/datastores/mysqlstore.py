from pyvcsshark.datastores.basestore import BaseStore


class MySQLStore(BaseStore):
    def initialize(self, config, repository_url, repository_type):
        return
        
    @property
    def store_identifier(self):
        """Must return the identifier for the store. This should match the configuration options"""
        return 'mysql'

    def add_commit(self, commit_model):
        """Add the commit to the datastore (e.g. mongoDB, mySQL, a model, ...). How this is
        handled depends on the implementation"""
        return

    def deleteAll(self):
        """Deletes all data of one project from the datastore"""
        return
    
    def finalize(self):
        return

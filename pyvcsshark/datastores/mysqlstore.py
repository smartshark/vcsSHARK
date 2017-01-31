from pyvcsshark.datastores.basestore import BaseStore


class MySQLStore(BaseStore):
    def initialize(self, config, repository_url, repository_type):
        """
        Initializes the mongostore by connecting to the mongodb, creating the project in the project collection \
        and setting up processes (see: :class:`pyvcsshark.datastores.mongostore.CommitStorageProcess`, which
        read commits out of the commitqueue, process them and store them into the mongodb.

        :param config: all configuration
        :param repository_url: url of the repository, which is to be analyzed
        :param repository_type: type of the repository, which is to be analyzed (e.g. "git")
        """
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


class ArgparserMock(object):
    def __init__(self, db_driver, db_user, db_password, db_database, db_hostname, db_port, db_authentication, path,
                 debug_level, project_name, ssl, no_hunks,
                 no_commit_branch_info, recursive, cores_per_job):
        self.db_driver = db_driver
        self.db_user = db_user
        self.db_password = db_password
        self.db_database = db_database
        self.db_hostname = db_hostname
        self.db_port = int(db_port)
        self.db_authentication = db_authentication
        self.path = path
        self.log_level = debug_level
        self.project_name = project_name
        self.ssl = ssl
        self.no_hunks = no_hunks
        self.no_commit_branch_info = no_commit_branch_info
        self.recursive = recursive
        self.cores_per_job = cores_per_job

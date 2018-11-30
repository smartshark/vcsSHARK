class ErrorLoadingConfig(Exception):
    """Exception class, which is used for config loading exceptions. """

    def __init__(self, config_file, message=None):
        message = 'Failed in reading config file %s. Original message: %s' % (config_file, message)
        Exception.__init__(self, message)


class Config(object):
    """
    Holds configuration information

    :param args: argumentparser of the class :class:`argparse.ArgumentParser`
    """
    def __init__(self, args):
        self.db_driver = args.db_driver
        self.db_user = args.db_user
        self.db_password = args.db_password
        self.db_database = args.db_database
        self.db_hostname = args.db_hostname
        self.db_port = args.db_port
        self.db_authentication = args.db_authentication
        self.path = args.path.rstrip('/')
        self.debug_level = args.log_level
        self.project_name = args.project_name
        self.cores_per_job = args.cores_per_job
        self.ssl_enabled = args.ssl

    def __str__(self):
        return "Driver: %s, User: %s, Password: %s, Database: %s, Hostname: %s, Port: %s, AuthenticationDB: %s, " \
               "Path: %s, Debug: %s, Project Name: %s" % (
                   self.db_driver,
                   self.db_user,
                   self.db_password,
                   self.db_database,
                   self.db_hostname,
                   self.db_port,
                   self.db_authentication,
                   self.path,
                   self.debug_level,
                   self.project_name,
               )

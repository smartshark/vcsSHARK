import configparser
from .utils import readable_dir

class ErrorLoadingConfig(Exception):
    """Exception class, which is used for config loading exceptions. """
    def __init__(self, config_file, message=None):
        message = 'Failed in reading config file %s. Original message: %s' % (config_file, message)
        Exception.__init__(self, message)

class Config(object):
    """A class that represents the parsed config.
    
    :param no_parse: If true, the data is not parsed and only the extensions are executed
    :param db_driver: name of the datastore driver (e.g. **mongo**)
    :param db_user: datastore username (e.g. **root**)
    :param db_password: datastore password
    :param db_database: database of the datastore
    :param db_hostname: hostname where the datastore runs on
    :param db_port: port where the datastore is listening on
    :param db_authentication: database to authenticate against
    :param uri: path to the repository
    """
    
    def __init__(self, db_driver="mongo", db_user="root", db_password="root", db_database="vcsSHARK",
                 db_hostname="localhost", db_port=27017, db_authentication='admin', uri="."):

        self.db_driver = db_driver
        self.db_user = db_user
        self.db_password = db_password
        self.db_database = db_database
        self.db_hostname = db_hostname
        self.db_port = int(db_port)
        self.db_authentication = db_authentication
        self.uri = uri.rstrip('/')
        
    
    def _str2bool(self, v):
        """ Checks if a string containts yes, true, t or 1. This way we can check if
        a value is set to true in the config
        
        :param v: string that should be checked"""
        return v.lower() in ("yes", "true", "t", "1")
    
    def _readConfigOption(self, section, option, returnBool=False, returnList=False):
        """ Helper method to read a config option. We can specify the return value with
        the different parameters
        
        :param section: section of the configruation, where the option is in
        :param option: option from which the value should be read
        :param returnBool: specifies if the return value should be a boolean
        :param returnList: specifies if the return value should be a list"""
        value = self.configParser.get(section,option)
        if(value != None and value):
            if(returnBool):
                return self._str2bool(value)
            elif(returnList):
                return value.split(",")
            else:
                return value
        
        return getattr(self, option)
        
            
    def load_from_file(self, config_file):
        """ Load the configuration from the specified file.
        
        :param config_file: path to configuration file
        """
        try:
            
            self.configParser = configparser.ConfigParser(allow_no_value=True)
            self.configParser.read(config_file)
            

            self.uri = self._readConfigOption("RepositoryConfiguration", "uri").rstrip('/')
            self.db_driver = self._readConfigOption("Database", "db_driver")
            self.db_user = self._readConfigOption("Database", "db_user")
            self.db_password = self._readConfigOption("Database", "db_password")
            self.db_database = self._readConfigOption("Database", "db_database")
            self.db_hostname = self._readConfigOption("Database", "db_hostname")
            self.db_port = int(self._readConfigOption("Database", "db_port"))
            self.db_authentiacation = self._readConfigOption("Database", "db_authentication")

            # Check if dirs are readable
            readable_dir(self.uri)

           
        except Exception as e:
            raise Exception('Failed in reading config file %s. Original message: %s' % (config_file, e))

    def __str__(self):
        return "<Config(uri='%s', db_driver='%s', db_user='%s', db_password='%s', "\
               "db_database='%s', db_hostname='%s', db_port='%s', db_authentication='%s'" % \
               (self.uri, self.db_driver, self.db_user, self.db_password, self.db_database,
                self.db_hostname, self.db_port, self.db_authentication)
               
               
               
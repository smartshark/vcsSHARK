'''
Created on 09.12.2015

@author: fabian
'''
import configparser
from .utils import readable_dir

class ErrorLoadingConfig(Exception):
    def __init__(self, config_file, message=None):
        message = 'Failed in reading config file %s. Original message: %s' % (config_file, message)
        Exception.__init__(self, message)

class Config(object):
    '''
    classdocs
    '''
    
    
    def __init__(self, debug, quiet, writable_path, no_parse,
                              db_driver, db_user, db_password, db_database,
                              db_hostname, db_port, extensions, uri):
        
        self.debug = debug
        self.quiet = quiet
        self.writable_path = writable_path
        self.no_parse = no_parse
        self.db_driver = db_driver
        self.db_user = db_user
        self.db_password = db_password
        self.db_database = db_database
        self.db_hostname = db_hostname
        self.db_port = int(db_port)
        self.extensions = extensions
        self.uri = uri.rstrip('/')
        
        #TODO: if self.writable_path == None:
        #    self.createDirectories()
        
        
    def str2bool(self, v):
        return v.lower() in ("yes", "true", "t", "1")
    
    def readConfigOption(self, section, option, returnBool=False, returnList=False):
        value = self.configParser.get(section,option)
        if(value != None and value):
            if(returnBool):
                return self.str2bool(value)
            elif(returnList):
                return value.split(",")
            else:
                return value
        
        return getattr(self, option)
        
            
    def load_from_file(self, config_file):
        try:
            
            self.configParser = configparser.ConfigParser(allow_no_value=True)
            self.configParser.read(config_file)
            

            self.debug = self.readConfigOption("General", "debug", True)
            self.quiet = self.readConfigOption("General", "quiet", True)
            self.writable_path = self.readConfigOption("General", "writable_path")
            self.no_parse = self.readConfigOption("General", "no_parse", True)
            self.uri = self.readConfigOption("RepositoryConfiguration", "uri").rstrip('/')
            self.extensions = self.readConfigOption("Extensions", "extensions", False, True)
            self.db_driver = self.readConfigOption("Database", "db_driver")
            self.db_user = self.readConfigOption("Database", "db_user")
            self.db_password = self.readConfigOption("Database", "db_password")
            self.db_database = self.readConfigOption("Database", "db_database")
            self.db_hostname = self.readConfigOption("Database", "db_hostname")
            self.db_port = int(self.readConfigOption("Database", "db_port"))

            # Check if dirs are readable
            readable_dir(self.writable_path)
            readable_dir(self.uri)

           
        except Exception as e:
            raise ErrorLoadingConfig(config_file, e)
        
    def __str__(self):
        return "<Config(debug='%s', quiet='%s', writable_path='%s', no_parse='%s', " \
               "uri='%s', extensions='%s', db_driver='%s', db_user='%s', db_password='%s', "\
               "db_database='%s', db_hostname='%s', db_port='%s'" % (self.debug, self.quiet, 
                                                                     self.writable_path, self.no_parse,
                                                                     self.uri, ','.join(self.extensions),
                                                                     self.db_driver, self.db_user, self.db_password,
                                                                     self.db_database, self.db_hostname, self.db_port)
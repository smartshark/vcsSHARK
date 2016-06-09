'''
Created on 21.01.2016

@author: fabian
'''
import unittest
import os

from pyvcsshark.config import Config



class ConfigTest(unittest.TestCase):


    def test_load_config_from_file(self):
        config = Config()
        config.load_from_file(os.path.dirname(os.path.realpath(__file__))+"/data/testconfig.cfg")
        
        
        self.assertEqual("admin", config.db_authentication)
        self.assertEqual("mongo", config.db_driver)
        self.assertEqual("root", config.db_user)
        self.assertEqual("test", config.db_password)
        self.assertEqual("testRun", config.db_database)
        self.assertEqual("localhost", config.db_hostname)
        self.assertEqual(27017, config.db_port)
        self.assertEqual("..", config.uri)
        
    def test_config_default(self):
        config = Config()
        
        self.assertEqual("admin", config.db_authentication)
        self.assertEqual("mongo", config.db_driver)
        self.assertEqual("root", config.db_user)
        self.assertEqual("root", config.db_password)
        self.assertEqual("vcsSHARK", config.db_database)
        self.assertEqual("localhost", config.db_hostname)
        self.assertEqual(27017, config.db_port)
        self.assertEqual(".", config.uri)
    
    


if __name__ == "__main__":
    unittest.main()

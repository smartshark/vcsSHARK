'''
Created on 21.01.2016

@author: fabian
'''
import unittest
import logging
import os
import datetime
from pymongo import MongoClient
import uuid

from pyvcsshark.config import Config
from pyvcsshark.datastores.mongostore import MongoStore
from pyvcsshark.dbmodels.models import CommitModel, BranchModel, TagModel,\
    PeopleModel, FileModel, Hunk


class Test(unittest.TestCase):

    config = None
    mongostore = None
    projectUrl = None
    projectName = None
    mongoClient = None

    @classmethod
    def setUpClass(cls):
        # Setup logging
        logging.basicConfig(level=logging.ERROR)
        
        # Read testconfig
        cls.config = Config()
        cls.config.load_from_file(os.path.dirname(os.path.realpath(__file__))+"/data/used_test_config.cfg")
        
        # Initialize mongoclient
        cls.mongoClient = MongoClient(cls.config.db_hostname, cls.config.db_port)
        cls.mongoClient.admin.authenticate(cls.config.db_user, cls.config.db_password, mechanism='SCRAM-SHA-1')
        
    def setUp(self):
        # Drop database
        self.mongoClient.drop_database(self.config.db_database)
        
         # Initialize mongostore
        self.mongostore = MongoStore()
        self.projectName = str(uuid.uuid4())
        self.projectUrl = "local/"+self.projectName
        self.mongostore.initialize(self.config.db_database, self.config.db_hostname, self.config.db_port, 
                                  self.config.db_user, self.config.db_password, self.projectName, self.projectUrl, "git")

    def test_storeIdentifier(self):
        self.assertEqual("mongo", self.mongostore.storeIdentifier)
        
    def addingCommit(self):
        # Creating rather complex commit
        
        ## Create author/committer/tagger
        people = PeopleModel("Fabian Trautsch", "ftrautsch@googlemail.com")
        
        ## Create branches
        branch1 = BranchModel('refs/heads/master')
        branch2 = BranchModel('refs/heads/testbranch1')
        
        ## Create tag
        tag = TagModel("release1", "tag release 1", people , 1453380457, 60)
        
        ## ChangedFile
        hunks = []
        hunks.append(Hunk(old_start=1, old_lines=1, new_start=0, new_lines=0, content='-line1\n'))
        hunks.append(Hunk(old_start=20, old_lines=1, new_start=19, new_lines=1, content='-line20\n+\n'))
        hunks.append(Hunk(old_start=40, old_lines=0, new_start=40, new_lines=1, content='+line41\n'))
        #hunks.append("@@ -1,4 +1,3 @@ \n-line1\n line2\n line3\n line4\n")
        #hunks.append("@@ -17,7 +16,7 @@ \n line17\n line18\n line19\n-line20\n+\n line21\n line22\n line23\n")
        #hunks.append("@@ -38,3 +37,4 @@ \n line38\n line39\n line40\n+line41\n")
        testFile = FileModel("lib/lib.txt", 266, 2, 2, False, "M", hunks, None)
        
        
        commit = CommitModel("830c29f111f261e26897d42e94c15960a512c0e4", set([branch1, branch2]), [tag],
                     ['204d306b10e123f2474612a297b83be6ac79e519'], people, people, "testCommit", [testFile]
                     , 1453380157, 60, 1453380357, 60)
        
        self.mongostore.addCommit(commit)
        
        # Wait till mongostore finalized
        self.mongostore.finalize()
        
    def test_deleteAll(self):
        self.addingCommit()
        # Check if it was inserted
        db = self.mongoClient[self.config.db_database]
        self.assertEqual(1, db.commit.find().count())
        self.assertEqual(1, db.tag.find().count())
        self.assertEqual(1, db.file.find().count())
        self.assertEqual(1, db.file_action.find().count())
        self.assertEqual(1, db.project.find().count())
        self.assertEqual(1, db.people.find().count())
        self.assertEqual(3, db.hunk.find().count())
        
        # Delete everything, EXCEPT people, because they can be associated to something else
        self.mongostore.deleteAll()
        
        self.assertEqual(0, db.commit.find().count())
        self.assertEqual(0, db.tag.find().count())
        self.assertEqual(0, db.file.find().count())
        self.assertEqual(0, db.file_action.find().count())
        self.assertEqual(0, db.project.find().count())
        self.assertEqual(1, db.people.find().count())
        self.assertEqual(0, db.hunk.find().count())
        
        
        
        
    def test_addCommit(self):
        self.addingCommit()
        
                
        # Check if it was inserted
        db = self.mongoClient[self.config.db_database]

        # check if only inserted once
        commits = db.commit.find()
        self.assertEqual(1, commits.count())
        commit = commits[0]
        
        # Check commit data
        tags = db.tag.find()
        self.assertEqual(1, tags.count())
        tag = tags[0]
        
        # File
        files = db.file.find()
        self.assertEqual(1, files.count())
        file = files[0]
        
        # file_action
        fileActions = db.file_action.find()
        self.assertEqual(1, fileActions.count())
        fileAction = fileActions[0]
        
        # Project
        projects = db.project.find()
        self.assertEqual(1, projects.count())
        project = projects[0]
        
        # People
        people = db.people.find()
        self.assertEqual(1, people.count())
        ppl = people[0]
        
        # Hunks
        hunks = db.hunk.find()
        self.assertEqual(3, hunks.count())
        hunk1 = hunks[0]
        hunk2 = hunks[1]
        hunk3 = hunks[2]


        # Check Commit
        self.assertEqual(commit['projectId'], project['_id'])
        self.assertEqual('830c29f111f261e26897d42e94c15960a512c0e4', commit['revisionHash'])
        self.assertEqual(2, len(commit['branches']))
        self.assertIn('refs/heads/master', commit['branches'])
        self.assertIn('refs/heads/testbranch1', commit['branches'])
        self.assertEqual(1, len(commit['tagIds']))
        self.assertEqual(tag['_id'], commit['tagIds'][0])
        self.assertEqual(1, len(commit['parents']))
        self.assertIn('204d306b10e123f2474612a297b83be6ac79e519', commit['parents'])
        self.assertEqual(ppl['_id'], commit['authorId'])
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380157), commit['authorDate'])
        self.assertEqual(60, commit['authorOffset'])
        self.assertEqual(ppl['_id'], commit['committerId'])
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380357), commit['committerDate'])
        self.assertEqual(60, commit['committerOffset'])
        self.assertEqual('testCommit', commit['message'])
        self.assertEqual(1, len(commit['fileActionIds']))
        self.assertEqual(fileAction['_id'], commit['fileActionIds'][0])
        
        # Check file
        self.assertEqual(file['_id'], fileAction['fileId'])
        self.assertEqual('lib.txt', file['name'])
        self.assertEqual('lib/lib.txt', file['path'])
        self.assertEqual(project['_id'], file['projectId'])
        
        # Check file action
        self.assertEqual(project['_id'], fileAction['projectId'])
        self.assertEqual('830c29f111f261e26897d42e94c15960a512c0e4', fileAction['revisionHash'])
        self.assertEqual('M', fileAction['mode'])
        self.assertEqual(266, fileAction['sizeAtCommit'])
        self.assertEqual(2, fileAction['linesAdded'])
        self.assertEqual(2, fileAction['linesDeleted'])
        self.assertEqual(False, fileAction['isBinary'])
        self.assertEquals(3, len(fileAction['hunkIds']))
        self.assertIn(hunk1['_id'], fileAction['hunkIds'])
        self.assertIn(hunk2['_id'], fileAction['hunkIds'])
        self.assertIn(hunk3['_id'], fileAction['hunkIds'])
        
        # Check hunks
        self.assertEqual(0, hunk1['new_lines'])
        self.assertEqual(0, hunk1['new_start'])
        self.assertEqual(1, hunk1['old_start'])
        self.assertEqual(1, hunk1['old_lines'])
        self.assertEqual("-line1\n",hunk1['content'])

        self.assertEqual(1, hunk2['new_lines'])
        self.assertEqual(19, hunk2['new_start'])
        self.assertEqual(20, hunk2['old_start'])
        self.assertEqual(1, hunk2['old_lines'])
        self.assertEqual("-line20\n+\n",hunk2['content'])

        self.assertEqual(1, hunk3['new_lines'])
        self.assertEqual(40, hunk3['new_start'])
        self.assertEqual(40, hunk3['old_start'])
        self.assertEqual(0, hunk3['old_lines'])
        self.assertEqual("+line41\n",hunk3['content'])
        
        # Check people
        self.assertEqual("Fabian Trautsch", ppl['name'])
        self.assertEqual("ftrautsch@googlemail.com", ppl['email'])
        
        # Check project
        self.assertEqual(self.projectUrl, project['url'])
        self.assertEqual(self.projectName, project['name'])
        self.assertEqual('git', project['repositoryType'])
        
        # Check tag
        self.assertEqual('release1', tag['name'])
        self.assertEqual(project['_id'], tag['projectId'])
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380457), tag['date'])
        self.assertEqual(60, tag['offset'])
        self.assertEqual('tag release 1', tag['message'])
        self.assertEqual(ppl['_id'], tag['taggerId'])

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
import unittest
import logging
import configparser
import os
import datetime
from pymongo import MongoClient
import uuid

from pyvcsshark.config import Config
from pyvcsshark.datastores.mongostore import MongoStore
from pyvcsshark.parser.models import CommitModel, BranchModel, TagModel,\
    PeopleModel, FileModel, Hunk


class ArgparserMock(object):
    def __init__(self, db_driver, db_user, db_password, db_database, db_hostname, db_port, db_authentication, path,
                 debug_level, project_name, ssl, cores_per_job):
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
        self.cores_per_job = cores_per_job


class Test(unittest.TestCase):

    config = None
    mongo_store = None
    project_url = None
    project_name = None
    mongo_client = None

    @classmethod
    def setUpClass(cls):
        # Setup logging
        logging.basicConfig(level=logging.ERROR)

        # Create test config
        config = configparser.ConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__))+"/data/used_test_config.cfg")
        parser = ArgparserMock('mongo', config['Database']['db_user'], config['Database']['db_password'],
                               config['Database']['db_database'], config['Database']['db_hostname'],
                               config['Database']['db_port'], config['Database']['db_authentication'], '..',
                               'ERROR', 'testproject', False, 2)

        cls.config = Config(parser)

        # Initialize mongo client
        cls.mongo_client = MongoClient(cls.config.db_hostname, cls.config.db_port)
        if cls.config.db_password:
            cls.mongo_client[cls.config.db_authentication].authenticate(cls.config.db_user,
                                                                        cls.config.db_password, mechanism='SCRAM-SHA-1')

    def setUp(self):
        # Drop database
        self.mongo_client.drop_database(self.config.db_database)
        self.mongo_client[self.config.db_database].project.insert_one({"name": "testproject"})

        # Initialize mongo store
        self.mongo_store = MongoStore()
        self.project_name = str(uuid.uuid4())
        self.project_url = "local/" + self.project_name
        self.mongo_store.initialize(self.config, self.project_url, "git")

    def test_storeIdentifier(self):
        self.assertEqual("mongo", self.mongo_store.store_identifier)

    def addingCommit(self):
        # Creating rather complex commit

        # Create author/committer/tagger
        people = PeopleModel("Fabian Trautsch", "ftrautsch@googlemail.com")

        # Create branches
        branch1 = BranchModel('refs/heads/master')
        branch2 = BranchModel('refs/heads/testbranch1')

        # Create tag
        tag = TagModel("release1", "tag release 1", people, 1453380457, 60)

        # ChangedFile
        hunks = [Hunk(old_start=1, old_lines=1, new_start=0, new_lines=0, content='-line1\n'),
                 Hunk(old_start=20, old_lines=1, new_start=19, new_lines=1, content='-line20\n+\n'),
                 Hunk(old_start=40, old_lines=0, new_start=40, new_lines=1, content='+line41\n')]
        test_file = FileModel("lib/lib.txt", 266, 2, 2, False, "M", hunks, None,
                              "204d306b10e123f2474612a297b83be6ac79e519")

        commit = CommitModel("830c29f111f261e26897d42e94c15960a512c0e4", {branch1, branch2}, [tag],
                             ['204d306b10e123f2474612a297b83be6ac79e519'], people, people, "testCommit", [test_file],
                             1453380157, 60, 1453380357, 60)

        self.mongo_store.add_commit(commit)

        # Wait till mongo store finalized
        self.mongo_store.finalize()

    def test_addCommit(self):
        self.addingCommit()

        # Check if it was inserted
        db = self.mongo_client[self.config.db_database]

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
        file_actions = db.file_action.find()
        self.assertEqual(1, file_actions.count())
        file_action = file_actions[0]

        # VCS System
        vcs_systems = db.vcs_system.find()
        self.assertEqual(1, vcs_systems.count())
        vcs_system = vcs_systems[0]

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
        self.assertEqual(commit['vcs_system_id'], vcs_system['_id'])
        self.assertEqual('830c29f111f261e26897d42e94c15960a512c0e4', commit['revision_hash'])
        self.assertEqual(2, len(commit['branches']))
        self.assertIn('refs/heads/master', commit['branches'])
        self.assertIn('refs/heads/testbranch1', commit['branches'])
        self.assertEqual(1, len(commit['parents']))
        self.assertIn('204d306b10e123f2474612a297b83be6ac79e519', commit['parents'])
        self.assertEqual(ppl['_id'], commit['author_id'])
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380157), commit['author_date'])
        self.assertEqual(60, commit['author_date_offset'])
        self.assertEqual(ppl['_id'], commit['committer_id'])
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380357), commit['committer_date'])
        self.assertEqual(60, commit['committer_date_offset'])
        self.assertEqual('testCommit', commit['message'])

        # Check file
        self.assertEqual('lib/lib.txt', file['path'])
        self.assertEqual(vcs_system['_id'], file['vcs_system_id'])

        # Check file action
        self.assertEqual(file['_id'], file_action['file_id'])
        self.assertEqual(commit['_id'], file_action['commit_id'])
        self.assertEqual('M', file_action['mode'])
        self.assertEqual(266, file_action['size_at_commit'])
        self.assertEqual(2, file_action['lines_added'])
        self.assertEqual(2, file_action['lines_deleted'])
        self.assertEqual(False, file_action['is_binary'])
        self.assertEqual("204d306b10e123f2474612a297b83be6ac79e519", file_action['parent_revision_hash'])

        # Check hunks
        self.assertEqual(file_action['_id'], hunk1['file_action_id'])
        self.assertEqual(0, hunk1['new_lines'])
        self.assertEqual(0, hunk1['new_start'])
        self.assertEqual(1, hunk1['old_start'])
        self.assertEqual(1, hunk1['old_lines'])
        self.assertEqual("-line1\n", hunk1['content'])

        self.assertEqual(file_action['_id'], hunk2['file_action_id'])
        self.assertEqual(1, hunk2['new_lines'])
        self.assertEqual(19, hunk2['new_start'])
        self.assertEqual(20, hunk2['old_start'])
        self.assertEqual(1, hunk2['old_lines'])
        self.assertEqual("-line20\n+\n", hunk2['content'])

        self.assertEqual(file_action['_id'], hunk3['file_action_id'])
        self.assertEqual(1, hunk3['new_lines'])
        self.assertEqual(40, hunk3['new_start'])
        self.assertEqual(40, hunk3['old_start'])
        self.assertEqual(0, hunk3['old_lines'])
        self.assertEqual("+line41\n", hunk3['content'])

        # Check people
        self.assertEqual("Fabian Trautsch", ppl['name'])
        self.assertEqual("ftrautsch@googlemail.com", ppl['email'])

        # Check tag
        self.assertEqual('release1', tag['name'])
        self.assertEqual(commit['_id'], tag['commit_id'])
        self.assertEqual(vcs_system['_id'], tag['vcs_system_id'])
        self.assertEqual('tag release 1', tag['message'])
        self.assertEqual(ppl['_id'], tag['tagger_id'])
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380457), tag['date'])
        self.assertEqual(60, tag['date_offset'])


if __name__ == "__main__":
    unittest.main()

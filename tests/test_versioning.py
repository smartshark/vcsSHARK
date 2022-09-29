# To Run This Test: python -m unittest tests.test_versioning.Test
import unittest
import logging
import configparser
import os
from pymongo import MongoClient
import pygit2
import shutil

from mongoengine import connect
from pyvcsshark.config import Config
from pyvcsshark.datastores.mongostore import MongoStore
from pycoshark.mongomodels import Commit, Tag
from pycoshark.utils import create_mongodb_uri_string


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
        self.unit_testing = True


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
        config.read(os.path.dirname(os.path.realpath(__file__)) +
                    "/data/used_test_config.cfg")
        parser = ArgparserMock('mongo', config['Database']['db_user'], config['Database']['db_password'],
                               config['Database']['db_database'], config['Database']['db_hostname'],
                               config['Database']['db_port'], config['Database']['db_authentication'], '..',
                               'ERROR', 'test_versioning_project', False, 2)

        cls.config = Config(parser)

        # Initialize mongo client
        cls.mongo_client = MongoClient(
            cls.config.db_hostname, cls.config.db_port)
        if cls.config.db_password:
            cls.mongo_client[cls.config.db_authentication].authenticate(cls.config.db_user,
                                                                        cls.config.db_password, mechanism='SCRAM-SHA-1')
        # Drop Testing database
        cls.mongo_client.drop_database(cls.config.db_database)
        cls.mongo_client[cls.config.db_database].project.insert_one(
            {"name": "test_versioning_project"})

        # Create test project
        cls.project_name = "test_versioning_project"
        cls.repository_path = os.path.dirname(
            os.path.realpath(__file__)) + "/data/" + cls.project_name

        # Clean Previous repo if needed
        cls.dropGitRepo(cls, cls.repository_path)

        #Init testing repo
        cls.repository = pygit2.init_repository(cls.repository_path)

        # create test init commit
        msg = "test init commit"
        cls.addGitCommit(cls, msg, "HEAD")

    def setUp(self):
        try:
            # Initialize mongo store globally
            self.mongo_store = MongoStore()
            uri = create_mongodb_uri_string(self.config.db_user, self.config.db_password, self.config.db_hostname, self.config.db_port,
                                            self.config.db_authentication, self.config.ssl_enabled)
            connect(self.config.db_database, host=uri, connect=False)
        except:
            print("err in mongo connection")

    def syncPlugin(self):
        os.system("python vcsshark.py -D mongo -DB vcs_run -H localhost -p 27017 -n " +
                  self.project_name + " --path " + str(self.repository_path) + ' --log-level ERROR --unit-testing True')

    def addGitCommit(self, msg, branchName="master"):

        test_author = pygit2.Signature("test", "test@email.edu")
        try:
            lastCommit = self.repository.head.peel()
        except:
            lastCommit = None

        try:
            if branchName != "HEAD":
                branch = self.repository.branches[branchName]
                branchName = branch.name
        except:
            branch = self.repository.branches.local.create(
                branchName, commit=lastCommit)
            branchName = branch.name

        if branchName != "HEAD":
            self.repository.checkout(branch)

        try:
            lastCommit = self.repository.head.peel()
            parent = [lastCommit.oid]
        except:
            lastCommit = None
            parent = []

        (index := self.repository.index).add_all()
        index.write()
        tree = index.write_tree()
        return self.repository.create_commit(branchName, test_author, test_author, msg, tree, parent)

    def changeHeadMsg(self):
        lastCommit = self.repository.head.peel()

        # pygit2=0.26.0 doesn't support amend, so we have to do it using git
        os.system("git -C ./tests/data/"+str(self.project_name) +
                  " commit --amend -m 'amended msg!' --allow-empty")
        self.git_gc()

        return lastCommit.oid

    def git_gc(self):
        # Repository Garbage Collection
        os.system("git -C ./tests/data/"+str(self.project_name) +
                  " reflog expire --expire-unreachable=now --all")
        os.system("git -C ./tests/data/" +
                  str(self.project_name)+" gc --prune=now")

    def test_delete_Commit(self):
        """
        Test if plugin mark commit as deleted if no longer exists in repo
        """

        # add commits samples
        self.addGitCommit("master c1")
        self.addGitCommit("master c2")
        self.addGitCommit("master c3")

        # sync mongo
        self.syncPlugin()

        # delete head commit using amend or anything
        updatedMsgOid = self.changeHeadMsg()

        # sync mongo again
        self.syncPlugin()

        # assert check
        check_commit = Commit.objects(revision_hash=updatedMsgOid.hex).get()

        self.assertEqual(updatedMsgOid.hex,
                         check_commit.revision_hash, "not same")
        self.assertIsNotNone(check_commit.deleted_at, "mark as deleted failed")

    def test_previous_state(self):
        """
        Test: Plugin should have older state if commit has changed any values
        """

        # store old init commit
        init_commit_old = Commit.objects(message="test init commit")[0]
        init_commit_old.branches.sort()

        # we can add more branches to test further.
        sample_branches = ["D1", "D2"]
        for sample_branch in sample_branches:
            # add sample commit on new branch
            self.addGitCommit("commit on branch "+sample_branch, sample_branch)

            # sync plugin
            self.syncPlugin()

            # get updated init commit
            init_commit_updated = Commit.objects(message="test init commit")[0]
            init_commit_updated.branches.sort()

            # Assert Values
            repo_branch = self.repository.branches[sample_branch]
            self.assertNotEqual(
                init_commit_old.branches, init_commit_updated.branches, " Branch not updated")
            self.assertTrue(
                repo_branch.name in init_commit_updated.branches, sample_branch+" is not in updated branches")

            # get updated init commit
            init_commit_updated = Commit.objects(message="test init commit")[0]
            init_commit_updated.branches.sort()

        # Assert - Previous states holds total states = total sample branches
        self.assertEqual(len(init_commit_updated.previous_states),
                         len(sample_branches), "previous states is not maintained!")
    
    def delete_tag(self,tag_name=''):
        # delete tag, clean garbage collection
        os.system("git -C ./tests/data/"+str(self.project_name) +
                  " tag -d "+tag_name)

        # Repository Garbage Collection
        self.git_gc()
                         
    def test_tag(self):
        test_author = pygit2.Signature("test", "test@email.edu")

        # get latest commit from git repo
        latest_commit = self.repository.revparse_single("HEAD~1")

        # create tag on it
        self.repository.create_tag(
            "test_tag", latest_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "test tag message")
        self.repository.create_tag(
            "test_tag_2", latest_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "test tag 2 message")

        # run plugin
        self.syncPlugin()

        # delete tag, clean garbage collection
        self.delete_tag('test_tag')

        # run plugin
        self.syncPlugin()

        # assert check with mongo - deleted_at for commit hash
        mongo_tag_1 = Tag.objects(name='test_tag')[0]
        self.assertIsNotNone(mongo_tag_1.deleted_at,
                             "tag not deleted in mongo but deleted in git")

        mongo_tag_2 = Tag.objects(name='test_tag_2')[0]
        self.assertIsNone(mongo_tag_2.deleted_at,
                          "Tag shown as deleted but actually not deleted")

        # Check if behavior for re-added tag for same commit where it was mark as deleted before
        recreate_tag_commit = self.repository.revparse_single("HEAD~3")
        self.repository.create_tag(
            "recreate_tag_test", recreate_tag_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "test tag message")
        
        self.syncPlugin()

        # -> Check tag is created
        mongo_tag_check = Tag.objects(name='recreate_tag_test')[0]
        self.assertIsNone(mongo_tag_check.deleted_at,
                            "Tag shown as deleted but actually not deleted")

        # Delete tag & recreate tag
        self.delete_tag('recreate_tag_test')

        self.syncPlugin()

        self.repository.create_tag(
            "recreate_tag_test", recreate_tag_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "test tag message 2")
        
        self.syncPlugin()
        mongo_tag_check = Tag.objects(name='recreate_tag_test')[0]
        self.assertIsNone(mongo_tag_check.deleted_at,
                            "Tag shown as deleted in mongodb but it recreated for same commit.")

        # Again Delete & Recreate tag
        self.delete_tag('recreate_tag_test')

        self.syncPlugin()

        self.repository.create_tag(
            "recreate_tag_test", recreate_tag_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "test tag message 2")
        
        self.syncPlugin()

        # Final Check
        mongo_tag_test_tag = Tag.objects(id=mongo_tag_1.id).get()
        mongo_tag_test_tag_2 = Tag.objects(id=mongo_tag_2.id).get()
        mongo_tag_recreate_tag_test = Tag.objects(id=mongo_tag_check.id).get()

        self.assertIsNotNone(mongo_tag_test_tag.deleted_at,
                             f"Final Test: {mongo_tag_test_tag.name} Tag not deleted in mongo but deleted in git")
        self.assertIsNone(mongo_tag_test_tag_2.deleted_at,
                          f"Final Test: {mongo_tag_test_tag_2.name} Tag shown as deleted but actually not deleted")
        self.assertIsNone(mongo_tag_recreate_tag_test.deleted_at,
                          f"Final Test: {mongo_tag_recreate_tag_test.name} Tag shown as deleted but actually not deleted")
        self.assertEqual(len(mongo_tag_recreate_tag_test.previous_states),2,'Tag previous states not maintained. It should be created count - 1')

        # It Check if tag is deleted from Git but not from mongo then again recreated with new message, then plugin should know that only message has been updated
        # It checks behavior of plugin for tag message that is updated without marked as deleted in mongoDB

        new_tag_commit = self.repository.revparse_single("HEAD~3")
        self.repository.create_tag(
            "new_tag", new_tag_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "message A")

        self.syncPlugin()

        self.delete_tag('new_tag')
        self.syncPlugin()

        self.repository.create_tag(
            "new_tag", new_tag_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "message A") # Intentionally same message

        self.syncPlugin()

        mongo_tag_new_tag = Tag.objects(name='new_tag')[0]
        self.assertEqual(len(mongo_tag_new_tag.previous_states),
                         1, 'previous state length should be 1')
        self.assertEqual(
            "message" not in mongo_tag_new_tag.previous_states[-1], True, 'message should not be in previous state as it is not updated')

        # Here, Tag deleted in git and again recreated with new message without sync plugin
        self.delete_tag('new_tag')

        self.repository.create_tag(
            "new_tag", new_tag_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "message C")
        self.syncPlugin()

        self.delete_tag('new_tag')
        self.syncPlugin()

        self.repository.create_tag(
            "new_tag", new_tag_commit.id, pygit2.GIT_OBJ_COMMIT, test_author, "message D")
        self.syncPlugin()

        self.delete_tag('new_tag')
        self.syncPlugin()

        mongo_tag_new_tag = Tag.objects(name='new_tag')[0]

        self.assertEqual(mongo_tag_new_tag.message,
                         'message D', 'Tag message not updated')
        self.assertIsNotNone(mongo_tag_new_tag.deleted_at,
                             f"Final Test: {mongo_tag_new_tag.name} Tag is deleted in repository but found not deleted in mongoDB")
        self.assertEqual(len(mongo_tag_new_tag.previous_states),
                         2, 'Tag previous states not maintained. It should be 3')
        self.assertEqual(
            mongo_tag_new_tag.previous_states[0]['message'], 'message A', 'Tag message should be message A')
        self.assertEqual(
            mongo_tag_new_tag.previous_states[1]['message'], 'message C', 'Tag message should be message C')

    def dropGitRepo(self, repository_path):
        try:
            shutil.rmtree(repository_path)
        except:
            pass
        print("Cleared testing git repo!")

    @classmethod
    def tearDownClass(cls):
        # Drop git repo after all tests
        cls.dropGitRepo(cls, cls.repository_path)


if __name__ == "__main__":
    unittest.main()

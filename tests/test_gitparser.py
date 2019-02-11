import unittest
import logging
import os
import datetime

from pyvcsshark.parser.gitparser import GitParser
from tests.datastoremock import DatastoreMock


class GitParserTest(unittest.TestCase):

    parser = None
    
    def setUp(self):
        # Setup logging
        logging.basicConfig(level=logging.ERROR)
        
        self.parser = GitParser()
        self.parser.detect(os.path.dirname(os.path.realpath(__file__))+"/data/testdatarepository")
        pass
    
    def test_detect(self):
        self.assertFalse(self.parser.detect("./nonsense/path"))
        pass
   
    def test_repositoryType(self):
        self.assertEqual(self.parser.repository_type, "git")
        pass
            

class GitParserCommitsTest(GitParserTest):
    
    list_of_commits = []
    
    @classmethod
    def setUpClass(cls):
        # Setup logging
        logging.basicConfig(level=logging.ERROR)
        
        cls.parser = GitParser()
        cls.parser.detect(os.path.dirname(os.path.realpath(__file__))+"/data/testdatarepository")
        cls.parser.initialize()
                
        datastore = DatastoreMock()
        cls.parser.parse(os.path.dirname(os.path.realpath(__file__))+"/data/testdatarepository", datastore, 2)

        # get the commits from our mockdatastore
        queue = datastore.get_commit_queue()
        
        while not queue.empty():
            cls.list_of_commits.append(queue.get())
            
        # sort the generated list
        cls.list_of_commits.sort(key=lambda x: x.committerDate)

    def test_parsing_commit1(self):
        commit1 = self.list_of_commits[0]
        
        # Checking commit attributes
        self.assertEqual("3c0a6fc133b8b50b8c217642fef7eb948f29b690", commit1.id)
        self.assertListEqual([], commit1.parents)
        self.assertEqual("first commit\n", commit1.message)
        self.assertListEqual([], commit1.tags)
        
        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)
        
        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453374841), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453374841), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)
        
        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.author.email)
        
        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.committer.email)
        
        # Check changed files
        self.assertEqual(3, len(commit1.changedFiles))
        
        # lib.jar
        test_file = [file for file in commit1.changedFiles if file.path == "lib.jar"][0]
        self.assertEqual("lib.jar", test_file.path)
        self.assertEqual(0, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertTrue(test_file.isBinary)
        self.assertEqual("A", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(30747, test_file.size)
        self.assertEqual(None, test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 0)
        
        # test.txt
        test_file = [file for file in commit1.changedFiles if file.path == "test.txt"][0]
        self.assertEqual("test.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("A", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(6, test_file.size)
        self.assertEqual(None, test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(0, test_file.hunks[0].old_start)
        self.assertEqual(0, test_file.hunks[0].old_lines)
        self.assertEqual("+test1\n", test_file.hunks[0].content)      

        # test2.txt
        test_file = [file for file in commit1.changedFiles if file.path == "test2.txt"][0]
        self.assertEqual("test2.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("A", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(6, test_file.size)
        self.assertEqual(None, test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(0, test_file.hunks[0].old_start)
        self.assertEqual(0, test_file.hunks[0].old_lines)
        self.assertEqual("+test2\n", test_file.hunks[0].content)

    def test_parsing_commit2(self):
        commit1 = self.list_of_commits[1]
        
        # Checking commit attributes
        self.assertEqual("022a1584a31ccc0816d20bfbbeb5c45aa290c7dd", commit1.id)
        self.assertListEqual(['3c0a6fc133b8b50b8c217642fef7eb948f29b690'], commit1.parents)
        self.assertEqual("second commit\n", commit1.message)
        self.assertListEqual([], commit1.tags)
        
        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)
        
        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453375367), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453375367), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)

        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.author.email)
        
        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.committer.email)
        
        # Check changed files
        self.assertEqual(3, len(commit1.changedFiles))
        
        # test3.txt
        test_file = [file for file in commit1.changedFiles if file.path == "test3.txt"][0]
        self.assertEqual("test3.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("A", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(6, test_file.size)
        self.assertEqual('3c0a6fc133b8b50b8c217642fef7eb948f29b690', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        
        # test.txt
        test_file = [file for file in commit1.changedFiles if file.path == "test.txt"][0]
        self.assertEqual("test.txt", test_file.path)
        self.assertEqual(0, test_file.linesAdded)
        self.assertEqual(1, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("D", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(0, test_file.size)
        self.assertEqual('3c0a6fc133b8b50b8c217642fef7eb948f29b690', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(0, test_file.hunks[0].new_lines)
        self.assertEqual(0, test_file.hunks[0].new_start)
        self.assertEqual(1, test_file.hunks[0].old_start)
        self.assertEqual(1, test_file.hunks[0].old_lines)
        self.assertEqual("-test1\n", test_file.hunks[0].content)        
        
        # test2.txt
        test_file = [file for file in commit1.changedFiles if file.path == "test2.txt"][0]
        self.assertEqual("test2.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(1, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("M", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(5, test_file.size)
        self.assertEqual('3c0a6fc133b8b50b8c217642fef7eb948f29b690', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(1, test_file.hunks[0].old_start)
        self.assertEqual(1, test_file.hunks[0].old_lines)
        self.assertEqual("-test2\n+test\n", test_file.hunks[0].content)
        
    def test_parsing_commit3(self):
        commit1 = self.list_of_commits[2]
        
        # Checking commit attributes
        self.assertEqual("5ed91aa4557b5042fa7096bf6c69463024c46b6f", commit1.id)
        self.assertListEqual(['022a1584a31ccc0816d20bfbbeb5c45aa290c7dd'], commit1.parents)
        self.assertEqual("test$#.*;ßöä%!&\n", commit1.message)

        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)
        
        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453375768), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453375768), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)
        
        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.author.email)
        
        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.committer.email)
        
        # Check changed files
        self.assertEqual(1, len(commit1.changedFiles))
        
        # test3.txt
        test_file = [file for file in commit1.changedFiles if file.path == "program.py"][0]
        self.assertEqual("program.py", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("A", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(15, test_file.size)
        self.assertEqual('022a1584a31ccc0816d20bfbbeb5c45aa290c7dd', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(0, test_file.hunks[0].old_start)
        self.assertEqual(0, test_file.hunks[0].old_lines)
        self.assertEqual("+import nothing\n", test_file.hunks[0].content)    
                               
    def test_parsing_commit4(self):
        commit1 = self.list_of_commits[3]
        
        # Checking commit attributes
        self.assertEqual("6fe2eff1f0bbc3220128e082385a01558e3306a6", commit1.id)
        self.assertListEqual(['5ed91aa4557b5042fa7096bf6c69463024c46b6f'], commit1.parents)
        self.assertEqual("moved\n", commit1.message)
        self.assertListEqual([], commit1.tags)
        
        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)
        
        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453379814), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453379814), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)
        
        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.author.email)
        
        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.committer.email)
        
        # Check changed files
        self.assertEqual(2, len(commit1.changedFiles))
        
        # lib.jar
        test_file = [file for file in commit1.changedFiles if file.path == "libs/lib.jar"][0]
        self.assertEqual("libs/lib.jar", test_file.path)
        self.assertEqual(0, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertTrue(test_file.isBinary)
        self.assertEqual("R", test_file.mode)
        self.assertEqual('lib.jar', test_file.oldPath)
        self.assertEqual(30747, test_file.size)
        self.assertEqual('5ed91aa4557b5042fa7096bf6c69463024c46b6f', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(0, len(test_file.hunks))

        # program1.py
        test_file = [file for file in commit1.changedFiles if file.path == "program1.py"][0]
        self.assertEqual("program1.py", test_file.path)
        self.assertEqual(0, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("R", test_file.mode)
        self.assertEqual('program.py', test_file.oldPath)
        self.assertEqual(15, test_file.size)
        self.assertEqual('5ed91aa4557b5042fa7096bf6c69463024c46b6f', test_file.parent_revision_hash)

        # hunks
        self.assertEqual(0, len(test_file.hunks))
        
    def test_parsing_commit5(self):
        commit1 = self.list_of_commits[4]
        
        # Checking commit attributes
        self.assertEqual("a8dfa0944a8c3d97f217d34705de2ae1c7e68793", commit1.id)
        self.assertListEqual(['6fe2eff1f0bbc3220128e082385a01558e3306a6'], commit1.parents)
        self.assertEqual("branch3\n", commit1.message)
        
        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)
        
        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380347), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380347), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)
        
        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.author.email)
        
        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.committer.email)
        
        # Check changed files
        self.assertEqual(1, len(commit1.changedFiles))
        
        # branch1.txt
        test_file = [file for file in commit1.changedFiles if file.path == "branch3.txt"][0]
        self.assertEqual("branch3.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("A", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(8, test_file.size)
        self.assertEqual('6fe2eff1f0bbc3220128e082385a01558e3306a6', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(0, test_file.hunks[0].old_start)
        self.assertEqual(0, test_file.hunks[0].old_lines)
        self.assertEqual("+branch3\n", test_file.hunks[0].content)

    def test_parsing_commit6(self):
        commit1 = self.list_of_commits[5]
        
        # Checking commit attributes
        self.assertEqual("e91b0419196248c664f2b2e06c9a2c97452fda5c", commit1.id)
        self.assertListEqual(['a8dfa0944a8c3d97f217d34705de2ae1c7e68793'], commit1.parents)
        self.assertEqual("testbranch3\n", commit1.message)
        self.assertListEqual([], commit1.tags)

        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)

        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380366), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380366), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)

        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.author.email)
        
        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.committer.email)

        # Check changed files
        self.assertEqual(1, len(commit1.changedFiles))
        
        # testbranch3.txt
        test_file = [file for file in commit1.changedFiles if file.path == "testbranch3.txt"][0]
        self.assertEqual("testbranch3.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("A", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(12, test_file.size)
        self.assertEqual('a8dfa0944a8c3d97f217d34705de2ae1c7e68793', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(0, test_file.hunks[0].old_start)
        self.assertEqual(0, test_file.hunks[0].old_lines)
        self.assertEqual("+testbranch3\n", test_file.hunks[0].content)

    def test_parsing_commit7(self):
        commit1 = self.list_of_commits[6]
        
        # Checking commit attributes
        self.assertEqual("204d306b10e123f2474612a297b83be6ac79e519", commit1.id)
        self.assertListEqual(['e91b0419196248c664f2b2e06c9a2c97452fda5c'], commit1.parents)
        self.assertEqual("lines\n", commit1.message)
        self.assertListEqual([], commit1.tags)

        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)

        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380546), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453380546), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)

        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.author.email)
        
        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.committer.email)

        # Check changed files
        self.assertEqual(1, len(commit1.changedFiles))

        # lines.txt
        test_file = [file for file in commit1.changedFiles if file.path == "lines.txt"][0]
        self.assertEqual("lines.txt", test_file.path)
        self.assertEqual(40, test_file.linesAdded)
        self.assertEqual(0, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("A", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(271, test_file.size)
        self.assertEqual('e91b0419196248c664f2b2e06c9a2c97452fda5c', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)
        self.assertEqual(40, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(0, test_file.hunks[0].old_start)
        self.assertEqual(0, test_file.hunks[0].old_lines)
        self.assertEqual("+line1\n+line2\n+line3\n+line4\n+line5\n+line6\n+line7\n+line8\n+line9\n+line10\n" +
                         "+line11\n+line12\n+line13\n+line14\n+line15\n+line16\n+line17\n+line18\n+line19\n+line20\n" +
                         "+line21\n+line22\n+line23\n+line24\n+line25\n+line26\n+line27\n+line28\n+line29\n+line30\n" +
                         "+line31\n+line32\n+line33\n+line34\n+line35\n+line36\n+line37\n+line38\n+line39\n+line40\n",
                         test_file.hunks[0].content)
        
    def test_parsing_commit8(self):
        commit1 = self.list_of_commits[7]

        # Checking commit attributes
        self.assertEqual("830c29f111f261e26897d42e94c15960a512c0e4", commit1.id)
        self.assertListEqual(['204d306b10e123f2474612a297b83be6ac79e519'], commit1.parents)
        self.assertEqual("changed lines\n", commit1.message)
        self.assertListEqual([], commit1.tags)

        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)

        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453381291), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1453381291), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)

        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.author.email)

        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("ftrautsch@googlemail.com", commit1.committer.email)

        # Check changed files
        self.assertEqual(1, len(commit1.changedFiles))

        # branch1.txt
        test_file = [file for file in commit1.changedFiles if file.path == "lines.txt"][0]
        self.assertEqual("lines.txt", test_file.path)
        self.assertEqual(2, test_file.linesAdded)
        self.assertEqual(2, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("M", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(266, test_file.size)
        self.assertEqual('204d306b10e123f2474612a297b83be6ac79e519', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 3)

        self.assertEqual(0, test_file.hunks[0].new_lines)
        self.assertEqual(0, test_file.hunks[0].new_start)
        self.assertEqual(1, test_file.hunks[0].old_start)
        self.assertEqual(1, test_file.hunks[0].old_lines)
        self.assertEqual("-line1\n", test_file.hunks[0].content)

        self.assertEqual(1, test_file.hunks[1].new_lines)
        self.assertEqual(19, test_file.hunks[1].new_start)
        self.assertEqual(20, test_file.hunks[1].old_start)
        self.assertEqual(1, test_file.hunks[1].old_lines)
        self.assertEqual("-line20\n+\n", test_file.hunks[1].content)

        self.assertEqual(1, test_file.hunks[2].new_lines)
        self.assertEqual(40, test_file.hunks[2].new_start)
        self.assertEqual(40, test_file.hunks[2].old_start)
        self.assertEqual(0, test_file.hunks[2].old_lines)
        self.assertEqual("+line41\n", test_file.hunks[2].content)

    def test_merge_commit(self):
        commit1 = self.list_of_commits[11]

        # Checking commit attributes
        self.assertEqual("c298c565ac291bb3fd8e74da9798cc5d9a49e4e5", commit1.id)
        self.assertListEqual(['88750d1abeff99a162801d2a38a1ffa3b0f0d759', '6730077bc66400329f01a06c27e7dc9163f14f3f'],
                             commit1.parents)
        self.assertEqual("blub\n", commit1.message)
        self.assertListEqual([], commit1.tags)

        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)

        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1549887589), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1549887589), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)

        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("fabian.trautsch@informatik.uni-goettingen.de", commit1.author.email)

        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("fabian.trautsch@informatik.uni-goettingen.de", commit1.committer.email)

        # Check changed files
        self.assertEqual(2, len(commit1.changedFiles))

        # lines.txt
        test_file = [file for file in commit1.changedFiles if file.path == "lines.txt"][0]
        self.assertEqual("lines.txt", test_file.path)
        self.assertEqual(2, test_file.linesAdded)
        self.assertEqual(2, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("M", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(266, test_file.size)
        self.assertEqual('6730077bc66400329f01a06c27e7dc9163f14f3f', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)

        self.assertEqual(2, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(1, test_file.hunks[0].old_start)
        self.assertEqual(2, test_file.hunks[0].old_lines)
        self.assertEqual("-line1\n-line3\n+line2\n+line4\n", test_file.hunks[0].content)

        # test2.txt
        test_file = [file for file in commit1.changedFiles if file.path == "test2.txt"][0]
        self.assertEqual("test2.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(1, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("M", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(6, test_file.size)
        self.assertEqual('88750d1abeff99a162801d2a38a1ffa3b0f0d759', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)

        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(1, test_file.hunks[0].old_start)
        self.assertEqual(1, test_file.hunks[0].old_lines)
        self.assertEqual("-test\n+test2\n", test_file.hunks[0].content)

    def test_merge_commit_changed_on_master_and_feature_branch(self):
        commit1 = self.list_of_commits[15]

        # Checking commit attributes
        self.assertEqual("b104c54f5f7e4614afa4b9cf3e7e21f0050abc1c", commit1.id)
        self.assertListEqual(['09788da8a216799a6d611a9b06bd54162b44c5d2', 'd4aba22cd313977e5e6e6b4f915df0bce6ac7468'],
                             commit1.parents)
        self.assertEqual("Merge branch 'lines'\n", commit1.message)
        self.assertListEqual([], commit1.tags)

        # Checking branches
        list_of_branch_names = []
        for branchModel in commit1.branches:
            list_of_branch_names.append(branchModel.name)

        self.assertEqual(3, len(commit1.branches))
        self.assertIn("refs/heads/master", list_of_branch_names)
        self.assertIn("refs/remotes/origin/HEAD", list_of_branch_names)
        self.assertIn("refs/remotes/origin/master", list_of_branch_names)

        # Check times
        self.assertEqual(datetime.datetime.utcfromtimestamp(1549889088), commit1.authorDate)
        self.assertEqual(datetime.datetime.utcfromtimestamp(1549889088), commit1.committerDate)
        self.assertEqual(60, commit1.authorOffset)
        self.assertEqual(60, commit1.committerOffset)

        # Check author
        self.assertEqual("Fabian Trautsch", commit1.author.name)
        self.assertEqual("fabian.trautsch@informatik.uni-goettingen.de", commit1.author.email)

        # Check committer
        self.assertEqual("Fabian Trautsch", commit1.committer.name)
        self.assertEqual("fabian.trautsch@informatik.uni-goettingen.de", commit1.committer.email)

        # Check changed files
        self.assertEqual(3, len(commit1.changedFiles))

        # lines.txt (master branch)
        test_file = [file for file in commit1.changedFiles if file.path == "lines.txt"][0]
        self.assertEqual("lines.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(1, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("M", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(266, test_file.size)
        self.assertEqual('09788da8a216799a6d611a9b06bd54162b44c5d2', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)

        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(40, test_file.hunks[0].new_start)
        self.assertEqual(40, test_file.hunks[0].old_start)
        self.assertEqual(1, test_file.hunks[0].old_lines)
        self.assertEqual("-line41\n+line42\n", test_file.hunks[0].content)

        # lines.txt (feature branch)
        test_file = [file for file in commit1.changedFiles if file.path == "lines.txt"][1]
        self.assertEqual("lines.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(1, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("M", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(266, test_file.size)
        self.assertEqual('d4aba22cd313977e5e6e6b4f915df0bce6ac7468', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)

        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(1, test_file.hunks[0].old_start)
        self.assertEqual(1, test_file.hunks[0].old_lines)
        self.assertEqual("-line2\n+line1\n", test_file.hunks[0].content)

        # test2.txt
        test_file = [file for file in commit1.changedFiles if file.path == "test2.txt"][0]
        self.assertEqual("test2.txt", test_file.path)
        self.assertEqual(1, test_file.linesAdded)
        self.assertEqual(1, test_file.linesDeleted)
        self.assertFalse(test_file.isBinary)
        self.assertEqual("M", test_file.mode)
        self.assertEqual(None, test_file.oldPath)
        self.assertEqual(6, test_file.size)
        self.assertEqual('09788da8a216799a6d611a9b06bd54162b44c5d2', test_file.parent_revision_hash)

        # Hunks
        self.assertEqual(len(test_file.hunks), 1)

        self.assertEqual(1, test_file.hunks[0].new_lines)
        self.assertEqual(1, test_file.hunks[0].new_start)
        self.assertEqual(1, test_file.hunks[0].old_start)
        self.assertEqual(1, test_file.hunks[0].old_lines)
        self.assertEqual("-test2\n+test3\n", test_file.hunks[0].content)


if __name__ == "__main__":
    unittest.main()

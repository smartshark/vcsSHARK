import datetime

class CommitModel(object):
    """Model that represents a commit to a repository
    
    :param id: id of the ocmmit (e.g. a revision hash)
    :param branches: set of branches to which the commit belongs to
    :param tags: list of tags of type :class:`pyvcsshark.dbmodels.models.TagModel`
    :param parents: list of strings, which contains the parent ids of the commit
    :param author: author of the commit. Must be of type :class:`pyvcsshark.dbmodels.models.PeopleModel`
    :param committer: committer of the commit. Must be of type :class:`pyvcsshark.dbmodels.models.PeopleModel`
    :param message: string of the commit message
    :param changedFiles: list of files of type :class:`pyvcsshark.dbmodels.models.FileModel`
    :param authorDate: date of the creation of the change of the commit (must be a UNIX timestamp)
    :param authorOffset: offset for the authordate (timezone)
    :param committerDate: date of the commit (must be a UNIX timestamp)
    :param committerOffset: offset for the committerdate (timezone)
    
    .. NOTE:: If your parser do not provide all information, then just use the default ones
    """
    
    def __init__(self, id, branches=[], tags=[], parents=[], 
                 author=None, committer=None, message=None, changedFiles=[], authorDate=None,
                 authorOffset=None, committerDate=None, committerOffset=None):
        self.id = id
        self.branches = branches
        self.tags = tags
        self.parents = parents
        self.author = author
        self.committer = committer
        self.message = message
        self.changedFiles = changedFiles
        self.authorDate = authorDate
        self.authorOffset = authorOffset
        self.committerDate = committerDate
        self.committerOffset = committerOffset
        
    @property
    def authorDate(self):
        return self._authorDate
    
    @authorDate.setter
    def authorDate(self, value):
        if(value is not None and not isinstance(value, int)):
            raise Exception("Date must be a UNIX timestamp!")
        self._authorDate = datetime.datetime.utcfromtimestamp(value)
        
    @property
    def committerDate(self):
        return self._committerDate
    
    @committerDate.setter
    def committerDate(self, value):
        if(value is not None and not isinstance(value, int)):
            raise Exception("Date must be a UNIX timestamp!")
        self._committerDate = datetime.datetime.utcfromtimestamp(value)
        
    @property
    def branches(self):
        return self._branches
        
    @branches.setter
    def branches(self, value):
        if(value is not None and type(value) is not set):
            raise Exception("Branches must be a set!")
        
        if(value is not None):
            for branch in value:
                if(not isinstance(branch, BranchModel) and branch is not None):
                    raise Exception("Branch is not a Branch model or None!")
        
        self._branches = value
    
    @property
    def tags(self):
        return self._tags
    
    @tags.setter
    def tags(self, value):
        if(value is not None and type(value) is not list):
            raise Exception("Tags must be a list!")
        
        if(value is not None):
            for tag in value:
                if(not isinstance(tag, TagModel)):
                    raise Exception("Tag is not a Tag model!")
        
        self._tags = value
    
    @property
    def author(self):
        return self._author
    
    @author.setter
    def author(self, value):
        if(value is not None and not isinstance(value, PeopleModel)):
            raise Exception("Author must be of type PeopleModel!")
        
        self._author = value
    
    @property
    def committer(self):
        return self._committer
    
    @committer.setter
    def committer(self, value):
        if(value is not None and not isinstance(value, PeopleModel)):
            raise Exception("Committer must be of type PeopleModel!")
        
        self._committer = value
        
    @property
    def changedFiles(self):
        return self._changedFiles
    
    @changedFiles.setter
    def changedFiles(self, value):
        if(value is not None and type(value) is not list):
            raise Exception("ChangedFiles must be a list!")
        
        if(value is not None):
            for file in value:
                if(not isinstance(file, FileModel)):
                    raise Exception("File must be of type FileModel!")
        
        self._changedFiles = value
        
        

    def __str__(self):
        files = ""
        for file in self.changedFiles:
            files += file.path
            
        branches = ""
        for branch in self.branches:
            branches+=branch.name
            
        tags = ""
        for tag in self.tags:
            tags+=tag.name
        
        return "<CommitHash: %s>, <Branches: %s>, <Tags: %s>, <Parents: %s>, <AuthorName: %s>,"\
               "<AuthorEmail: %s>, <AuthorTime: %s>, <AuthorOffset: %s>, <CommitterName: %s>, "\
                "<CommitterEmail: %s>, <CommitterTime: %s>, <CommitterOffset: %s>, <Message: %s>"\
                "<ChangedFiles: %s>" % (self.id, branches, tags,
                                        ",".join(self.parents), self.author.name, self.author.email,
                                        self.authorDate, self.authorOffset, self.committer.name,
                                        self.committer.email, self.committerDate, self.committerOffset,
                                        self.message, files)
        
        
        
class FileModel(object):
    """ Model that holds the changes of the files.
    
    :param path: path to the file that was changed
    :param size: size of the file that was changed
    :param linesAdded: count of how many lines were added to the file
    :param linesDeleted: count of how many lines were deleted 
    :param isBinary: boolean, which is true if the file is a binary file
    :param mode: mode of the file action (e.g. "A" for file was added)
    :param hunks: list of hunks for the file
    :param oldPath: old path to the file, which only exist if a file was copied or moved
    :param parent_revision_hash: hash of the parent commit
    """
    def __init__(self, path, size=None, linesAdded=None, linesDeleted=None,
                 isBinary= None, mode=None, hunks=[], oldPath=None, parent_revision_hash=None):
        self.path = path
        self.size = size
        self.linesAdded = linesAdded
        self.linesDeleted = linesDeleted
        self.isBinary = isBinary
        self.mode = mode
        self.hunks = hunks
        self.oldPath = oldPath
        self.parent_revision_hash = parent_revision_hash
        
    @property
    def hunks(self):
        return self._hunks
        
    @hunks.setter
    def hunks(self, value):
        # Check hunks
        if(value is not None and type(value) is not list):
            raise Exception("Hunks must be a list!")
        
        self._hunks = value


class Hunk(object):
    def __init__(self, new_start, new_lines, old_start, old_lines, content):
        self.new_start = new_start
        self.new_lines = new_lines
        self.old_start = old_start
        self.old_lines = old_lines
        self.content = content

    def __str__(self):
        return "@@ -%s,%s +%s,%s @@ \n %s" % (self.old_start, self.old_lines, self.new_start, self.new_lines, self.content)


class TagModel(object):
    """ Model that holds the information for the different tags.

    :param name: name of the tag
    :param message: message of the tag
    :param tagger: creator of the tag. Must be of type :class:`pyvcsshark.dbmodels.models.PeopleModel`.
    :param taggerDate: date of the creation of the tag. Must be a UNIX timestamp.
    :param taggerOffset: offset for taggerdate (timezone)
    """
    def __init__(self, name, message=None, tagger=None, taggerDate=None, taggerOffset=None):
        self.name = name
        self.message = message
        self.tagger = tagger
        self.taggerDate = taggerDate
        self.taggerOffset = taggerOffset

    @property
    def taggerDate(self):
        return self._taggerDate
    
    @taggerDate.setter
    def taggerDate(self, value):
        if(value is not None and not isinstance(value, int)):
            raise Exception("Date must be a UNIX timestamp!")
        
        if(value is not None):
            self._taggerDate = datetime.datetime.utcfromtimestamp(value)
        else:
            self._taggerDate = None
            
    @property
    def tagger(self):
        return self._tagger
    
    @tagger.setter
    def tagger(self, value):
        if(value is not None and not isinstance(value, PeopleModel)):
            raise Exception("Tagger is not a People model!")
        self._tagger = value


class BranchTipModel(object):

    def __init__(self, name, target_revision_hash, is_origin_head):
        self.name = name
        self.target = target_revision_hash
        self.is_origin_head = is_origin_head

        def __repr__(self):
            return '{} -> {} is_origin_head: {}'.format(self.name, self.target, self.is_origin_head)

        def __str__(self):
            return self.name


class BranchModel(object):
    """ Model which holds the branch information.

    :param name: name of the branch
    """
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(repr(self))


class PeopleModel(object):
    """ Model that holds the people information.

    :param name: name of the person
    :param email: email of the person
    """
    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

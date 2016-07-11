from mongoengine import Document, StringField, DateTimeField, ListField, DateTimeField, IntField, BooleanField, ObjectIdField

class FileAction(Document):
    """ Document that inherits from :class:`mongoengine.Document`. Holds information for the fileaction collection.

    
    :property projectId: id of the project, which belongs to the file action (type: :class:`mongoengine.fields.ObjectIdField`)
    :property fileId: id of the file, which belongs to the file action (type: :class:`mongoengine.fields.ObjectIdField`)
    :property revisionHash: hash of the revision (type: :class:`mongoengine.fields.StringField`)
    :property mode: mode of the file action (type: :class:`mongoengine.fields.StringField`)
    
        .. NOTE:: It can only be ("A")dded, ("D")eleted, ("M")odified, ("C")opied or Moved, "T" for links (special in git)
        
    :property sizeAtCommit: size of the file on commit (type: :class:`mongoengine.fields.IntField`)
    :property linesAdded: number of lines added in this action (type: :class:`mongoengine.fields.IntField`)
    :property linesDeleted: number of lines deleted in this action (type: :class:`mongoengine.fields.IntField`)
    :property isBinary: indicates if the file is a binary file or not (type: :class:`mongoengine.fields.BooleanField`)
    :property oldFilePathId: object id of old file (if it was moved or copied) (type: :class:`mongoengine.fields.ObjectIdField`)
    :property hunkIds: list of ids to the different hunks of this action (type: :class:`mongoengine.fields.ListField(:class:`mongoengine.fields.ObjectIdField`)`)
        
    .. NOTE:: Unique (or primary key) are the fields: projectId, fileId, and revisionHash.
    
    .. NOTE:: oldFilePathId only exists, if the file was created due to a copy or move action
    

    """
    MODES = ('A', 'M', 'D', 'C', 'T')
    #pk fileId, revisionhash, projectId
    projectId = ObjectIdField(required=True,unique_with=['fileId', 'revisionHash'] )
    fileId = ObjectIdField(required=True,unique_with=['projectId', 'revisionHash'] )
    revisionHash = StringField(max_length=50, required=True,unique_with=['projectId', 'fileId'] )
    mode = StringField(max_length=1, required=True, choices=MODES)
    sizeAtCommit = IntField()
    linesAdded = IntField()
    linesDeleted = IntField()
    isBinary = BooleanField()

    # oldFilePathId is only set, if we detected a copy or move operation
    oldFilePathId = ObjectIdField()
    hunkIds = ListField(ObjectIdField())
    
        
    


class Hunk(Document):
    """ Document that inherits from :class:`mongoengine.Document`. Holds information for the hunk collection.
    :property new_start: new starting of the hunk in new file
    :property new_lines: number of new lines
    :property old_start: old start of the hunk in the old file
    :property old_lines: old number of lines
    :property content: content of the hunk.

    For more information: https://en.wikipedia.org/wiki/Diff#Unified_format)
    """

    new_start = IntField(required=True)
    new_lines = IntField(required=True)
    old_start = IntField(required=True)
    old_lines = IntField(required=True)
    content = StringField(required=True)


class File(Document):
    """ Document that inherits from :class:`mongoengine.Document`. Holds information for the file collection.
    
    :property projectId: id of the project, which belongs to the file action (type: :class:`mongoengine.fields.ObjectIdField`)
    :property path: path of the file (type: :class:`mongoengine.fields.StringField`)
    :property name: name of the file (type: :class:`mongoengine.fields.StringField`)
    
    .. NOTE:: Unique (or primary key) are the fields: path, name, and projectId.
    """
    
    #PK path, name, projectId
    projectId = ObjectIdField(required=True,unique_with=['path', 'name'] )
    path = StringField(max_length=300, required=True,unique_with=['projectId', 'name'] )
    name = StringField(max_length=100, required=True,unique_with=['path', 'projectId'] )

class Tag(Document):
    """ Document that inherits from :class:`mongoengine.Document`. Holds information for the tag collection.
    
    :property projectId: id of the project, which belongs to the file action (type: :class:`mongoengine.fields.ObjectIdField`)
    :property name: name of the tag (type: :class:`mongoengine.fields.StringField`)
    :property message: message of the tag (type: :class:`mongoengine.fields.StringField`)
    :property taggerId: id of the person who created the tag (type: :class:`mongoengine.fields.ObjectIdField`)
    :property date: date of the creation of the tag (type: :class:`mongoengine.fields.DateTimeField`)
    :property offset: offset of the tag creation date for timezones (type: :class:`mongoengine.fields.IntField`)
    
    .. NOTE:: Unique (or primary key) are the fields: name and projectId.
    """
    
    
     #PK: project, name
    projectId = ObjectIdField(required=True,unique_with=['name'] )#
    name = StringField(max_length=150, required=True, unique_with=['projectId'])
    message = StringField()
    taggerId = ObjectIdField()
    date = DateTimeField()
    offset = IntField()
    
class People(Document):
    """ Document that inherits from :class:`mongoengine.Document`. Holds information for the people collection.
    
    :property name: name of the person (type: :class:`mongoengine.fields.StringField`)
    :property email: email of the person (type: :class:`mongoengine.fields.StringField`)
    
    .. NOTE:: Unique (or primary key) are the fields: name and email.
    """
    
     #PK: email, name
    email = StringField(max_length=150, required=True, unique_with=['name'])             
    name = StringField(max_length=150, required=True, unique_with=['email'])

    def __hash__(self):
        return hash(self.name+self.email)
    
    
class Project(Document):
    """ Document that inherits from :class:`mongoengine.Document`. Holds information for the project collection.
    
    :property url: url to the project repository (type: :class:`mongoengine.fields.StringField`)
    :property name: name of the project (type: :class:`mongoengine.fields.StringField`)
    :property repositoryType: type of the repository (type: :class:`mongoengine.fields.StringField`)
    
    .. NOTE:: Unique (or primary key) is the field url.
    """
    # PK uri
    url = StringField(max_length=400, required=True, unique=True)
    name = StringField(max_length=100, required=True)
    repositoryType = StringField(max_length=15)
    
        

class Commit(Document):
    """ Document that inherits from :class:`mongoengine.Document`. Holds information for the commit collection.
    
    :property projectId: id of the project, which belongs to the file action (type: :class:`mongoengine.fields.ObjectIdField`)
    :property revisionHash: revision hash of the commit (type: :class:`mongoengine.fields.StringField`)
    :property branches: list of branches to which the commit belongs to (type: :class:`mongoengine.fields.ListField(:class:`mongoengine.fields.StringField`)`)
    :property tagIds: list of tag ids, which belong to the commit (type: :class:`mongoengine.fields.ListField(:class:`mongoengine.fields.ObjectIdField`)`)
    :property parents: list of parents of the commit (type: :class:`mongoengine.fields.ListField(:class:`mongoengine.fields.StringField`)`)
    :property authorId: id of the author of the commit (type: :class:`mongoengine.fields.ObjectIdField`)
    :property authorDate: date when the commit was created (type: :class:`mongoengine.fields.DateTimeField`)
    :property authorOffset: offset of the authorDate (type: :class:`mongoengine.fields.IntField`)
    :property committerId: id of the committer of the commit (type: :class:`mongoengine.fields.ObjectIdField`)
    :property committerDate: date when the commit was committed (type: :class:`mongoengine.fields.DateTimeField`)
    :property committerOffset: offset of the committerDate (type: :class:`mongoengine.fields.IntField`)
    :property message: commit message (type: :class:`mongoengine.fields.StringField`)
    :property fileActionIds: list of file action ids, which belong to the commit (type: :class:`mongoengine.fields.ListField(:class:`mongoengine.fields.ObjectIdField`)`)
    
    .. NOTE:: Unique (or primary key) are the fields projectId and revisionHash.
    """

    #PK: projectId and revisionhash
    projectId = ObjectIdField(required=True,unique_with=['revisionHash'] )
    revisionHash = StringField(max_length=50, required=True, unique_with=['projectId'])
    branches = ListField(StringField(max_length=100))
    tagIds = ListField(ObjectIdField())
    parents = ListField(StringField(max_length=50))
    authorId = ObjectIdField()
    authorDate = DateTimeField()
    authorOffset = IntField()
    committerId = ObjectIdField()
    committerDate = DateTimeField()
    committerOffset = IntField()
    message = StringField()
    fileActionIds = ListField(ObjectIdField())

    
    def __str__(self):
        return ""


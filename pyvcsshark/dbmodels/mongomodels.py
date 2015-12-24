'''
Created on 09.12.2015

@author: fabian
'''

from mongoengine import Document, StringField, DateTimeField, ListField, DateTimeField, IntField, BooleanField, ObjectIdField

class FileAction(Document):
    #pk fileId, revisionhash, projectId
    projectId = ObjectIdField(required=True,unique_with=['fileId', 'revisionHash', 'mode'] )
    fileId = ObjectIdField(required=True,unique_with=['projectId', 'revisionHash', 'mode'] )
    revisionHash = StringField(max_length=50, required=True,unique_with=['projectId', 'fileId', 'mode'] )
    mode = StringField(max_length=3, required=True, unique_with=['projectId', 'fileId', 'revisionHash'])
    sizeAtCommit = IntField()
    linesAdded = IntField()
    linesDeleted = IntField()
    isBinary = BooleanField()
    
    
    # oldFilePathId is only set, if we detected a copy or move operation
    oldFilePathId = ObjectIdField()
    hunkIds = ListField(ObjectIdField())
    
        
    


class Hunk(Document):
    content = StringField(required=True)

class File(Document):
    #PK path, name, projectId
    projectId = ObjectIdField(required=True,unique_with=['path', 'name'] )
    path = StringField(max_length=300, required=True,unique_with=['projectId', 'name'] )
    name = StringField(max_length=100, required=True,unique_with=['path', 'projectId'] )

class Tag(Document):
    
     #PK: project, name
    projectId = ObjectIdField(required=True,unique_with=['name'] )#
    name = StringField(max_length=150, required=True, unique_with=['projectId'])
    message = StringField()
    taggerId = ObjectIdField()
    date = DateTimeField()
    offset = IntField()
    
class People(Document):
    
     #PK: email, name
    email = StringField(max_length=150, required=True, unique_with=['name'])             
    name = StringField(max_length=150, required=True, unique_with=['email'])

    def __hash__(self):
        return hash(self.name+self.email)
    
    
class Project(Document):
    # PK uri
    url = StringField(max_length=400, required=True, unique=True)
    name = StringField(max_length=100, required=True)
    repositoryType = StringField(max_length=15)
    
        

class Commit(Document):

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
    

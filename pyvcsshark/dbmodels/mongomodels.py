from mongoengine import Document, StringField, ListField, DateTimeField, IntField, BooleanField, ObjectIdField, \
    DictField


class Project(Document):
    meta = {
        'indexes': [
            '#name'
        ],
        'shard_key': ('name', ),
    }

    # PK: name
    # Shard Key: hashed name
    name = StringField(max_length=200, required=True, unique=True)


class MailingList(Document):
    meta = {
        'indexes': [
            '#name'
        ],
        'shard_key': ('name', ),
    }

    # PK: name
    # Shard Key: hashed name

    project_id = ObjectIdField(required=True)
    name = StringField(required=True)
    last_updated = DateTimeField()


class Message(Document):
    meta = {
        'indexes': [
            'message_id'
        ],
        'shard_key': ('message_id', 'mailing_list_id'),
    }

    # PK: message_id
    # Shard Key: message_id, mailing_list_id

    message_id = StringField(required=True, unique_with=['mailing_list_id'])
    mailing_list_id = ObjectIdField(required=True)
    reference_ids = ListField(ObjectIdField())
    in_reply_to_id = ObjectIdField()
    from_id = ObjectIdField()
    to_ids = ListField(ObjectIdField())
    cc_ids = ListField(ObjectIdField())
    subject = StringField()
    body = StringField()
    date = DateTimeField()
    patches = ListField(StringField())


class IssueSystem(Document):
    meta = {
        'indexes': [
            '#url'
        ],
        'shard_key': ('url', ),
    }

    # PK: url
    # Shard Key: hashed url

    project_id = ObjectIdField(required=True)
    url = StringField(required=True)
    last_updated = DateTimeField()


class Issue(Document):
    meta = {
        'indexes': [
            'external_id',
            'issue_system_id'
        ],
        'shard_key': ('external_id', 'issue_system_id'),
    }

    # PK: external_id, issue_system_id
    # Shard Key: external_id, issue_system_id

    external_id = StringField(unique_with=['issue_system_id'])
    issue_system_id = ObjectIdField(required=True)
    title = StringField()
    desc = StringField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    creator_id = ObjectIdField()
    reporter_id = ObjectIdField()

    issue_type = StringField()
    priority = StringField()
    status = StringField()
    affects_versions = ListField(StringField())
    components = ListField(StringField())
    labels = ListField(StringField())
    resolution = StringField()
    fix_versions = ListField(StringField())
    assignee_id = ObjectIdField()
    issue_links = ListField(DictField())
    parent_issue_id = ObjectIdField()
    original_time_estimate=IntField()
    environment = StringField()

    def __str__(self):
        return "System_id: %s, issue_system_id: %s, title: %s, desc: %s, created_at: %s, updated_at: %s, issue_type: %s," \
               " priority: %s, affects_versions: %s, components: %s, labels: %s, resolution: %s, fix_versions: %s," \
               "assignee: %s, issue_links: %s, status: %s, time_estimate: %s, environment: %s, creator: %s, " \
               "reporter: %s" % (
            self.external_id, self.issue_system_id, self.title, self.desc, self.created_at, self.updated_at, self.issue_type,
            self.priority, ','.join(self.affects_versions), ','.join(self.components), ','.join(self.labels),
            self.resolution, ','.join(self.fix_versions), self.assignee_id, str(self.issue_links), self.status,
            str(self.original_time_estimate), self.environment, self.creator_id, self.reporter_id
        )


class Event(Document):
    STATI = (
        ('created', 'The issue was created by the actor.'),
        ('closed','The issue was closed by the actor. When the commit_id is present, it identifies the commit '
                  'that closed the issue using "closes / fixes #NN" syntax.'),
        ('reopened', 'The issue was reopened by the actor.'),
        ('subscribed', 'The actor subscribed to receive notifications for an issue.'),
        ('merged','The issue was merged by the actor. The `commit_id` attribute is the SHA1 of the HEAD '
                  'commit that was merged.'),
        ('referenced', 'The issue was referenced from a commit message. The `commit_id` attribute is the '
                       'commit SHA1 of where that happened.'),
        ('mentioned', 'The actor was @mentioned in an issue body.'),
        ('assigned', 'The issue was assigned to the actor.'),
        ('unassigned', 'The actor was unassigned from the issue.'),
        ('labeled', 'A label was added to the issue.'),
        ('unlabeled', 'A label was removed from the issue.'),
        ('milestoned', 'The issue was added to a milestone.'),
        ('demilestoned', 'The issue was removed from a milestone.'),
        ('renamed', 'The issue title was changed.'),
        ('locked', 'The issue was locked by the actor.'),
        ('unlocked','The issue was unlocked by the actor.'),
        ('head_ref_deleted', 'The pull requests branch was deleted.'),
        ('head_ref_restored', 'The pull requests branch was restored.'),
        ('description', 'The description was changed.'),
        ('priority', 'The issue was added to a milestone.'),
        ('status', 'The status was changed.'),
        ('resolution', 'The resolution was changed.'),
        ('issuetype','The issuetype was changed.'),
        ('environment', 'The environment was changed.'),
        ('timeoriginalestimate', 'The original time estimation for fixing the issue was changed.'),
        ('version', 'The affected versions was changed.'),
        ('component', 'The component list was changed.'),
        ('labels', 'The labels of the issue were changed.'),
        ('fix version', 'The fix versions of the issue were changed.'),
        ('link', 'Issuelinks were added or deleted.'),
        ('attachment','The attachments of the issue were changed.'),
        ('release note', 'A release note was changed.'),
        ('remoteissuelink', 'A remote link was added to the issue.'),
        ('comment', 'A comment was deleted or added to the issue.'),
        ('hadoop flags', 'Hadoop flags were change to the issue.'),
        ('timeestimate', 'Time estimation was changed in the issue.'),
        ('tags', 'Tags of the issue were changed.')
    )

    meta = {
        'indexes': [
            'issue_id',
            '#external_id',
            ('issue_id', '-created_at')
        ],
        'shard_key': ('external_id', 'issue_id'),
    }

    # PK: external_id, issue_id
    # Shard Key: external_id, issue_id

    external_id = StringField(unique_with=['issue_id'])
    issue_id = ObjectIdField()
    created_at = DateTimeField()
    status = StringField(max_length=50, choices=STATI)
    author_id = ObjectIdField()

    old_value = StringField()
    new_value = StringField()

    def __str__(self):
        return "external_id: %s, issue_id: %s, created_at: %s, status: %s, author_id: %s, " \
               "old_value: %s, new_value: %s" % (
                    self.external_id,
                    self.issue_id,
                    self.created_at,
                    self.status,
                    self.author_id,
                    self.old_value,
                    self.new_value
               )


class IssueComment(Document):
    meta = {
        'indexes': [
            'issue_id',
            '#external_id',
            ('issue_id', '-created_at')
        ],
        'shard_key': ('external_id', 'issue_id'),
    }

    external_id = StringField(unique_with=['issue_id'])
    issue_id = ObjectIdField()
    created_at = DateTimeField()
    author_id = ObjectIdField()
    comment = StringField()

    def __str__(self):
        return "external_id: %s, issue_id: %s, created_at: %s, author_id: %s, comment: %s" % (
            self.external_id, self.issue_id, self.created_at, self.author_id, self.comment
        )


class VCSSystem(Document):
    meta = {
        'collection': 'vcs_system',
        'indexes': [
            '#url'
        ],
        'shard_key': ('url', ),
    }

    # PK: url
    # Shard Key: hashed url

    url = StringField(required=True, unique=True)
    project_id = ObjectIdField(required=True)
    repository_type = StringField(required=True)
    last_updated = DateTimeField()


class FileAction(Document):

    meta = {
        'indexes': [
            '#id',
            'commit_id',
            ('commit_id', 'file_id'),
        ],
        'shard_key': ('id',),
    }

    # PK: file_id, commit_id
    # Shard Key: hashed id. Reasoning: The id is most likely the most queried part. Furthermore, a shard key consisting
    # of commit_id and file_id would be very bad.

    MODES = ('A', 'M', 'D', 'C', 'T', 'R')
    file_id = ObjectIdField(required=True)
    commit_id = ObjectIdField(required=True)
    mode = StringField(max_length=1, required=True, choices=MODES)
    size_at_commit = IntField()
    lines_added = IntField()
    lines_deleted = IntField()
    is_binary = BooleanField()

    # old_file_id is only set, if we detected a copy or move operation
    old_file_id = ObjectIdField()


class Hunk(Document):

    meta = {
        'indexes': [
            '#file_action_id',
        ],
        'shard_key': ('file_action_id',),
    }

    # PK: id
    # Shard Key: file_action_id. Reasoning: file_action_id is most likely often queried

    file_action_id = ObjectIdField()
    new_start = IntField(required=True)
    new_lines = IntField(required=True)
    old_start = IntField(required=True)
    old_lines = IntField(required=True)
    content = StringField(required=True)


class File(Document):
    meta = {
        'indexes': [
            'vcs_system_id',
        ],
        'shard_key': ('path', 'vcs_system_id',),
    }

    # PK: path, vcs_system_id
    # Shard Key: path, vcs_system_id

    vcs_system_id = ObjectIdField(required=True)
    path = StringField(max_length=300, required=True,unique_with=['vcs_system_id'])


class Tag(Document):
    meta = {
        'indexes': [
            'commit_id',
            'name',
            ('name', 'commit_id'),
        ],
        'shard_key': ('commit_id', 'name'),
    }

    # PK: commit_id
    # Shard Key: hashed commit_id

    name = StringField(max_length=150, required=True, unique_with=['commit_id'])
    commit_id = ObjectIdField(required=True)
    message = StringField()
    tagger_id = ObjectIdField()
    date = DateTimeField()
    date_offset = IntField()

    def __eq__(self,other):
        return self.commit_id, self.name == other.commit_id, other.name

    def __hash__(self):
        return hash((self.commit_id, self.name))


class People(Document):
    meta = {
        'shard_key': ('email', 'name',)
    }

    # PK: email, name
    # Shard Key: email, name

    email = StringField(max_length=150, required=True, unique_with=['name'])
    name = StringField(max_length=150, required=True)
    username = StringField(max_length=300)

    def __hash__(self):
        return hash(self.name+self.email)


class Commit(Document):
    meta = {
        'indexes': [
            'vcs_system_id',
        ],
        'shard_key': ('revision_hash', 'vcs_system_id'),
    }

    # PK: revision_hash, vcs_system_id
    # Shard Key: revision_hash, vcs_system_id

    vcs_system_id = ObjectIdField(required=True)
    revision_hash = StringField(max_length=50, required=True, unique_with=['vcs_system_id'])
    branches = ListField(StringField(max_length=500))
    parents = ListField(StringField(max_length=50))
    author_id = ObjectIdField()
    author_date = DateTimeField()
    author_date_offset = IntField()
    committer_id = ObjectIdField()
    committer_date = DateTimeField()
    committer_date_offset = IntField()
    message = StringField()


class TestState(Document):
    meta = {
        'indexes': [
            'commit_id',
        ],
        'shard_key': ('long_name', 'commit_id', 'file_id'),
    }

    # PK: long_name, commit_id, file_id
    # Shard Key: long_name, commit_id, file_id

    long_name = StringField(required=True, unique_with=['commit_id', 'file_id'])
    commit_id = ObjectIdField(required=True)
    file_id = ObjectIdField(required=True)
    file_type = StringField()
    depends_on_ids = ListField(ObjectIdField())
    direct_imp_ids = ListField(ObjectIdField())
    mock_cut_dep_ids = ListField(ObjectIdField())
    mocked_modules_ids = ListField(ObjectIdField())
    uses_mock = BooleanField()
    error = BooleanField()



class CodeEntityState(Document):
    meta = {
        'indexes': [
            'commit_id',
            'file_id',
        ],
        'shard_key': ('long_name', 'commit_id', 'file_id'),
    }

    # PK: long_name, commit_id, file_id
    # Shard Key: long_name, commit_id, file_id

    long_name = StringField(required=True, unique_with=['commit_id', 'file_id'])
    commit_id = ObjectIdField(required=True)
    file_id = ObjectIdField(required=True)
    ce_parent_id = ObjectIdField()
    cg_ids = ListField(ObjectIdField())
    ce_type = StringField()
    start_line = IntField()
    end_line = IntField()
    start_column = IntField()
    end_column = IntField()
    metrics = DictField()


class CodeGroupState(Document):
    meta = {
        'indexes': [
            'commit_id'
        ],
        'shard_key': ('long_name', 'commit_id'),
    }

    # PK: long_name, commit_id
    # Shard Key: long_name, commit_id

    long_name = StringField(require=True, unique_with=['commit_id'])
    commit_id = ObjectIdField(required=True)
    cg_parent_ids = ListField(ObjectIdField())
    cg_type = StringField()
    metrics = DictField()


class CloneInstance(Document):
    meta = {
        'indexes': [
            'commit_id',
            'file_id',
        ],
        'shard_key': ('name', 'commit_id', 'file_id'),
    }

    # PK: name, commit_id, file_id
    # Shard Key: name, commit_id, file_id

    name = StringField(required=True, unique_with=['commit_id', 'file_id'])
    commit_id = ObjectIdField(required=True)
    file_id = ObjectIdField(required=True)
    start_line = IntField(required=True)
    end_line = IntField(required=True)
    start_column = IntField(required=True)
    end_column = IntField(required=True)
    clone_instance_metrics = DictField(required=True)
    clone_class = StringField(required=True)
    clone_class_metrics = DictField(required=True)
==================
API Documentation
==================

Main Module
===========
.. automodule:: pyvcsshark
   :members:

Application
===========
.. autoclass:: pyvcsshark.Application
   :members:

Configuration and Misc
======================

Configuration
-------------
.. autoclass:: pyvcsshark.Config
   :members:

Utils
-----
.. automodule:: pyvcsshark.utils
   :members:

Datastores
==========

BaseDatastore
-------------
.. autoclass:: pyvcsshark.datastores.basestore.BaseStore
   :members:

MongoStore
----------


Database Design
^^^^^^^^^^^^^^^

.. image:: images/dbschema.png


API
^^^

.. autoclass:: pyvcsshark.datastores.mongostore.MongoStore
   :members:


.. autoclass:: pyvcsshark.datastores.mongostore.CommitStorageProcess
   :members:

.. autoclass:: pyvcsshark.dbmodels.mongomodels.Project

.. autoclass:: pyvcsshark.dbmodels.mongomodels.Commit

.. autoclass:: pyvcsshark.dbmodels.mongomodels.FileAction

.. autoclass:: pyvcsshark.dbmodels.mongomodels.File

.. autoclass:: pyvcsshark.dbmodels.mongomodels.Hunk

.. autoclass:: pyvcsshark.dbmodels.mongomodels.Tag

.. autoclass:: pyvcsshark.dbmodels.mongomodels.People




Models
======
.. autoclass:: pyvcsshark.dbmodels.models.CommitModel

.. autoclass:: pyvcsshark.dbmodels.models.FileModel

.. autoclass:: pyvcsshark.dbmodels.models.TagModel

.. autoclass:: pyvcsshark.dbmodels.models.BranchModel

.. autoclass:: pyvcsshark.dbmodels.models.PeopleModel



Parser
======

BaseParser
----------
.. autoclass:: pyvcsshark.parser.baseparser.BaseParser
   :members:

GitParser
---------
.. autoclass:: pyvcsshark.parser.gitparser.GitParser
   :members:

.. autoclass:: pyvcsshark.parser.gitparser.CommitParserProcess
   :members:

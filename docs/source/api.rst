==================
API Documentation
==================

Main Module
===========
.. automodule:: pyvcsshark.main
    :members:
    :undoc-members:

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

API
^^^

.. autoclass:: pyvcsshark.datastores.mongostore.MongoStore
   :members:


.. autoclass:: pyvcsshark.datastores.mongostore.CommitStorage
   :members:



Models
======
.. autoclass:: pyvcsshark.parser.models.CommitModel

.. autoclass:: pyvcsshark.parser.models.FileModel

.. autoclass:: pyvcsshark.parser.models.Hunk

.. autoclass:: pyvcsshark.parser.models.TagModel

.. autoclass:: pyvcsshark.parser.models.BranchModel

.. autoclass:: pyvcsshark.parser.models.PeopleModel



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

.. autoclass:: pyvcsshark.parser.gitparser.CommitParser
   :members:

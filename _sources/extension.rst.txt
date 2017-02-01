How to Extend
=============

**vcsSHARK** has two different extension possibilities. First, you can add new parsers for new repository
types (e.g. SVN, CVS). Currently, only GIT repositories can  be parsed. Second, there is the possibility to add
new datastores (e.g. MySQL). Currently, only MongoDB is supported as a datastore backend.
This chapter will show what needs to be done to extend **vcsSHARK**.


Parsers
-------

All parsers are stored in pyvcsshark/parser folder. There are conditions, which must be fulfilled by a parser so
that it is accepted by **vcsSHARK**:

1.	The \*.py file for this parser must be stored in the pyvcsshark/parser folder.

2.	It must inherit from :class:`~pyvcsshark.parser.baseparser.BaseParser` and implement the methods defined there.

The process of chosing the parser is the following:

*	Every parser gets instantiated

*	The detect method is executed

*	If a parser returns true for the detect method, this parser is used for the repository


There are several important things to note:

1.	If you want to use a logger for your implementation, get it via

	.. code-block:: python

		logger = logging.getLogger("parser")


2.	You must call the :func:`~pyvcsshark.datastores.basestore.BaseStore.add_commit` function of the datastore,
that is given to the parser as argument of the parse method, to add commits.

3.	You must use the models as they are defined in in the module **pyvcsshark.dbmodels.models**, as otherwise the
interfaces do not match

4.	The execution logic is in the application class and explained here :class:`~pyvcsshark.Application`.

Datastores
----------

All datastores are stored in the pyvcsshark/datastores folder. There are conditions, which must be fulfilled by a
datastore so that it is accepted by **vcsSHARK**:

1.	The \*.py file for this datastore must be stored in the pyvcsshark/datastore folder.

2.	It must inherit from :class:`~pyvcsshark.datastores.basestore.BaseStore` and implement the methods defined there.

	.. NOTE:: The store_identifier property must just return a string, which represents your datastore and is not used by another datastore

The process of choosing the datastore is the following:

*	Every datastore gets instantiated

*	The store_identifier property is compared to the db-driver that was chosen by the user

*	If they are equal, the correct datastore was found


There are several important things to note:

1.	If you want to use a logger for your implementation, get it via

	.. code-block:: python

		logger = logging.getLogger("datastore")

2.	The :func:`~pyvcsshark.datastores.basestore.BaseStore.add_commit` method gets a commit model
of class :class:`~pyvcsshark.dbmodels.models.CommitModel` as parameter. Think about this first!

3.	The execution logic is in the application class and explained here :class:`~pyvcsshark.Application`.

.. NOTE:: Dont mind if your datastore do not need all the information of the :func:`~pyvcsshark.datastores.basestore.BaseStore.initialize` function.

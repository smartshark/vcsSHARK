============
Introduction
============

This introduction will show how to use and extend **vcsSHARK**. Furthermore, we list all requirements for this tool here, so that an
easy installation is possible.

.. WARNING:: This software is highly experimental and still in development.


.. _requirements:

Requirements
============

There are several requirements for **vcsSHARK**:

*	Python3+ (only tested with python 3.5.0)
*	Mongoengine (0.10.5) - available here: http://mongoengine.org/
*	Pygit2 (0.23.2) - available here: http://www.pygit2.org/
*	Pymongo (3.2) - available here: https://api.mongodb.org/python/current/


.. NOTE:: It may be possible, that **vcsSHARK** also works with other versions of the named libraries. But we only tested the versions, which are given in brackets.

Tests
=====
**vcsSHARK** can be tested by calling 

	.. code-block:: bash

		$ python setup.py test

The tests can be found in the folder "tests". 

.. WARNING:: The generated tests are not fully complete! They just test the very basic functionality and it can happen, that something is not working but the tests say everything is fine!


How to Use
==========
In this chapter, we explain how you can install **vcsSHARK** or use it directly from the command line. Furhtermore, a short step-by-step tutorial shows,
how **vcsSHARK** can be used for analyzing the repository of `checkstyle <https://github.com/checkstyle/checkstyle>`_.


Installation
------------
The installation process is straight forward. First, clone the repository of **vcsSHARK**.  After you have cloned it you can either:

1.	Install **vcsSHARK** via or

	.. code-block:: bash

		$ sudo python setup.py install


2.	Execute **vcsSHARK** via

	.. code-block:: bash

		$ python vcsshark.py <arguments>


.. NOTE:: It is advisable to change the location, where the logs are written to. They can be changed in the **pyvcsshark/loggerConfiguration.json**. There are differnt file handlers defined. Just change the "filename"-attribute to a location of your wish.


.. _usage:

Usage
-----
**vcsSHARK** is easy to use. Nevertheless, you need to checkout/clone the repository you want to analyze first. 

**vcsSHARK** supports different commandline arguments:

.. option:: --help, -h

	shows the help page for this command

.. option:: --version, -v

	shows the version

.. option:: --no-parse, -n

	skips the parsing process (only makes sense, if you want to execute extensions only)

		.. WARNING:: This is not implemented yet

.. option:: --uri <PATH>, -u <PATH>

	path to the repository
	
		.. WARNING:: Must be a local path, therefore you need to check the repository out beforehand!

.. option:: --db-driver <DRIVER>, -D <DRIVER>

	output datastore driver. Currently only mongodb is supported

.. option:: --db-user <USER>, -U <USER>

	datastore user name

.. option:: --db-password <PASSWORD>, -P <PASSWORD>

	datastore password

.. option:: --db-hostname <HOSTNAME>, -H <HOSTNAME>

	hostname, where the datastore runs on

.. option:: --db-port <PORT>, -p <PORT>

	port, where the datastore runs on

.. option:: --list-extensions, -e

	shows all available extensions

		.. WARNING:: This is not implemented yet

.. option:: --config-file <CONFIG_FILE>, -f <CONFIG_FILE>
	
	path to a custom configuration file

		.. NOTE:: A sample configuration file can be found in the repository (config.sample)



Configuration File
------------------

The configuration file is a simple key-value pair file. An example can be found in the repository (config.sample) and here:

.. include:: ../../config.sample
	:literal:


The options described in this configuration file are the same as described above in :ref:`usage`.


Small Tutorial
--------------

In this section we show step-by-step how you can analyze and store the repository of the `checkstyle <https://github.com/checkstyle/checkstyle>`_ project in a mongodb.

1.	First, if you want to use the mongodb datastore you need to have a mongodb running (version 3.0+). How this can be achieved is explained `here <https://docs.mongodb.org/manual/>`_.

.. WARNING:: Make sure, that you activated the authentication of mongodb (**vcsSHARK** also works without authentication, but this way it is much safer!). Hints how this can be achieved are given `here <https://docs.mongodb.org/manual/core/authentication/>`_.

2. Clone the **vcsSHARK** repository via

	.. code-block:: bash

		$ git clone https://github.com/ftrautsch/vcsSHARK

3. Enter the **vcsSHARK** directory via

	.. code-block:: bash

		$ cd vcsSHARK

4. Test if everything works as expected

	.. code-block:: bash

		$ python vcsshark.py --help

	.. NOTE:: If you receive an error here, it is most likely, that you do not have installed all requirements mentioned in :ref:`requirements`. You can try step 5, as most requirements can be automatically installed.

5. (**optional**) Install vcsshark via the setup script

	.. code-block:: bash

		$ sudo python setup.py install

6. Clone the checkstyle repository to your home directory (or another place)

	.. code-block:: bash

		$ git clone https://github.com/checkstyle/checkstyle ~/checkstyle

7. Execute **vcsSHARK** if you have installed it via:

	.. code-block:: bash

		$ vcsshark -D mongo -U root -P root -DB vcsshark -H localhost -p 27017 -u ~/checkstyle

	or if not:

	.. code-block:: bash

		$ python vcsshark.py -D mongo -U root -P root -DB vcsshark -H localhost -p 27017 -u ~/checkstyle

	.. NOTE:: Here you must be in the vcsSHARK directory!


.. NOTE:: If any errors occure here, please make sure that you use the correct versions of the requirements mentioned in :ref:`requirements`.

Thats it. The database scheme for the mongodb can be found in the API documentation of the mongodb datastore.






How to Extend
=============

**vcsSHARK** has two different extension possibilities. First, you can add new parsers for new repository types (e.g. SVN, CVS). Currently, only GIT repositories can  be parsed. Second, there is the possibility to add new datastores (e.g. MySQL). Currently, only MongoDB is supported as a datastore backend. This chapter will show what needs to be done to extend **vcsSHARK**.


Parsers
-------

All parsers are stored in pyvcsshark/parser folder. There are conditions, which must be fulfiled by a parser so that it is accepted by **vcsSHARK**:

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


2.	You must call the :func:`~pyvcsshark.datastores.basestore.BaseStore.addCommit` function of the datastore, that is given to the parser as argument of the parse method, to add commits.

3.	You must use the models as they are defined in in the module **pyvcsshark.dbmodels.models**, as otherwise the interfaces do not match

4.	The execution logic is in the application class and explained here :class:`~pyvcsshark.Application`.

Datastores
----------

All datastores are stored in the pyvcsshark/datastores folder. There are conditions, which must be fulfilled by a datastore so that it is accepted by **vcsSHARK**:

1.	The \*.py file for this datastore must be stored in the pyvcsshark/datastore folder.

2.	It must inherit from :class:`~pyvcsshark.datastores.basestore.BaseStore` and implement the methods defined there.

	.. NOTE:: The storeIdentifier property must just return a string, which represents your datastore and is not used by another datastore

The process of chosing the datastore is the following:

*	Every datastore gets instantiated

*	The storeIdentifier property is compared to the db-driver that was chosen by the user

*	If they are equal, the correct datastore was found


There are several important things to note:

1.	If you want to use a logger for your implementation, get it via 
	
	.. code-block:: python
	
		logger = logging.getLogger("datastore")

2.	The :func:`~pyvcsshark.datastores.basestore.BaseStore.addCommit` method gets a commitModel of class :class:`~pyvcsshark.dbmodels.models.CommitModel` as parameter. Think about this first!

3.	The execution logic is in the application class and explained here :class:`~pyvcsshark.Application`.

.. NOTE:: Dont mind if your datastore do not need all the information of the :func:`~pyvcsshark.datastores.basestore.BaseStore.initialize` function.

============
Introduction
============

This introduction will show how the requirements of **vcsSHARK** , how it is installed, tested, and executed. Furthermore,
a small tutorial in the end will show step by step, how to use this tool.

vcsFoo is written in Python and uses the official libgit2 library for collecting the data. Furthermore,
to speed up the whole storage and parsing process, vcsFoo uses the multiprocessing library of Python. Hence, several
processes are started for parsing and storing the data.

We use a vanilla Ubuntu 16.04 operating system as basis for the steps that we describe. If necessary, we give hints
on how to perform this step with a different operating system.


.. WARNING:: This software is still in development.


.. _installation:
Installation
============
The installation process is straight forward. For a vanilla Ubuntu 16.04, we need to install the following packages:

.. code-block:: bash

	$ sudo apt-get install git python3-pip python3-cffi libgit2-24 libgit2-dev

.. NOTE::
	If you are using an older version of Ubuntu (or another operating system), you need to install libgit by hand.
	The installation process is explained here: http://www.pygit2.org/install.html.
	But, you need to choose a version, which is compatible with pygit2 0.24.2.


Furthermore, you need a running MongoDB. The process of setting up a MongoDB is explained here: https://docs.mongodb.com/manual/installation/


After these requirements are met, first clone the **vcsSHARK** `repository <https://github.com/smartshark/vcsSHARK/>`_ repository
to a folder you want. In the following, we assume that you have cloned the repository to **~/vcsSHARK**. Afterwards,
the installation of **vcsSHARK** can be done in two different ways:

via Pip
-------
.. code-block:: bash

	$ sudo pip3 install https://github.com/smartshark/vcsSHARK/zipball/master --process-dependency-links

via setup.py
------------
.. code-block:: bash

	$ sudo python3.5 ~/vcsSHARK/setup.py install



.. NOTE::
	It is advisable to change the location, where the logs are written to.
	They can be changed in the **pyvcsshark/loggerConfiguration.json**. There are different file handlers defined.
	Just change the "filename"-attribute to a location of your wish.


Tests
=====
The tests of **vcsSHARK** can be executed by calling

	.. code-block:: bash

		$ python3.5 ~/vcsSHARK/setup.py test

The tests can be found in the folder "tests". 

.. WARNING:: The generated tests are not fully complete. They just test the basic functionality.


Execution
==========
In this chapter, we explain how you can execute **vcsSHARK**. Furthermore, the different execution parameters are
explained in detail.

1) Checkout the repository from which you want to collect the data.

2) Make sure that your MongoDB is running!

	.. code-block:: bash

		$ sudo systemctl status mongodb

3) Make sure that the project from which you collect data is already in the project collection of the MongoDB. If not,
you can add them by:

	.. code-block:: bash

		$ db.project.insert({"name": <PROJECT_NAME>})


4) Execute **vcsSHARK** by calling

	.. code-block:: bash

		$ python3.5 ~/vcsSHARK/vcsshark.py


**vcsSHARK** supports different commandline arguments:

.. option:: --help, -h

	shows the help page for this command

.. option:: --version, -v

	shows the version

.. option:: --db-driver <DRIVER>, -D <DRIVER>

	output datastore driver. Currently only mongodb is supported

.. option:: --db-user <USER>, -U <USER>

	datastore user name

.. option:: --db-password <PASSWORD>, -P <PASSWORD>

	datastore password

.. option:: --db-database <DATABASENAME>, -DB <DATABASENAME>

	database name (e.g., name of the mongodb database that should be used)

.. option:: --db-hostname <HOSTNAME>, -H <HOSTNAME>

	hostname, where the datastore runs on

.. option:: --db-port <PORT>, -p <PORT>

	port, where the datastore runs on

.. option:: --db-authentication <DB_AUTHENTICATION> -a <DB_AUTHENTICATION>

	name of the authentication database

.. option:: --debug <DEBUG_LEVEL>, -d <DEBUG_LEVEL>

	Debug level (INFO, DEBUG, WARNING, ERROR)

.. option:: --project-name <PROJECT_NAME>

	Name of the project, from which the data is collected

.. option:: --path <PATH>

	Path to the checked out repository directory


Tutorial
========

In this section we show step-by-step how you can analyze and store the repository of the
`checkstyle <https://github.com/checkstyle/checkstyle>`_ project in a mongodb.

1.	First, if you want to use the mongodb datastore you need to have a mongodb running (version 3.2+).
How this can be achieved is explained `here <https://docs.mongodb.org/manual/>`_.

.. WARNING::
	Make sure, that you activated the authentication of mongodb
	(**vcsSHARK** also works without authentication, but this way it is much safer!). Hints how this can be achieved are given `here <https://docs.mongodb.org/manual/core/authentication/>`_.

2. Add checkstyle to the projects table in MongoDB.

	.. code-block:: bash

		$ mongo
		$ use vcsshark
		$ db.project.insert({"name": "checkstyle"})

3. Install **vcsSHARK**. An explanation is given above.

3. Enter the **vcsSHARK** directory via

	.. code-block:: bash

		$ cd vcsSHARK

4. Test if everything works as expected

	.. code-block:: bash

		$ python3.5 vcsshark.py --help

	.. NOTE:: If you receive an error here, it is most likely, that the installation process failed.

5. Clone the checkstyle repository to your home directory (or another place)

	.. code-block:: bash

		$ git clone https://github.com/checkstyle/checkstyle ~/checkstyle

6. Execute **vcsSHARK**:

	.. code-block:: bash

		$ cd ~/vcsSHARK
		$ python3.5 vcsshark.py -D mongo -DB vcsshark -H localhost -p 27017 -n checkstyle --path ~/checkstyle


Thats it. The results are explained on the webpage of `SmartSHARK <http://smartshark2.informatik.uni-goettingen.de/documentation/>`_.


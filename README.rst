vcsSHARK
========


Documentation
==============

The complete documentation can be found here: `documentation <http://ftrautsch.github.io/vcsSHARK/index.html>`_.


The documentation can also be built via

	.. code-block:: bash

		$ sphinx-build -b html docs/source docs/build


For the documentation `sphinx <http://sphinx-doc.org/>`_ is used. Be aware, that if **vcsSHARK** is not working on your computer, the API documentation is empty as sphinx autodoc extension requires a runnable script.



Requirements
============

There are several requirements for **vcsSHARK**:

*	Python3+ (only tested with python 3.5.0)
*	Mongoengine (0.10.5) - available here: http://mongoengine.org/
*	Pygit2 (0.23.2) - available here: http://www.pygit2.org/
*	Pymongo (3.2) - available here: https://api.mongodb.org/python/current/


CARE: It may be possible, that **vcsSHARK** also works with other versions of the named libraries. But we only tested the versions, which are given in brackets.


Tests
=====
vcsSHARK can be tested by calling

	.. code-block:: bash

		$ python setup.py test

The tests can be found in the folder "tests".

WARNING: The generated tests are not fully complete! They just test the very basic functionality and it can happen, that something is not working but the tests say everything is fine!


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


CARE:  It is advisable to change the location, where the logs are written to. They can be changed in the **pyvcsshark/loggerConfiguration.json**. There are differnt file handlers defined. Just change the "filename"-attribute to a location of your wish.


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

	NOTE: If you receive an error here, it is most likely, that you do not have installed all requirements mentioned in requirements. You can try step 5, as most requirements can be automatically installed.

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


NOTE: If any errors occure here, please make sure that you use the correct versions of the requirements mentioned in requirements.

Thats it. The database scheme for the mongodb can be found in the API documentation of the mongodb datastore.

'''
Created on 21.01.2016

@author: fabian
'''
from os import listdir
from os.path import dirname
import sys
import unittest


def test_suite():
    # Sometimes importing pygit2 fails, we try this first to get an
    # informative traceback.
    import pygit2

    # Build the list of modules
    modules = []
    for name in listdir(dirname(__file__)):
        if name.startswith('test_') and name.endswith('.py'):
            module = 'tests.%s' % name[:-3]
            # Check the module imports correctly, have a nice error otherwise
            __import__(module)
            modules.append(module)

    # Go
    return unittest.defaultTestLoader.loadTestsFromNames(modules)


def main():
    unittest.main(module=__name__, defaultTest='test_suite', argv=sys.argv[:1])


if __name__ == '__main__':
    main()
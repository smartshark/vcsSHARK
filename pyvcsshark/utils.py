import os
import sys


def readable_dir(prospective_dir):
    """ Function that checks if a path is a directory, if it exists and if it is accessible and only
    returns true if all these three are the case
    
    :param prospective_dir: path to the directory"""
    if prospective_dir is not None:
        if not os.path.isdir(prospective_dir):
            raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            return prospective_dir
        else:
            raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))


def find_plugins(plugin_dir):
    """Finds all python files in the specified path and imports them. This is needed, if we want to
    detect automatically, which datastore and parser we can apply
    
    :param plugin_dir: path to the plugin directory"""
    plugin_files = [x[:-3] for x in os.listdir(plugin_dir) if x.endswith(".py")]
    sys.path.insert(0, plugin_dir)
    for plugin in plugin_files:
        __import__(plugin)


def get_immediate_subdirectories(a_dir):
    """ Helper method, which gets the **immediate** subdirectories of a path. Is helpful, if one want to create a
    parser, which looks if certain folders are there.

    :param a_dir: directory from which **immediate** subdirectories should be listed """

    return [name for name in os.listdir(a_dir) if os.path.isdir(os.path.join(a_dir, name))]


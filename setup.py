import os
import sys

from setuptools import setup, find_packages


# Check dependencies
deps = ['mongoengine >= 0.11.0',
        'pygit2 == 0.24.0',
        'pymongo >= 3.2']

setup(name="vcsSHARK",
      version="0.1",
      author="Fabian Trautsch",
      author_email="ftrautsch@googlemail.com",
      description="vcsSHARK is a tool to analyze source code repositories",
      install_requires=deps,
      url="https://github.com/ftrautsch/vcsSHARK",
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'vcsshark = pyvcsshark:start'
          ]
      },
      test_suite = 'tests',
      zip_safe=False,
      include_package_data=True,
      package_data={
        'pyvcsshark': ['loggerConfiguration.json'],
      },)

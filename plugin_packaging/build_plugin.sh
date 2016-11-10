#!/bin/bash

current=`pwd`
mkdir -p /tmp/vcsSHARK/
cp -R ../pyvcsshark /tmp/vcsSHARK/
cp ../setup.py /tmp/vcsSHARK/
cp ../vcsshark.py /tmp/vcsSHARK
cp * /tmp/vcsSHARK/
cd /tmp/vcsSHARK/

tar -cvf "$current/vcsSHARK_plugin.tar" --exclude=*.tar --exclude=build_plugin.sh --exclude=*/tests --exclude=*/__pycache__ --exclude=*.pyc *

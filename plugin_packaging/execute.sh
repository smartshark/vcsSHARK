#!/bin/sh
PLUGIN_PATH=$1
REPOSITORY_PATH=$2
NEW_UUID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

cp -R $REPOSITORY_PATH "/dev/shm/$NEW_UUID"

COMMAND="python3.5 $PLUGIN_PATH/vcsshark.py --db-driver mongo --db-hostname $3 --db-port $4 --db-database $5 --uri /dev/shm/$NEW_UUID"

if [ ! -z ${6+x} ]; then
	COMMAND="$COMMAND --db-user ${6}"
fi

if [ ! -z ${7+x} ]; then
	COMMAND="$COMMAND --db-password ${7}"
fi

if [ ! -z ${8+x} ]; then
	COMMAND="$COMMAND --db-authentication ${8}"
fi

$COMMAND

rm -rf "/dev/shm/$NEW_UUID"
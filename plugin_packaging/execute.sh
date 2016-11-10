#!/bin/sh
PLUGIN_PATH=$8
REPOSITORY_PATH=$7
NEW_UUID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

cp -R $7 "/dev/shm/$NEW_UUID"

python3.5 $8/vcsshark.py --db-driver mongo --db-user $1 --db-password $2 --db-database $3 --db-hostname $4 --db-port $5 --db-authentication $6 --uri "/dev/shm/$NEW_UUID"

rm -rf "/dev/shm/$NEW_UUID"
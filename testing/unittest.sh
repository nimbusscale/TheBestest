#!/bin/bash
set -e

DYNDB_PATH=./dynamodb

if [[ ! -d ${DYNDB_PATH} ]]; then
    curl -o dynamodb_local_latest.zip https://s3-us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.zip
    unzip -q -d ${DYNDB_PATH} dynamodb_local_latest.zip
fi

# Check to see if local DynamoDB is running, if so kill it so we can start a new one
PID=$(ps -ef | grep [D]ynamoDBLocal.jar | awk '{print $2}')
if [ $PID ]; then
    echo "killing already running Local DynamoDB"
    kill $PID
fi

# Start Local DynamoDB
java -Djava.library.path=${DYNDB_PATH}/DynamoDBLocal_lib -jar ${DYNDB_PATH}/DynamoDBLocal.jar -sharedDb -inMemory &

# Initialize DynDB for Testing
chmod +x init_local_dyn_db.py
./init_local_dyn_db.py

# Unit Test Lambdas
pytest

# Kill Local DynDB
echo "Killing Local DynamoDB"
kill %1


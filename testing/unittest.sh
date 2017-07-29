#!/bin/bash
DYNDB_PATH=./dynamodb

pip3 install -r ../requirements.txt

if [[ ! -d ${DYNDB_PATH} ]]; then
    wget https://s3-us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.zip
    unzip -q -d ${DYNDB_PATH} dynamodb_local_latest.zip
fi

# Start Local DynamoDB
java -Djava.library.path=${DYNDB_PATH}/DynamoDBLocal_lib -jar ${DYNDB_PATH}/DynamoDBLocal.jar -sharedDb -inMemory &

# Initialize DynDB for Testing
./init_local_dyn_db.py

# Unit Test Lambdas
pytest

# Kill Local DynDB
echo "Killing Local DynamoDB"
kill %1


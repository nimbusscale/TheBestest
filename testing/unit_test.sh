#!/bin/bash
DYNDB_PATH=/home/jjk3/dynamodb

# Start Local DynamoDB
java -Djava.library.path=${DYNDB_PATH}/DynamoDBLocal_lib -jar ${DYNDB_PATH}/DynamoDBLocal.jar -sharedDb -inMemory &

# Initialize DynDB for Testing
./init_local_dyn_db.py

# Unit Test Lambdas
pytest

# Kill Local DynDB
echo "Killing Local DynamoDB"
kill %1


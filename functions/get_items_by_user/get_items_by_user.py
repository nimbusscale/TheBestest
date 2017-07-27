#!/usr/bin/env python3
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key, Attr

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.INFO)

if ('AWS_DEFAULT_REGION' in os.environ
    and os.environ['AWS_DEFAULT_REGION'] != 'LOCAL'):
    print(os.environ['AWS_DEFAULT_REGION'])
    region = os.environ['AWS_DEFAULT_REGION']
    logging.info("Using DynamoDB instance in {} region".format(region))
    dynamodb = boto3.resource(service_name='dynamodb',
                              region_name=region)
else:
    dynamodb = boto3.resource(service_name='dynamodb',
                              endpoint_url='http://localhost:8000')
    logging.info("Using local DynamoDB instance")

table = dynamodb.Table(os.environ['itemsTableName'])

def lambda_handler(event, context):
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(event['user_id'])
    )
    return response



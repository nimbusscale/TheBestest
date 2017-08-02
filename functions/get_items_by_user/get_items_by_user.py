#!/usr/bin/env python3
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if ('AWS_DEFAULT_REGION' in os.environ
    and os.environ['AWS_DEFAULT_REGION'] != 'LOCAL'):
    print(os.environ['AWS_DEFAULT_REGION'])
    region = os.environ['AWS_DEFAULT_REGION']
    logger.info("Using DynamoDB instance in {} region".format(region))
    dynamodb = boto3.resource(service_name='dynamodb',
                              region_name=region)
else:
    dynamodb = boto3.resource(service_name='dynamodb',
                              endpoint_url='http://localhost:8000')
    logger.info("Using local DynamoDB instance")

table = dynamodb.Table(os.environ['itemsTableName'])

def lambda_handler(event, context):
    api_request_id = event['metadata']['requestId']
    user_id = event['metadata']['userId']
    logger.info("Handling API request {} for user {}".format(api_request_id,
                                                              user_id))
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    return response



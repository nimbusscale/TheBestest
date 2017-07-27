#!/usr/bin/env python3
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key, Attr

region = os.environ['AWS_DEFAULT_REGION']
dynamodb = boto3.resource('dynamodb', region_name=region)
table = dynamodb.Table(os.environ['itemsTableName'])


def lambda_handler(event, context):
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(event['user_id'])
    )
    return(response)



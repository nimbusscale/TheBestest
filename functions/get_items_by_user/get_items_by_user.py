#!/usr/bin/env python3
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('items')


def lambda_handler(event,context):
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(event['user_id'])
    )
    return(response)



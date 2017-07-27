#!/usr/bin/env python3
"""
Reads a CloudFormation YAML template, identifies DynamoDB table resources
and creates DynamoDB tables in a locally running DynamoDB server.

This is intended to be used for unit testing of lambda functions against a
locally running DynamoDB server. Using the specification defined in the
CloudFormation template will ensure the test environment mimics prod.
"""
import argparse
import json
import yaml

import boto3

parser = argparse.ArgumentParser(
    description="Reads a CloudFormation YAML template, identifies DynamoDB "
                "table resources and creates DynamoDB tables in a locally "
                "running DynamoDB server.")
parser.add_argument(
    '--template-path',
    default="../stack.yaml",
    help="Path to the CloudFormation YAML template"
)
args = parser.parse_args()

dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')

with open(args.template_path) as template:
    cfn_text = template.read()

# CFN uses ! to mark functions, but this is also used by YAML
# Must remove ! before loading YAML otherwise it will exit with error
cfn_yaml = yaml.safe_load(cfn_text.replace("!", ""))

for resource_id in cfn_yaml['Resources']:
    if cfn_yaml['Resources'][resource_id]['Type'] == "AWS::DynamoDB::Table":
        properties = cfn_yaml['Resources'][resource_id]['Properties']
        dynamodb.create_table(**properties)








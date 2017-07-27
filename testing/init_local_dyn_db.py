#!/usr/bin/env python3
"""
Creates tables in a local DynDB instance based on a CloudFormation template and
then loads test data into those tables.

This is intended to be used for unit testing of lambdas. Using the
specification defined in the CloudFormation template will ensure the test
environment mimics prod.
"""
import argparse
import logging
import yaml

import boto3

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.INFO)

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

dynamodb = boto3.resource(service_name='dynamodb',
                          endpoint_url='http://localhost:8000')

def create_dynamodb_tables(template_path):
    """Creates dynDB tables defined in a CFN template"""
    # Todo: Ideally set timeout to very low as service is running on localhost.
    # Attempted to set timeout, but was unable tog get it to work.
    logging.info("reading CFN Template {}".format(args.template_path))
    with open(template_path) as template:
        cfn_text = template.read()

    # CFN uses ! to mark functions, but this is also used by YAML
    # Must remove ! before loading YAML otherwise it will exit with error
    cfn_yaml = yaml.safe_load(cfn_text.replace("!", ""))

    for resource_id in cfn_yaml['Resources']:
        if cfn_yaml['Resources'][resource_id]['Type'] == "AWS::DynamoDB::Table":
            logging.info("Identified CFN Resource {}".format(resource_id))
            properties = cfn_yaml['Resources'][resource_id]['Properties']
            logging.info("Creating table {}".format(properties['TableName']))
            dynamodb.create_table(**properties)


def seed_items_table():
    """Loads test data into the items table"""
    table = dynamodb.Table('thebestest_items')
    # list of dicts that will be created as records into the table
    items = [
        {'user_id': "jjk3", 'category_name': "bbq",
         'place_name': "central bbq"},
        {'user_id': "jdebari", 'category_name': "bbq", 'place_name': "AJs"}
    ]
    for item in items:
        table.put_item(Item=item)

if __name__ == '__main__':
    create_dynamodb_tables(args.template_path)
    seed_items_table()





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
    default="../deploy/stack.yaml",
    help="Path to the CloudFormation YAML template"
)
args = parser.parse_args()

# Todo: Ideally set timeout to very low as service is running on localhost.
# Attempted to set timeout, but was unable tog get it to work.
dynamodb = boto3.resource(service_name='dynamodb',
                          endpoint_url='http://localhost:8000')


def get_dynamodb_table_specs(template_path):
    """Identifies DynDB tables in a CFN template and returns dict of configs"""
    dynamodb_table_specs = {}
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
            dynamodb_table_specs[resource_id] = properties
    return dynamodb_table_specs


def create_dynamodb_tables(table_specs):
    """Creates dynDB tables based on dict of table specs"""
    for table in table_specs.keys():
        properties = table_specs[table]
        logging.info("Creating table {}".format(properties['TableName']))
        dynamodb.create_table(**properties)


def seed_items_table(table_name):
    """Loads test data into the items table"""
    table = dynamodb.Table(table_name)
    # list of dicts that will be created as records into the table
    items = [
        {'user_id': "jjk3", 'category_name': "bbq",
         'place_name': "central bbq"},
        {'user_id': "jdebari", 'category_name': "bbq", 'place_name': "AJs"}
    ]
    for item in items:
        table.put_item(Item=item)

if __name__ == '__main__':
    table_specs = get_dynamodb_table_specs(args.template_path)
    create_dynamodb_tables(table_specs)
    seed_items_table(table_specs['itemTable']['TableName'])





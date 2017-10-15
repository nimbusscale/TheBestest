import logging
import time

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()


class Stack:

    def __init__(self, name):
        self.name = name
        self.cfn = boto3.client('cloudformation')

    @property
    def arn(self):
        try:
            response = self.cfn.describe_stacks(StackName=self.name)
        except ClientError as e:
            if "does not exist" in e.response['Error']['Message']:
                return None
            else:
                raise
        return response['Stacks'][0]['StackId']

    def create(self, template_path):
        # Check if stack already exists, if rolled back, then delete stack,
        # Otherwise skip creation
        with open(template_path) as template_file:
            template = template_file.read()
            logger.info("Validating CFN template {}".format(template_path))
            self.cfn.validate_template(TemplateBody=template)
            logger.info("Creating stack {}".format(self.name))
            response = self.cfn.create_stack(
                StackName=self.name,
                TemplateBody=template,
                Capabilities=['CAPABILITY_IAM']
            )
        stack_id = response['StackId']
        logger.info("StackId {}".format(stack_id))
        wait = 0
        max_wait = 180
        sleep_seconds = 10
        logger.info("Waiting up to {} for stack creation.".format(max_wait))
        while wait <= max_wait:
            time.sleep(sleep_seconds)
            status = self.status
            logger.info("stack status is {}".format(status))
            if status == 'CREATE_COMPLETE':
                break
            elif status == 'CREATE_IN_PROGRESS':
                wait = wait + sleep_seconds
            elif (status == 'ROLLBACK_COMPLETE'
                  or status == 'ROLLBACK_IN_PROGRESS'):
                events_response = self.cfn.describe_stack_events(
                        StackName=self.name)
                for event in events_response['StackEvents']:
                    if event['ResourceStatus'] == 'CREATE_FAILED':
                        logger.error(event['ResourceStatusReason'])
                raise RuntimeError(
                    "Stack failed to create with status {}".format(
                        self.status))
            else:
                raise RuntimeError(
                    "Stack returned unhandled status of {}".format(
                        self.status))

    def delete(self):
        self.cfn.delete_stack(StackName=self.arn)

    @property
    def status(self):
        try:
            response = self.cfn.describe_stacks(StackName=self.name)
        except ClientError as e:
            if "does not exist" in e.response['Error']['Message']:
                return None
            else:
                raise
        return response['Stacks'][0]['StackStatus']



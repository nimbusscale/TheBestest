import logging

import boto3
from botocore.exceptions import ClientError, WaiterError

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
        if self.status == 'ROLLBACK_COMPLETE':
            self.delete()

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
        arn = response['StackId']
        logger.info("StackId {}".format(arn))
        create_waiter = self.cfn.get_waiter('stack_create_complete')
        waiter_delay = 10
        waiter_max_attempts = 18
        logger.info("Waiting up to {} seconds for stack creation.".format(
            str(waiter_delay * waiter_max_attempts)
        ))
        try:
            create_waiter.wait(StackName=arn,
                               WaiterConfig={
                                    'Delay': waiter_delay,
                                    'MaxAttempts': waiter_max_attempts
                                    }
                               )
        except WaiterError:
            events_response = self.cfn.describe_stack_events(
                StackName=self.name)
            for event in events_response['StackEvents']:
                if event['ResourceStatus'] == 'CREATE_FAILED':
                    logger.error(event['ResourceStatusReason'])
            raise RuntimeError(
                "Stack failed to create with status {}".format(
                    self.status))
        logger.info("Stack {} created".format(self.name))

    def delete(self):
        arn = self.arn
        logger.info("Deleting stack with ARN {}".format(arn))
        delete_waiter = self.cfn.get_waiter('stack_delete_complete')
        waiter_delay = 10
        waiter_max_attempts = 6
        logger.info("Waiting up to {} seconds for stack deletion.".format(
            str(waiter_delay * waiter_max_attempts)
        ))
        self.cfn.delete_stack(StackName=arn)
        delete_waiter.wait(StackName=arn,
                           WaiterConfig={
                               'Delay': waiter_delay,
                               'MaxAttempts': waiter_max_attempts
                            }
                           )

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

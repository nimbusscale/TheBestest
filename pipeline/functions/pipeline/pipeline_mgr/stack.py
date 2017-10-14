import logging

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
        with open(template_path) as template_file:
            template=template_file.read()
            self.cfn.validate_template(TemplateBody=template)
            self.cfn.create_stack(
                StackName=self.name,
                TemplateBody=template,
                Capabilities=['CAPABILITY_IAM']
            )

    def delete(self):
        self.cfn.delete_stack(StackName=self.arn)



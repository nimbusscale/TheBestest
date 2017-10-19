import logging

import boto3
from botocore.exceptions import ClientError, WaiterError

logger = logging.getLogger()


class Stack:

    def __init__(self, spec):
        self._name = spec.get('name')
        self._arn =  spec.get('arn')
        self.cfn = boto3.client('cloudformation')

    def __repr__(self):
        return "Stack(" + str(self.to_dict()) + ")"

    def __str__(self):
        return str(self.to_dict())

    @property
    def arn(self):
        if not self._arn:
            try:
                response = self.cfn.describe_stacks(StackName=self.name)
            except ClientError as e:
                if "does not exist" in e.response['Error']['Message']:
                    return None
                else:
                    raise
            self._arn = response['Stacks'][0]['StackId']
        return self._arn

    @arn.setter
    def arn(self, arn):
        self._arn = arn

    def create(self, template_path, parameters=None):
        # Check if stack already exists, if rolled back, then delete stack,
        # Otherwise skip creation
        if self.status == 'ROLLBACK_COMPLETE':
            self.delete()

        with open(template_path) as template_file:
            template = template_file.read()
            logger.info("Validating CFN template {}".format(template_path))
            self.cfn.validate_template(TemplateBody=template)
            if parameters:
                cfn_params = [
                    {'ParameterKey': key,
                     'ParameterValue': parameters[key]}
                    for key in parameters]
            else:
                cfn_params = []
            logger.info(
                "Creating CFN stack {} from {} with Params {}".format(
                    self.name,
                    template_path,
                    cfn_params
                )
            )
            response = self.cfn.create_stack(
                StackName=self.name,
                TemplateBody=template,
                Capabilities=['CAPABILITY_IAM'],
                Parameters=cfn_params
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
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

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

    def to_dict(self):
        return {
                'arn': self.arn,
                'name': self.name,
                'status': self.status
        }


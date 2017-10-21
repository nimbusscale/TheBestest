from hashlib import sha1
import logging

import boto3
from botocore.exceptions import ClientError, WaiterError

logger = logging.getLogger()


class Stack:

    def __init__(self, spec):
        self._name = spec.get('name')
        self._arn = spec.get('arn')
        self._hexdigest = spec.get('hexdigest')
        self.cfn = boto3.client('cloudformation')

    def __repr__(self):
        return "Stack(" + str(self.to_dict()) + ")"

    def __str__(self):
        return str(self.to_dict())

    def __cfn_wait(self, condition):
        create_waiter = self.cfn.get_waiter(condition)
        waiter_delay = 10
        waiter_max_attempts = 18
        logger.info("Waiting up to {} seconds for {}.".format(
            str(waiter_delay * waiter_max_attempts),
            condition
        ))
        try:
            create_waiter.wait(StackName=self.arn,
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

    def apply_template(self, template_path, parameters=None):
        """applies a cfn template to stack, this may create the stack from
        scratch or update an existing stack"""
        # Check if stack already exists, if rolled back, then delete stack
        if self.status == 'ROLLBACK_COMPLETE':
            logger.info(
                "CFN stack {} in a ROLLBACK_COMPLETE state.".format(self.name)
            )
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
        # See if create from scratch or update
        # add new line to end of file if one doesn't exist
        if not template.endswith('\n'):
            template = template + '\n'
        hexdigest = sha1(template.encode()).hexdigest()
        if self.hexdigest is None:
            self.create(template, cfn_params)
        elif hexdigest != self.hexdigest:
            self.update(template, cfn_params)
        else:
            logger.info("CFN stack {} already up-to-date.".format(self.name))

    @property
    def arn(self):
        if self.status:
            if not self._arn:
                try:
                    response = self.cfn.describe_stacks(StackName=self.name)
                except ClientError as e:
                    if "does not exist" in e.response['Error']['Message']:
                        return None
                    else:
                        raise
                self._arn = response['Stacks'][0]['StackId']
        else:
            self._arn = None
        return self._arn

    @arn.setter
    def arn(self, arn):
        self._arn = arn

    def create(self, template, param_list=None):
            logger.info(
                "Creating CFN stack {} with Params {}".format(
                    self.name,
                    param_list
                )
            )
            response = self.cfn.create_stack(
                StackName=self.name,
                TemplateBody=template,
                Capabilities=['CAPABILITY_IAM'],
                Parameters=param_list
            )

            arn = response['StackId']
            logger.info("StackId {}".format(arn))
            self.__cfn_wait('stack_create_complete')
            logger.info("Stack {} created".format(self.name))

    def delete(self):
        arn = self.arn
        logger.info("Deleting stack with ARN {}".format(arn))
        self.cfn.delete_stack(StackName=arn)
        self.__cfn_wait('stack_delete_complete')
        logger.info("Stack {} deleted".format(self.name))

    @property
    def hexdigest(self):
        if self.status:
            if not self._hexdigest:
                cfn_response = self.cfn.get_template(StackName=self.arn)
                stack_template = cfn_response['TemplateBody']
                self._hexdigest = sha1(stack_template.encode()).hexdigest()
            return self._hexdigest
        else:
            return None

    @hexdigest.setter
    def hexdigest(self, digest):
        self._hexdigest = digest

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
                'hexdigest': self.hexdigest,
                'name': self.name,
                'status': self.status
        }

    def update(self, template, param_list=None):
        logger.info(
            "Updating CFN stack {} with Params {}".format(
                self.name,
                param_list
            )
        )
        self.cfn.update_stack(
            StackName=self.name,
            TemplateBody=template,
            Capabilities=['CAPABILITY_IAM'],
            Parameters=param_list
        )
        self.__cfn_wait('stack_update_complete')
        logger.info("Stack {} updated".format(self.name))

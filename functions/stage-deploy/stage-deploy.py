#!/usr/bin/env python3
import json
import boto3


def lambda_handler(event, context):
    job_data = event['CodePipeline.job']['data']
    job_config = job_data['actionConfiguration']['configuration']
    user_params = json.loads(job_config['UserParameters'])
    apigw = boto3.client('apigateway')
    cloudformation = boto3.resource('cloudformation')
    cfn_stack = cloudformation.Stack(user_params['stackName'])
    apiGwId = None
    for output in cfn_stack.outputs:
        if output['OutputKey'] == 'apiGwId':
            apiGwId = output['OutputValue']
    if apiGwId is None:
        raise Exception("apiGwId is not defined as an output for "
                "the stack {}".format(user_params['stackName']))
    apigw.create_deployment(restApiId=apiGwId,
                            stageName=user_params['stageName'])
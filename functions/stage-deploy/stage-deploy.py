#!/usr/bin/env python3
import json
import boto3

# Todo add better error handling and Logging
def lambda_handler(event, context):
    apigw = boto3.client('apigateway')
    cloudformation = boto3.resource('cloudformation')
    codepipeline = boto3.client('codepipeline')
    # Get CodePipeline Job Info
    job_id = event['CodePipeline.job']['id']
    job_data = event['CodePipeline.job']['data']
    job_config = job_data['actionConfiguration']['configuration']
    user_params = json.loads(job_config['UserParameters'])
    # Get apiGwId from cloudformation stack. The stack name is defined as a
    # parameter in the DeployApi Invoke Action in CodeDeploy Deploy Stack stage
    cfn_stack = cloudformation.Stack(user_params['stackName'])
    apiGwId = None
    for output in cfn_stack.outputs:
        if output['OutputKey'] == 'apiGwId':
            apiGwId = output['OutputValue']
    if apiGwId is None:
        raise Exception("apiGwId is not defined as an output for "
                "the stack {}".format(user_params['stackName']))
    # Deploy the API
    apigw.create_deployment(restApiId=apiGwId,
                            stageName=user_params['stageName'])
    # Confirm Success back to codepipeline
    codepipeline.put_job_success_result(jobId=job_id)

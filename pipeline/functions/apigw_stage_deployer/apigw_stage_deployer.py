#!/usr/bin/env python3
import json
import logging

import boto3
from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def deploy_stage(event, context):
    apigw = boto3.client('apigateway')
    apigw_id = event['ResourceProperties']['RestApiId']
    stage_name = event['ResourceProperties']['StageName']

    # Assume success, will set to FAILURE if issues are encountered
    status = 'SUCCESS'

    # If Create or Update then deploy to stage, if Delete do nothing and
    # send by success as the entire GW is likely to be deleted
    if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
        # Deploy the API
        try:
            apigw.create_deployment(restApiId=apigw_id,
                                    stageName=stage_name)
        except Exception as e:
            logger.error("Unable to deploy to stage. Error: {}".format(str(e)))
            status = 'FAILED'

        # Make sure logging is enabled
        try:
            apigw.update_stage(restApiId=apigw_id,
                               stageName=stage_name,
                               patchOperations=[
                                   {'op': 'replace',
                                    'path': '/*/*/logging/loglevel',
                                    'value': 'INFO'}
                               ])
        except Exception as e:
            logger.error("Unable to enable logging on stage. Error: "
                         "{}".format(str(e)))
            status = 'FAILED'

    cfn_response(event, context, status, None)


def cfn_response(event, context, status, response_data,
                 physical_resource_id=None):
    """CFN custom resource response. Code adapted from
    http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-lambda-function-code.html#cfn-lambda-function-code-cfnresponsemodule
    """
    response_url = event['ResponseURL']

    response_body = {}
    response_body['Status'] = status
    response_body['Reason'] = (
        "See the details in CloudWatch Log Stream: {}/{}".format(
            context.log_group_name, context.log_stream_name))
    response_body['PhysicalResourceId'] = (physical_resource_id
                                           or context.log_stream_name)
    response_body['StackId'] = event['StackId']
    response_body['RequestId'] = event['RequestId']
    response_body['LogicalResourceId'] = event['LogicalResourceId']
    response_body['Data'] = response_data

    json_response_body = json.dumps(response_body)

    headers = {
        'content-type' : '',
        'content-length' : str(len(json_response_body))
    }

    logger.info("sending response {} to {}".format(json_response_body,
                                                  response_url))
    response = requests.put(response_url,
                            data=json_response_body,
                            headers=headers)
    print(response)
    logger.info(response)


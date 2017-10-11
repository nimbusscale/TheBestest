#!/usr/bin/env python3
import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import boto3
import github3

from pipeline_mgr.pull_request import PullRequest

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def webhook_handler(event, context):
    """Lambda that evaluates the input provided by the API GW and determines
    if it's a valid PR Open Webhook notice.
    """
    pipeline_info = {}
    try:
        pr_data = event['pull_request']
        pull_request = PullRequest(pr_data)
    except:
        logger.error(event)
        raise Exception("Invalid Github PR Webhook")
    pipeline_info['pull_request'] = pull_request.__dict__

    pipeline_action = "none"
    if event['action'] in ['opened', 'synchronize']:
        pipeline_action = "test"
    elif event['action'] == 'closed' and event['pull_request']['merged']:
        pipeline_action = "prod_deploy"
    pipeline_info['action'] = pipeline_action
    logger.info("{} for PR {} ({}) of branch {}".format(pipeline_action,
                                                         pull_request.title,
                                                         pull_request.url,
                                                         pull_request.branch_name))
    return pipeline_info


def retrieve_source(event, context):
    """Lambda that retrieves a zipball of source based on a SHA and uploads
    it to S3
    """
    pr = PullRequest(event['pull_request']['data'])
    token = os.environ['OAUTH_TOKEN']
    bucket = os.environ['S3_BUCKET']
    s3_version_id = pr.retrieve_source(token, bucket)
    event['version_id'] = s3_version_id
    return event


def start_pipeline(event, context):
    """Lambda that starts a codepipeline.

    Pipeline name is provided by Env Var
    """
    pr = PullRequest(event['pull_request']['data'])
    pipeline_name = os.environ['PIPELINE_NAME']
    token = os.environ['OAUTH_TOKEN']
    codepipeline = boto3.client('codepipeline')
    response = codepipeline.start_pipeline_execution(name=pipeline_name)
    execution_id = response['pipelineExecutionId']
    pr.set_status(token,
                  'pending',
                  pipeline_name,
                  execution_id)
    event['execution_id'] = execution_id
    event['pipeline_status'] = 'InProgress'
    return event

def check_pipeline_status(event, context):
    """Lambda that checks that status of a codepipeline execution id"""
    pipeline_name = os.environ['PIPELINE_NAME']
    execution_id = event['execution_id']
    codepipeline = boto3.client('codepipeline')
    status_response = codepipeline.get_pipeline_execution(
        pipelineName=pipeline_name,
        pipelineExecutionId=execution_id)
    event['pipeline_status'] = status_response['pipelineExecution']['status']
    return event

def set_github_status(event, context):
    """Lambda that sets the status of the PR to failure"""
    pr = PullRequest(event['pull_request']['data'])
    execution_id = event['execution_id']
    token = os.environ['OAUTH_TOKEN']
    pipeline_name = os.environ['PIPELINE_NAME']
    pipeline_status = event['pipeline_status']
    if pipeline_status == 'Succeeded':
        pr_status = 'success'
    elif pipeline_status == 'Failed':
        pr_status = 'failure'
    elif pipeline_status == 'Superseded':
        pr_status = 'error'
    pr.set_status(token,
                  pr_status,
                  pipeline_name,
                  execution_id)
    return event











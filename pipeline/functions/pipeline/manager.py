#!/usr/bin/env python3
import logging
import os

import boto3

from pipeline_mgr.pull_request import PullRequest
from pipeline_mgr.pipeline import Pipeline

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
    token = os.environ['OAUTH_TOKEN']
    bucket = os.environ['S3_BUCKET']
    pr = PullRequest(event['pull_request']['data'])
    s3_version_id = pr.retrieve_source(token, bucket)
    event['version_id'] = s3_version_id
    return event


def start_pipeline(event, context):
    """Lambda that starts a codepipeline.

    Pipeline name is provided by Env Var
    """
    pipeline_name = os.environ['PIPELINE_NAME']
    token = os.environ['OAUTH_TOKEN']
    pr = PullRequest(event['pull_request']['data'])
    pipeline = Pipeline({'name': pipeline_name})
    execution_id = pipeline.start()
    pr.set_status(token,
                  'pending',
                  pipeline_name,
                  execution_id)
    event['pipeline'] = pipeline.to_dict()
    return event

def check_pipeline_status(event, context):
    """Lambda that checks that status of a codepipeline execution id"""
    pipeline = Pipeline(event['pipeline'])
    event['pipeline'] = pipeline.to_dict()
    return event

def set_github_status(event, context):
    """Lambda that sets the status of the PR to failure"""
    token = os.environ['OAUTH_TOKEN']
    pr = PullRequest(event['pull_request']['data'])
    pipeline = Pipeline(event['pipeline'])
    pipeline_status = pipeline.staus
    if pipeline_status == 'Succeeded':
        pr_status = 'success'
    elif pipeline_status == 'Failed':
        pr_status = 'failure'
    elif pipeline_status == 'Superseded':
        pr_status = 'error'
    pr.set_status(token,
                  pr_status,
                  pipeline.name,
                  pipeline.execution_id)
    return event











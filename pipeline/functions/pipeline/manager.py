#!/usr/bin/env python3
import logging
import os

import boto3

from pipeline_mgr.pull_request import PullRequest
from pipeline_mgr.pipeline import Pipeline

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Determines course of action based on action property passed to it by
    state machine.
    """
    action = event['pipeline_action']

    if action == 'HandleWebhook':
        return webhook_handler(event)
    elif action == 'RetrieveSource':
        return retrieve_source(event)


def webhook_handler(event):
    """Evaluates the input provided by the API GW and determines
    if it's a valid PR Open Webhook notice.
    """
    pipeline_info = {}
    try:
        pr_data = event['pull_request']
        pull_request = PullRequest(pr_data)
    except:
        logger.error(event)
        raise Exception("Invalid Github PR Webhook")
    pipeline_info['pull_request'] = pull_request.to_dict()
    pipeline_action = "none"
    if event['action'] == 'opened':
        pipeline_action = 'build_stack'
    elif event['action'] == 'synchronize':
        pipeline_action = 'test'
    elif event['action'] == 'closed' and event['pull_request']['merged']:
        pipeline_action = 'prod_deploy'
    elif event['action'] == 'closed' and not event['pull_request']['merged']:
        pipeline_action = 'delete_stack'
    pipeline_info['pipeline_action'] = pipeline_action
    logger.info(
        "{} for PR {} ({}) of branch {}".format(pipeline_action,
                                                pull_request.title,
                                                pull_request.url,
                                                pull_request.branch_name)
    )
    return pipeline_info


def retrieve_source(event):
    """Retrieves a zipball of source based on a SHA and uploads
    it to S3
    """
    token = os.environ['OAUTH_TOKEN']
    bucket = os.environ['S3_BUCKET']
    pr = PullRequest(event['pull_request'])
    s3_version_id = pr.retrieve_source(token, bucket)
    event['version_id'] = s3_version_id
    return event


def start_pipeline(event, context):
    """Lambda that starts a codepipeline.

    Pipeline name is provided by Env Var
    """
    pipeline_name = os.environ['PIPELINE_NAME']
    token = os.environ['OAUTH_TOKEN']
    pr = PullRequest(event['pull_request'])
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
    pr = PullRequest(event['pull_request'])
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











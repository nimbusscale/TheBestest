#!/usr/bin/env python3
import logging
import os

import boto3

from pipeline_mgr.manager import Manager
from pipeline_mgr.pull_request import PullRequest
from pipeline_mgr.pipeline import Pipeline
from pipeline_mgr.stack import Stack
from pipeline_mgr.source import Source

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
        manager = Manager(event['manager'])
        manager.source.retrieve_source()
        event['manager'] = manager.to_dict()
        return event
    elif action == 'BuildPipeline':
        manager = Manager(event['manager'])
        # Set from project root
        template_path = 'pipeline/pipeline_deploy_stack.yaml'
        manager.pipeline.build(manager.source,
                               template_path)
        event['manager'] = manager.to_dict()
        return event
    elif action == 'StartTest':
        manager = Manager(event['manager'])
        execution_id = manager.pipeline.start()
        manager.pull_request.set_status(manager.oath_token,
                                        'pending',
                                        manager.pipeline.name,
                                        execution_id)
        event['manager'] = manager.to_dict()
        return event
    elif action == 'CheckTestStatus':
        # Simply rehydrating the manager object will update the pipeline status
        manager = Manager(event['manager'])
        event['manager'] = manager.to_dict()
        logger.info("Pipeline status {}".format(manager.pipeline.status))
        return event
    elif action == 'SetTestStatus':
        manager = Manager(event['manager'])
        if manager.pipeline.status == 'Succeeded':
            pr_status = 'success'
        elif manager.pipeline.status == 'Failed':
            pr_status = 'failure'
        else:
            pr_status = 'error'
        manager.pull_request.set_status(manager.oath_token,
                                        pr_status,
                                        manager.pipeline.name,
                                        manager.pipeline.execution_id)


def webhook_handler(event):
    """Evaluates the input provided by the API GW and determines
    if it's a valid PR Open Webhook notice.
    """
    state = {}
    bucket_name = os.environ['S3_BUCKET']
    oath_token = os.environ['OAUTH_TOKEN']
    manager = Manager(
        {
            'bucket_name': bucket_name,
            'pull_request': event['pull_request'],
            'oath_token': oath_token
        }
    )

    if event['action'] == 'opened':
        state['pipeline_action'] = 'build_stack'
    elif event['action'] == 'synchronize':
        state['pipeline_action'] = 'test'
    elif event['action'] == 'closed' and event['pull_request']['merged']:
        state['pipeline_action'] = 'prod_deploy'
    elif event['action'] == 'closed' and not event['pull_request']['merged']:
        state['pipeline_action'] = 'delete_stack'
    logger.info(
        "{} for PR {} ({}) of branch {}".format(state['pipeline_action'],
                                                manager.pull_request.title,
                                                manager.pull_request.url,
                                                manager.pull_request.branch_name)
    )
    state['manager'] = manager.to_dict()
    return state











#!/usr/bin/env python3
# webhook test 7
import logging
import github3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def webhook_handler(event, context):
    """Evaluates the imput provided by the API GW and determines if it's a
    valid PR Open Webhook notice.
    """
    pipeline_info = {}
    try:
        pr_info = {}
        pr_info['number'] = event['number']
        pr_info['title'] = event['pull_request']['title']
        pr_info['branch'] = event['pull_request']['head']['ref']
        pr_info['sha'] = event['pull_request']['head']['sha']
    except:
        logger.error(event)
        raise Exception("Invalid Github PR Webhook")
    pipeline_info['pr_info'] = pr_info

    pipeline_action = "none"
    if event['action'] in ['opened', 'synchronize']:
        pipeline_action = "test"
    elif event['action'] == 'closed' and event['pull_request']['merged']:
        pipeline_action = "deploy"
    pipeline_info['action'] = pipeline_action
    logger.info("{} for PR {} (#{}) of branch {}".format(pipeline_action,
                                                         pr_info['title'],
                                                         pr_info['number'],
                                                         pr_info['branch']))
    return pipeline_info

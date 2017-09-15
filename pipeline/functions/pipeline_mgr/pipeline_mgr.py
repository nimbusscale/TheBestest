#!/usr/bin/env python3
# webhook test 3
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
        pr_info['action'] = event['action']
        pr_info['number'] = event['number']
        pr_info['branch'] = event['pull_request']['head']['ref']
        pr_info['sha'] = event['pull_request']['head']['sha']
    except:
        log(event)
        raise Exception("Invalid PR Webhook")
    pipeline_info['pr_info'] = pr_info
    return pipeline_info
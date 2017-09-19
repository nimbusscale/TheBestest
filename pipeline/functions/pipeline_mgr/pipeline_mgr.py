#!/usr/bin/env python3
# webhook test 11
import logging
import os

import boto3
import github3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def webhook_handler(event, context):
    """Lambda that evaluates the input provided by the API GW and determines
    if it's a valid PR Open Webhook notice.
    """
    pipeline_info = {}
    try:
        pull_request = event['pull_request']
        pr_info = {}
        pr_info['owner'] = pull_request['head']['repo']['owner']['login']
        pr_info['repo'] = pull_request['head']['repo']['name']
        pr_info['url'] = pull_request['url']
        pr_info['title'] = pull_request['title']
        pr_info['branch'] = pull_request['head']['ref']
        pr_info['sha'] = pull_request['head']['sha']
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
    logger.info("{} for PR {} ({}) of branch {}".format(pipeline_action,
                                                         pr_info['title'],
                                                         pr_info['url'],
                                                         pr_info['branch']))
    return pipeline_info

def retrieve_source(event, context):
    """Lambda that retrieves a zipball of source based on a SHA and uploads
    it to S3
    """
    owner = event['pr_info']['owner']
    repo_name = event['pr_info']['repo']
    sha = event['pr_info']['sha']
    token = os.environ['OAUTH_TOKEN']
    bucket = os.environ['S3_BUCKET']
    # Download zipball from GH
    gh = github3.login(token=token)
    repo = gh.repository(owner, repo_name)
    download_path = '/tmp/' + sha + '.zip'
    logger.info("Downloading zipball to {}".format(download_path))
    repo.archive('zipball', path=download_path, ref=sha)
    # Upload zipball from S3
    s3 = boto3.client('s3')
    logger.info("Uploading zipball to s3://{}/thebestest-source.zip".format(
        bucket
    ))
    with open(download_path, 'rb') as zipball:
        response = s3.put_object(Bucket=bucket,
                                 Key='thebestest-source.zip',
                                 Body=zipball)
    etag = response['ETag']
    logger.info("Upload has ETag {}".format(etag))
    # Cleanup
    logger.info("Removing {}".format(download_path))
    os.remove(download_path)
    # Return
    event['etag'] = etag
    return event









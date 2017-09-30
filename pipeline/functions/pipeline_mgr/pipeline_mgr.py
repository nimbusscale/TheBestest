#!/usr/bin/env python3
import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import boto3
import github3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

"""Helper Functions"""


def repackage_source(src_zip_path, dest_zip_path):
    """Repackages a zipball retrieved from Github to be as expected by
    codepipeline.
    """
    logger.info("Repackaging {} to {}".format(src_zip_path, dest_zip_path))
    work_path = '/tmp'
    with ZipFile(src_zip_path) as src_zip:
        zip_info = src_zip.infolist()
        unzip_dir = work_path + '/' + zip_info[0].filename
        src_zip.extractall(path=work_path)
    with ZipFile(dest_zip_path, mode='w',
                 compression=ZIP_DEFLATED) as dest_zip:
        for root, dirs, files in os.walk(unzip_dir):
            for file in files:
                src_path = os.path.join(root, file)
                arc_path = src_path.replace(unzip_dir, '')
                dest_zip.write(src_path, arcname=arc_path)


"""Lambda's"""


def webhook_handler(event, context):
    """Lambda that evaluates the input provided by the API GW and determines
    if it's a valid PR Open Webhook notice.
    """
    pipeline_info = {}
    try:
        pull_request = event['pull_request']
        pr_info = {
            'owner': pull_request['head']['repo']['owner']['login'],
            'repo': pull_request['head']['repo']['name'],
            'url': pull_request['url'],
            'title': pull_request['title'],
            'branch': pull_request['head']['ref'],
            'sha': pull_request['head']['sha']
        }
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
    # Repackage
    zipball_name = 'thebestest-source.zip'
    zipball_path = '/tmp/' + zipball_name
    repackage_source(download_path, zipball_path)
    # Upload zipball from S3
    s3 = boto3.client('s3')
    logger.info("Uploading {} to s3://{}/{}".format(zipball_path, bucket,
                                                     zipball_name))
    with open(zipball_path, 'rb') as zipball:
        response = s3.put_object(Bucket=bucket,
                                 Key=zipball_name,
                                 Body=zipball)
    event['version_id'] = response['VersionId']
    logger.info("Upload has Version ID {}".format(event['version_id']))
    # Cleanup
    logger.info("Removing {}".format(download_path))
    os.remove(download_path)
    logger.info("Removing {}".format(zipball_path))
    os.remove(zipball_path)
    # Return
    return event


def start_pipeline(event, context):
    """Lambda that starts a codepipeline.

    Pipeline name is provided by Env Var
    """
    owner = event['pr_info']['owner']
    repo_name = event['pr_info']['repo']
    sha = event['pr_info']['sha']
    url = event['pr_info']['url']
    pipeline_name = os.environ['PIPELINE_NAME']
    token = os.environ['OAUTH_TOKEN']
    codepipeline = boto3.client('codepipeline')
    response = codepipeline.start_pipeline_execution(name=pipeline_name)
    execution_id = response['pipelineExecutionId']
    # Set status on the PR in Github
    gh = github3.login(token=token)
    repo = gh.repository(owner, repo_name)
    repo.create_status(sha, 'pending',
                       target_url=url,
                       context=pipeline_name,
                       description=execution_id)
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
    owner = event['pr_info']['owner']
    repo_name = event['pr_info']['repo']
    sha = event['pr_info']['sha']
    url = event['pr_info']['url']
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
    gh = github3.login(token=token)
    repo = gh.repository(owner, repo_name)
    repo.create_status(sha, pr_status,
                       target_url=url,
                       context=pipeline_name,
                       description=execution_id)
    return event











#!/usr/bin/env python3
"""Deploys TheBestest Pipeline manager.

This includes Lambda and API GW to handle webhooks from github.

aws cli is used to deploy cloudformation stack vs boto3. This is because cli
has additional functionality for packaging CFN templates that is not found in
boto3.

Most of this was copied from a shell script hence a lot of calls to CLI
commands.
"""
import argparse
import os
import shutil
from subprocess import run

import boto3
import github3


def arg_parse():
    parser = argparse.ArgumentParser(
        description="Deploys TheBestest Pipeline manager")

    parser.add_argument(
        '--token', '-t',
        help=("OAuthToken used to communicate with Github. Only needed for "
              "stack creation or to update the token.")
    )

    return parser.parse_args()


def prep_lambdas():
    """Copies functions to temp location and then installs 3rd party packages
    into temp copy. Temp location is referenced by the cfn template.
    """
    if os.path.exists('./functions_deploy'):
        shutil.rmtree('./functions_deploy')

    rsync_cmd = "rsync -av ./functions/ ./functions_deploy/"
    run(rsync_cmd.split(), check=True)

    gh_install = "pip install github3.py -t ./functions_deploy/pipeline_mgr/"
    run(gh_install.split(), check=True)


def cfn_deploy():
    print("## Validate")
    validate_cmd = ("aws cloudformation validate-template "
                    "--template-body file://pipeline_mgr_stack.yaml")
    run(validate_cmd.split(), check=True)

    print("## Package")
    pkg_cmd = ("aws cloudformation package "
                "--template-file pipeline_mgr_stack.yaml "
                "--s3-bucket thebestest-pipeline "
                "--output-template-file pipeline_mgr_stack_deploy.yaml")
    run(pkg_cmd.split(), check=True)

    print("## Deploy")
    deploy_opts = ("--template-file pipeline_mgr_stack_deploy.yaml "
                   "--stack-name thebestest-pipeline-mgr "
                   "--capabilities CAPABILITY_IAM")

    if args.token:
        deploy_opts = (deploy_opts +
                       " --parameter-overrides OAuthToken={}".format(
                           args.token))

    deploy_cmd = "aws cloudformation deploy {}".format(deploy_opts)
    run(deploy_cmd.split(), check=True)


def cleanup():
    if os.path.exists('./functions_deploy'):
        shutil.rmtree('./functions_deploy')

    if os.path.exists('pipeline_mgr_stack_deploy.yaml'):
        os.remove('pipeline_mgr_stack_deploy.yaml')


def get_oauth_from_cfn(stack_name):
    cfn = boto3.client('cloudformation')
    stack = cfn.describe_stacks(StackName=stack_name)['Stacks'][0]
    for param in stack['Parameters']:
        if param['ParameterKey'] == 'OAuthToken':
            return param['ParameterValue']
    else:
        raise Exception("stack {} doesn't have OAuthToken as a "
                        "Parameter".format(stack_name))


def update_webhook():
    # Get Webhook URL
    pipelinemgr_api_name = 'thebestest-pipelinemgr-api'
    stage_name = 'pipelinemgr'
    region = boto3.session.Session().region_name
    apigw = boto3.client('apigateway')
    rest_apis = apigw.get_rest_apis()['items']
    for rest_api in rest_apis:
        if rest_api['name'] == pipelinemgr_api_name:
            api_id = rest_api['id']
            break
    else:
        raise Exception("Unabel to find Rest API with name {}.".format(
            pipelinemgr_api_name
        ))

    api_url = "https://{}.execute-api.{}.amazonaws.com/{}/webhook".format(
        api_id, region, stage_name
    )
    # Create or Update Webhook config
    token = (args.token if args.token else
             get_oauth_from_cfn('thebestest-pipeline-mgr'))
    gh = github3.login(token=token)
    repo = gh.repository('nimbusscale', 'TheBestest')
    webhooks = repo.iter_hooks()
    webhook_config = {'content_type': 'json',
                      'insecure_ssl': '0',
                      'url': api_url}
    for webhook in webhooks:
        url = webhook.config['url']
        if stage_name in url:
            webhook.edit(config=webhook_config)
            break
    else:
        repo.create_hook('web',
                         webhook_config,
                         events=['pull_request'])

if __name__ == '__main__':
    args = arg_parse()
    prep_lambdas()
    cfn_deploy()
    cleanup()
    update_webhook()




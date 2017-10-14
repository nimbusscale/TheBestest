#!/usr/bin/env python3
"""Deploys TheBestest Pipeline manager.

This includes Lambda and API GW to handle webhooks from github.

aws cli is used to deploy cloudformation stack vs boto3. This is because cli
has additional functionality for packaging CFN templates that is not found in
boto3.

This initially started as a shell script, so there is still some left over CLI
commands that should ideally be moved to native python.
"""
import argparse
import os
import shutil
import subprocess

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
    subprocess.run(rsync_cmd.split(), check=True)

    gh_install = "pip install github3.py -t ./functions_deploy/pipeline/"
    subprocess.run(gh_install.split(), check=True)


def cfn_deploy(stack_name, template_path):
    cfn = boto3.client('cloudformation')
    print("## Validate - {}".format(template_path))
    with open(template_path) as template_file:
        validation_response = cfn.validate_template(
            TemplateBody=template_file.read())
    print(validation_response)

    # if OAuthToken is a template param, then check if one has been set via
    # args.
    token = None
    for params in validation_response['Parameters']:
        if params['ParameterKey'] == 'OAuthToken':
            if args.token:
                token = args.token

    deploy_file = template_path.replace('.yaml', '_deploy.yaml')

    print("## Package - {}".format(template_path))
    pkg_cmd = ("aws cloudformation package "
                "--template-file {} "
                "--s3-bucket thebestest-pipeline "
                "--output-template-file {}"
               ).format(template_path, deploy_file)
    subprocess.run(pkg_cmd.split(), check=True)

    print("## Deploy - {}".format(deploy_file))
    deploy_opts = ("--template-file {} "
                   "--stack-name {} "
                   "--capabilities CAPABILITY_IAM"
                   ).format(deploy_file, stack_name)

    if token:
        deploy_opts = (deploy_opts +
                       " --parameter-overrides OAuthToken={}".format(
                           token))

    deploy_cmd = "aws cloudformation deploy {}".format(deploy_opts)
    try:
        subprocess.run(deploy_cmd.split(), stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        # If error encountered see if it is because the template hasn't changed
        # if so, then ignore error
        if "didn't contain changes" not in str(e.stderr):
            raise
        else:
            print("No new updates for stack {}".format(stack_name))



def cleanup(template_path):
    if os.path.exists('./functions_deploy'):
        print('removing functions_deploy dir')
        shutil.rmtree('./functions_deploy')

    deploy_file = template_path.replace('.yaml', '_deploy.yaml')
    if os.path.exists(deploy_file):
        print("removing {}".format(deploy_file))
        os.remove(deploy_file)


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
    # Ordered list tuples of stacks to deploy. Tuples include stack name,
    # template file path and env name (use None if no pertinent env name)
    stacks = [
        ('thebestest-pipeline-prod', 'pipeline_deploy_stack.yaml'),
        ('thebestest-pipeline-mgr', 'pipeline_mgr_stack.yaml')
    ]
    args = arg_parse()
    prep_lambdas()

    for stack_name, template_path in stacks:
        cfn_deploy(stack_name, template_path)

    # Cleanup needs to wait till after all stacks deployed otherwise lambda
    # temp folder is removed before it's needed
    print("## Cleanup")
    for stack_name, template_path in stacks:
        cleanup(template_path)

    update_webhook()




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

if __name__ == '__main__':
    args = arg_parse()
    prep_lambdas()
    cfn_deploy()
    cleanup()




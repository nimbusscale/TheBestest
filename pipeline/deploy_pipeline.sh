#!/bin/bash
set -e



function usage() {
cat <<EOM
Usage: `basename $0` --pipeline [value] --env [value] [OPTION]
Arguments:
    --pipeline          Pipeline type: test or deploy (defaults to test)
    --branch            Git branch to checkout (defaults to master)
    --env               Environment name (defaults to sanitized branch name)
EOM

exit
}

function arg_parse() {
# Default params, maybe overrided by args
PIPELINE="test"
GIT_BRANCH="master"
ENV=${GIT_BRANCH//[\_\.]/-}

# Parse Args
while [[ $# -gt 1 ]]
do
    ARG="$1"

    case $ARG in
        -b|--branch)
        GIT_BRANCH="$2"
        shift
        ;;
        -e|--env)
        ENV="$2"
        shift
        ;;
        -p|--pipeline)
        PIPELINE="$2"
        shift
        ;;
        *)
        usage
        ;;
    esac
    shift
done
}

function cfn_deploy() {
STACK_NAME="thebestest-${ENV}-${PIPELINE}-pipeline"

echo "## Validate"
aws cloudformation validate-template --template-body file://pipeline_${PIPELINE}_stack.yaml

echo "## Package"
aws cloudformation package  --template-file pipeline_${PIPELINE}_stack.yaml \
                            --s3-bucket thebestest-pipeline \
                            --output-template-file pipeline_stack_${PIPELINE}_deploy.yaml

echo "## Deploy"
aws cloudformation deploy   --template-file pipeline_stack_${PIPELINE}_deploy.yaml \
                            --stack-name ${STACK_NAME} \
                            --capabilities CAPABILITY_IAM \
                            --parameter-overrides "gitBranch"=${GIT_BRANCH} "envName"=${ENV}
}

arg_parse $@
cfn_deploy
rm *_deploy.yaml
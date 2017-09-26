#!/bin/bash
set -e

function usage() {
cat <<EOM
Usage: `basename $0` --pipeline [value] --env [value] [OPTION]
Arguments:
    --pipeline          Pipeline type: test or deploy (defaults to test)
    --env               Environment name (only used for deploy pipelines and
                        defaults to "stage")
EOM

exit
}

function arg_parse() {
# Default params, maybe overrided by args
PIPELINE="test"
ENV="stage"

# Parse Args
while [[ $# -gt 1 ]]
do
    ARG="$1"

    case $ARG in
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
if [[ "$PIPELINE" == "deploy" ]]; then
    STACK_NAME="thebestest-pipeline-deploy-${ENV}"
else
    STACK_NAME="thebestest-pipeline-test"
fi

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
                            --parameter-overrides "envName"=${ENV}
}

arg_parse $@
cfn_deploy
rm *_deploy.yaml
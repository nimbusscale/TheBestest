#!/bin/bash
set -e

function usage() {
cat <<EOM
Usage: `basename $0` --token [value]
Arguments:
    --token          OAuthToken used to communicate with Github
EOM

exit
}

function arg_parse() {
if [[ $# -lt 1 ]] ; then
    usage
fi

# Parse Args
while [[ $# -gt 1 ]]
do
    ARG="$1"

    case $ARG in
        --token)
        TOKEN="$2"
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
STACK_NAME="thebestest-pipeline-infra"

echo "## Validate"
aws cloudformation validate-template --template-body file://pipeline_infra.yaml

echo "## Package"
aws cloudformation package  --template-file pipeline_infra.yaml \
                            --s3-bucket thebestest-pipeline \
                            --output-template-file pipeline_infra_deploy.yaml

echo "## Deploy"
aws cloudformation deploy   --template-file pipeline_infra_deploy.yaml \
                            --stack-name ${STACK_NAME} \
                            --capabilities CAPABILITY_IAM \
                            --parameter-overrides "OAuthToken"=${TOKEN}
}


arg_parse $@
cfn_deploy
rm *_deploy.yaml
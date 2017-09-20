#!/bin/bash
set -e

function usage() {
cat <<EOM
Usage: `basename $0` --token [value]
Arguments:
    --token         OAuthToken used to communicate with Github
                    (Only needed for stack creation or to update the token)

EOM

exit
}

function arg_parse() {
STACK_NAME="thebestest-pipeline-infra"

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

function prep_lambdas() {
# Copies functions to temp location and then installs 3rd party packages into
# temp copy. Temp location is referenced by the cfn template.

rsync -av ./functions/ ./functions_deploy/

pip install github3.py -t ./functions_deploy/pipeline_mgr/

}

function cfn_deploy() {
echo "## Validate"
aws cloudformation validate-template --template-body file://pipeline_infra.yaml

echo "## Package"
aws cloudformation package  --template-file pipeline_infra.yaml \
                            --s3-bucket thebestest-pipeline \
                            --output-template-file pipeline_infra_deploy.yaml

echo "## Deploy"
OPTS="--template-file pipeline_infra_deploy.yaml \
      --stack-name ${STACK_NAME} \
      --capabilities CAPABILITY_IAM"

if [[ $TOKEN ]] ; then
    OPTS="${OPTS} --parameter-overrides "OAuthToken"=${TOKEN}"
fi

aws cloudformation deploy $OPTS
}


arg_parse $@
prep_lambdas
cfn_deploy
rm *_deploy.yaml
rm -rf functions_deploy
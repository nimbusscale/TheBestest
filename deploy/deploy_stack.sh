#!/bin/bash
#Script to do manual deployment of theBestest stack. Deployment should ideally be done via the pipeline.
set -e

echo "## Validate"
aws cloudformation validate-template --template-body file://stack.yaml

echo "## Package"
aws cloudformation package --template-file stack.yaml --s3-bucket thebestest-pipeline --output-template-file stack_deploy.yaml

echo "## Deploy Stack"
aws cloudformation deploy --template-file stack_deploy.yaml --stack-name thebestest-stack --capabilities CAPABILITY_IAM

echo "## Deploy API"
API_ID=$(aws cloudformation describe-stacks --stack-name thebestest-stack --output text | grep apiGwId | awk '{print $3}')
aws apigateway create-deployment --rest-api-id ${API_ID} --stage-name "v1"
aws apigateway update-stage --rest-api-id ${API_ID} --stage-name "v1" --patch-operations op=replace,path=/*/*/logging/loglevel,value=INFO
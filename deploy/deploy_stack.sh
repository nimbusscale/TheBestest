#!/bin/bash
#Script to do manual deployment of theBestest stack. Deployment should ideally be done via the pipeline.
set -e

echo "## Validate"
aws cloudformation validate-template --template-body file://stack.yaml

echo "## Package"
aws cloudformation package --template-file stack.yaml --s3-bucket thebestest-pipeline --output-template-file stack_deploy.yaml

echo "## Deploy Stack"
aws cloudformation deploy --template-file stack_deploy.yaml --stack-name thebestest-testing --capabilities CAPABILITY_IAM
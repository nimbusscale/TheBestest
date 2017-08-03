#!/bin/bash
set -e

echo "## Validate"
aws cloudformation validate-template --template-body file://pipeline_stack.yaml

echo "## Package"
aws cloudformation package --template-file pipeline_stack.yaml --s3-bucket thebestest-pipeline --output-template-file pipeline_stack_deploy.yaml

echo "## Deploy"
aws cloudformation deploy --template-file pipeline_stack_deploy.yaml --stack-name thebestest-pipeline --capabilities CAPABILITY_IAM
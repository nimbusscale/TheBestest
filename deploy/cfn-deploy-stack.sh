#!/bin/bash
set -e

echo "## Validate"
aws cloudformation validate-template --template-body file://stack.yaml

echo "## Package"
aws cloudformation package --template-file stack.yaml --s3-bucket thebestest-pipeline --output-template-file stack_deploy.yaml

echo "## Deploy"
aws cloudformation deploy --template-file stack_deploy.yaml --stack-name thebestest-stack --capabilities CAPABILITY_IAM
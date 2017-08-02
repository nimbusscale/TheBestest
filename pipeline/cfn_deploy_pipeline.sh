#!/bin/bash
set -e

echo "## Validate"
aws cloudformation validate-template --template-body file://pipeline.yaml

echo "## Package"
aws cloudformation package --template-file pipeline.yaml --s3-bucket thebestest-pipeline --output-template-file pipeline_deploy.yaml

echo "## Deploy"
aws cloudformation deploy --template-file pipeline_deploy.yaml --stack-name thebestest-pipeline --capabilities CAPABILITY_IAM
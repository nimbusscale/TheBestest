import json
import logging

import boto3
from pipeline_mgr.stack import Stack

logger = logging.getLogger()


class Pipeline:

    def __init__(self, spec):
        if type(spec) == dict:
            self._name = spec.get('name')
            self._execution_id = spec.get('execution_id')
        else:
            raise TypeError(
                "spec is a {} not a dict.".format(type(spec))
            )

    def __repr__(self):
        return ("Pipeline(" +
                str({'name': self.name,
                    'execution_id': self.execution_id,
                     'status': self.status})
                + ")"

        )

    def build(self, source, template_path):
        """Builds a pipeline with a test and deploy stack"""
        stack = Stack(self.name)
        if stack.status == 'ROLLBACK_COMPLETE':
            stack.delete()
        if not stack.arn:
            logger.info("CFN stack {} does not exist.".format(self.name))
            source.download_from_s3()
            source.unzip()
            unzipdir = source.unzip_dir
            stack.create(unzipdir + template_path,
                         parameters={'S3SourceKey': source.s3_path})
        else:
            logger.info("CFN stack {} already exists".format(self.name))

    @property
    def execution_id(self):
        return self._execution_id

    @execution_id.setter
    def execution_id(self, pipeline_execution_id):
        self._execution_id = pipeline_execution_id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, pipeline_name):
        self._name = pipeline_name

    def to_dict(self):
        return {'name': self.name,
                'execution_id': self.execution_id,
                'status': self.status}

    def start(self):
        codepipeline = boto3.client('codepipeline')
        response = codepipeline.start_pipeline_execution(name=self.name)
        self.execution_id = response['pipelineExecutionId']
        return self.execution_id

    @property
    def status(self):
        if self.execution_id:
            codepipeline = boto3.client('codepipeline')
            status_response = codepipeline.get_pipeline_execution(
                pipelineName=self.name,
                pipelineExecutionId=self.execution_id)
            return status_response['pipelineExecution']['status']
        else:
            return None

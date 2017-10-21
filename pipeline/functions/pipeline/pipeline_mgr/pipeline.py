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
            self._app_stack_name = spec.get('app_stack_name')
            if spec.get('stack'):
                self._stack = (
                    spec['stack'] if type(spec['stack']) is Stack
                    else Stack(spec['stack'])
                )
            else:
                self._stack = Stack({'name': self.name})
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

    @property
    def app_stack_name(self):
        return self._app_stack_name

    @app_stack_name.setter
    def app_stack_name(self, name):
        self._app_stack_name = name

    def build(self, source, template_path):
        """Builds a pipeline with a test and deploy stack"""
        source.download_from_s3()
        source.unzip()
        unzipdir = source.unzip_dir
        self.stack.apply_template(
            unzipdir + template_path,
            parameters={
                'S3SourceKey': source.s3_path,
                'AppStackName': self.app_stack_name
            }
        )

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
    def stack(self):
        return self._stack

    @stack.setter
    def stack(self, stack_obj):
        if type(stack_obj) is Stack:
            self._stack = stack_obj
        else:
            raise TypeError("stack must be Stack object")

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

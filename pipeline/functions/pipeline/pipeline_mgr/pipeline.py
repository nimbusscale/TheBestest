import json
import logging

import boto3

logger = logging.getLogger()


class Pipeline:

    def __init__(self, pipeline_def):
        if type(pipeline_def) == dict:
            self.name = pipeline_def.get('name', None)
            self.execution_id = pipeline_def.get('execution_id', None)
        else:
            raise TypeError(
                "pipeline_def is a {} not a dict.".format(type(pipeline_def))
            )

    def __repr__(self):
        return (
           str({'name': self.name,
                'execution_id': self.execution_id,
                'status': self.staus})
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
                'status': self.staus}

    def start(self):
        codepipeline = boto3.client('codepipeline')
        response = codepipeline.start_pipeline_execution(name=self.name)
        self.execution_id = response['pipelineExecutionId']
        return self.execution_id

    @property
    def staus(self):
        if self.execution_id:
            codepipeline = boto3.client('codepipeline')
            status_response = codepipeline.get_pipeline_execution(
                pipelineName=self.name,
                pipelineExecutionId=self.execution_id)
            return status_response['pipelineExecution']['status']
        else:
            return None

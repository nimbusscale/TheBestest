import logging

from pipeline_mgr.pipeline import Pipeline
from pipeline_mgr.pull_request import PullRequest
from pipeline_mgr.source import Source

logger = logging.getLogger()


class Manager:

    def __init__(self, spec):
        if type(spec) is dict:
            self._bucket_name = spec['bucket_name']
            self._pull_request = (
                spec['pull_request'] if type(spec['pull_request']) 
                                        is PullRequest 
                else PullRequest(spec['pull_request'])
            )
            self._oath_token = spec['oath_token']

            # If pipeline or source spec is included use it to build
            # objects ,otherwise build objects based on provided params
            if spec.get('pipeline'):
                self._pipeline = (
                    spec['pipeline'] if type(spec['pipeline']) 
                                            is Pipeline 
                    else Pipeline(spec['pipeline'])
                )
            else:
                pipeline_spec = {
                    'name': ("thebestest-pipeline-test-"
                             + str(self.pull_request.number))
                }
                self._pipeline = Pipeline(pipeline_spec)

            if spec.get('source'):
                self._source = (
                    spec['source'] if type(spec['source']) 
                                            is Source 
                    else Source(spec['source'])
                )
            else:
                src_spec = {
                    'bucket_name': self.bucket_name,
                    'id': self.pull_request.number,
                    'repo_owner': self.pull_request.owner,
                    'repo_name': self.pull_request.repo_name,
                    'sha': self.pull_request.sha,
                    'token': self.oath_token
                }
                self._source = Source(src_spec)
        else:
            raise TypeError(
                "spec is a {} not a dict.".format(type(spec))
            )

    def __repr__(self):
        return ("Manager(" +
                    str(
                            {
                                'bucket_name': self.bucket_name,
                                'pipeline': self.pipeline,
                                'pull_request': self.pull_request,
                                'source': self.source,
                                'oath_token': self.oath_token
                            }
                        )
                + ")"
                )

    @property
    def bucket_name(self):
        return self._bucket_name

    @bucket_name.setter
    def bucket_name(self, name):
        self._bucket_name = name

    @property
    def pipeline(self):
        return self._pipeline

    @pipeline.setter
    def pipeline(self, pipeline_obj):
        if type(pipeline_obj) is Pipeline:
            self._pipeline = pipeline_obj
        else:
            raise TypeError("pipeline must be a Pipeline object")

    @property
    def pull_request(self):
        return self._pull_request

    @pull_request.setter
    def pull_request(self, pr_obj):
        if type(pr_obj) is PullRequest:
            self._pull_request = pr_obj
        else:
            raise TypeError("pull_request must be a PullRequest object")

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source_obj):
        if type(source_obj) is Pipeline:
            self._source = source_obj
        else:
            raise TypeError("source must be a Source object")


    @property
    def oath_token(self):
        return self._oath_token

    @oath_token.setter
    def oath_token(self, token):
        self._oath_token = token

    def to_dict(self):
        return {
            'bucket_name':  self.bucket_name,
            'pipeline':     self.pipeline.to_dict(),
            'pull_request': self.pull_request.to_dict(),
            'source':       self.source.to_dict(),
            'oath_token':   self.oath_token
        }

import logging

import github3
from pipeline_mgr.source import Source

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PullRequest:

    def __init__(self, pr_data):
        if type(pr_data) == dict:
            self.data = pr_data
        else:
            raise TypeError(
                "pr_data is a {} not a dict.".format(type(pr_data))
            )

    def __repr__(self):
        return str(self.data)

    def __str__(self):
        pr_info = {
            'branch_name': self.branch_name,
            'owner': self.owner,
            'repo_name': self.repo_name,
            'sha': self.sha,
            'url': self.url
        }
        return str(pr_info)

    @property
    def branch_name(self):
        return self.data['head']['ref']

    def set_status(self, token, status, context,
                      description):
        valid_status = ['pending', 'success', 'failure', 'error']
        if status not in valid_status:
            raise TypeError(
                "{} is not a valid status. Valid statuses are {}".format(
                    status, valid_status
                )
            )
        gh = github3.login(token=token)
        repo = gh.repository(self.owner, self.repo_name)
        logger.info(
            "Setting status on {}@{}:{} for {} to {}".format(
                self.owner,
                self.repo_name,
                self.sha,
                context,
                status
            )
        )
        repo.create_status(self.sha,
                           status,
                           target_url=self.url,
                           context=context,
                           description=description
                           )

    @property
    def owner(self):
        return self.data['head']['repo']['owner']['login']

    @property
    def repo_name(self):
        return self.data['head']['repo']['name']

    def retrieve_source(self, token, bucket_name):
        source = Source(token, self.owner, self.repo_name, self.sha,
                        bucket_name)
        source.download_archive()
        source.repackage_archive()
        version_id = source.upload_archive()
        return version_id

    @property
    def sha(self):
        return self.data['head']['sha']

    @property
    def title(self):
        return self.data['title']

    @property
    def url(self):
        return self.data['url']




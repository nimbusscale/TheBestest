import logging

import github3

logger = logging.getLogger()


class PullRequest:

    def __init__(self, spec):
        if type(spec) == dict:
            self._data = spec
        else:
            raise TypeError(
                "spec is a {} not a dict.".format(type(spec))
            )

    def __repr__(self):
        return "PullRequest(" + str(self.to_dict()) + ")"

    def __str__(self):
        pr_info = {
            'branch_name': self.branch_name,
            'number': self.number,
            'owner': self.owner,
            'repo_name': self.repo_name,
            'sha': self.sha,
            'url': self.url
        }
        return str(pr_info)

    @property
    def branch_name(self):
        return self._data['head']['ref']

    @property
    def number(self):
        return self._data['number']

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
        return self._data['head']['repo']['owner']['login']

    @property
    def repo_name(self):
        return self._data['head']['repo']['name']

    @property
    def sha(self):
        return self._data['head']['sha']

    @property
    def title(self):
        return self._data['title']

    def to_dict(self):
        return {
                'title': self.title,
                'url': self.url,
                'number': self.number,
                'head':
                    {
                        'ref': self.branch_name,
                        'sha': self.sha,
                        'repo':
                            {
                                'name': self.repo_name,
                                'owner':
                                    {
                                        'login': self.owner
                                    }
                            }
                    }
                }

    @property
    def url(self):
        return self._data['url']




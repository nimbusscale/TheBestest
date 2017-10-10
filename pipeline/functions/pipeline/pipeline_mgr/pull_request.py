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

    @property
    def owner(self):
        return self.data['head']['repo']['owner']['login']

    @property
    def repo_name(self):
        return self.data['head']['repo']['name']

    @property
    def sha(self):
        return self.data['head']['sha']

    @property
    def title(self):
        return self.data['title']

    @property
    def url(self):
        return self.data['url']




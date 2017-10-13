logger = logging.getLogger()

from pipeline_mgr.pull_request import PullRequest


class Manager:

    def __init__(self, token):
        self.token = token

    def hanlde_webhook(webhook):
        try:
            pull_request = PullRequest(webhook['pull_request'])
        except:
            logger.error(webhook)
            raise Exception("Invalid Github PR Webhook")
        logger.info(
            "PR {} ({}) of branch {}".format(pull_request.title,
                                             pull_request.url,
                                             pull_request.branch_name)
        )
        return pull_request.to_dict()

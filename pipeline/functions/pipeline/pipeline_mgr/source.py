import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import boto3
import github3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Source:

    def __init__(self, token, repo_owner, repo_name, sha, bucket_name ):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.sha = sha
        self.bucket_name = bucket_name

        self.download_path = '/tmp/' + sha + '.zip'
        self.zipball_name = 'thebestest-source.zip'
        self.zipball_path = '/tmp/' + self.zipball_name

    def download_archive(self):
        gh = github3.login(token=self.token)
        repo = gh.repository(self.repo_owner, self.repo_name)
        logger.info("Downloading zipball to {}".format(self.download_path))
        repo.archive('zipball', path=self.download_path, ref=self.sha)

    def repackage_archive(self):
        """Repackages a zipball retrieved from Github to be as expected by
        codepipeline.
        """
        logger.info("Repackaging {} to {}".format(
            self.download_path, self.zipball_path))
        work_path = '/tmp'
        with ZipFile(self.download_path) as src_zip:
            zip_info = src_zip.infolist()
            unzip_dir = work_path + '/' + zip_info[0].filename
            src_zip.extractall(path=work_path)
        with ZipFile(self.zipball_path, mode='w',
                     compression=ZIP_DEFLATED) as dest_zip:
            for root, dirs, files in os.walk(unzip_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    arc_path = src_path.replace(unzip_dir, '')
                    dest_zip.write(src_path, arcname=arc_path)

    def upload_archive(self):
        s3 = boto3.client('s3')
        logger.info("Uploading {} to s3://{}/{}".format(
            self.zipball_path, self.bucket_name, self.zipball_name))
        with open(self.zipball_path, 'rb') as zipball:
            response = s3.put_object(Bucket=self.bucket_name,
                                     Key=self.zipball_name,
                                     Body=zipball)
        version_id = response['VersionId']
        logger.info("Upload has Version ID {}".format(version_id))
        logger.info("Removing {}".format(self.download_path))
        os.remove(self.download_path)
        logger.info("Removing {}".format(self.zipball_path))
        os.remove(self.zipball_path)
        return version_id


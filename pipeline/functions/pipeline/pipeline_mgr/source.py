import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import boto3
import github3

logger = logging.getLogger()


class Source:

    def __init__(self, token, repo_owner, repo_name, id, sha,
                 bucket_name):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.id = str(id)
        self.sha = sha
        self.bucket_name = bucket_name

        self.work_path = '/tmp'
        self._unzip_dir = None

        self.download_path = '/tmp/' + self.sha + '.zip'
        self.zipball_name = 'thebestest-' + self.id + '.zip'
        self.s3_path = 'source/' + self.zipball_name
        self.zipball_path = '/tmp/' + self.zipball_name

    def download_from_github(self):
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
        self.unzip()
        self.zip()

    def unzip(self):
        with ZipFile(self.download_path) as src_zip:
            zip_info = src_zip.infolist()
            unzip_dir = self.work_path + '/' + zip_info[0].filename
            logger.info("unzipping {} to {}".format(self.download_path,
                                                    unzip_dir))
            src_zip.extractall(path=self.work_path)
            self.unzip_dir = unzip_dir

    @property
    def unzip_dir(self):
        return self._unzip_dir

    @unzip_dir.setter
    def unzip_dir(self, path):
        if os.path.isdir(path):
            self._unzip_dir = path
        else:
            raise ValueError(
                "{} is not a path to a directory that exists.".format(path)
            )

    def zip(self):
        logger.info("zipping {} into {}".format(self.unzip_dir,
                                                self.zipball_path))
        with ZipFile(self.zipball_path, mode='w',
                     compression=ZIP_DEFLATED) as dest_zip:
            for root, dirs, files in os.walk(self.unzip_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    arc_path = src_path.replace(self.unzip_dir, '')
                    dest_zip.write(src_path, arcname=arc_path)

    def upload_to_s3(self):
        s3 = boto3.client('s3')
        logger.info("Uploading {} to s3://{}/{}".format(
            self.zipball_path, self.bucket_name, self.s3_path))
        with open(self.zipball_path, 'rb') as zipball:
            response = s3.put_object(Bucket=self.bucket_name,
                                     Key=self.s3_path,
                                     Body=zipball)
        version_id = response['VersionId']
        logger.info("Upload has Version ID {}".format(version_id))
        logger.info("Removing {}".format(self.download_path))
        os.remove(self.download_path)
        logger.info("Removing {}".format(self.zipball_path))
        os.remove(self.zipball_path)
        return version_id

    def download_from_s3(self):
        s3 = boto3.client('s3')
        logger.info("Downloading s3://{}/{} to {}".format(
            self.bucket_name, self.s3_path, self.zipball_path))



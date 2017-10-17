import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import boto3
import github3

logger = logging.getLogger()


class Source:

    def __init__(self, spec):
        if type(spec) == dict:
            self._token = spec.get('token')
            self._repo_owner = spec.get('repo_owner')
            self._repo_name = spec.get('repo_name')
            self._id = str(spec.get('id'))
            self._sha = spec.get('sha')
            self._bucket_name = spec.get('bucket_name')
            self._work_path = spec.get('work_path', '/tmp')
        else:
            raise TypeError(
                "spec is a {} not a dict.".format(type(spec))
            )

        self._unzip_dir = None
        self._download_path = None
        self._zipball_name = 'thebestest-' + self._id + '.zip'
        self._s3_path = 'source/' + self._zipball_name
        self._zipball_path = '/tmp/' + self._zipball_name

    def __repr__(self):
        return "Source(" + str(self.to_dict()) + ")"

    def download_from_github(self):
        gh = github3.login(token=self._token)
        repo = gh.repository(self._repo_owner, self._repo_name)
        self.download_path = '/tmp/' + self._sha + '.zip'
        logger.info("Downloading zipball to {}".format(self.download_path))
        repo.archive('zipball', path=self.download_path, ref=self._sha)

    def download_from_s3(self):
        s3 = boto3.resource('s3')
        logger.info("Downloading s3://{}/{} to {}".format(
            self._bucket_name, self._s3_path, self._zipball_path))
        s3.meta.client.download_file(self._bucket_name,
                                     self._s3_path,
                                     self._zipball_path)
        self.download_path = self._zipball_path

    @property
    def download_path(self):
        return self._download_path

    @download_path.setter
    def download_path(self, path):
        self._download_path = path

    def repackage_archive(self):
        """Repackages a zipball retrieved from Github to be as expected by
        codepipeline.
        """
        logger.info("Repackaging {} to {}".format(
            self.download_path, self._zipball_path))
        self.unzip()
        self.zip()

    def retrieve_source(self):
        self.download_from_github()
        self.repackage_archive()
        self.upload_to_s3()

    def to_dict(self):
        return {
                    'bucket_name': self._bucket_name,
                    'id': self._id,
                    'repo_owner': self._repo_owner,
                    'repo_name': self._repo_name,
                    'sha': self._sha,
                    'token': self._token
                }

    def unzip(self):
        with ZipFile(self.download_path) as src_zip:
            zip_info = src_zip.infolist()
            # check to see if the zipball has a dir at the root as it would
            # from Github, or if files are at the root as it would after it's
            # been repacked or downloaded from S3.
            first_file_in_zip = zip_info[0].filename
            if first_file_in_zip.endswith('/'):
                unzip_root = self._work_path
                self.unzip_dir = self._work_path + '/' + first_file_in_zip
            else:
                unzip_root= (
                    self._work_path + '/' + 'thebestest-' + self._id + '/'
                )
                self.unzip_dir = unzip_root
                try:
                    os.mkdir(unzip_root)
                except FileExistsError:
                    logging.debug("{} exists".format(unzip_root))
            logger.debug("unzip_dir set to {}".format(self.unzip_dir))
            logger.info("unzipping {} to {}".format(self.download_path,
                                                    unzip_root))
            src_zip.extractall(path=unzip_root)
            logger.debug(os.listdir(unzip_root))

    @property
    def unzip_dir(self):
        return self._unzip_dir

    @unzip_dir.setter
    def unzip_dir(self, path):
        self._unzip_dir = path

    def upload_to_s3(self):
        s3 = boto3.client('s3')
        logger.info("Uploading {} to s3://{}/{}".format(
            self._zipball_path, self._bucket_name, self._s3_path))
        with open(self._zipball_path, 'rb') as zipball:
            response = s3.put_object(Bucket=self._bucket_name,
                                     Key=self._s3_path,
                                     Body=zipball)
        version_id = response['VersionId']
        logger.info("Upload has Version ID {}".format(version_id))
        logger.info("Removing {}".format(self.download_path))
        os.remove(self.download_path)
        logger.info("Removing {}".format(self._zipball_path))
        os.remove(self._zipball_path)
        return version_id

    def zip(self):
        logger.info("zipping {} into {}".format(self.unzip_dir,
                                                self._zipball_path))
        with ZipFile(self._zipball_path, mode='w',
                     compression=ZIP_DEFLATED) as dest_zip:
            for root, dirs, files in os.walk(self.unzip_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    arc_path = src_path.replace(self.unzip_dir, '')
                    logger.debug(
                        "zipping file {} to {}:{}".format(
                            src_path, self._zipball_path, arc_path
                        )
                    )
                    dest_zip.write(src_path, arcname=arc_path)
            logger.debug(dest_zip.infolist())

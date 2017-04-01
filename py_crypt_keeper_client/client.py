#   Copyright 2017 Maurice Carey
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

import requests
from requests_toolbelt.streaming_iterator import StreamingIterator
import json
from os import getcwd, stat
from os.path import getsize, join, basename
from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN
from .cipher import Cipher, AES_CBC
from .utility import EncryptingFileIterator

DEFAULT_ENCRYPTION_TYPE = AES_CBC

log = getLogger(__name__)

URL_V1 = '{base_url}/api/v1/secure_document_service'

class CryptKeeperClient(object):
    def __init__(self, url, user, api_key):
        self.url = URL_V1.format(base_url=url)
        self.user = user
        self.api_key = api_key
        if not all([url, user, api_key]):
            raise ValueError('Must initialize url, user, and api_key. (%s, %s, %s)' % (url, user, api_key))

    def get_upload_url(self, document_metadata):
        log.debug('***Entering CryptKeeperClient.get_upload_url({document_metadata})'.format(
            document_metadata=document_metadata))
        data = {
            'document_metadata': document_metadata,
        }
        try:
            url = '%s/upload_url/' % self.url
            response = requests.post(
                url=url,
                headers={
                    'Accept': 'application/json',
                    'Authorization': 'ApiKey %s:%s' % (self.user, self.api_key),
                    'Content-Type': 'application/json; charset=utf-8',
                },
                data=json.dumps(data)
            )
            log.debug('Crypt-Keeper upload Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            log.debug('Crypt-Keeper upload Response HTTP Response Body: {content}'.format(
                content=response.content))
            if response.status_code == 201:
                return json.loads(response.content.decode('utf-8'))
        except requests.exceptions.RequestException as e:
            log.exception('Crypt-Keeper HTTP upload Request failed: %s', e)
        return None

    def get_download_url(self, document_id):
        log.debug('***Entering CryptKeeperClient.get_download_url({document_id})'.format(document_id=document_id))
        try:
            url = '%s/download_url/%s/' % (self.url, document_id)
            log.debug('Trying URL: %s', url)
            response = requests.get(
                url=url,
                headers={
                    'Accept': 'application/json',
                    'Authorization': 'ApiKey %s:%s' % (self.user, self.api_key),
                },
            )
            log.debug('Crypt-Keeper Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            log.debug('Crypt-Keeper Response HTTP Response Body: {content}'.format(
                content=response.content))
            if response.status_code == 200:
                return json.loads(response.content.decode('utf-8'))
        except requests.exceptions.RequestException as e:
            log.exception('Crypt-Keeper HTTP Request failed: %s', e)
        return None

    def get_share(self, document_id):
        log.debug('***Entering CryptKeeperClient.get_share({document_id})'.format(document_id=document_id))
        try:
            url = '{base_url}/share/{document_id}/'.format(
                base_url=self.url,
                document_id=document_id
            )
            log.debug('Trying URL: %s', url)
            response = requests.get(
                url=url,
                headers={
                    'Accept': 'application/json',
                    'Authorization': 'ApiKey %s:%s' % (self.user, self.api_key),
                },
            )
            log.debug('Crypt-Keeper get share Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            log.debug('Crypt-Keeper get share Response HTTP Response Body: {content}'.format(
                content=response.content))
            if response.status_code == 200:
                return json.loads(response.content.decode('utf-8'))
        except requests.exceptions.RequestException as e:
            log.exception('Crypt-Keeper get share HTTP Request failed: %s', e)
        return None

    def post_share(self, document_id, username):
        log.debug('***Entering CryptKeeperClient.post_share({document_id}, {username})'.format(
            document_id=document_id,
            username=username,
        ))
        data = {
            'document_id': document_id,
            'username': username,
        }
        try:
            url = '%s/share/' % self.url
            response = requests.post(
                url=url,
                headers={
                    'Accept': 'application/json',
                    'Authorization': 'ApiKey %s:%s' % (self.user, self.api_key),
                    'Content-Type': 'application/json; charset=utf-8',
                },
                data=json.dumps(data)
            )
            log.debug('Crypt-Keeper post share Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            log.debug('Crypt-Keeper post share Response HTTP Response Body: {content}'.format(
                content=response.content))
            if response.status_code == 201:
                return json.loads(response.content.decode('utf-8'))
        except requests.exceptions.RequestException as e:
            log.exception('Crypt-Keeper HTTP post share Request failed: %s', e)
        return None


class EncryptingS3Client(object):
    def __init__(self, encryption_type, key, file_size, block_size=None):
        self.encryption_type = encryption_type
        self.key = key
        self.file_size = file_size
        self.block_size = block_size

    def upload(self, file, url):
        try:
            cipher = Cipher(self.encryption_type, self.key, self.file_size)
            iterator = EncryptingFileIterator(file, cipher)
            streamer = StreamingIterator(cipher.get_encrypted_file_size(), iterator)
            response = requests.put(
                url=url,
                data=streamer,
            )
            log.debug('S3 Upload HTTP Response Body: {content}'.format(
                content=response.content))
            return True
        except requests.exceptions.RequestException as e:
            log.exception('S3 HTTP Request failed: %s', e)
        return False

    def download(self, file, url):
        try:
            byte_generator = self.get_byte_steam_for_url(self.block_size, url)
            cipher = Cipher(self.encryption_type, self.key, self.file_size, byte_generator)
            for b in byte_generator:
                decoded = cipher.decrypt(b)
                file.write(decoded)
            return True
        except requests.exceptions.RequestException as e:
            log.exception('S3 HTTP Request failed: %s', e)
            raise e

    @staticmethod
    def get_byte_steam_for_url(block_size, url):
        response = requests.get(
            url=url,
            headers={
                "Content-Type": "application/octet-stream",
            },
            stream=True
        )
        log.debug('S3 Download Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        byte_generator = response.iter_content(block_size)
        return byte_generator


class SimpleClient(object):
    def __init__(self, crypt_keeper_client, content_type='text/plain'):
        self.crypt_keeper_client = crypt_keeper_client
        self.content_type = content_type

    @classmethod
    def create(cls, url, user, api_key, content_type='text/plain'):
        crypt_keeper_client = CryptKeeperClient(url, user, api_key)
        return cls(crypt_keeper_client, content_type)

    def upload_file(self, filename):
        file_size = getsize(filename)
        document_metadata = {
            'content_length': file_size,
            'content_type': self.content_type,
            'name': basename(filename),
            'compressed': False,
            'encryption_type': DEFAULT_ENCRYPTION_TYPE,
        }
        upload_info = self.crypt_keeper_client.get_upload_url(document_metadata)
        if not upload_info:
            return None
        with open(filename, 'rb') as file:
            key = upload_info.get('symmetric_key')
            encryption_type = document_metadata.get('encryption_type', DEFAULT_ENCRYPTION_TYPE)
            s3_client = EncryptingS3Client(encryption_type, key, file_size)
            url = upload_info.get('single_use_url')
            if s3_client.upload(file, url):
                return upload_info.get('document_id')
        return None

    def download_file(self, document_id, file_name=None, file_path=None):
        download_info = self.crypt_keeper_client.get_download_url(document_id)
        if download_info is None:
            return False
        document_metadata = download_info.get('document_metadata', {})
        encryption_type = document_metadata.get('encryption_type', DEFAULT_ENCRYPTION_TYPE)
        key = download_info.get('symmetric_key')
        file_size = int(document_metadata.get('content_length'))
        filename = self.generate_file_name(document_id, document_metadata, file_name, file_path)
        block_size = Cipher.get_block_size(encryption_type)
        url = download_info.get('single_use_url')
        s3_client = EncryptingS3Client(encryption_type, key, file_size, block_size)
        with open(filename, 'wb') as file:
            s3_client.download(file, url)
            file.flush()
            file.close()
        return True

    def get_share(self, document_id):
        users = []
        share_info = self.crypt_keeper_client.get_share(document_id)
        if share_info is not None:
            users = share_info.get('users', []) or []
        return users

    def post_share(self, document_id, username):
        share_info = self.crypt_keeper_client.post_share(document_id, username)
        if share_info is None:
            return False
        return share_info.get('resource_uri')

    @staticmethod
    def generate_file_name(document_id, document_metadata, file_name, file_path):
        path = getcwd() if file_path is None else file_path
        filename = join(path, document_metadata.get('name', document_id) if file_name is None else file_name)
        return filename

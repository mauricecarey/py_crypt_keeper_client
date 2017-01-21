import requests
from requests_toolbelt.streaming_iterator import StreamingIterator
import json
from os import getcwd, stat
from os.path import getsize, join, basename
from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN
from .cipher import Cipher, AES_CBC

DEFAULT_ENCRYPTION_TYPE = AES_CBC

log = getLogger(__name__)
log.setLevel(WARN)


class FileIterator(object):
    def __init__(self, file):
        self.file = file

    def __iter__(self):
        return self

    def __next__(self):
        byte = self.file.read(1)
        if not byte:
            raise StopIteration
        else:
            return byte


class EncryptingFileIterator(object):
    def __init__(self, file, cipher):
        self.file = file
        self.cipher = cipher
        self.block_size = cipher.block_size
        self.iv = cipher.get_iv()
        self.first = True

    def __iter__(self):
        return self

    def __next__(self):
        if self.first:
            self.first = False
            return self.iv
        read = self.file.read(self.block_size)
        if not read:
            raise StopIteration
        else:
            return self.cipher.encrypt(read)


class CryptKeeperClient(object):
    user = None
    api_key = None
    url = None
    content_type = None

    def __init__(self, url, user, api_key, content_type='text/plain'):
        self.url = url
        self.user = user
        self.api_key = api_key
        self.content_type = content_type
        if not all([url, user, api_key]):
            raise ValueError('Must initialize url, user, and api_key. (%s, %s, %s)' % (url, user, api_key))

    def get_upload_url(self, document_metadata):
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
            log.debug('Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            log.debug('Response HTTP Response Body: {content}'.format(
                content=response.content))
            if response.status_code == 201:
                return json.loads(response.content.decode('utf-8'))
        except requests.exceptions.RequestException as e:
            log.exception('HTTP Request failed!', e)
        return None

    def get_download_url(self, document_id):
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
            log.debug('Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            log.debug('Response HTTP Response Body: {content}'.format(
                content=response.content))
            if response.status_code == 200:
                return json.loads(response.content.decode('utf-8'))
        except requests.exceptions.RequestException as e:
            log.exception('HTTP Request failed!', e)
        return None

    def upload_file(self, filename):
        file_size = getsize(filename)
        document_metadata = {
            'content_length': file_size,
            'content_type': self.content_type,
            'uri': "http://www.mauricecarey.com/",
            'name': basename(filename),
            'compressed': False,
            'encryption_type': DEFAULT_ENCRYPTION_TYPE,
        }
        upload_info = self.get_upload_url(document_metadata)
        if not upload_info:
            return None
        try:
            with open(filename, 'rb') as file:
                key = upload_info.get('symmetric_key')
                encryption_type = document_metadata.get('encryption_type', DEFAULT_ENCRYPTION_TYPE)
                cipher = Cipher(encryption_type, key, file_size)
                iterator = EncryptingFileIterator(file, cipher)
                streamer = StreamingIterator(cipher.get_encrypted_file_size(), iterator)
                response = requests.put(
                    url=upload_info.get('single_use_url'),
                    data=streamer,
                )
                log.debug('Response HTTP Response Body: {content}'.format(
                    content=response.content))
                return upload_info.get('document_id')
        except requests.exceptions.RequestException as e:
            log.exception('HTTP Request failed!', e)
        return None

    def download_file(self, document_id, file_name=None, file_path=None):
        download_info = self.get_download_url(document_id)
        document_metadata = download_info.get('document_metadata', {})
        path = getcwd() if file_path is None else file_path
        filename = join(path, document_metadata.get('name', document_id)) if file_name is None else file_name
        encryption_type = document_metadata.get('encryption_type', DEFAULT_ENCRYPTION_TYPE)
        try:
            response = requests.get(
                url=download_info.get('single_use_url'),
                headers={
                    "Content-Type": "application/octet-stream",
                },
                stream=True
            )
            log.debug('Response HTTP Status Code: {status_code}'.format(
                status_code=response.status_code))
            block_size = Cipher.get_block_size(encryption_type)
            byte_generator = response.iter_content(block_size)
            key = download_info.get('symmetric_key')
            file_size = int(document_metadata.get('content_length'))
            cipher = Cipher(encryption_type, key, file_size, byte_generator)
            with open(filename, 'wb') as file:
                for b in byte_generator:
                    decoded = cipher.decrypt(b)
                    file.write(decoded)
                file.flush()
                file.close()
        except requests.exceptions.RequestException as e:
            log.exception('HTTP Request failed', e)
            raise e
        return True

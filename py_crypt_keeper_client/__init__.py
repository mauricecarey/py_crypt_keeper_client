import requests
from requests_toolbelt.streaming_iterator import StreamingIterator
import json
from os import getcwd, stat
from os.path import getsize, join, basename
from Crypto.Cipher import AES
from Crypto import Random
from base64 import b64encode, b64decode
from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN


__console_handler = StreamHandler()
__console_handler.setLevel(WARN)

__formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
__console_handler.setFormatter(__formatter)

log = getLogger()
log.addHandler(__console_handler)

log = getLogger(__name__)
log.setLevel(WARN)


def decode_key(key_text):
    return b64decode(key_text.encode('utf-8'))


def calculate_encrypted_file_size(file_size, block_size):
    # we have 1 block for the iv plus number of whole blocks in file.
    base_multiplier = 1 + int(file_size/block_size)
    # plus another block for any partial block in the file.
    if file_size % block_size > 0:
        base_multiplier += 1
    return block_size * base_multiplier


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


class Cipher(object):
    __block_sizes__ = {
        'AES': AES.block_size
    }

    def __init__(self, cipher_type, key, file_size=None, iv_generator=None):
        self.key = decode_key(key)
        self.cipher_type = cipher_type
        self.file_size = file_size
        self.block_size = Cipher.get_block_size(self.cipher_type)
        if self.file_size:
            self.last_block_size = self.file_size % self.block_size
            self.number_of_blocks_remaining = int(self.file_size/self.block_size)
        if iv_generator:
            self.iv = next(iv_generator)
        else:
            self.iv = self.generate_iv()
        self.cipher = self.get_cipher()

    @staticmethod
    def get_block_size(cipher_type):
        return Cipher.__block_sizes__.get(cipher_type)

    def generate_iv(self):
        return Random.new().read(self.get_block_size(self.cipher_type))

    def get_cipher(self):
        cipher = {
            'AES': AES.new(self.key, AES.MODE_CBC, self.iv)
        }
        return cipher.get(self.cipher_type)

    def get_iv(self):
        return self.iv

    def get_encrypted_file_size(self):
        return calculate_encrypted_file_size(self.file_size, self.block_size)

    def decrypt(self, cipher_text):
        plain_text = self.cipher.decrypt(cipher_text)
        if self.file_size:
            if self.number_of_blocks_remaining == 0:
                return plain_text[:self.last_block_size]
            self.number_of_blocks_remaining -= 1
        return plain_text

    def encrypt(self, b):
        if len(b) < self.block_size:
            b = b.ljust(self.block_size)
        return self.cipher.encrypt(b)


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

    def get_cipher(self, key, iv):
        return AES.new(key, AES.MODE_CBC, iv)

    def get_block_size(self):
        return AES.block_size

    def generate_iv(self):
        return Random.new().read(self.get_block_size())

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
            'compressed': False
        }
        upload_info = self.get_upload_url(document_metadata)
        if not upload_info:
            return None
        try:
            with open(filename, 'r') as file:
                key = upload_info.get('symmetric_key')
                cipher = Cipher('AES', key, file_size)
                iterator = EncryptingFileIterator(file, cipher)
                streamer = StreamingIterator(cipher.get_encrypted_file_size(), iterator)
                response = requests.put(
                    url=upload_info.get('single_use_url'),
                    data=streamer,
                )
                log.debug('Response HTTP Response Body: {content}'.format(
                    content=response.content))
                return response
        except requests.exceptions.RequestException as e:
            log.exception('HTTP Request failed!', e)
        return None

    def download_file(self, document_id):
        download_info = self.get_download_url(document_id)
        document_metadata = download_info.get('document_metadata', {})
        filename = join(getcwd(), document_metadata.get('name', document_id))
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
            block_size = Cipher.get_block_size('AES')
            byte_generator = response.iter_content(block_size)
            key = download_info.get('symmetric_key')
            file_size = int(document_metadata.get('content_length'))
            cipher = Cipher('AES', key, file_size, byte_generator)
            with open(filename, 'wb') as file:
                for b in byte_generator:
                    decoded = cipher.decrypt(b)
                    file.write(decoded)
                file.flush()
                file.close()
        except requests.exceptions.RequestException as e:
            log.exception('HTTP Request failed', e)

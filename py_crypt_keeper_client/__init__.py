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
    def __init__(self, file, cipher, iv, block_size=16):
        self.file = file
        self.cipher = cipher
        self.block_size = block_size
        self.iv = iv
        self.first = True

    def __iter__(self):
        return self

    def __next__(self):
        if self.first:
            self.first = False
            print('Returning iv: %s' % self.iv)
            return self.iv
        read = self.file.read(self.block_size)
        print('Read %s bytes: %s' % (len(read), read))
        if not read:
            raise StopIteration
        else:
            if len(read) < self.block_size:
                read = read.ljust(self.block_size)
                print('Padding read %s bytes: %s' % (len(read), read))
            cipher_text = self.cipher.encrypt(read)
            print('Cipher text: %s' % cipher_text)
            return cipher_text


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
                key = decode_key(key)
                iv = self.generate_iv()
                cipher = self.get_cipher(key, iv)
                iterator = EncryptingFileIterator(file, cipher, iv)
                encrypted_file_size = calculate_encrypted_file_size(file_size, self.get_block_size())
                streamer = StreamingIterator(encrypted_file_size, iterator)
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
            byte_generator = response.iter_content(self.get_block_size())
            iv = next(byte_generator)
            key = download_info.get('symmetric_key')
            key = decode_key(key)
            cipher = self.get_cipher(key, iv)
            content_length = int(document_metadata.get('content_length',
                                 response.headers['content-length'] - self.get_block_size()))
            original_content_blocks = int(content_length/self.get_block_size())
            partial_block_size = content_length - self.get_block_size() * original_content_blocks
            with open(filename, 'wb') as file:
                for b in byte_generator:
                    decoded = cipher.decrypt(b)
                    if original_content_blocks > 0:
                        file.write(decoded)
                    else:
                        file.write(decoded[:partial_block_size])
                    original_content_blocks -= 1
                file.flush()
                file.close()
        except requests.exceptions.RequestException as e:
            log.exception('HTTP Request failed', e)

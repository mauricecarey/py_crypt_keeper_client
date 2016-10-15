import requests
from requests_toolbelt.streaming_iterator import StreamingIterator
import json
from os import getcwd, stat
from os.path import getsize, join, basename
from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN


__console_handler = StreamHandler()
__console_handler.setLevel(WARN)

__formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
__console_handler.setFormatter(__formatter)

log = getLogger()
log.addHandler(__console_handler)

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
            'compressed': False
        }
        upload_info = self.get_upload_url(document_metadata)
        if not upload_info:
            return None
        try:
            with open(filename, 'r') as file:
                streamer = StreamingIterator(file_size, FileIterator(file))
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
        # http://docs.python-requests.org/en/master/api/#requests.Response.iter_content
        # use requests.get with stream=True to get chunk-encoded responses.
        pass

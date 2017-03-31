from unittest import TestCase, mock
from py_crypt_keeper_client.client import CryptKeeperClient, SimpleClient, EncryptingS3Client
from py_crypt_keeper_client.cipher import Cipher, AES_CBC
from py_crypt_keeper_client.utility import encode_key
from collections import namedtuple
import json
import requests
from os import getcwd
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from base64 import b64encode

KEY_SIZE = AES.key_size[0]

API_KEY = 'test'
USER = 'cryptkeeper-user'
URL = 'http://test'
EXPECTED_URL = 'http://test/api/v1/secure_document_service'


class BaseClientTest(TestCase):
    Response = namedtuple('Response', ['content', 'status_code'])
    upload_response = Response(
        content=b'{"document_id": "a5689603-9570-4af5-9b95-5fbcdcde4201", "document_metadata": {"compressed": false, "content_length": 1304, "content_type": "text/plain", "encryption_type": "AES|CBC", "name": "test_upload.txt", "uri": "http://www.mauricecarey.com/"}, "resource_uri": "/api/v1/document_service/upload_url/a5689603-9570-4af5-9b95-5fbcdcde4201/", "single_use_url": "https://s3.amazonaws.com/akiaih2mae6qzuluramq-crypt-keeper/a5689603-9570-4af5-9b95-5fbcdcde4201?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIH2MAE6QZULURAMQ%2F20170201%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-SignedHeaders=host&X-Amz-Expires=600&X-Amz-Date=20170201T200757Z&X-Amz-Signature=d5028cd4762ad097e3b11462585480694d92c983eafb1d890328aee07cdda860", "symmetric_key": "HG8KLpzDkhrFS5Thl9spbLs3A79TcVwL0hk4/HaddqI="}',
        status_code=201
    )
    download_response = Response(
        content=b'{"document_id": "a5689603-9570-4af5-9b95-5fbcdcde4201", "document_metadata": {"compressed": false, "content_length": "1304", "content_type": "text/plain", "name": "test_upload.txt", "uri": "http://www.mauricecarey.com/"}, "resource_uri": "/api/v1/document_service/download_url/a5689603-9570-4af5-9b95-5fbcdcde4201/", "single_use_url": "https://s3.amazonaws.com/akiaih2mae6qzuluramq-crypt-keeper/a5689603-9570-4af5-9b95-5fbcdcde4201?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIH2MAE6QZULURAMQ%2F20170201%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-SignedHeaders=host&X-Amz-Expires=600&X-Amz-Date=20170201T200828Z&X-Amz-Signature=3f21c75891dd628de421bb02bd78622e31287467ec4c2ab6fd81c7c47fa69e63", "symmetric_key": "HG8KLpzDkhrFS5Thl9spbLs3A79TcVwL0hk4/HaddqI="}',
        status_code=200
    )
    get_share_response = Response(
        content=b'{"document_id": "a5689603-9570-4af5-9b95-5fbcdcde4201", "users": ["cryptkeeper-user", "other-user"], "resource_uri": "/api/v1/document_service/share/a5689603-9570-4af5-9b95-5fbcdcde4201/"}',
        status_code=200
    )
    post_share_response = Response(
        content=b'{"document_id": "a5689603-9570-4af5-9b95-5fbcdcde4201", "username": "cryptkeeper-user", "resource_uri": "/api/v1/document_service/share/a5689603-9570-4af5-9b95-5fbcdcde4201/"}',
        status_code=201
    )
    document_id = 'a5689603-9570-4af5-9b95-5fbcdcde4201'


class TestCryptKeeperClient(BaseClientTest):
    def test_init(self):
        fail = False
        try:
            CryptKeeperClient(URL, USER, None)
        except ValueError:
            fail = True
        self.assertTrue(fail)
        fail = False
        try:
            CryptKeeperClient(URL, None, API_KEY)
        except ValueError:
            fail = True
        self.assertTrue(fail)
        fail = False
        try:
            CryptKeeperClient(None, USER, API_KEY)
        except ValueError:
            fail = True
        self.assertTrue(fail)

    @mock.patch('requests.post')
    def test_get_upload_url(self, post_mock):
        post_mock.return_value = self.upload_response
        client = CryptKeeperClient(URL, USER, API_KEY)
        headers = {
            'Accept': 'application/json',
            'Authorization': 'ApiKey %s:%s' % (USER, API_KEY),
            'Content-Type': 'application/json; charset=utf-8',
        }
        metadata = {'tst': 'tst'}
        response = client.get_upload_url(metadata)
        self.assertIsNotNone(response)
        post_mock.assert_called_with(
            url='%s/upload_url/' % EXPECTED_URL,
            headers=headers,
            data=json.dumps({'document_metadata': metadata})
        )

    @mock.patch('requests.post')
    def test_get_upload_url_error(self, post_mock):
        post_mock.side_effect = requests.exceptions.RequestException('ERROR')
        client = CryptKeeperClient(URL, USER, API_KEY)
        metadata = {'tst': 'tst'}
        response = client.get_upload_url(metadata)
        self.assertIsNone(response)

    @mock.patch('requests.get')
    def test_get_download_url(self, get_mock):
        get_mock.return_value = self.download_response
        client = CryptKeeperClient(URL, USER, API_KEY)
        headers = {
            'Accept': 'application/json',
            'Authorization': 'ApiKey %s:%s' % (USER, API_KEY),
        }
        response = client.get_download_url(self.document_id)
        self.assertIsNotNone(response)
        get_mock.assert_called_with(
            url='%s/download_url/%s/' % (EXPECTED_URL, self.document_id),
            headers=headers,
        )

    @mock.patch('requests.get')
    def test_get_download_url_error(self, get_mock):
        get_mock.side_effect = requests.exceptions.RequestException('ERROR')
        client = CryptKeeperClient(URL, USER, API_KEY)
        response = client.get_download_url(self.document_id)
        self.assertIsNone(response)

    @mock.patch('requests.get')
    def test_get_share(self, get_mock):
        get_mock.return_value = self.get_share_response
        client = CryptKeeperClient(URL, USER, API_KEY)
        headers = {
            'Accept': 'application/json',
            'Authorization': 'ApiKey %s:%s' % (USER, API_KEY),
        }
        response = client.get_share(self.document_id)
        self.assertIsNotNone(response)
        get_mock.assert_called_with(
            url='%s/share/%s/' % (EXPECTED_URL, self.document_id),
            headers=headers,
        )

    @mock.patch('requests.post')
    def test_post_share(self, post_mock):
        post_mock.return_value = self.post_share_response
        client = CryptKeeperClient(URL, USER, API_KEY)
        headers = {
            'Accept': 'application/json',
            'Authorization': 'ApiKey %s:%s' % (USER, API_KEY),
            'Content-Type': 'application/json; charset=utf-8',
        }
        response = client.post_share(self.document_id, USER)
        self.assertIsNotNone(response)
        post_mock.assert_called_with(
            url='%s/share/' % EXPECTED_URL,
            headers=headers,
            data=json.dumps({
                'document_id': self.document_id,
                'username': USER,
            })
        )


class TestEncryptingS3Client(BaseClientTest):
    def setUp(self):
        key = SHA256.new('test'.encode()).digest()[:KEY_SIZE]
        self.key = b64encode(key).decode('utf-8', 'backslashreplace')

    @mock.patch('requests.put')
    def test_upload_error_put(self, put_mock):
        put_mock.side_effect = requests.exceptions.RequestException('ERROR')
        client = EncryptingS3Client('AES|CBC', self.key, 1)
        file = mock.MagicMock()
        url = 'test_url'
        result = client.upload(file, url)
        self.assertFalse(result)

    @mock.patch('requests.put')
    def test_upload(self, put_mock):
        put_mock.return_value = self.upload_response
        client = EncryptingS3Client('AES|CBC', self.key, 1)
        file = mock.MagicMock()
        file.read.return_value = 'a'
        url = 'test_url'
        result = client.upload(file, url)
        self.assertTrue(result)


class TestSimpleClient(BaseClientTest):
    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_upload_url')
    def test_upload_file_error_upload_info(self, get_upload_url_mock):
        get_upload_url_mock.return_value = None
        client = SimpleClient.create(URL, USER, API_KEY)
        document_id = client.upload_file(__file__)
        self.assertIsNone(document_id)

    @mock.patch('py_crypt_keeper_client.client.EncryptingS3Client.upload')
    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_upload_url')
    def test_upload_file_error_put(self, get_upload_url_mock, s3_client_upload_mock):
        get_upload_url_mock.return_value = json.loads(self.upload_response.content.decode('utf-8'))
        s3_client_upload_mock.return_value = False
        client = SimpleClient.create(URL, USER, API_KEY)
        document_id = client.upload_file(__file__)
        self.assertIsNone(document_id)

    @mock.patch('py_crypt_keeper_client.client.EncryptingS3Client.upload')
    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_upload_url')
    def test_upload_file(self, get_upload_url_mock, s3_client_upload_mock):
        get_upload_url_mock.return_value = json.loads(self.upload_response.content.decode('utf-8'))
        s3_client_upload_mock.return_value = True
        client = SimpleClient.create(URL, USER, API_KEY)
        document_id = client.upload_file(__file__)
        self.assertIsNotNone(document_id)
        self.assertEqual(document_id, self.document_id)

    @mock.patch('py_crypt_keeper_client.client.EncryptingS3Client.download')
    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_download_url')
    def test_download_file(self, get_download_url_mock, s3_client_mock):
        get_download_url_mock.return_value = json.loads(self.download_response.content.decode('utf-8'))
        s3_client_mock.return_value = True
        client = SimpleClient.create(URL, USER, API_KEY)
        result = client.download_file(self.document_id)
        self.assertTrue(result)

    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_share')
    def test_get_share(self, get_share_mock):
        get_share_mock.return_value = json.loads(self.get_share_response.content.decode('utf-8'))
        client = SimpleClient.create(URL, USER, API_KEY)
        result = client.get_share(self.document_id)
        self.assertIsNotNone(result)
        self.assertIn(USER, result)

    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_share')
    def test_get_share_share_is_none(self, get_share_mock):
        get_share_mock.return_value = None
        client = SimpleClient.create(URL, USER, API_KEY)
        result = client.get_share(self.document_id)
        self.assertIsNotNone(result)
        self.assertEqual([], result)

    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_share')
    def test_get_share_share_is_empty(self, get_share_mock):
        get_share_mock.return_value = {}
        client = SimpleClient.create(URL, USER, API_KEY)
        result = client.get_share(self.document_id)
        self.assertIsNotNone(result)
        self.assertEqual([], result)

    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_share')
    def test_get_share_users_is_none(self, get_share_mock):
        get_share_mock.return_value = json.loads(self.get_share_response.content.decode('utf-8'))
        get_share_mock.return_value['users'] = None
        client = SimpleClient.create(URL, USER, API_KEY)
        result = client.get_share(self.document_id)
        self.assertIsNotNone(result)
        self.assertEqual([], result)

    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.get_share')
    def test_get_share_users_is_empty(self, get_share_mock):
        get_share_mock.return_value = json.loads(self.get_share_response.content.decode('utf-8'))
        get_share_mock.return_value['users'] = []
        client = SimpleClient.create(URL, USER, API_KEY)
        result = client.get_share(self.document_id)
        self.assertIsNotNone(result)
        self.assertEqual([], result)

    @mock.patch('py_crypt_keeper_client.client.CryptKeeperClient.post_share')
    def test_post_share(self, post_share_mock):
        post_share_mock.return_value = json.loads(self.post_share_response.content.decode('utf-8'))
        client = SimpleClient.create(URL, USER, API_KEY)
        result = client.post_share(self.document_id, USER)
        self.assertIsNotNone(result)
        self.assertEqual(result, '/api/v1/document_service/share/a5689603-9570-4af5-9b95-5fbcdcde4201/')

    def test_generate_file_name(self):
        tests = [
            {
                'document_id': 'test_id',
                'document_metadata': {},
                'file_name': 'testfile.txt',
                'file_path': 'path',
                'expected': 'path/testfile.txt'
            },
            {
                'document_id': 'test_id',
                'document_metadata': {},
                'file_name': None,
                'file_path': 'path',
                'expected': 'path/test_id'
            },
            {
                'document_id': 'test_id',
                'document_metadata': {'name': 'metadata_filename'},
                'file_name': None,
                'file_path': 'path',
                'expected': 'path/metadata_filename'
            },
            {
                'document_id': 'test_id',
                'document_metadata': {'name': 'metadata_filename'},
                'file_name': None,
                'file_path': None,
                'expected': '%s/metadata_filename' % getcwd()
            },
        ]
        for test in tests:
            with self.subTest(test=test):
                document_id = test.get('document_id')
                document_metadata = test.get('document_metadata')
                file_name = test.get('file_name')
                file_path = test.get('file_path')
                filename = SimpleClient.generate_file_name(document_id, document_metadata, file_name, file_path)
                self.assertEqual(filename, test.get('expected'))

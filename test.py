import py_crypt_keeper_client
from os import getcwd, stat, remove, urandom
from os.path import getsize, join, basename, exists
import filecmp
from unittest import TestCase, main
import requests

'''
The server must be running for these tests to succeed. Configure as follows or change the API_KEY, USER, and
DOCUMENT_SERVICE URL to reflect your configuration.

1. Run the following to install a local server, be sure to set USER to the username created by the createsuperuser command:
    git clone git@bitbucket.org:prometheussoftware/crypt-keeper.git
    cd crypt-keeper
    cd crypt-keeper-django
    virtualenv -p `which python3` env
    source env/bin/activate
    pip install -r requirements.txt
    cd crypt_keeper_server
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py initial_setup 'aws_access_key' --aws_secret_key key
    python manage.py runserver
2. Next login to the server at http://localhost:8000/admin using the user created above.
3. Setup the user by adding an api key, this should match API_KEY below
'''

API_KEY = 'test'
USER = 'cryptkeeper-user'
DOCUMENT_SERVICE = 'http://localhost:8000/api/v1/document_service'

UPLOAD_FILENAME = 'test_upload.txt'
DOWNLOAD_FILENAME = 'test_download.txt'


class CryptKeeperClientIntegrationTest(TestCase):
    def setUp(self):
        self.url = DOCUMENT_SERVICE
        self.test_input_filename = join(getcwd(), UPLOAD_FILENAME)
        self.test_output_filename = join(getcwd(), DOWNLOAD_FILENAME)

    def tearDown(self):
        # remove test files
        if exists(self.test_input_filename):
            remove(self.test_input_filename)
        if exists(self.test_output_filename):
            remove(self.test_output_filename)

    def download(self, document_id):
        return self.client.download_file(document_id, file_name=DOWNLOAD_FILENAME)

    def upload(self):
        return self.client.upload_file(self.test_input_filename)

    def test_file_upload_and_download(self):
        self.assertIsNotNone(self.url)
        # check that url is valid.
        try:
            request = requests.get(self.url)
        except:
            request = None
        self.assertIsNotNone(request)
        self.assertTrue(request.status_code == 200 or request.status_code == 404)
        # create client
        crypt_keeper_client = py_crypt_keeper_client.CryptKeeperClient(self.url, USER, API_KEY)
        self.client = py_crypt_keeper_client.SimpleClient(crypt_keeper_client)
        self.assertIsNotNone(self.client)
        # create random file
        with open(self.test_input_filename, 'wb') as file:
            file.write(urandom(1304))
        # upload the file
        doc_id = self.upload()
        self.assertIsNotNone(doc_id)
        # download the file
        self.assertTrue(self.download(doc_id))
        # check files are the same
        self.assertTrue(filecmp.cmp(UPLOAD_FILENAME, DOWNLOAD_FILENAME))


if __name__ == '__main__':
    main()

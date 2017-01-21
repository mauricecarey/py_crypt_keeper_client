import py_crypt_keeper_client
from os import getcwd, stat
from os.path import getsize, join, basename
import filecmp


def download(document_id='2183250d-a857-49e3-bb28-6273606edc46'):
    url = 'http://localhost:8000/api/v1/document_service'
    client = py_crypt_keeper_client.CryptKeeperClient(url, 'maurice', 'test')
    r = client.download_file(document_id, file_name='test_download.txt')
    print(r)


def upload():
    filename = join(getcwd(), 'test.txt')
    print(filename)
    url = 'http://localhost:8000/api/v1/document_service'
    client = py_crypt_keeper_client.CryptKeeperClient(url, 'maurice', 'test')
    r = client.upload_file(filename)
    print(r)
    return r


def main():
    r = upload()
    if r is None:
        download()
    else:
        download(document_id=r)
    e = filecmp.cmp('test.txt', 'test_download.txt')
    print(e)

if __name__ == '__main__':
    main()

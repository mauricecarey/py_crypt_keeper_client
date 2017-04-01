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

from unittest import TestCase, mock
from base64 import b64encode
from py_crypt_keeper_client.utility import (
    calculate_encrypted_file_size,
    decode_key,
    encode_key,
    EncryptingFileIterator,
    FileIterator,
)
from py_crypt_keeper_client.cipher import Cipher, AES_CBC


class UtilityTest(TestCase):

    def setUp(self):
        self.file_sizes = [(16, 32), (32, 48), (31, 48), (15, 32), (27, 48), (62, 80)]
        self.block_size = 16
        self.bytes = b'test'
        self.key_text = b64encode(self.bytes).decode()

    def test_calculate_encrypted_file_size(self):
        for file_size, encrypted_size in self.file_sizes:
            with self.subTest(file_size=file_size, encrypted_size=encrypted_size):
                self.assertEqual(calculate_encrypted_file_size(file_size, self.block_size), encrypted_size)

    def test_decode_key(self):
        self.assertEqual(decode_key(self.key_text), self.bytes)


class TestFileIterator(TestCase):
    def setUp(self):
        pass

    def test_read_file(self):
        file = mock.MagicMock()
        file.read = mock.MagicMock(side_effect=['test', None])
        fi = FileIterator(file)
        out = []
        for v in fi:
            out.append(v)
        self.assertTrue(len(out) == 1)
        self.assertIs(out[0], 'test')


class TestEncryptingFileIterator(TestCase):
    def setUp(self):
        pass

    def test_read_file(self):
        key = encode_key(b'keykeykeykeykeyk')
        cipher = Cipher(AES_CBC, key)
        cipher.get_iv = mock.MagicMock(return_value='iv')
        values = {'test': 'cipher'}
        cipher.encrypt = mock.MagicMock(side_effect=lambda x: values[x])
        file = mock.MagicMock()
        file.read = mock.MagicMock(side_effect=['test', None])
        efi = EncryptingFileIterator(file, cipher)
        out = []
        for v in efi:
            out.append(v)
        self.assertTrue(len(out) == 2)
        self.assertIs(out[0], 'iv')
        self.assertIs(out[1], 'cipher')


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
from py_crypt_keeper_client.cipher import Cipher, AES_CBC
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from base64 import b64encode

KEY_SIZE = AES.key_size[0]
AES_BLOCK_SIZE = AES.block_size


class CipherTest(TestCase):
    def setUp(self):
        key = SHA256.new('test'.encode()).digest()[:KEY_SIZE]
        self.key = b64encode(key).decode('utf-8', 'backslashreplace')
        self.cipher_type = AES_CBC
        self.create_unit()

    def create_unit(self):
        self.unit = Cipher(self.cipher_type, self.key)

    def test_get_block_size(self):
        self.assertEqual(AES_BLOCK_SIZE, Cipher.get_block_size(AES_CBC))

    def test_generate_iv(self):
        iv = self.unit.generate_iv()
        self.assertIsNotNone(iv)

    def test_get_cipher(self):
        cipher = self.unit.get_cipher()
        self.assertTrue(isinstance(cipher, AES.AESCipher))

    def test_get_iv(self):
        iv = self.unit.get_iv()
        self.assertIsNotNone(iv)

    @mock.patch('Crypto.Cipher.AES.AESCipher.encrypt')
    def test_encrypt(self, mock_cipher_encrypt):
        text = b'test'
        mock_cipher_encrypt.return_value = b'test'
        cipher_text = self.unit.encrypt(text)
        self.assertIsNotNone(cipher_text)

    @mock.patch('Crypto.Cipher.AES.AESCipher.decrypt')
    def test_decrypt(self, mock_cipher_decrypt):
        cipher_text = 'cipher'
        mock_cipher_decrypt.return_value = 'text'
        text = self.unit.decrypt(cipher_text)
        self.assertIsNotNone(text)

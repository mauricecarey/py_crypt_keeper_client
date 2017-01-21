from unittest import TestCase
from base64 import b64encode
from py_crypt_keeper_client.utility import calculate_encrypted_file_size, decode_key


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

from Crypto.Cipher import AES
from Crypto import Random
from logging import getLogger, DEBUG, WARN
from .utility import decode_key, calculate_encrypted_file_size

log = getLogger(__name__)
log.setLevel(WARN)


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

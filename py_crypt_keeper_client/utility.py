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

from base64 import b64decode, b64encode
from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN


log = getLogger(__name__)
log.setLevel(WARN)


def encode_key(key_bytes):
    return b64encode(key_bytes).decode('utf-8', 'backslashreplace')


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



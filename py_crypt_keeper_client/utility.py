from base64 import b64decode
from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN


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

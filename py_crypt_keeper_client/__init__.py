from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN
from .client import CryptKeeperClient, SimpleClient

console_handler = StreamHandler()
console_handler.setLevel(WARN)


__log = getLogger()
__log.addHandler(console_handler)

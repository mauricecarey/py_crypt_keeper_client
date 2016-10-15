from logging import getLogger, StreamHandler, Formatter, DEBUG, WARN
from .client import CryptKeeperClient

__console_handler = StreamHandler()
__console_handler.setLevel(WARN)

__formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
__console_handler.setFormatter(__formatter)

log = getLogger()
log.addHandler(__console_handler)

log = getLogger(__name__)
log.setLevel(WARN)
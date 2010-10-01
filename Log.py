from os import remove
from os.path import isfile
import logging

LOGGING_ENABLED = False

BOT_LOG_FILENAME = 'mybot.log'
GAME_LOG_FILENAME = 'game.log'

if LOGGING_ENABLED:
    if isfile(BOT_LOG_FILENAME):
        remove(BOT_LOG_FILENAME)
    if isfile(GAME_LOG_FILENAME):
        remove(GAME_LOG_FILENAME)
    logging.basicConfig(filename=BOT_LOG_FILENAME,level=logging.DEBUG,format='%(asctime)s %(message)s')
    log = open(GAME_LOG_FILENAME, 'w')

def game_log(message):
    if LOGGING_ENABLED:
        log.write(message)
        log.flush()

def debug(message):
    if LOGGING_ENABLED:
        logging.debug(message)
    

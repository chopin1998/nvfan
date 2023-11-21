#!/usr/bin/python3

import os
import sys
import time
import logging
import logging.handlers

from Xlib.display import Display
from Xlib.ext.nvcontrol import Gpu, Cooler
from lark import logger
from py import log

INTERVAL = 5

logger = logging.getLogger('nvfan')
logger.setLevel(logging.INFO)
# create a rotating file handler

handler = logging.handlers.RotatingFileHandler(
    '/run/shm/nvfan.log', maxBytes=1024, backupCount=1)

handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def daemon():
    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError as error:
        logger.error('fork #1 failed: %d (%s)' % (error.errno, error.strerror))
        sys.exit(1)

    os.chdir('/')
    os.setsid()
    os.umask(0)

    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError as error:
        logger.error('fork #2 failed: %d (%s)' % (error.errno, error.strerror))
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'a+')
    se = open(os.devnull, 'a+')

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    _core()

def _core():
    disp = Display()
    if not disp.has_extension('NV-CONTROL'):
        logger.error('NV-CONTROL extension not found')
        sys.exit(1)
    
    logger.info('NV-CONTROL extension found')
    while True:
        temp = disp.nvcontrol_get_core_temp(Gpu(0))
        curr_fan = disp.nvcontrol_get_fan_duty(Cooler(0))
        
        if temp < 40:
            disp.nvcontrol_set_fan_duty(Cooler(0), 17)
        elif temp < 50:
            disp.nvcontrol_set_fan_duty(Cooler(0), 25)
        elif temp > 70:
            disp.nvcontrol_set_fan_duty(Cooler(0), 40)
        
        logger.info('curr temp: %d, fan: %d' % (temp, curr_fan))
        time.sleep(INTERVAL)

if __name__ == "__main__":
    daemon()
    # _core()
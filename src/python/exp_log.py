#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; -*-
# @(#) exp_log.py  Time-stamp: <Julian Qian 2015-11-27 17:09:08>
# Copyright 2015 Julian Qian
# Author: Julian Qian <junist@gmail.com>
# Version: $Id: exp_log.py,v 0.1 2015-11-27 17:08:44 jqian Exp $
#

import logging

def getLogger(logfile=None, logtostderr=False,
              logname="logagent", loglevel=logging.INFO):
    logger = logging.getLogger(logname)
    logger.setLevel(loglevel)
    formatter = logging.Formatter(
        '%(asctime)s %(name)s [%(levelname)s] '
        '<%(filename)s:%(lineno)d> %(funcName)s: %(message)s')
    if logfile:                 # append to file
        fh = logging.handlers.RotatingFileHandler(logfile,
                                                  maxBytes=20*1024*1024,
                                                  backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    if logtostderr:             # append to sys.stderr
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

logger = getLogger(None, loglevel=logging.INFO, logtostderr=False)

def main():
    pass

if __name__ == "__main__":
    main()

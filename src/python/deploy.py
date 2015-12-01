#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; -*-
# @(#) deploy.py  Time-stamp: <Julian Qian 2015-12-01 18:01:16>
# Copyright 2015 Julian Qian
# Author: Julian Qian <junist@gmail.com>
# Version: $Id: deploy.py,v 0.1 2015-11-10 11:24:01 jqian Exp $
#

'''
1. build previous experiment space from pb
2. read current experiments from db
3. merge them
4. write back to pb
'''

import argparse
import ConfigParser

from exp_deploy import DbConf, ExpDeploy
from exp_db import ExpDb, ExpPb


def main():
    parser = argparse.ArgumentParser(description='generate exp_sys pb file')
    parser.add_argument('--conf', type=str, help='config file')
    parser.add_argument('--input', type=str, help='input file name')
    parser.add_argument('--output', type=str, help='output file name')
    parser.add_argument('--dry', action='store_true', help='whether dry run')
    parser.add_argument('--verbose', action='store_true', help='print verbose log')
    args = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read(args.conf)
    dbconf = DbConf._make([config.get('mysql', 'host'),
                           config.get('mysql', 'port'),
                           config.get('mysql', 'user'),
                           config.get('mysql', 'passwd'),
                           config.get('mysql', 'dbname')])
    db = ExpDb(dbconf)
    pb = ExpPb(args.input)
    ed = ExpDeploy(db, pb)
    data = ed.build()
    with open(args.output, 'w') as fp:
        fp.write(data)


if __name__ == "__main__":
    main()

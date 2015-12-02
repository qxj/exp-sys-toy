#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; -*-
# @(#) exp_db.py  Time-stamp: <Julian Qian 2015-12-02 14:58:36>
# Copyright 2015 Julian Qian
# Author: Julian Qian <junist@gmail.com>
# Version: $Id: exp_db.py,v 0.1 2015-11-27 17:07:33 jqian Exp $
#

import sys
import collections
import experiment_pb2 as expb
import mysql.connector

from exp_log import logger

DbConf = collections.namedtuple('DbConf', 'host,port,user,password,database')

DomainRow = collections.namedtuple('DomainRow', 'id,parent_id,name,buckets_num')
LayerRow = collections.namedtuple('LayerRow', 'id,domain_id,name,launch')
ExpRow = collections.namedtuple('ExpRow', 'id,layer_id,name,diversion,start_time,' +
                                'end_time,conditions,parameters,buckets_num')
ParamRow = collections.namedtuple('ParamRow', 'name,value,type')


class ExpDb(object):
    def __init__(self, dbconf):
        self.cnx = mysql.connector.connect(**dbconf._asdict())

    def get_domains(self):
        sql = '''select id,parent_id,name,buckets_num from domain where enabled=1
            order by id'''
        cur = self.cnx.cursor()
        cur.execute(sql)
        domains = map(DomainRow._make, cur.fetchall())
        return domains

    def get_layers(self):
        sql = '''select id,domain_id,name,launch from layer where enabled=1
            order by id'''
        cur = self.cnx.cursor()
        cur.execute(sql)
        layers = map(LayerRow._make, cur.fetchall())
        return layers

    def get_experiments(self):
        # TODO: treate `PAUSE`` status
        sql = '''select id,layer_id,name,diversion,start_time,end_time,
            conditions,parameters,buckets_num
            from experiment where status in ('published','deploy')
            order by id
        '''
        cur = self.cnx.cursor()
        cur.execute(sql)
        exps = map(ExpRow._make, cur.fetchall())
        return exps

    def get_parameter(self, name):
        sql = '''select name, value, type
        from parameter where name='{}'
        '''.format(name)
        cur = self.cnx.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            return ParamRow._make(row)
        else:
            return None


class ExpPb(object):
    def __init__(self, pbfile):
        self.deploy = expb.Deployment()
        # TODO: error treatment
        data = open(pbfile).read()
        self.deploy.ParseFromString(data)

    def get_experiments(self):
        return self.deploy.experiments

    def write(self, pbdata, pbfile):
        with open(pbfile, 'w') as fp:
            fp.write(pbdata)


def main():
    dbconf = DbConf('localhost', 3306, 'root', 'ppzuche', 'exp_sys')
    ed = ExpDb(dbconf)
    print ed.get_domains()

if __name__ == "__main__":
    main()

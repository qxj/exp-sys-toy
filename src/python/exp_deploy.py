#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; -*-
# @(#) exp_deploy.py  Time-stamp: <Julian Qian 2015-12-18 16:41:32>
# Copyright 2015 Julian Qian
# Author: Julian Qian <junist@gmail.com>
# Version: $Id: exp_deploy.py,v 0.1 2015-11-27 17:05:18 jqian Exp $
#

import json
from exp_defs import *
from exp_log import logger


class ExpDeploy(object):
    def __init__(self, expdb, json=None):
        self.db = expdb
        self.json = json
        #
        self.domains = {}
        self.layers = {}
        self.exps = {}

    def _build_domains(self):
        domains = self.db.get_domains()
        # TODO: polish this stupid bfs method
        # find root domain
        root_domain = None
        for d in domains:
            if d.id == d.parent_id:
                root_domain = Domain.from_num(d.id, 0, d.buckets_num)
                self.domains[d.id] = root_domain
                logger.debug('root domain %d, buckets_num %d',
                             d.id, d.buckets_num)
                break
        # find subdomain
        for d in domains:
            if d.parent_id == root_domain.id and d.id != root_domain.id:
                logger.debug('process subdomain %d, buckets_num %d',
                             d.id, d.buckets_num)
                bucketRanges = root_domain.assign(d.id, d.buckets_num)
                self.domains[d.id] = Domain(d.id, bucketRanges)

    def _build_layers(self):
        layers = self.db.get_layers()
        for l in layers:
            logger.debug('process layer %d in domain %d',
                         l.id, l.domain_id)
            layer = Layer(l.id, self.domains[l.domain_id])
            self.layers[l.id] = layer

    @staticmethod
    def _eq_exp(exp, expRow):
        if exp.id == expRow.id and \
           exp.layer_id == expRow.layer_id and \
           exp.get_buckets_num() == expRow.buckets_num:
            return True
        return False

    def _build_experiments(self):
        # merge with existed experiments
        db_exps = {}
        for e in self.db.get_experiments():
            db_exps[e.id] = e
        json_exps = []
        if self.json:
            for e in self.json.get_experiments():
                json_exps.append(Experiment.from_json(e))
        for e in json_exps:
            layer = self.layers.get(e.layer_id)
            if not layer:
                logger.warn('layer %d is not exists for exp %d',
                             e.layer_id, e.id)
                continue
            if e.id in db_exps and self._eq_exp(e, db_exps[e.id]):
                cnt = layer.load(e.id, e.ranges)
                self.exps[e.id] = e
                del db_exps[e.id]
                logger.info('load existed experiment %d, assigned %d buckets',
                            e.id, cnt)
        for row in db_exps.values():
            exp = Experiment.from_db(row)
            layer = self.layers.get(row.layer_id)
            # TODO catch exception
            bucketRanges = layer.assign(row.id, row.buckets_num)
            exp.set_bucket_ranges(bucketRanges)
            self.exps[row.id] = exp
            logger.info('assign new experiment %d in layer %d',
                        row.id, row.layer_id)

    def build(self):
        self._build_domains()
        self._build_layers()
        self._build_experiments()
        deploy = {}
        # parameters & experiments
        params = {}
        deploy['experiments'] = []
        for e in self.exps.values():
            deploy['experiments'].append(e.to_json())
            for p in e.parameters:
                pp = self.db.get_parameter(p.name)
                param = Parameter(pp.name, pp.value, pp.type)
                params[pp.name] = param
        deploy['parameters'] = []
        for p in params.values():
            deploy['parameters'].append(p.to_json())
        # domains
        deploy['domains'] = []
        for d in self.domains.values():
            deploy['domains'].append(d.to_json())
        # layers
        deploy['layers'] = []
        for l in self.layers.values():
            deploy['layers'].append(l.to_json())
        return json.dumps(deploy)


def main():
    pass

if __name__ == "__main__":
    main()

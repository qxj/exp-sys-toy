#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; -*-
# @(#) exp_deploy.py  Time-stamp: <Julian Qian 2015-12-01 17:50:28>
# Copyright 2015 Julian Qian
# Author: Julian Qian <junist@gmail.com>
# Version: $Id: exp_deploy.py,v 0.1 2015-11-27 17:05:18 jqian Exp $
#

import sys
import experiment_pb2 as expb
from exp_defs import *
from exp_log import logger


def ExpDeploy(object):
    def __init__(self, expdb, pb=None):
        self.db = expdb
        self.pb = pb
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
                root_domain = Domain.from_num(d.id, d.buckets_num)
                self.domains[d.id] = root_domain
                break
        # find subdomain
        for d in domains:
            if d.parent_id == root_domain.id:
                bucketRanges = root_domain.assign(d.id, d.buckets_num)
                self.domains[d.id] = Domain(d.id, bucketRanges)

    def _build_layers(self):
        layers = self.db.get_layers()
        for l in layers:
            layer = Layer(l.id, self.domains[l.domain_id])
            self.layers[l.id] = layer

    def _build_experiments(self):
        # merge with existed experiments
        db_exps = {}
        for e in self.db.get_experiments():
            db_exps[e.id] = e
        pb_exps = {}
        if self.pb:
            for l in self.pb.experiments:
                pb_exps[l.id] = Experiment.from_pb(l)
        for e in pb_exps:
            layer = self.layers.get(e.layer_id)
            if not layer:
                logger.warn('layer %d is not exists for exp %d',
                             e.layer_id, e.id)
                continue
            if e.id in db_exps:
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
        deploy = expb.Deployment()
        # parameters & experiments
        for e in self.exps.values():
            deploy.experiments.append(e.to_pb())
            for p in e.parameters:
                pp = self.db.get_parameter(p.name)
                param = Parameter(pp.name, pp.value, pp.value)
                deploy.parameters.append(param.to_pb())
        # domains
        for d in self.domains.values():
            deploy.domains.append(d.to_pb())
        # layers
        for d in self.layers.values():
            deploy.layers.append(d.to_pb())
        return deploy


def main():
    pass

if __name__ == "__main__":
    main()

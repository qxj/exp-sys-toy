#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; -*-
# @(#) exp_defs.py  Time-stamp: <Julian Qian 2015-12-01 17:49:49>
# Copyright 2015 Julian Qian
# Author: Julian Qian <junist@gmail.com>
# Version: $Id: exp_defs.py,v 0.1 2015-11-13 17:09:51 jqian Exp $
#

import collections
import json

import experiment_pb2 as expb
from exp_log import logger


Bucket = collections.namedtuple('Bucket', 'offset,assign_id')


class BucketError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Buckets(object):
    def __init__(self, bucketRanges, init_id=-1):
        self.buckets = []
        self.init_id = init_id
        for br in bucketRanges:
            for i in range(br.start, br.end):
                self.buckets.append(Bucket(i, self.init_id))

    def __str__(self):
        return '<%d buckets, inited %d>' % (len(self.buckets), self.init_id)

    def get_bucket_ranges(self):
        # TODO O(1) or O(n)?
        bucketRanges = []
        for bucket in self.buckets:
            bucketRanges.append(BucketRange(bucket.offset, bucket.offset+1))
        return self._merge_bucket_ranges(bucketRanges)

    def buckets_num(self):
        return len(self.buckets)

    @classmethod
    def from_num(cls, start_offset, num, init_id=-1):
        bucketRanges = [BucketRange(start_offset, start_offset + num)]
        return cls(bucketRanges, init_id)

    def _merge_bucket_ranges(self, bucketRanges):
        '''merge bucket ranges

        @param BucketRange list
        @return merged BucketRange list
        '''
        ret_brs = []
        alen = len(bucketRanges)
        if alen > 1:
            for i in range(1, alen):
                if bucketRanges[i-1].end == bucketRanges[i].start: # merge
                    bucketRanges[i].start = bucketRanges[i-1].start
                else:
                    ret_brs.append(bucketRanges[i-1])
                if i == alen-1:
                    ret_brs.append(bucketRanges[i])
        else:
            ret_brs = bucketRanges
        return ret_brs

    def assign(self, assign_id, assign_num):
        '''assign buckets to domain/experiments

        @return a list of assigned BucketRanges
        '''
        brs = []
        for bucket in self.buckets:
            if bucket.assign_id == assign_id:
                assign_num -= 1
                brs.append(BucketRange(bucket.offset, bucket.offset+1))
            elif bucket.assign_id == self.init_id: # empty bucket, assign it
                bucket.assign_id = assign_id
                assign_num -= 1
                brs.append(BucketRange(bucket.offset, bucket.offset+1))
            if assign_num == 0:
                break
        if assign_num != 0:
            raise BucketError('remaining %d buckets' % assign_num)
        return self._merge_bucket_ranges(brs)

    def load(self, assign_id, bucketRanges):
        '''load buckets for domain/experiments

        @param buckets, a list of assigned buckets
        '''
        loaded_cnt = 0
        for br in bucketRanges:
            if br.start < self.buckets[0].offset or \
               br.end > self.buckets[-1].offset:
                # raise exception?
                logger.error('bucket range %s error, exceed ranges!', br)
                raise BucketError('bucket range %s error, exceed ranges!' % br)
            else:
                for bkt in self.buckets:
                    if br.start <= bkt.offset < br.end:
                        if bkt.assign_id == self.init_id:
                            bkt.assign_id = assign_id
                            logger.info('assign bucket %d to %d',
                                         bkt.offset, assign_id)
                            loaded_cnt += 1
                        else:
                            logger.error('bucket %d has been assigned to %d',
                                         bkt.offset, bkt.assign_id)
                            raise BucketError('bucket %d has been assigned to %d' \
                                              % (bkt.offset, bkt.assign_id))
        return loaded_cnt


# BucketRange = collections.namedtuple('BucketRange', 'start,end')
class BucketRange(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    @classmethod
    def from_pb(cls, pb):
        return cls(pb.start, pb.end)

    def to_pb(self):
        pb = expb.BucketRange()
        pb.start = self.start
        pb.end = self.end
        return pb

    def __eq__(self, o):
        return self.start == o.start and self.end == o.end

    def __str__(self):
        return '<BucketRange [%d-%d)>' % (self.start, self.end)


class Domain(object):
    def __init__(self, id, bucketRanges):
        self.id = id
        self.buckets = Buckets(bucketRanges, -10000 + self.id)

    @classmethod
    def from_num(cls, id, offset, buckets_num):
        bucketRanges = [BucketRange(offset, offset+buckets_num)]
        return cls(id, bucketRanges)

    def to_pb(self):
        pb = expb.Domain()
        pb.id = self.id
        for i in pb.get_bucket_ranges():
            pb.ranges.append(i)
        return pb

    def assign(self, assign_id, buckets_num):
        return self.buckets.assign(assign_id, buckets_num)


class Layer(object):
    def __init__(self, id, domain):
        '''
        @param domain, Domain
        '''
        self.id = id
        self.domain_id = domain.id
        bucketRanges = domain.buckets.get_bucket_ranges()
        self.buckets = Buckets(bucketRanges, -1000 + self.id)

    def to_pb(self):
        pb = expb.Layer()
        pb.id = self.id
        pb.domain_id = self.domain_id
        return pb

    def load(self, assign_id, bucketRanges):
        return self.buckets.load(assign_id, bucketRanges)

    def assign(self, assign_id, buckets_num):
        return self.buckets.assign(assign_id, buckets_num)


class Diversion(object):
    def __init__(self, type):
        self.type = type

    @classmethod
    def from_pb(cls, type):
        return cls(type)

    @classmethod
    def from_db(cls, type):
        t = expb.Diversion.RANDOM
        if type == 'uuid':
            t = expb.Diversion.UUID
        elif type == 'user':
            t = expb.Diversion.USER
        return cls(t)

    def to_pb(self):
        return self.type


class Condition(object):
    def __init__(self, name, args):
        '''@param args, list of condition string
        '''
        self.name = name
        self.args = args

    @classmethod
    def from_pb(cls, pb):
        return cls(pb.name, [i for i in pb.args])

    def to_pb(self):
        pb = expb.Condition()
        pb.name = self.name
        for arg in self.args:
            pb.args.append(arg)
        return pb


class Parameter(object):
    def __init__(self, name, value, type=None):
        self.name = name
        self.value = value
        self.type = type

    @classmethod
    def from_pb(cls, pb):
        return cls(pb.name, pb.value, pb.type)

    def to_pb(self):
        pb = expb.Parameter()
        pb.name = self.name
        pb.value = self.value
        return pb


class Experiment(object):
    def __init__(self, id, layer_id, diversion,
                 start_time, end_time,
                 ranges, parameters, conditions):
        '''
        @diversion Diversion
        @ranges BucketRanges
        @parameters Parameters
        @conditions Conditions
        '''
        self.id = id
        self.layer_id = layer_id
        self.diversion = diversion
        self.start_time = start_time
        self.end_time = end_time
        self.ranges = ranges
        self.parameters = parameters
        self.conditions = conditions

    @classmethod
    def from_pb(cls, pb):
        diversion = Diversion.from_pb(pb.diversion)
        ranges = [BucketRange.from_pb(i) for i in pb.ranges]
        parameters = [Parameter.from_pb(i) for i in pb.parameters]
        conditions = [Condition.from_pb(i) for i in pb.conditions]
        return cls(pb.id, pb.layer_id, diversion,
                   pb.start_time, pb.end_time,
                   ranges, parameters, conditions)

    @classmethod
    def from_db(cls, row):
        diversion = Diversion.from_db(row.diversion)
        ret = json.loads(row.parameters)
        parameters = []
        if isinstance(ret, dict):
            parameters = [Parameter(name, value) for name, value in ret.items()]
        ret = json.loads(row.conditions)
        conditions = []
        if isinstance(ret, dict):
            conditions = [Condition(name, args) for name, args in ret.items()]
        return cls(row.id, row.layer_id, diversion,
                   row.start_time, row.end_time,
                   None, parameters, conditions)

    def to_pb(self):
        pb = expb.Experiment()
        pb.id = self.id
        pb.layer_id = self.layer_id
        pb.diversion = self.diversion.to_pb()
        pb.start_time = self.start_time
        pb.end_time = self.end_time
        for i in self.ranges:
            pb.ranges.append(i.to_pb())
        for i in self.parameters:
            pb.parameters.append(i.to_pb())
        for i in self.conditions:
            pb.conditions.append(i.to_pb())

    def set_bucket_ranges(self, bucketRanges):
        '''fill BucketRanges after calling `from_db`
        '''
        self.ranges = bucketRanges

    def __eq__(self, o):
        if self.id == o.id and \
           self.layer_id == o.layer_id:
            if len(self.ranges) == len(o.ranges):
                for i, r in enumerate(self.ranges):
                    if o.ranges[i] != r:
                        return False
                return True
        return False


def main():
    pass

if __name__ == "__main__":
    main()

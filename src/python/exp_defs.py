#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; -*-
# @(#) exp_defs.py  Time-stamp: <Julian Qian 2015-12-18 16:39:54>
# Copyright 2015 Julian Qian
# Author: Julian Qian <junist@gmail.com>
# Version: $Id: exp_defs.py,v 0.1 2015-11-13 17:09:51 jqian Exp $
#

import collections
import json

from exp_log import logger


class BucketError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Bucket(object):
    def __init__(self, offset, assign_id):
        self.offset = offset
        self.assign_id = assign_id


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
        '''@return a list of BucketRange
        '''
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
                            # logger.debug('assign bucket %d to %d',
                            #              bkt.offset, assign_id)
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
    def from_json(cls, json):
        return cls(json[0], json[1])

    def to_json(self):
        return [self.start, self.end]

    def __eq__(self, o):
        return self.start == o.start and self.end == o.end

    def __str__(self):
        return '<BucketRange [%d-%d)>' % (self.start, self.end)

    def get_buckets_num(self):
        return self.end - self.start


class Domain(object):
    def __init__(self, id, bucketRanges):
        self.id = id
        self.buckets = Buckets(bucketRanges, -10000 + self.id)

    @classmethod
    def from_num(cls, id, offset, buckets_num):
        bucketRanges = [BucketRange(offset, offset+buckets_num)]
        return cls(id, bucketRanges)

    def to_json(self):

        bucketRanges = self.buckets.get_bucket_ranges()
        if len(bucketRanges) > 1:
            logger.warn('domain %d, something wrong? to many buckets',
                        self.id)
        return {'id': self.id,
                'range': bucketRanges[0].to_json()}

    def assign(self, assign_id, buckets_num):
        return self.buckets.assign(assign_id, buckets_num)

    def __str__(self):
        return "<Domain %d: %s>" % (self.id, self.buckets)


class Layer(object):
    def __init__(self, id, domain):
        '''
        @param domain, Domain
        '''
        self.id = id
        self.domain_id = domain.id
        bucketRanges = domain.buckets.get_bucket_ranges()
        self.buckets = Buckets(bucketRanges, -1000 + self.id)

    def to_json(self):
        return {'id': self.id,
                'domain_id': self.domain_id}

    def load(self, assign_id, bucketRanges):
        return self.buckets.load(assign_id, bucketRanges)

    def assign(self, assign_id, buckets_num):
        return self.buckets.assign(assign_id, buckets_num)

    def __str__(self):
        return "<Layer %d (D%d)>" % (self.id, self.domain_id)


class Condition(object):
    def __init__(self, name, args):
        '''@param args, list of condition string
        '''
        self.name = name
        self.args = args

    @classmethod
    def from_json(cls, json):
        return cls(json['name'], json['args'])

    def to_json(self):
        return {'name': self.name,
                'args': self.args}

    def __str__(self):
        return "<Condition %s>" % self.name


class Parameter(object):
    def __init__(self, name, value, type=None):
        self.name = name
        if type:
            self.type = self._trans_type(type)
        else:
            self.type = self._valid_type(value)
        self.value = self._trans_value(value, self.type)

    @staticmethod
    def _valid_type(value):
        t = 'string'
        if isinstance(value, bool):
            t = 'bool'
        elif isinstance(value, int):
            t = 'int'
        elif isinstance(value, float):
            t = 'double'
        return t

    @staticmethod
    def _trans_type(t):
        if t in ('bool', 'int', 'string', 'double'):
            return str(t)
        else:
            return 'string'

    @staticmethod
    def _trans_value(value, type):
        if Parameter._valid_type(value) == type:
            return value
        # else value is a string
        ret = None
        if type == 'bool':
            if value.lower() == 'true':
                ret = True
            else:
                ret = False
        elif type == 'int':
            ret = int(value)
        elif type == 'double':
            ret = float(value)
        else:
            ret = str(value)
        return ret

    @classmethod
    def from_json(cls, json):
        return cls(json['name'], json['value'], json['type'])

    def to_json(self):
        return {'name': self.name,
                'value': self.value,
                'type': self.type}

    def __str__(self):
        return "<Parameter %s: %s>" % (self.name, self.value)


class Diversion(object):
    @staticmethod
    def valid(d):
        if d in ('uuid', 'user', 'random'):
            return d
        else:
            return 'random'


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
    def from_json(cls, json):
        ranges = [BucketRange.from_json(i) for i in json['ranges']]
        parameters = [Parameter.from_json(i) for i in json['parameters']]
        conditions = [Condition.from_json(i) for i in json['conditions']]
        return cls(json['id'], json['layer_id'], json['diversion'],
                   json['start_time'], json['end_time'],
                   ranges, parameters, conditions)

    @classmethod
    def from_db(cls, row):
        diversion = Diversion.valid(row.diversion)
        logger.debug('row: %s', row)
        ret = json.loads(row.parameters) if row.parameters else {}
        parameters = [Parameter(name, value) for name, value in ret.items()]
        ret = json.loads(row.conditions) if row.conditions else {}
        conditions = [Condition(name, args) for name, args in ret.items()]
        return cls(row.id, row.layer_id, diversion,
                   '%s' % row.start_time, '%s' % row.end_time,
                   None, parameters, conditions)

    def to_json(self):
        # return self.__dict__
        return {'id': self.id,
                'layer_id': self.layer_id,
                'diversion': self.diversion,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'ranges': [i.to_json() for i in self.ranges],
                'parameters': [i.to_json() for i in self.parameters],
                'conditions': [i.to_json() for i in self.conditions]}

    def set_bucket_ranges(self, bucketRanges):
        '''fill BucketRanges after calling `from_db`
        '''
        self.ranges = bucketRanges

    def get_buckets_num(self):
        num = 0
        for br in self.ranges:
            num += br.get_buckets_num()
        return num

    def __eq__(self, o):
        if self.id == o.id and \
           self.layer_id == o.layer_id:
            if len(self.ranges) == len(o.ranges):
                for i, r in enumerate(self.ranges):
                    if o.ranges[i] != r:
                        return False
                return True
        return False

    def __str__(self):
        return "<Experiment %d, Layer %d, Buckets %d)>" % (
            self.id, self.layer_id, self.get_buckets_num())


def main():
    pass

if __name__ == "__main__":
    main()

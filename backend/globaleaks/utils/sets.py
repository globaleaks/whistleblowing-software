# -*- coding: utf-8 -*-

def disjoint_union(*dictionaries):
    d_f = {}

    for d_x in dictionaries:
        s_x = set(d_x.keys())
        s_f = set(d_f.keys())
        if not s_f.isdisjoint(s_x):
            i = s_x & s_f # compute intersect
            raise TypeError('Passed dicts are not disjoint w/ keys: %s' % i)
        d_f = dict(d_f, **d_x)

    return d_f

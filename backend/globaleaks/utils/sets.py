# -*- coding: utf-8 -*-

def merge_dicts(*dicts):
    ret = {}
    for k in set(k for d in dicts for k in d):
        for d in dicts:
            if k in d:
                ret[k] = d[k]

    return ret

#!/usr/bin/env python
#-*- coding: utf-8 -*-
import os
import re
import sys
import shutil
import hashlib
import urllib2
from zipfile import ZipFile
from setuptools import setup

######################################################################
# Temporary fix to https://github.com/globaleaks/GlobaLeaks/issues/572
#                  https://github.com/habnabit/txsocksx/issues/5
from distutils import version
version.StrictVersion = version.LooseVersion
######################################################################

import globaleaks

glclient_path = 'glclient'

if not sys.version_info[:2] == (2, 7):
    print "Error, GlobaLeaks is tested only with python 2.7"
    print "https://github.com/globaleaks/GlobaLeaks/wiki/Technical-requirements"
    raise AssertionError

def pip_to_requirements(s):
    """
    Change a PIP-style requirements.txt string into one suitable for setup.py
    """
    m = re.match('(.*)([>=]=[.0-9a-zA-Z]*).*', s)
    if m:
        return '%s (%s)' % (m.group(1), m.group(2))
    return s.strip()

def get_requires():
    with open('requirements.txt') as f:
        requires = map(pip_to_requirements, f.readlines())
        return requires

def list_files(path):
    result = []
    for f in os.listdir(path):
        f = os.path.join(path, f)
        if os.path.isfile(f):
            result.append(f)

    return result

data_files = [
    ('/usr/share/globaleaks/glclient',
     list_files(os.path.join(glclient_path))),
    ('/usr/share/globaleaks/glclient/data',
     list_files(os.path.join(glclient_path, 'data'))),
    ('/usr/share/globaleaks/glclient/fonts',
     list_files(os.path.join(glclient_path, 'fonts'))),
    ('/usr/share/globaleaks/glclient/img',
     list_files(os.path.join(glclient_path, 'img'))),
    ('/usr/share/globaleaks/glclient/l10n',
     list_files(os.path.join(glclient_path, 'l10n'))),
    ('/usr/share/globaleaks/glbackend',
     ['requirements.txt'] + list_files('staticdata'))
]

setup(
    name='globaleaks',
    version=globaleaks.__version__,
    author=globaleaks.__author__,
    author_email=globaleaks.__email__,
    url='https://globaleaks.org/',
    package_dir={'globaleaks': 'globaleaks'},
    package_data={'globaleaks': [
        'db/sqlite.sql',
        'db/default_ECNT.txt',
        'db/default_EFNT.txt',
        'db/default_EMNT.txt',
        'db/default_ETNT.txt',
        'db/default_PCNT.txt',
        'db/default_PFNT.txt',
        'db/default_PMNT.txt',
        'db/default_PTNT.txt',
        'db/default_ZCT.txt',
        'db/default_MNT.txt',
    ]},
    packages=[
        'globaleaks',
        'globaleaks.db',
        'globaleaks.handlers',
        'globaleaks.jobs',
        'globaleaks.plugins',
        'globaleaks.rest',
        'globaleaks.third_party',
        'globaleaks.third_party.rstr',
        'globaleaks.utils',
    ],
    data_files=data_files,
    scripts=[
        'bin/globaleaks',
        'bin/globaleaksadmin',
        'scripts/glclient-build',
        'bin/gl-fix-permissions',
    ],
    requires=get_requires(),
)

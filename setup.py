#!/usr/bin/env python
#-*- coding: utf-8 -*-
import os
import re
import sys
import shutil
import hashlib
import urllib2
from zipfile import ZipFile
from distutils.core import setup

######################################################################
# Temporary fix to https://github.com/globaleaks/GlobaLeaks/issues/572
#                  https://github.com/habnabit/txsocksx/issues/5
from distutils import version
version.StrictVersion = version.LooseVersion
######################################################################

from globaleaks import __version__

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
        result.append(os.path.join(path, f))

    return result

data_files = [
    ('/usr/share/globaleaks/glclient',
     list_files(os.path.join(glclient_path))),
    ('/usr/share/globaleaks/glclient/fonts',
     list_files(os.path.join(glclient_path, 'fonts'))),
    ('/usr/share/globaleaks/glclient/img',
     list_files(os.path.join(glclient_path, 'img'))),
    ('/usr/share/globaleaks/glclient/l10n',
     list_files(os.path.join(glclient_path, 'l10n'))),
    ('/usr/share/globaleaks/glbackend',
     ['requirements.txt'] + list_files('staticdata'))
]

print data_files
exit(1)

setup(
    name="globaleaks",
    version = __version__,
    author="Random GlobaLeaks developers",
    author_email = "info@globaleaks.org",
    url="https://globaleaks.org/",
    package_dir={'globaleaks': 'globaleaks'},
    package_data = {'globaleaks': ['db/sqlite.sql', 'db/default_TNT.txt',
                                   'db/default_CNT.txt', 'db/default_FNT.txt']},
    packages=['globaleaks', 'globaleaks.db', 'globaleaks.handlers',
        'globaleaks.jobs', 'globaleaks.plugins', 'globaleaks.rest',
        'globaleaks.utils', 'globaleaks.third_party', 'globaleaks.third_party.rstr'],
    data_files=data_files,
    scripts=["bin/globaleaks", "scripts/glclient-build", 'bin/gl-reset-password', 'bin/gl-fix-permissions'],
    requires = get_requires(),
)

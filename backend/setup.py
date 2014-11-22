#!/usr/bin/env python
#-*- coding: utf-8 -*-
from __future__ import print_function

from importlib import import_module
import os
import sys

from pip.req import parse_requirements
from setuptools import setup
from setuptools.command.test import test as _TestCommand

######################################################################
# Temporary fix to https://github.com/globaleaks/GlobaLeaks/issues/572
#                  https://github.com/habnabit/txsocksx/issues/5
from distutils import version
version.StrictVersion = version.LooseVersion
######################################################################

import globaleaks

GLCLIENT_PATH = os.path.join(os.path.dirname(__file__),
                             '..', 'client', 'build')

if not sys.version_info[:2] == (2, 7):
    print('Error, GlobaLeaks is tested only with python 2.7')
    print('https://github.com/globaleaks/GlobaLeaks/wiki/Technical-requirements')
    raise AssertionError


install_requires = [str(r.req) for r in parse_requirements('requirements.txt')]

def list_files(path):
    """
    Return the list of files present in a directory.
    """
    result = []
    if not os.path.exists(path):
        print('Warning: {} does not exist.'.format(path))
        return []

    for f in os.listdir(path):
        f = os.path.join(path, f)
        if os.path.isfile(f):
            result.append(f)

    return result

class TestCommand(_TestCommand):
    def run_tests(self):
        from twisted.trial import runner, reporter

        testsuite_runner= runner.TrialRunner(reporter.TreeReporter)
        loader = runner.TestLoader()
        suite = loader.loadPackage(import_module(self.test_suite), True)
        testsuite_runner.run(suite)

data_files = [
    ('/usr/share/globaleaks/glclient',
     list_files(os.path.join(GLCLIENT_PATH))),
    ('/usr/share/globaleaks/glclient/data',
     list_files(os.path.join(GLCLIENT_PATH, 'data'))),
    ('/usr/share/globaleaks/glclient/fonts',
     list_files(os.path.join(GLCLIENT_PATH, 'fonts'))),
    ('/usr/share/globaleaks/glclient/img',
     list_files(os.path.join(GLCLIENT_PATH, 'img'))),
    ('/usr/share/globaleaks/glclient/l10n',
     list_files(os.path.join(GLCLIENT_PATH, 'l10n'))),
    ('/usr/share/globaleaks/glbackend',
     ['requirements.txt'] + list_files('staticdata'))
]

setup(
    name='globaleaks',
    version=globaleaks.__version__,
    author=globaleaks.__author__,
    author_email=globaleaks.__email__,
    url='https://globaleaks.org/',
    cmdclass={'test': TestCommand},
    package_dir={'globaleaks': 'globaleaks'},
    test_suite='globaleaks.tests',
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
    install_requires=install_requires,
)

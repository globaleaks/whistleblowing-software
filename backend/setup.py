#!/usr/bin/env python
#-*- coding: utf-8 -*-
from __future__ import print_function

from importlib import import_module
import os
import sys

from pip.req import parse_requirements
from setuptools import find_packages, setup
from setuptools.command.test import test as _TestCommand

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
        test_result = testsuite_runner.run(suite)
        sys.exit(not test_result.wasSuccessful())

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
    ]},
    packages=find_packages(exclude=['*.tests', '*.tests.*']),
    data_files=data_files,
    scripts=[
        'bin/globaleaks',
        'bin/gl-admin',
        'bin/gl-fix-permissions',
    ],
    install_requires=install_requires,
    tests_require=['mock'],
)

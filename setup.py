#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import shutil
import hashlib
import urllib2
from zipfile import ZipFile
from distutils.core import setup


glclient_path = 'glclient-d03f2fbb'
def download_glclient():
    glclient_url = "https://globaleaks.org/builds/GLClient/"+glclient_path+".zip"
    print "[+] Downloading glclient from %s" % glclient_url

    o = open('glclient.zip', 'w+')
    f = urllib2.urlopen(glclient_url)
    o.write(f.read())
    o.close()
    print "    ...done."

def verify_glclient():
    print "[+] Checking GLClient hash..."
    glclient_hash = "e2456c49d9ed6828be573a5b823885a8bf92b8283c178a452ffe1831"
    with open('glclient.zip') as f:
        h = hashlib.sha224(f.read()).hexdigest()
        if not h == glclient_hash:
            raise Exception("%s != %s" % (h, glclient_hash))
    print "    ...success."

def uncompress_glclient(glclient_path):
    print "[+] Uncompressing GLClient..."
    zipfile = ZipFile('glclient.zip')
    zipfile.extractall()
    os.unlink('glclient.zip')
    shutil.move(glclient_path, 'glclient')
    print "    ...done."

def build_glclient():
    print "[+] Building GLClient..."
    os.chdir(glclient_path)
    os.system("npm install -d")
    os.system("grunt build")
    os.chdir('..')
    print "    ...done."

if not os.path.isdir('glclient'):
    download_glclient()
    verify_glclient()
    uncompress_glclient(glclient_path)
glclient_path = 'glclient'
#build_glclient()

install_requires = []
requires = [
"twisted (==12.3.0)",
"apscheduler (==2.1.0)",
"zope.component (==4.1.0)",
"zope.interface (==4.0.5)",
"cyclone (==1.1)",
"storm (==0.19)",
"transaction (==1.4.1)",
"txsocksx (==0.0.2)",
"PyCrypto (==2.6)",
"scrypt (==0.5.5)",
"Pillow (==2.0.0)"
]

data_files = [('/usr/share/globaleaks/glclient', [os.path.join(glclient_path, 'index.html'),
    os.path.join(glclient_path, 'styles.css'),
    os.path.join(glclient_path, 'scripts.js'),
]),
    ('/usr/share/globaleaks/glclient/images', [
    os.path.join(glclient_path, 'images', 'flags.png'),
    os.path.join(glclient_path, 'images', 'glyphicons-halflings.png'),
    os.path.join(glclient_path, 'images', 'glyphicons-halflings-white.png')
]), ('/usr/share/globaleaks/glbackend', [
    'staticdata/torrc',
    'staticdata/globaleaks_logo.png'])]

setup(
    name="globaleaks",
    version="0.2",
    author="Random GlobaLeaks developers",
    author_email = "info@globaleaks.org",
    url="https://globaleaks.org/",
    package_dir={'globaleaks': 'globaleaks'},
    package_data = {'globaleaks': ['db/sqlite.sql', 'db/default_TNT.txt',
                                   'db/default_CNT.txt', 'db/default_FNT.txt']},
    packages=['globaleaks', 'globaleaks.db', 'globaleaks.handlers',
        'globaleaks.jobs', 'globaleaks.plugins',
        'globaleaks.rest', 'globaleaks.third_party', 'globaleaks.third_party.rstr'],
    data_files=data_files,
    scripts=["bin/globaleaks"],
    #install_requires=open("requirements.txt").readlines(),
    requires=requires
)
shutil.rmtree(glclient_path)

#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import shutil
import hashlib
import urllib2
from zipfile import ZipFile
from distutils.core import setup

glclient_path = 'glclient-3e23dde0'
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
    glclient_hash = "67e519adb74b319ed65baa3a4b50e4f282a17ec47af011c08210878e"
    with open('glclient.zip') as f:
        h = hashlib.sha224(f.read()).hexdigest()
        if not h == glclient_hash:
            raise Exception("%s != %s" % (h, glclient_hash))
    print "    ...success."

def uncompress_glclient():
    print "[+] Uncompressing GLClient..."
    zipfile = ZipFile('glclient.zip')
    zipfile.extractall()
    print "    ...done."

def build_glclient():
    print "[+] Building GLClient..."
    os.chdir(glclient_path)
    os.system("npm install -d")
    os.system("grunt build")
    os.chdir('..')
    print "    ...done."

download_glclient()
verify_glclient()
uncompress_glclient()
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

data_files = [('glclient', [os.path.join(glclient_path, 'build', 'index.html'),
    os.path.join(glclient_path, 'build', 'styles.css'),
    os.path.join(glclient_path, 'build', 'scripts.js'),
    os.path.join(glclient_path, 'build', 'images', 'flags.png'),
    os.path.join(glclient_path, 'build', 'images', 'glyphicons-halflings.png'),
    os.path.join(glclient_path, 'build', 'images', 'glyphicons-halflings-white.png')
])]

setup(
    name="globaleaks",
    version="0.2",
    author="Random GlobaLeaks developers",
    author_email = "info@globaleaks.org",
    url="https://globaleaks.org/",
    package_dir={'globaleaks': 'globaleaks'},
    package_data = {'globaleaks': ['db/sqlite.sql',
                                   'db/emailnotification_template']},
    packages=['globaleaks', 'globaleaks.db', 'globaleaks.handlers',
        'globaleaks.jobs', 'globaleaks.plugins',
        'globaleaks.rest', 'globaleaks.third_party', 'globaleaks.third_party.rstr'],
    data_files=data_files,
    scripts=["bin/globaleaks"],
    #install_requires=open("requirements.txt").readlines(),
    requires=requires
)

def cleanup():
    shutil.rmtree(glclient_path)
    os.unlink('glclient.zip')
cleanup()

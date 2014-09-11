#!twistd -ny
"""
Manhole to get your hands dirty in globaleaks.

Run this file with:
$ twistd -ny scripts/debug.tac
Note: it will ask for username and password - they are empty.
Note: to initialize the database, at the moment it is required to perform:
 >>> from globaleaks.db import create_tables
 >>> create_tables()
AS FIRST COMMAND
"""
from __future__ import with_statement

import tempfile

from twisted.conch import manhole_tap

# XXX. shitty hack to get the application working without passing for the whole
# configuration
from globaleaks.settings import GLSetting
GLSetting.bind_addresses = ['localhost']
GLSetting.set_devel_mode()
GLSetting.logging = None
#GLSetting.scheduler_threadpool = FakeThreadPool()
GLSetting.memory_copy.allow_unencrypted = True
GLSetting.sessions = {}
GLSetting.failed_login_attempts = 0
GLSetting.working_path = './working_path'
GLSetting.ramdisk_path = './working_path/ramdisk'
GLSetting.eval_paths()
GLSetting.remove_directories()
GLSetting.create_directories()

from globaleaks.backend import application

# FUCK YOU TWISTED
with tempfile.NamedTemporaryFile(prefix='gldebug_pwd', delete=False) as pfile:
    pfile.write(':\n')

    manhole_tap.makeService({
        'sshPort': None,
        'passwd': pfile.name,
        'namespace': None,
        'telnetPort': '6666',
    }).setServiceParent(application)

#!twistd -ny
"""
Manhole to get your hands dirty in globaleaks.

Run this file with:
$ twistd -ny scripts/debug.tac
Note: it will ask for username and password - they are empty.
"""
from __future__ import with_statement

import tempfile

from twisted.conch import manhole_tap

# XXX. shitty hack to get the application working without passing for the whole
# configuration
from globaleaks.settings import GLSetting
GLSetting.eval_paths()
GLSetting.bind_addresses = ['localhost']
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

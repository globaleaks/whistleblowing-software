import os
from cyclone.util import ObjectDict as OD

glbackend = OD()

class ConfigError(Exception):
    pass

# XXX move all these variables to a config file
try:
    this_directory = os.path.dirname(__file__)
    glclient_path = os.path.join(this_directory, '..', '..')
    glclient_path = os.path.join(glclient_path, 'GLClient', 'www')
    path = os.path.abspath(glclient_path)
    if not os.path.isdir(path):
        raise ConfigError("GLClient not found at the %s path" % glclient_path)
except ConfigError, e:
    print e
    path = '/tmp'

print "Serving GLClient from %s" % path
glbackend.glclient_path = path

# temporary use for implement whistleblower.py
glbackend.test = OD()
glbackend.test.wbCanSetReceivers = True
glbackend.test.defaultAllReceiverSets = True
glbackend.test.permitReceiptChoose = True

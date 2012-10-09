import os
from cyclone.util import ObjectDict as OD

glbackend = OD()

# XXX move all these variables to a config file
try:
    path = os.path.abspath('../../GLClient/www/')
except:
    path = '/tmp'
print "Path %s" % path
glbackend.glclient_path = path

# temporary use for implement submission.py
glbackend.test = OD()
glbackend.test.wbCanSetReceivers = True
glbackend.test.defaultAllReceiverSets = True
glbackend.test.permitReceiptChoose = True

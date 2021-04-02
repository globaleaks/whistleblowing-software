#!/usr/bin/env python

from time import time
import cProfile
import txtorcon

proto = txtorcon.TorControlProtocol()
state = txtorcon.TorState(proto)

data = open('consensus', 'r').read()
routers = 5494  # number of routers in above file
iters = 5

start = time()
if False:
    cProfile.run('state._update_network_status(data)')
else:
    for x in range(iters):
        state._update_network_status(data)
diff = time() - start
print("%fs: %f microdescriptors/second" % (diff, (routers * iters) / diff))

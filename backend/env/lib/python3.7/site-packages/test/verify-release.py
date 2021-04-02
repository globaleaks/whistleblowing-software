# this does the "download and verify release from web + hidden-service
# machine" for txtorcon release-checklist.

import sys
import hashlib
from os.path import join, split, exists

import txtorcon

from twisted.internet import defer, task
from twisted.web.client import readBody
from twisted.python.failure import Failure


@task.react
@defer.inlineCallbacks
def main(reactor):
    if len(sys.argv) != 2:
        print('usage: {} <version>'.format(__file__))
        raise SystemExit(1)
    version = sys.argv[1]
    announce = join(split(__file__)[0], '..', 'release-announce-{}'.format(version))
    if not exists(announce):
        print('no announcement file: {}'.format(announce))
        raise SystemExit(2)

    sums = None
    with open(announce, 'r') as f:
        for line in f.readlines():
            if line.strip() == 'cat <<EOF | sha256sum --check':
                sums = []
            elif line.strip() == 'EOF':
                break
            elif sums is not None:
                checksum, fname = line.split()
                sums.append((checksum, split(fname)[1]))

    tor = yield txtorcon.connect(reactor)
    agent = tor.web_agent()

    for sha256, fname in sums:
        print("Verifying '{}'".format(fname))
        uri = b'http://timaq4ygg2iegci7.onion/' + fname.encode('ascii')
        try:
            resp = yield agent.request(b'GET', uri)
        except Exception:
            print(Failure())
            raise
        data = yield readBody(resp)
        print('data: {} {}'.format(type(data), len(data)))
        hasher = hashlib.new('sha256')
        hasher.update(data)
        alleged_sum = hasher.hexdigest()
        if alleged_sum != sha256:
            print("Checksum mismatch:")
            print("wanted: {}".format(sha256))
            print("   got: {}".format(alleged_sum))
            raise SystemExit(45)

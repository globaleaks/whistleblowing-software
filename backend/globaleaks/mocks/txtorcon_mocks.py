# A shim taken from v0.19.3 release to support EphemeralHiddenServices

from txtorcon.util import find_keywords

from twisted.internet import defer
from twisted.python import log


class EphemeralHiddenService(object):
    def __init__(self, ports, key_blob_or_type='NEW:BEST'):
        if not isinstance(ports, list):
            ports = [ports]

        self._ports = [x.replace(' ', ',') for x in ports]
        self._key_blob = key_blob_or_type

    @defer.inlineCallbacks
    def add_to_tor(self, protocol):
        """
        Returns a Deferred which fires with 'self' after at least one
        descriptor has been uploaded. Errback if no descriptor upload
        succeeds.
        """
        ports = ' '.join(map(lambda x: 'Port=' + x.strip(), self._ports))
        cmd = 'ADD_ONION %s %s' % (self._key_blob, ports)
        ans = yield protocol.queue_command(cmd)
        ans = find_keywords(ans.split('\n'))
        self.hostname = ans['ServiceID'] + '.onion'
        if self._key_blob.startswith('NEW:'):
            self.private_key = ans['PrivateKey']
        else:
            self.private_key = self._key_blob

        log.msg('Created hidden-service at', self.hostname)

        # Now we want to wait for the descriptor uploads. This doesn't
        # quite work, as the UPLOADED events always say "UNKNOWN" for
        # the HSAddress so we can't correlate it to *this* onion for
        # sure :/ "yet", though. Yawning says on IRC this is coming.

        # XXX Hmm, still UPLOADED always says UNKNOWN, but the UPLOAD
        # events do say the address -- so we save all those, and
        # correlate to the target nodes. Not sure if this will really
        # even work, but better than nothing.

        uploaded = defer.Deferred()
        attempted_uploads = set()
        confirmed_uploads = set()
        failed_uploads = set()

        def hs_desc(evt):
            """
            From control-spec:
            "650" SP "HS_DESC" SP Action SP HSAddress SP AuthType SP HsDir
            [SP DescriptorID] [SP "REASON=" Reason] [SP "REPLICA=" Replica]
            """

            args = evt.split()
            subtype = args[0]
            if subtype == 'UPLOAD':
                if args[1] == self.hostname[:-6]:
                    attempted_uploads.add(args[3])

            elif subtype == 'UPLOADED':
                # we only need ONE successful upload to happen for the
                # HS to be reachable. (addr is args[1])
                if args[3] in attempted_uploads:
                    confirmed_uploads.add(args[3])
                    log.msg("Uploaded '{}' to '{}'".format(self.hostname, args[3]))
                    uploaded.callback(self)

            elif subtype == 'FAILED':
                if args[1] == self.hostname[:-6]:
                    failed_uploads.add(args[3])
                    if failed_uploads == attempted_uploads:
                        msg = "Failed to upload '{}' to: {}".format(
                            self.hostname,
                            ', '.join(failed_uploads),
                        )
                        uploaded.errback(RuntimeError(msg))

        log.msg("Created '{}', waiting for descriptor uploads.".format(self.hostname))
        yield protocol.add_event_listener('HS_DESC', hs_desc)
        yield uploaded
        yield protocol.remove_event_listener('HS_DESC', hs_desc)

    @defer.inlineCallbacks
    def remove_from_tor(self, protocol):
        """
        Returns a Deferred which fires with None
        """
        r = yield protocol.queue_command('DEL_ONION %s' % self.hostname[:-6])
        if r.strip() != 'OK':
            raise RuntimeError('Failed to remove hidden service: "%s".' % r)

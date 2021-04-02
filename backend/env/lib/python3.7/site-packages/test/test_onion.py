import os

from zope.interface.verify import verifyClass, verifyObject

from mock import Mock

from twisted.trial import unittest
from twisted.internet import defer

from txtorcon.onion import EphemeralHiddenService
from txtorcon.onion import FilesystemOnionService
from txtorcon.onion import IOnionService  # FIXME interfaces.py


class OnionInterfaceTests(unittest.TestCase):
    def test_ephemeral_class(self):
        # as far as I can tell, this is worthless? just seems to check
        # that there's an @implemeter(IOnionService) on the class
        # (i.e. doesn't verify an Attribute, anyway...)
        verifyClass(IOnionService, EphemeralHiddenService)

    def test_ephemeral_obj(self):
        verifyObject(
            IOnionService,
            EphemeralHiddenService(Mock(), [])
        )


class FilesystemServiceTests(unittest.TestCase):

    def test_invalid_ports(self):
        with self.assertRaises(ValueError) as ctx:
            FilesystemOnionService(Mock(), '/dev/null', (123, 456))
        self.assertTrue("'ports' must be" in str(ctx.exception))

    def test_load_private_key(self):
        d = self.mktemp()
        os.mkdir(d)
        with self.assertRaises(IOError) as ctx:
            o = FilesystemOnionService(Mock(), d, [123])
            o.private_key
        self.assertIn("No such file or", str(ctx.exception))

    def test_load_private_key_for_realz(self):
        d = self.mktemp()
        os.mkdir(d)
        with open(os.path.join(d, 'private_key'), 'w') as f:
            f.write('was it worth it?')

        fos = FilesystemOnionService(Mock(), d, [123])
        self.assertEqual("was it worth it?", fos.private_key)


class EphemeralServiceTests(unittest.TestCase):

    @defer.inlineCallbacks
    def test_upload_no_discard_private(self):
        """
        Inconsistent to specify a priv-key and discard=True
        """
        try:
            yield EphemeralHiddenService.create(
                Mock(),
                ['80 127.0.0.1:80'],
                detach=True,
                discard_key=True,
                private_key='RSA1024:deadbeefdeadbeefdeadbeefdeadbeef',
            )
            self.fail("Should get an error")
        except ValueError as e:
            self.assertTrue('private_key' in str(e))

    @defer.inlineCallbacks
    def test_upload_options(self):

        class FakeProtocol(object):
            listener = None

            def queue_command(s, cmd):
                self.assertTrue('Detach' in cmd)
                self.assertTrue('DiscardPK' in cmd)
                self.assertTrue('NEW:BEST' in cmd)
                return "ServiceID=deadbeefdeadbeef\nPrivateKey=RSA1024:xxxx"

            def add_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                s.listener = listener

            def remove_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                self.assertTrue(listener == s.listener)
                s.listener = None

        class FakeConfig(object):
            EphemeralOnionServices = []
            tor_protocol = FakeProtocol()

        progress = Mock()
        config = FakeConfig()
        hs = EphemeralHiddenService.create(
            config,
            ['80 127.0.0.1:80'],
            detach=True,
            discard_key=True,
            progress=progress,
        )

        self.assertTrue(config.tor_protocol.listener is not None)
        config.tor_protocol.listener('UPLOAD deadbeefdeadbeef x hs_dir_0')
        config.tor_protocol.listener('UPLOADED deadbeefdeadbeef x hs_dir_0')
        hs = yield hs
        # should have removed listener by now
        self.assertTrue(config.tor_protocol.listener is None)
        self.assertTrue(hs in config.EphemeralOnionServices)

    @defer.inlineCallbacks
    def test_upload_with_private_key(self):

        class FakeProtocol(object):
            listener = None

            def queue_command(s, cmd):
                return "if tor is broken we detect it"

            def add_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                s.listener = listener

            def remove_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                self.assertTrue(listener == s.listener)
                s.listener = None

        class FakeConfig(object):
            EphemeralOnionServices = []
            tor_protocol = FakeProtocol()

        progress = Mock()
        config = FakeConfig()
        try:
            yield EphemeralHiddenService.create(
                config,
                ['80 127.0.0.1:80'],
                progress=progress,
                # we test it works with no leading "RSA1024:" too
                private_key="deadbeefdeadbeef",
            )
            self.fail("Should get error")
        except RuntimeError as e:
            self.assertTrue(
                "Expected ADD_ONION to return" in str(e)
            )

    @defer.inlineCallbacks
    def test_remove_service(self):

        class FakeProtocol(object):
            listener = None
            commands = []

            def queue_command(s, cmd):
                s.commands.append(cmd)
                return "OK"

            def add_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                s.listener = listener

            def remove_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                self.assertTrue(listener == s.listener)
                s.listener = None

        class FakeConfig(object):
            EphemeralOnionServices = []
            tor_protocol = FakeProtocol()

        config = FakeConfig()

        hs = yield EphemeralHiddenService(
            config,
            ['80 127.0.0.1:80'],
            # we test it works with no leading "RSA1024:" too
            private_key="RSA1024:deadbeefdeadbeef",
        )
        hs._hostname = 'deadbeef.onion'
        yield hs.remove()
        self.assertIn("DEL_ONION deadbeef", config.tor_protocol.commands[-1])

    @defer.inlineCallbacks
    def test_remove_service_but_fails(self):

        class FakeProtocol(object):
            listener = None
            commands = []

            def queue_command(s, cmd):
                s.commands.append(cmd)
                return "something went wrong"

            def add_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                s.listener = listener

            def remove_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                self.assertTrue(listener == s.listener)
                s.listener = None

        class FakeConfig(object):
            EphemeralOnionServices = []
            tor_protocol = FakeProtocol()

        config = FakeConfig()

        hs = yield EphemeralHiddenService(
            config,
            ['80 127.0.0.1:80'],
            # we test it works with no leading "RSA1024:" too
            private_key="RSA1024:deadbeefdeadbeef",
        )
        hs._hostname = 'deadbeef.onion'
        with self.assertRaises(RuntimeError) as ctx:
            yield hs.remove()
        self.assertTrue("Failed to remove service" in str(ctx.exception))

    @defer.inlineCallbacks
    def test_uploads_fail(self):
        """
        When all descriptor uploads fail, we get an error
        """

        class FakeProtocol(object):
            listener = None

            def queue_command(s, cmd):
                return "ServiceID=deadbeefdeadbeef\nPrivateKey=RSA1024:xxxx"

            def add_event_listener(s, evt, listener):
                self.assertTrue(evt == 'HS_DESC')
                # should only get one listener added
                self.assertTrue(s.listener is None)
                s.listener = listener

        class FakeConfig(object):
            EphemeralOnionServices = []
            tor_protocol = FakeProtocol()

        progress = Mock()
        config = FakeConfig()
        hs = EphemeralHiddenService.create(
            config,
            ['80 127.0.0.1:80'],
            progress=progress,
        )

        for x in range(6):
            config.tor_protocol.listener(
                'UPLOAD deadbeefdeadbeef x hs_dir_{}'.format(x)
            )

        for x in range(6):
            config.tor_protocol.listener(
                'FAILED deadbeefdeadbeef x hs_dir_{}'.format(x)
            )

        try:
            hs = yield hs
            self.fail("should have gotten exception")
        except Exception as e:
            self.assertIn("Failed to upload 'deadbeefdeadbeef.onion'", str(e))
            for x in range(6):
                self.assertTrue("hs_dir_{}".format(x) in str(e))

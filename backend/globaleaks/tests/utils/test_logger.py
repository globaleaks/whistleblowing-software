# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks.utils.logger import LoggedEvent, adminLog, receiverLog, tipLog, LogQueue


class TestCollection(helpers.TestGL):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

    def test_adminLog(self):
        adminLog(['normal'], 'LOGIN_1', [])
        adminLog(['normal'], 'LOGIN_2', ['args'])
        adminLog(['normal'], 'LOGIN_1', [])
        adminLog(['normal'], 'LOGIN_1', [])

        x = LogQueue.picklogs('admin', 50)

        self.assertTrue(len(x) == 3)
        self.assertEqual(x[0].repeated, 1)
        self.assertEqual(x[1].log_code, 'LOGIN_2')


    def test_receiverLog(self):
        fake_uuidv4 = 'blah-this-is-an-UUID-v4'
        other_receiver = 'CallMeOther,ButIamWorkingHardLikeEveryOtherReceiver'

        receiverLog(['mail'], 'LOGIN_3', [], fake_uuidv4)
        receiverLog(['mail'], 'LOGIN_3', [], fake_uuidv4)
        receiverLog(['mail', 'normal'], 'SECURITY_1', [], fake_uuidv4)

        receiverLog(['normal'], 'LOGIN_3', [], other_receiver)
        receiverLog(['mail', 'normal'], 'SECURITY_1', [], fake_uuidv4)

        x = LogQueue.picklogs(
            LogQueue.create_subject_uuid('receiver', fake_uuidv4),
            50
        )
        self.assertEqual(x[0].repeated, 1)
        self.assertEqual(x[1].repeated, 1)


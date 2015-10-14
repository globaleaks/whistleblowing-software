# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks.utils.logger import receiverLog, LogQueue, picklogs
from globaleaks.tests.jobs.test_log_sched import clear_and_push_admin_logs

def push_receiver_logs(fake_uuidv4, number):
    for _ in xrange(number):
        receiverLog(['normal'], 'LOGIN_20', [], fake_uuidv4)

class TestCollection(helpers.TestGL):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

    @inlineCallbacks
    def test_adminLog(self):
        logs_number = 10
        clear_and_push_admin_logs(logs_number)
        x =  yield picklogs('admin', logs_number, -1)
        self.assertTrue(len(x) == logs_number)

    @inlineCallbacks
    def test_picklogs_more_than(self):
        logs_number = 10
        clear_and_push_admin_logs(logs_number)
        x =  yield picklogs('admin', logs_number * 2, -1)
        self.assertTrue(len(x) == logs_number)

    @inlineCallbacks
    def test_receiverLog(self):
        fake_uuidv4 = 'blah-this-is-an-UUID-v4'
        other_receiver = 'CallMeOther,ButIamWorkingHardLikeEveryOtherReceiver'

        receiverLog(['mail'], 'LOGIN_20', [], fake_uuidv4)
        receiverLog(['mail'], 'LOGIN_20', [], fake_uuidv4)
        receiverLog(['mail', 'normal'], 'SECURITY_20', [], fake_uuidv4)
        receiverLog(['normal'], 'LOGIN_20', [], other_receiver)
        receiverLog(['mail', 'normal'], 'SECURITY_20', [], fake_uuidv4)

        x = yield picklogs(
            LogQueue.create_subject_uuid('receiver', fake_uuidv4),
            50, -1 )
        self.assertEqual(len(x), 4)
        x = yield picklogs(
            LogQueue.create_subject_uuid('receiver', other_receiver),
            50, -1 )
        self.assertEqual(len(x), 1)


    @inlineCallbacks
    def test_picklogs(self):

        NUMBER = 10
        clear_and_push_admin_logs(NUMBER)

        adm = yield picklogs('admin', NUMBER, -1)
        self.assertEqual(len(adm), NUMBER )

        fake_uuidv4 = 'blah-this-is-an-UUID-v4'
        push_receiver_logs(fake_uuidv4, NUMBER)
        rcvr = yield picklogs("receiver_%s" % fake_uuidv4, NUMBER, -1)
        self.assertEqual(len(rcvr), NUMBER)

        adm = yield picklogs('admin', NUMBER, -1)
        self.assertEqual(len(adm), NUMBER )

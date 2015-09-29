# -*- encoding: utf-8 -*-
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks import models
from globaleaks.settings import transact
from globaleaks.utils.logger import LoggedEvent, adminLog, receiverLog, \
    tipLog, LogQueue, initialize_LoggedEvent

from globaleaks.jobs.log_sched import LogSchedule


def push_admin_logs(howmany):

    LogQueue._all_queues = {}
    for _ in xrange(howmany):
        adminLog(['normal'], 'LOGIN_1', [])


class TestLogFlush(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def test_initialize_high_id(self):

        yield initialize_LoggedEvent()
        FUFFA_NUMBER = 100
        push_admin_logs(FUFFA_NUMBER)

        yield LogSchedule().dump_fresh_logs()

        nextrun = LogSchedule()

        yield nextrun.initialize_highest_id()

        self.assertEqual(nextrun.highest_logged_id, FUFFA_NUMBER)


    @inlineCallbacks
    def test_stored_log(self):

        yield initialize_LoggedEvent()
        FUFFA_NUMBER = 42
        push_admin_logs(FUFFA_NUMBER)

        yield LogSchedule().dump_fresh_logs()

        adminLog(['normal'], 'LOGIN_2', ['a'])
        # TODO continue



    @inlineCallbacks
    def test_dump_fresh_log(self):

        yield initialize_LoggedEvent()
        FUFFA_NUMBER = 120
        push_admin_logs(FUFFA_NUMBER)

        yield LogSchedule().dump_fresh_logs()
        yield self.pull_logs(FUFFA_NUMBER)


    @transact
    def pull_logs(self, store, expected_amount):

        self.assertEqual(store.find(models.Log).count(), expected_amount)


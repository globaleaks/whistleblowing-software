# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks import models
from globaleaks.settings import transact
from globaleaks.utils.logger import adminLog, LogQueue, picklogs

from globaleaks.jobs.log_sched import LogSchedule


def clear_and_push_admin_logs(howmany):

    LogQueue._all_queues = {}
    for _ in xrange(howmany):
        adminLog(['normal'], 'LOGIN_1', [])


class TestLogFlush(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def test_stored_log(self):
        FUFFA_NUMBER = 3
        clear_and_push_admin_logs(FUFFA_NUMBER)
        number_dumped = yield LogSchedule().dump_fresh_logs()
        # self.assertEqual(FUFFA_NUMBER, number_dumped)
        adminLog(['normal'], 'LOGIN_2', ['a'])

        # The memory get flushed
        LogQueue._all_queues = {}

        # and therefore this call pull also from the DB
        # 0 because is only 'normal'
        x = yield picklogs('admin', FUFFA_NUMBER, 0)
        self.assertEqual(len(x), FUFFA_NUMBER)

    @inlineCallbacks
    def test_dump_fresh_log(self):
        """
        Note: this test works when tested alone. due to
            cache and IDs, cause when is tested separately works..
            * to be checked better *
        """

        FUFFA_NUMBER = 12
        clear_and_push_admin_logs(FUFFA_NUMBER)

        yield LogSchedule().dump_fresh_logs()
        yield self.pull_logs(FUFFA_NUMBER)

    @transact
    def pull_logs(self, store, expected_amount):
        self.assertEqual(store.find(models.Log).count(), expected_amount)


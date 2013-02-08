# -*- coding: UTF-8
#
#   debug 
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#

from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks
from globaleaks.transactors.crudoperations import CrudOperations
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest.errors import InvalidInputFormat


class EntryCollection(BaseHandler):
    """
    D1
    Interface for dumps elements in the tables, used in debug and detailed analysis.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, what, *uriargs):
        """
        Parameters: None
        Response: Unknown
        Errors: None

        /dump/overview GET should return up to all the tables of GLBackend
        """

        try:
            answer = yield CrudOperations().dump_models(what)

            self.set_status(answer['code'])
            self.json_write(answer['data'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class TaskInstance(BaseHandler):
    """
    D2
    controls task and scheduled
    """

    @asynchronous
    @inlineCallbacks
    def get(self, what, *uriargs):
        """
        Parameters: None
        Response: Unknown
        Errors: None

        /admin/tasks/ GET, force the execution of an otherwise scheduled event
        """
        from globaleaks.jobs.notification_sched import APSNotification
        from globaleaks.jobs.delivery_sched import APSDelivery
        from globaleaks.jobs.cleaning_sched import APSCleaning
        from globaleaks.jobs.statistics_sched import APSStatistics

        expected = [ 'statistics', 'delivery', 'notification', 'cleaning' ]

        if what == 'statistics':
            yield APSStatistics().operation()
        if what == 'delivery':
            yield APSDelivery().operation()
        if what == 'notification':
            yield APSNotification().operation()
        if what == 'cleaning':
            yield APSCleaning().operation()

        if not what in expected:
            self.set_status(405)
        else:
            self.set_status(200)

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, what, *uriargs):
        """
        Request: None
        Response: None
        Errors: None

        simply STOP the scheduler. Jobs operation would be performed only via GET /admin/tasks/
        """
        from globaleaks.runner import GLAsynchronous

        yield GLAsynchronous.shutdown(shutdown_threadpool=False)

        self.set_status(200)
        self.finish()

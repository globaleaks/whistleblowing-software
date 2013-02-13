# -*- coding: UTF-8
#
#   debug
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#

from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.settings import transact


class EntryCollection(BaseHandler):
    """
    D1
    Interface for dumps elements in the tables, used in debug and detailed analysis.
    """

    @transact
    def dump_models(self, store, expected):
        expected_dict = { 'itip' : InternalTip,
                          'wtip' : WhistleblowerTip,
                          'rtip' : ReceiverTip,
                          'receivers' : Receiver,
                          'comment' : Comment,
                          'file' : File,
                          'submission' : Submission,
                          'contexts' : Context }
        outputDict = {}
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        return outputDict
        if expected in ['count', 'all']:
            for key, object in expected_dict.iteritems():
                info_list = object().get_all()
                if expected == 'all':
                    outputDict[key] = info_list

                outputDict["%s_elements" % key] = len(info_list)

            self.returnData(outputDict)
            return self.prepareRetVals()

        # XXX plugins is not dumped with all or count!
        if expected == 'plugins':

            info_list = PluginManager.get_all()
            outputDict.update({expected : info_list, ("%s_elements" % expected) : len(info_list) })

            self.returnData(outputDict)
            return self.prepareRetVals()

        if expected_dict.has_key(expected):

            info_list = expected_dict[expected](store).get_all()
            outputDict.update({expected : info_list, ("%s_elements" % expected) : len(info_list) })

            self.returnData(outputDict)
            return self.prepareRetVals()

        raise InvalidInputFormat("Not acceptable '%s'" % expected)

    def get(self, what, *uriargs):
        """
        Parameters: None
        Response: Unknown
        Errors: None

        /dump/overview GET should return up to all the tables of GLBackend
        """

        return self.dump_models(what)


class TaskInstance(BaseHandler):
    """
    D2
    controls task and scheduled
    """

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

# -*- coding: UTF-8
#
#   debug 
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#

from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.models.externaltip import ReceiverTip, WhistleblowerTip, Comment, File
from globaleaks.models.options import PluginProfiles, ReceiverConfs
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.receiver import Receiver
from globaleaks.models.context import Context
from globaleaks.models.submission import Submission
from globaleaks.plugins.manager import PluginManager


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

        expected = [ 'itip', 'wtip', 'rtip', 'receivers', 'comment',
                     'profiles', 'rcfg', 'file', 'submission', 'contexts', 'plugins', 'all', 'count' ]

        outputDict = {}

        if what == 'receivers' or what == 'all' or what == 'count':
            receiver_iface = Receiver()
            receiver_list = yield receiver_iface.get_all()

            if what != 'count':
                outputDict.update({ 'receivers_elements' : len(receiver_list), 'receivers' : receiver_list})
            else:
                outputDict.update({ 'receivers_elements' : len(receiver_list)})

        if what == 'itip' or what == 'all' or what == 'count':
            itip_iface = InternalTip()
            itip_list = yield itip_iface.get_all()

            if what != 'count':
                outputDict.update({ 'internaltips_elements' : len(itip_list), 'internaltips' : itip_list })
            else:
                outputDict.update({ 'internaltips_elements' : len(itip_list)})

        if what == 'rtip' or what == 'all' or what == 'count':
            rtip_iface = ReceiverTip()
            rtip_list = yield rtip_iface.get_all()

            if what != 'count':
                outputDict.update({ 'rtip_elements' : len(rtip_list), 'receivers_tips' : rtip_list })
            else:
                outputDict.update({ 'rtip_elements' : len(rtip_list)})

        if what == 'wtip' or what == 'all' or what == 'count':
            wtip_iface = WhistleblowerTip()
            wtip_list = yield wtip_iface.get_all()

            if what != 'count':
                outputDict.update({ 'wtip_elements' : len(wtip_list), 'whistleblower_tips' : wtip_list })
            else:
                outputDict.update({ 'wtip_elements' : len(wtip_list)})

        if what == 'comment' or what == 'all' or what == 'count':
            comment_iface = Comment()
            comment_list = yield comment_iface.get_all()

            if what != 'count':
                outputDict.update({ 'comment_elements' : len(comment_list), 'comments' : comment_list })
            else:
                outputDict.update({ 'comment_elements' : len(comment_list)})

        if what == 'profiles' or what == 'all' or what == 'count':
            profile_iface = PluginProfiles()
            profile_list = yield profile_iface.get_all()

            if what != 'count':
                outputDict.update({ 'profiles_elements' : len(profile_list), 'profiles' : profile_list })
            else:
                outputDict.update({ 'profiles_elements' : len(profile_list)})

        if what == 'plugins' or what == 'all' or what == 'count':
            plugin_list = yield PluginManager.get_all()

            if what != 'count':
                outputDict.update({ 'plugins_elements' : len(plugin_list), 'plugins' : plugin_list })
            else:
                outputDict.update({ 'plugins_elements' : len(plugin_list) })

        if what == 'rcfg' or what == 'all' or what == 'count':
            rconf_iface = ReceiverConfs()
            rconf_list = yield rconf_iface.admin_get_all()

            if what != 'count':
                outputDict.update({ 'rcfg_elements' : len(rconf_list), 'settings' : rconf_list })
            else:
                outputDict.update({ 'rcfg_elements' : len(rconf_list)})

        if what == 'submission' or what == 'all' or what == 'count':
            submission_iface = Submission()
            submission_list = yield submission_iface.get_all()

            if what != 'count':
                outputDict.update({ 'submission_elements' : len(submission_list), 'submissions' : submission_list })
            else:
                outputDict.update({ 'submission_elements' : len(submission_list)})

        if what == 'file' or what == 'all' or what == 'count':
            file_iface = File()
            file_list = yield file_iface.get_all()

            if what != 'count':
                outputDict.update({ 'file_elements' : len(file_list), 'files' : file_list })
            else:
                outputDict.update({ 'file_elements' : len(file_list)})

        if what == 'contexts' or what == 'all' or what == 'count':
            context_iface = Context()
            context_list = yield context_iface.get_all()

            if what != 'count':
                outputDict.update({ 'contexts_elements' : len(context_list), 'contexts' : context_list })
            else:
                outputDict.update({ 'contexts_elements' : len(context_list)})


        if not what in expected:
            self.set_status(405)
        else:
            self.set_status(200)
            self.write(outputDict)

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
        from globaleaks.jobs.tip_sched import APSTip
        from globaleaks.jobs.delivery_sched import APSDelivery
        from globaleaks.jobs.welcome_sched import APSWelcome
        from globaleaks.jobs.cleaning_sched import APSCleaning
        from globaleaks.jobs.statistics_sched import APSStatistics
        from globaleaks.jobs.digest_sched import APSDigest

        expected = [ 'statistics', 'welcome', 'tip', 'delivery', 'notification', 'cleaning', 'digest' ]

        if what == 'statistics':
            yield APSNotification().operation()
        if what == 'welcome':
            yield APSWelcome().operation()
        if what == 'tip':
            yield APSTip().operation()
        if what == 'delivery':
            yield APSDelivery().operation()
        if what == 'notification':
            yield APSNotification().operation()
        if what == 'cleaning':
            yield APSCleaning().operation()
        if what == 'digest':
            yield APSDigest().operation()

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

        simply STOP the scheduler. Jobs operation whould be performed only via GET /admin/tasks/
        """
        from globaleaks.runner import GLAsynchronous

        yield GLAsynchronous.shutdown(shutdown_threadpool=False)

        self.set_status(200)
        self.finish()

# -*- coding: UTF-8
#
#   admin
#   *****
#
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks
import json

from globaleaks.handlers.base import BaseHandler
from globaleaks.models import node, context, receiver, options
from globaleaks.utils import log
from globaleaks.plugins.base import GLPluginManager

class NodeManagement(BaseHandler):
    """
    A1
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    This would be likely see as the starting point of the administration chain:
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNodeDescription
        Errors: None

        """
        #not yet implemented: admin_stats (stats need to be moved in contexts)
        #node_properties: should not be separate array
        #url_schema: no more needed ?
        #stats_delta couple.

        log.debug("[D] %s %s " % (__file__, __name__), "Class Admin Node", "GET")

        context_iface = context.Context()
        context_description_dicts = yield context_iface.admin_get_all()

        node_info = node.Node()
        node_description_dicts = yield node_info.get_admin_info()

        # it's obviously a madness that need to be solved
        node_description_dicts.update({"contexts": context_description_dicts})

        self.set_status(200)
        self.write(node_description_dicts)
        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Changes the node public node configuration settings
        Request: adminNodeDescription
        Response: adminNodeDescription
        Errors: InvalidInputFormat
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminNode", "POST")

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        node_info = node.Node()
        yield node_info.configure_node(request)

        # return value as GET
        yield self.get()

class ContextsAvailable(BaseHandler):
    """
    A2
    Return a list of all the available contexts, in elements
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminContextList
        Errors: None
        """
        pass


class ContextCrud(BaseHandler):
    """
    A3
    classic CRUD in the single Context resource. It
    """

    @asynchronous
    @inlineCallbacks
    def get(self, context_gus, *uriargs):
        """
        Parameters: None
        Response: adminContextDesc
        Errors: None
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "GET")

        context_iface = context.Context()

        try:
            context_description = yield context_iface.admin_get_single(context_gus)

            self.set_status(200)
            self.write(context_description)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "POST")

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.set_status(406)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        else:
            context_iface = context.Context()

            try:
                yield context_iface.update(context_gus, request)
                yield self.get(context_gus)

            except context.InvalidContext, e:

                self.set_status(e.http_status)
                self.write({'error_message': e.error_message, 'error_code' : e.error_code})
                self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ContextNotFound
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "PUT")
        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        context_iface = context.Context()

        # XXX detect which operation can fail, and eventually make an appropriate
        # exception, with the logic used in self.post
        new_context_gus = yield context_iface.new(request)

        # return value as GET
        yield self.get(new_context_gus)


    @asynchronous
    @inlineCallbacks
    def delete(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: None
        Errors: InvalidInputFormat, ContextNotFound
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContext", "DELETE", context_gus)


        context_iface = context.Context()

        # XXX just a litle consideration: if a context has some tip, jobs, whatever
        # in queue, maybe the client ask a sort of "are you really sure ?"
        # this operation is not related to this REST DELETE, but perhaps in the
        # administrative view of the contexts, also the presence|absence|description
        # of the queued operations, would be useful.

        # This DELETE operation, its fucking permanant, and kills all the Tip related
        # to the context. (not the receivers: they can be possesed also by other context,
        # but the tarGET context is DELETEd also in the receiver reference)

        try:
            yield context_iface.delete_context(context_gus)
            self.set_status(200)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ReceiversAvailable(BaseHandler):
    """
    A4
    List all available receivers present in the node.
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminReceiverList
        Errors: None
        """
        pass



class ReceiverCrud(BaseHandler):
    """
    A5
    AdminReceivers: classic CRUD in a 'receiver' resource
    A receiver can stay in more than one context, then is expected in POST/PUT
    operations a list of tarGET contexts is passed. Operation here, mostly are
    handled by models/receiver.py, and act on the administrative side of the
    receiver. a receiver performing operation in their profile, has an API
    implemented in handlers.receiver
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_gus, *uriargs):
        """
        Parameters: None
        Response: adminReceiverDesc
        Errors: None
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "GET", receiver_gus)

        receiver_iface = receiver.Receiver()

        try:
            receiver_description = yield receiver_iface.admin_get_single(receiver_gus)

            self.set_status(200)
            self.write(receiver_description)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except receiver.InvalidReceiver, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, receiver_gus, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "POST", receiver_gus)

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.

            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.set_status(400)
            self.finish()

        receiver_iface = receiver.Receiver()

        try:
            yield receiver_iface.admin_update(receiver_gus, request)

            yield self.get(receiver_gus)

        except context.InvalidContext:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})
            self.finish()

        except receiver.InvalidReceiver, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})
            self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, receiver_gus, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverNotFound
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "PUT", receiver_gus)

        request = json.loads(self.request.body)

        if not request:
            # holy fucking sick atheist god
            # no validation at the moment.
            self.write(__file__)
            self.write('error message to be managed using the appropriate format')
            self.finish()

        receiver_iface = receiver.Receiver()
        new_receiver_gus = yield receiver_iface.new(request)

        # return value as GET of the new receiver
        yield self.get(new_receiver_gus)


    @asynchronous
    @inlineCallbacks
    def delete(self, receiver_gus, *uriargs):
        """
        Request: adminReceiverDesc
        Response: None
        Errors: InvalidInputFormat, ReceiverNotFound
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "DELETE", receiver_gus)

        receiver_iface = receiver.Receiver()

        try:
            yield receiver_iface.receiver_delete(receiver_gus)
            self.set_status(200)

        except context.InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except receiver.InvalidReceiver, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

class PluginsAvailable(BaseHandler):
    """
    A6
    List all plugins available in the node (used as base resource for create profiles)
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminPluginList
        Errors: None
        """
        pass

class ProfileCrud(BaseHandler):
    """
    A7
    This class enable and configure the profiles, a profile is a plugin configuration,
    and the same plugin may have multiple
    """

    @asynchronous
    @inlineCallbacks
    def get(self, profile_gus, *uriargs):
        """
        Parameters: None
        Response: adminProfileDesc
        Errors: ProfileNotFound
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminPlugin", "GET", profile_gus)

        plugin_iface = options.PluginProfiles()

        try:
            profile_description = yield plugin_iface.admin_get_single(profile_gus)

            self.set_status(200)
            self.write(profile_description)

        except options.ProfileGusNotFoundError, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, profile_gus, *uriargs):
        """
        Request: adminProfileDesc
        Response: adminProfileDesc
        Errors: ProfileNotFound, InvalidInputFormat
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminPlugin", "POST")

        request = json.loads(self.request.body)

        # this is not the right approach, the validation would be implemented
        # correctly in short time, when can be reviewed the generation of doc and
        # validation of input/output
        if not request:
            self.write({'error_message': 'Missing request!', 'error_code' : 123})
            self.set_status(400)
            self.finish()
            # this behaviour cause an error from Cyclone

        plugin_manager = GLPluginManager()

        if not plugin_manager.plugin_exists(request['plugin_type'], request['plugin_name']):

            self.set_status(406)
            self.write({'error_message': 'Invalid plugin (type/name) requested', 'error_code' : 123 })

        else:
            # reach the GLPlugin class implementation
            plugin_code = plugin_manager.get_plugin(request['plugin_type'], request['plugin_name'])

            if plugin_code.validate_admin_opt(request['admin_fields']) and request['profile_name']:

                plugin_iface = options.PluginProfiles()

                try:
                    new_profile = yield plugin_iface.newprofile(request['plugin_type'], request['plugin_name'],
                        request['profile_name'],
                        { 'admin' : plugin_code.admin_fields, 'receiver' : plugin_code.admin_fields},
                        request['description'],  request['profile_settings'] )

                    self.set_status(200)
                    self.write({'profile_gus': new_profile})

                except options.ProfileNameConflict, e:

                    self.set_status(e.http_status)
                    self.write({'error_message': e.error_message, 'error_code' : e.error_code})

            else:
                self.set_status(406)
                self.write({'error_message':
                    'Invalid request format in Profile creation (profile name, fields content)',
                    'error_code' : 123 })

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, profile_gus, *uriargs):
        """
        Request: adminProfileDesc
        Response: adminProfileDesc
        Errors: ProfileNotFound, InvalidInputFormat
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminPlugin", "PUT", profile_gus)

        request = json.loads(self.request.body)

        if not request:
            self.write({'error_message': 'Missing request', 'error_code' : 123})
            self.set_status(400)

        else:

            plugin_manager = GLPluginManager()

            if not plugin_manager.plugin_exists(request['plugin_type'], request['plugin_name']):

                self.set_status(406)
                self.write({'error_message': 'Invalid plugin (type/name) requested', 'error_code' : 123 })

            else:

                # reach the GLPlugin class implementation
                plugin_code = plugin_manager.get_plugin(request['plugin_type'], request['plugin_name'])

                new_settings = request['admin_fields'] if request['admin_fields'] else None
                new_name = request['profile_name'] if request['profile_name']  else None
                new_desc = request['description'] if request['description'] else None

                if not plugin_code.validate_admin_opt(new_settings):
                    self.set_status(406)
                    self.write({'error_message':
                                    'Invalid request format in Profile creation (fields content)',
                                'error_code' : 123 })
                else:

                    plugin_iface = options.PluginProfiles()

                    try:
                        yield plugin_iface.update_profile(profile_gus, settings=new_settings, desc=new_desc, profname=new_name)

                        self.set_status(200)

                    except options.ProfileNameConflict, e:

                        self.set_status(e.http_status)
                        self.write({'error_message': e.error_message, 'error_code' : e.error_code})

                    except options.ProfileGusNotFoundError, e:

                        self.set_status(e.http_status)
                        self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, profile_gus, *uriargs):
        """
        Request: adminProfileDesc
        Response: None
        Errors: ProfileNotFound, InvalidInputFormat
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminPlugin -- NOT YET IMPLEMENTED -- ", "DELETE")


class StatisticsAvailable(BaseHandler):
    """
    A8
    Return all administrative statistics of the node.
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminStatsList
        Errors: None
        """
        pass


class EntryAvailable(BaseHandler):
    """
    A9
    Interface for dumps elements in the tables, used in debug and detailed analysis.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, what, *uriargs):
        """
        Parameters: None
        Response: Unknown
        Errors: None

        /admin/overview GET should return up to all the tables of GLBackend
        """
        from globaleaks.models.externaltip import ReceiverTip, WhistleblowerTip, Comment
        from globaleaks.models.options import PluginProfiles, ReceiverConfs
        from globaleaks.models.internaltip import InternalTip
        from globaleaks.models.receiver import Receiver

        expected = [ 'itip', 'wtip', 'rtip', 'receivers', 'comment', 'profiles', 'rcfg', 'all' ]

        if what == 'receivers' or what == 'all':
            receiver_iface = Receiver()
            receiver_list = yield receiver_iface.admin_get_all()
            self.write({ 'elements' : len(receiver_list), 'receivers' : receiver_list})

        if what == 'itip' or what == 'all':
            itip_iface = InternalTip()
            itip_list = yield itip_iface.admin_get_all()
            self.write({ 'elements' : len(itip_list), 'internaltips' : itip_list })

        if what == 'rtip' or what == 'all':
            rtip_iface = ReceiverTip()
            rtip_list = yield rtip_iface.admin_get_all()
            self.write({ 'elements' : len(rtip_list), 'receivers_tips' : rtip_list })

        if what == 'wtip' or what == 'all':
            wtip_iface = WhistleblowerTip()
            wtip_list = yield wtip_iface.admin_get_all()
            self.write({ 'elements' : len(wtip_list), 'whistleblower_tips' : wtip_list })

        if what == 'comment' or what == 'all':
            comment_iface = Comment()
            comment_list = yield comment_iface.admin_get_all()
            self.write({ 'elements' : len(comment_list), 'comments' : comment_list })

        if what == 'profiles' or what == 'all':
            profile_iface = PluginProfiles()
            profile_list = yield profile_iface.admin_get_all()
            self.write({ 'elements' : len(profile_list), 'profiles' : profile_list })

        if what == 'rcfg' or what == 'all':
            rconf_iface = ReceiverConfs()
            rconf_list = yield rconf_iface.admin_get_all()
            self.write({ 'elements' : len(rconf_list), 'settings' : rconf_list })


        if not what in expected:
            self.set_status(405)
        else:
            self.set_status(200)

        self.finish()


class TaskManagement(BaseHandler):
    """
    A0
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

        log.debug("[D] manual execution of scheduled operation (%s)" % what)

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
        log.debug("[D] stopped scheduled operations queue")

        self.set_status(200)
        self.finish()

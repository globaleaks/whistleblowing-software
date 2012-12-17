# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#

from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks
import json

from globaleaks.handlers.base import BaseHandler
from globaleaks.models import node, context, receiver, options
from globaleaks.utils import log
from globaleaks.plugins.base import GLPluginManager
from globaleaks.rest.errors import ContextGusNotFound, ReceiverGusNotFound,\
    NodeNotFound, InvalidInputFormat, ProfileGusNotFound, ProfileNameConflict
from globaleaks.rest.base import validateMessage
from globaleaks.rest import requests

class NodeInstance(BaseHandler):
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
        Response: adminNodeDesc
        Errors: NodeNotFound
        """

        #not yet implemented: admin_stats (stats need to be moved in contexts)
        #node_properties: should not be separate array
        #url_schema: no more needed ?
        #stats_delta couple.


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
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings
        """

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


class ContextsCollection(BaseHandler):
    """
    A2
    Return a list of all the available contexts, in elements
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminContextList
        Errors: None
        """

        context_iface = context.Context()
        all_contexts = yield context_iface.admin_get_all()

        self.set_status(200)
        # TODO output filter would include JSON inside of the method
        self.write(json.dumps(all_contexts))
        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat
        """

        context_iface = context.Context()
        try:

            request = validateMessage(self.request.body, requests.adminContextDesc)
            new_context_gus = yield context_iface.new(request)

            context_description = yield context_iface.admin_get_single(new_context_gus)

            self.set_status(201) # Created
            self.write(context_description)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ContextInstance(BaseHandler):
    """
    A3
    classic CRUD in the single Context resource. It
    """

    @asynchronous
    @inlineCallbacks
    def get(self, context_gus, *uriargs):
        """
        Parameters: context_gus
        Response: adminContextDesc
        Errors: ContextGusNotFound, InvalidInputFormat
        """

        try:
            # TODO REMIND XXX - context_gus validation - InvalidInputFormat
            context_iface = context.Context()
            context_description = yield context_iface.admin_get_single(context_gus)

            self.set_status(200)
            self.write(context_description)

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def put(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ContextGusNotFound
        """

        try:
            request = validateMessage(self.request.body, requests.adminContextDesc)

            context_iface = context.Context()

            yield context_iface.update(context_gus, request)
            context_description = yield context_iface.admin_get_single(context_gus)

            self.set_status(200)
            self.write(context_description)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def delete(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: None
        Errors: InvalidInputFormat, ContextGusNotFound
        """

        context_iface = context.Context()

        # XXX just a litle consideration: if a context has some tip, jobs, whatever
        # in queue, maybe the client ask a sort of "are you really sure ?"
        # this operation is not related to this REST DELETE, but perhaps in the
        # administrative view of the contexts, also the presence|absence|description
        # of the queued operations, would be useful.

        # This DELETE operation, its fucking permanent, and kills all the Tip related
        # to the context. (not the receivers: they can be possesed also by other context,
        # but the tarGET context is DELETEd also in the receiver reference)

        # TODO REMIND XXX - context_gus validation
        try:
            yield context_iface.delete_context(context_gus)
            self.set_status(200)

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ReceiversCollection(BaseHandler):
    """
    A4
    List all available receivers present in the node.
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminReceiverList
        Errors: None

        Admin operation: return all the receiver present in the Node
        """

        receiver_iface = receiver.Receiver()
        all_receivers = yield receiver_iface.admin_get_all()

        self.set_status(200)
        # TODO output filter would include JSON inside of the method
        self.write(json.dumps(all_receivers))
        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat

        Create a new receiver,
        """

        try:
            request = validateMessage(self.request.body, requests.adminReceiverDesc)

            receiver_iface = receiver.Receiver()
            new_receiver_gus = yield receiver_iface.new(request)

            new_receiver_desc = yield receiver_iface.admin_get_single(new_receiver_gus)

            self.set_status(201) # Created
            self.write(new_receiver_desc)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ReceiverInstance(BaseHandler):
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
        Parameters: receiver_gus
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound

        Get an existent Receiver instance.
        """

        try:

            # TODO parameter validation - InvalidInputFormat
            receiver_iface = receiver.Receiver()

            receiver_description = yield receiver_iface.admin_get_single(receiver_gus)

            self.set_status(200)
            self.write(receiver_description)

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, receiver_gus, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound

        Update information about a Receiver, return the instance updated.
        """

        try:
            # TODO parameter validation - InvalidInputFormat
            request = validateMessage(self.request.body, requests.adminReceiverDesc)

            receiver_iface = receiver.Receiver()

            yield receiver_iface.admin_update(receiver_gus, request)

            receiver_description = yield receiver_iface.admin_get_single(receiver_gus)
            self.set_status(200)
            self.write(receiver_description)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, receiver_gus, *uriargs):
        """
        Parameter: receiver_gus
        Request: None
        Response: None
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """

        receiver_iface = receiver.Receiver()

        try:
            # TODO parameter validation - InvalidInputFormat
            yield receiver_iface.receiver_delete(receiver_gus)
            self.set_status(200)

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


# BELOW ARE TO BE REFACTORED WITH THE NEW API

class PluginCollection(BaseHandler):
    """
    A6
    Return the list of all pluging (python file containing a self contained name, with an
    univoque name) available on the system.
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminPluginList
        Errors: None
        """
        pass


class ProfileCollection(BaseHandler):
    """
    A7
    Return the list of all profiles configured based on the selected plugin name

    GET|POST /admin/plugin/<plugin_name>/profile
    """

    def get(self, plugin_name, *uriargs):
        """
        Parameters: None
        Response: adminProfileList
        Errors: PluginNameNotFound
        """
        pass

    @asynchronous
    @inlineCallbacks
    def post(self, plugin_name, *uriargs):
        """
        Request: adminProfileDesc
        Response: adminProfileDesc
        Errors: ProfileGusNotFound, InvalidInputFormat, ProfileNameConflict, PluginNameNotFound
        """


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

                except ProfileNameConflict, e:

                    self.set_status(e.http_status)
                    self.write({'error_message': e.error_message, 'error_code' : e.error_code})

            else:
                self.set_status(406)
                self.write({'error_message':
                                'Invalid request format in Profile creation (profile name, fields content)',
                            'error_code' : 123 })

        self.finish()



class ProfileInstance(BaseHandler):
    """
    A8
    This class enable and configure the profiles, a profile is a plugin configuration,
    and the same plugin may have multiple
    """

    @asynchronous
    @inlineCallbacks
    def get(self, plugin_name, profile_gus, *uriargs):
        """
        Parameters: profile_gus
        Response: adminProfileDesc
        Errors: ProfileGusNotFound
        """

        plugin_iface = options.PluginProfiles()

        try:
            profile_description = yield plugin_iface.admin_get_single(profile_gus)

            self.set_status(200)
            self.write(profile_description)

        except ProfileGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def put(self, plugin_name, profile_gus, *uriargs):
        """
        Request: adminProfileDesc
        Response: adminProfileDesc
        Errors: ProfileGusNotFound, InvalidInputFormat, ProfileNameConflict
        """

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

                    except ProfileNameConflict, e:

                        self.set_status(e.http_status)
                        self.write({'error_message': e.error_message, 'error_code' : e.error_code})

                    except ProfileGusNotFound, e:

                        self.set_status(e.http_status)
                        self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, profile_gus, *uriargs):
        """
        Request: adminProfileDesc
        Response: None
        Errors: ProfileGusNotFound, InvalidInputFormat
        """


class StatisticsCollection(BaseHandler):
    """
    A9
    Return all administrative statistics of the node.
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminStatsList
        Errors: None
        """
        pass


class EntryCollection(BaseHandler):
    """
    AA
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


class TaskInstance(BaseHandler):
    """
    AB
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

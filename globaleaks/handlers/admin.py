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
from globaleaks.models.externaltip import ReceiverTip, WhistleblowerTip, Comment, File
from globaleaks.models.options import PluginProfiles, ReceiverConfs
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.receiver import Receiver
from globaleaks.models.context import Context
from globaleaks.models.node import Node
from globaleaks.models.submission import Submission

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

        try:
            node_info = Node()
            node_description_dicts = yield node_info.get_admin_info()

            self.set_status(200)
            self.write(node_description_dicts)

        except NodeNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def put(self, *uriargs):
        """
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings
        """

        try:
            request = validateMessage(self.request.body, requests.adminContextDesc)

            node_info = Node()
            yield node_info.configure_node(request)
            node_description_dicts = yield node_info.get_admin_info()

            self.set_status(201) # Created
            self.write(node_description_dicts)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


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

        context_iface = Context()
        all_contexts = yield context_iface.get_all()

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
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """

        try:
            request = validateMessage(self.request.body, requests.adminContextDesc)

            context_iface = Context()
            new_context_gus = yield context_iface.new(request)

            # 'receivers' it's a relationship between two tables, and is managed 
            # with a separate method of new()
            receiver_iface = Receiver()
            yield context_iface.context_align(new_context_gus, request['receivers'])
            yield receiver_iface.full_receiver_align(new_context_gus, request['receivers'])

            context_description = yield context_iface.get_single(new_context_gus)

            self.set_status(201) # Created
            self.write(context_description)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError, e: # Until validateMessage is not restored, it's needed.

            self.set_status(511)
            self.write({'error_message': "temporary error: %s" % e, 'error_code' : 123})

        self.finish()


class ContextInstance(BaseHandler):
    """
    A3
    classic CRUD in the single Context resource.
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
            context_iface = Context()
            context_description = yield context_iface.get_single(context_gus)

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
        Errors: InvalidInputFormat, ContextGusNotFound, ReceiverGusNotFound
        """

        try:
            request = validateMessage(self.request.body, requests.adminContextDesc)

            context_iface = Context()
            yield context_iface.update(context_gus, request)

            # 'receivers' it's a relationship between two tables, and is managed 
            # with a separate method of new()
            receiver_iface = Receiver()
            yield context_iface.context_align(context_gus, request['receivers'])
            yield receiver_iface.full_receiver_align(context_gus, request['receivers'])

            context_description = yield context_iface.get_single(context_gus)

            self.set_status(200)
            self.write(context_description)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError, e: # Until validateMessage is not restored, it's needed.

            self.set_status(511)
            self.write({'error_message': "temporary error: %s" % e, 'error_code' : 123})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def delete(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: None
        Errors: InvalidInputFormat, ContextGusNotFound
        """

        context_iface = Context()
        receivertip_iface = ReceiverTip()
        internaltip_iface = InternalTip()
        whistlebtip_iface = WhistleblowerTip()
        comment_iface = Comment()
        receiver_iface = Receiver()
        file_iface = File()

        # This DELETE operation, its permanent, and remove all the reference
        # a Context has within the system (in example: remove associated Tip,
        # remove

        try:

            context_desc = yield context_iface.get_single(context_gus)

            tips_related_blocks = yield receivertip_iface.get_tips_by_context(context_gus)

            print "Tip that need to be deleted, associated with the context",\
                context_gus, ":", len(tips_related_blocks)

            for tip_block in tips_related_blocks:

                internaltip_id = tip_block.get('internaltip')['internaltip_id']

                yield whistlebtip_iface.delete_access_by_itip(internaltip_id)
                yield receivertip_iface.massive_delete(internaltip_id)
                yield comment_iface.delete_comment_by_itip(internaltip_id)
                yield file_iface.delete_file_by_itip(internaltip_id)

                # and finally, delete the InternalTip
                yield internaltip_iface.tip_delete(internaltip_id)


            # (Just consistency check)
            receivers_associated = yield receiver_iface.get_receivers_by_context(context_gus)
            print "receiver associated by context POV:", len(receivers_associated),\
                "receiver associated by context DB-field:", len(context_desc['receivers'])

            # Align all the receiver associated to the context, that the context cease to exist
            yield receiver_iface.align_context_delete(context_desc['receivers'], context_gus)

            # TODO delete stats associated with context ?
            # TODO delete profile associated with the context

            # Finally, delete the context
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

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminReceiverList
        Errors: None

        Admin operation: return all the receiver present in the Node
        """

        receiver_iface = Receiver()
        all_receivers = yield receiver_iface.get_all()

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
        Errors: InvalidInputFormat, ContextGusNotFound

        Create a new receiver
        """

        try:
            request = validateMessage(self.request.body, requests.adminReceiverDesc)

            receiver_iface = Receiver()

            new_receiver_gus = yield receiver_iface.new(request)

            # 'contexts' it's a relationship between two tables, and is managed 
            # with a separate method of new()
            context_iface = Context()
            yield receiver_iface.receiver_align(new_receiver_gus, request['contexts'])
            yield context_iface.full_context_align(new_receiver_gus, request['contexts'])

            new_receiver_desc = yield receiver_iface.get_single(new_receiver_gus)

            self.set_status(201) # Created
            self.write(new_receiver_desc)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError, e: # Until validateMessage is not restored, it's needed.

            self.set_status(511)
            self.write({'error_message': "temporary error: %s" % e, 'error_code' : 123})

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
            receiver_iface = Receiver()

            receiver_description = yield receiver_iface.get_single(receiver_gus)

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
        Errors: InvalidInputFormat, ReceiverGusNotFound, ContextGus

        Update information about a Receiver, return the instance updated.
        """

        try:
            # TODO parameter validation - InvalidInputFormat
            request = validateMessage(self.request.body, requests.adminReceiverDesc)

            receiver_iface = Receiver()

            yield receiver_iface.admin_update(receiver_gus, request)

            # 'contexts' it's a relationship between two tables, and is managed 
            # with a separate method of new()
            context_iface = Context()
            yield receiver_iface.receiver_align(receiver_gus, request['contexts'])
            yield context_iface.full_context_align(receiver_gus, request['contexts'])

            receiver_description = yield receiver_iface.get_single(receiver_gus)

            self.set_status(200)
            self.write(receiver_description)

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError, e: # Until validateMessage is not restored, it's needed.

            self.set_status(511)
            self.write({'error_message': "temporary error: %s" % e, 'error_code' : 123})

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

        receiver_iface = Receiver()
        receivertip_iface = ReceiverTip()
        context_iface = Context()

        try:
            # TODO parameter receiver_gus validation - InvalidInputFormat
            receiver_desc = yield receiver_iface.get_single(receiver_gus)

            # Remove Tip possessed by the receiver
            related_tips = yield receivertip_iface.get_tips_by_receiver(receiver_gus)
            for tip in related_tips:
                yield receivertip_iface.personal_delete(tip['tip_gus'])
            # Remind: the comment are kept, and the name is not referenced but stored
            # in the comment entry.


            # Consistency checks between receiver and context tracking:
            contexts_associated = yield context_iface.get_contexts_by_receiver(receiver_gus)

            print "context associated by receiver POV:", len(contexts_associated),\
                "context associated by receiver-DB field:", len(receiver_desc['contexts'])

            yield context_iface.align_receiver_delete(receiver_desc['contexts'], receiver_gus)

            # TODO delete ReceiverConfs settings related.

            # Finally delete the receiver
            yield receiver_iface.receiver_delete(receiver_gus)
            self.set_status(200)

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


# _______________________________________
# BELOW TO BE REFACTORED WITH THE NEW API
# _______________________________________
# BELOW TO BE REFACTORED WITH THE NEW API
# _______________________________________

class PluginCollection(BaseHandler):
    """
    A6
    Return the list of all pluging (python file containing a self contained name, with an
    univoque name) available on the system.
    """

    @asynchronous
    @inlineCallbacks
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

    @asynchronous
    @inlineCallbacks
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

                plugin_iface = PluginProfiles()

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

        plugin_iface = PluginProfiles()

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

                    plugin_iface = PluginProfiles()

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

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminStatsList
        Errors: None
        """
        pass

# _______________________________________
# BEFORE NEED TO BE REFACTORED WITH THE NEW API
# _______________________________________
# BEFORE NEED TO BE REFACTORED WITH THE NEW API
# _______________________________________


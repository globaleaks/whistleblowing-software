# -*- coding: UTF-8
#
#   models/options
#   **************
#
# Options contain the plugin preferences settings. Is divided in two classes:
#
#  Admin preferences: from a single plugin are create one or more profile, stored here
#  Receiver preferences: from the available profiles, each receiver configured their settings
#

from storm.twisted.transact import transact
from storm.exceptions import NotOneError
from storm.locals import Int, Pickle, Unicode, Bool, DateTime
from storm.locals import Reference

from globaleaks.utils import idops, log, gltime
from globaleaks.models.base import TXModel
from globaleaks.models.receiver import Receiver
from globaleaks.models.context import Context
from globaleaks.rest.errors import ProfileGusNotFound, ProfileNameConflict, ReceiverConfNotFound,\
    InvalidInputFormat, ReceiverGusNotFound, ContextGusNotFound
from globaleaks.plugins.manager import PluginManager

__all__ = [ 'PluginProfiles', 'ReceiverConfs' ]

valid_plugin_types = [ u'notification', u'delivery', u'fileprocess' ]

class PluginProfiles(TXModel):
    """
    Every plugin has a series of settings, and a Node MAY have multiple
    profiles for every plugin. This table describe those profile. A profile
    can be accessed by Admin API (A4) and assigned/deassigned to a context,
    of from the /admin/context interface.
    """
    __storm_table__ = 'pluginprofiles'

    profile_gus = Unicode(primary=True)

    # These fields are assigned at creation time and can't be changed:
    plugin_type = Unicode()
    plugin_name = Unicode()
    plugin_description = Unicode()

    # admin_fields contain a copy of the Plugins requested fields and type
    admin_fields = Pickle()
    # admin_settings contain a key-value dictionary with the compiled information
    admin_settings = Pickle()

    # That's are not _settings, just a copy of the receiver_fields, that would be
    # printed between the resource information, or eventually be modified in
    # description by Administrator (feature not implemented nor requested)
    receiver_fields = Pickle()

    creation_time = DateTime()

    profile_description = Unicode()

    # It's checked to be unique, just to avoid Receiver mistake
    profile_name = Unicode()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)


    @transact
    def new(self, profile_dict):
        """
        @profile_dict need to contain the keys: 'plugin_type', 'plugin_name',
            'admin_settings',
        """

        store = self.getStore()
        newone = PluginProfiles()

        try:

            # below, before _import_dict, are checked profile_type, and plugin_name
            # both of them can't be updated, are chosen at creation time,

            if not unicode(profile_dict['plugin_type']) in valid_plugin_types:
                raise InvalidInputFormat("plugin_type not recognized")

            if not PluginManager.plugin_exists(profile_dict['plugin_name']):
                raise InvalidInputFormat("plugin_name not recognized between available plugins")

            newone._import_dict(profile_dict)

            # the name can be updated, but need to be checked to be UNIQUE
            if store.find(PluginProfiles, PluginProfiles.profile_name == newone.profile_name).count() >= 1:
                raise ProfileNameConflict

            plugin_info = PluginManager.get_plugin(profile_dict['plugin_name'])

            # initialize the three plugin_* fields, inherit by Plugin code
            newone.plugin_name = unicode(plugin_info['plugin_name'])
            newone.plugin_type = unicode(plugin_info['plugin_type'])
            newone.plugin_description = unicode(plugin_info['plugin_description'])
            newone.admin_fields = dict(plugin_info['admin_fields'])

            # Admin-only plugins are listed here, and they have not receiver_fields
            if newone.plugin_type in [ u'fileprocess' ]:
                newone.receiver_fields = []
            else:
                newone.receiver_fields = plugin_info['receiver_fields']

        except KeyError, e:
            raise InvalidInputFormat("Profile creation failed (missing %s)" % e)

        except TypeError, e:
            raise InvalidInputFormat("Profile creation failed (wrong %s)" % e)

        newone.profile_gus = idops.random_plugin_gus()
        newone.creation_time = gltime.utcTimeNow()

        store.add(newone)

        # build return value for the handler
        return newone._description_dict()


    @transact
    def update(self, profile_gus, profile_dict):

        store = self.getStore()

        try:
            looked_p = store.find(PluginProfiles, PluginProfiles.profile_gus == profile_gus).one()
        except NotOneError:
            raise ProfileGusNotFound
        if not looked_p:
            raise ProfileGusNotFound

        try:
            looked_p._import_dict(profile_dict)

            # the name can be updated, but need to be checked to be UNIQUE
            if store.find(PluginProfiles, PluginProfiles.profile_name == looked_p.profile_name).count() >= 1:
                raise ProfileNameConflict

        except KeyError, e:
            raise InvalidInputFormat("Profile update failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("Profile update failed (wrong %s)" % e)

        # build return value for the handler
        return looked_p._description_dict()

    @transact
    def delete_profile(self, profile_gus):

        store = self.getStore()

        try:
            looked_p = store.find(PluginProfiles, PluginProfiles.profile_gus == profile_gus).one()
        except NotOneError:
            raise ProfileGusNotFound
        if not looked_p:
            raise ProfileGusNotFound

        store.remove(looked_p)

    @transact
    def get_all(self):

        store = self.getStore()

        selected_plugins = store.find(PluginProfiles)

        retVal = []
        for single_p in selected_plugins:
            retVal.append(single_p._description_dict())

        return retVal


    @transact
    def get_single(self, profile_gus):

        store = self.getStore()

        try:
            looked_p = store.find(PluginProfiles, PluginProfiles.profile_gus == profile_gus).one()
        except NotOneError:
            raise ProfileGusNotFound
        if not looked_p:
            raise ProfileGusNotFound

        retVal = looked_p._description_dict()
        return retVal


    @transact
    def get_profiles_by_contexts(self, contexts):
        """
        From a contexts list return a list of profiles referenced
        """
        store = self.getStore()

        retList = []

        for cntx_gus in contexts:
            profiles = store.find(PluginProfiles, PluginProfiles.context_gus == unicode(cntx_gus))

            for p in profiles:
                retList.append(p._description_dict())

        return retList


    def _import_dict(self, received_dict):

        # TODO perform fields validation like in submission
        self.admin_settings = dict(received_dict['admin_settings'])

        self.profile_name = received_dict['profile_name']
        self.profile_description = received_dict['profile_description']
        self.context_gus = received_dict['context_gus']


    def _description_dict(self):

        retVal = {
            'plugin_name' : unicode(self.plugin_name),
            'plugin_type': unicode(self.plugin_type),
            'plugin_description' : unicode(self.plugin_description),
            'context_gus' : unicode(self.context_gus),
            'profile_gus' : unicode(self.profile_gus),
            'profile_name' : unicode(self.profile_name),
            'profile_description' : unicode(self.profile_description),
            'creation_time' : unicode(gltime.prettyDateTime(self.creation_time)),
            'admin_fields' : dict(self.admin_fields),
            'admin_settings' : dict(self.admin_settings),
            'receiver_fields' : dict(self.receiver_fields)
        }

        return dict(retVal)



class ReceiverConfs(TXModel):
    """
    ReceiverConfs table, collect the various receivers configuration. A receiver may have multiple
    settings, some active and some not, but all the settings need to be related to a specific
    PluginProfile. A ReceiverConf is applied to all the contexts which the profile is configured.
    """

    __storm_table__ = 'receiverconfs'
    id = Int(primary=True, default=AutoReload)

    creator_receiver = Unicode()

    profile_gus = Unicode()
    profile = Reference(profile_gus, PluginProfiles.profile_gus)
    plugin_type = Unicode()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    active = Bool()
    receiver_settings = Pickle()

    creation_time = DateTime()
    last_update = DateTime()


    @transact
    def new(self, creator_receiver, init_request):

        store = self.getStore()

        newcfg = ReceiverConfs()

        try:
            newcfg._import_dict(init_request)
        except KeyError, e:
            raise InvalidInputFormat("initialization failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("initialization failed (wrong %s)" % e)

        # align reference - receiver is a trusted information, because handler has detect them
        try:
            c_receiver = store.find(Receiver, Receiver.receiver_gus == creator_receiver).one()

        except NotOneError:
            raise ReceiverGusNotFound
        if c_receiver is None:
            raise ReceiverGusNotFound

        newcfg.creator_receiver = c_receiver.receiver_gus

        try:
            newcfg.profile_gus = unicode(init_request['profile_gus'])
            newcfg.profile = store.find(PluginProfiles, PluginProfiles.profile_gus == unicode(init_request['profile_gus'])).one()
        except NotOneError:
            raise ProfileGusNotFound
        if newcfg.profile is None:
            raise ProfileGusNotFound

        try:
            newcfg.context_gus = unicode(init_request['context_gus'])
            newcfg.context = store.find(Context, Context.context_gus == unicode(init_request['context_gus'])).one()
        except NotOneError:
            raise ContextGusNotFound
        if newcfg.context is None:
            raise ContextGusNotFound

        if newcfg.context_gus != newcfg.profile.context_gus:
            raise InvalidInputFormat("Context and Profile do not fit")

        if newcfg.creator_receiver not in newcfg.context.receivers:
            raise InvalidInputFormat("Receiver and Context do not fit")

        # TODO check in a strongest way if newcfg.receiver_setting fit with newcfg.profile.receiver_fields
        key_expectation_fail = None
        for expected_k in newcfg.profile.receiver_fields.iterkeys():
            if not newcfg.receiver_settings.has_key(expected_k):
                key_expectation_fail = expected_k
                break

        if key_expectation_fail:
            raise InvalidInputFormat("Expected field %s" % key_expectation_fail)
        # End of temporary check: why I'm not put the raise exception inside
        # of the for+if ? because otherwise Storm results locked in the future operations :(

        newcfg.plugin_type = newcfg.profile.plugin_type
        newcfg.creation_time = gltime.utcTimeNow()
        newcfg.last_update = gltime.utcTimeNow()

        store.add(newcfg)

        return newcfg._description_dict()


    @transact
    def update(self, conf_id, receiver_authorized, received_dict):

        store = self.getStore()

        try:
            looked_cfg = store.find(ReceiverConfs, ReceiverConfs.id == int(conf_id)).one()
        except NotOneError:
            raise ReceiverConfNotFound
        if not looked_cfg:
            raise ReceiverConfNotFound

        try:
            looked_cfg._import_dict(received_dict)
        except KeyError, e:
            raise InvalidInputFormat("configuration update failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("configuration update failed (wrong %s)" % e)

        # profile, context and receiver can't be changed by an update.
        # context_gus and profile_gus are ignored in the dict, but the receiver is detected
        # by the Tip auth token, than need to be verified before complete the update

        if unicode(receiver_authorized) != looked_cfg.creator_receiver:
            raise InvalidInputFormat("Invalid config_id requested")

        looked_cfg.last_update = gltime.utcTimeNow()
        return looked_cfg._description_dict()


    @transact
    def get_active_conf(self, receiver_gus, context_gus, requested_type):

        store = self.getStore()

        try:
            wanted = store.find(ReceiverConfs, ReceiverConfs.creator_receiver == unicode(receiver_gus),
                ReceiverConfs.context_gus == unicode(context_gus),
                ReceiverConfs.plugin_type == unicode(requested_type),
                ReceiverConfs.active == True).one()

            if not wanted:
                return None

            return wanted._description_dict()

        except NotOneError:
            Exception("Something is gone really bad: please debug")


    @transact
    def deactivate_all_but(self, keep_id, context_gus, receiver_gus, plugin_type):
        """
        @param keep_id: the ReceiverConfs.id that has to be kept as 'active'
        @param context_gus: part of the combo
        @param receiver_gus: part of the combo
        @param plugin_type: part of the combo
        @return: None or exception
        """
        store = self.getStore()

        active = store.find(ReceiverConfs, ReceiverConfs.creator_receiver == unicode(receiver_gus),
            ReceiverConfs.context_gus == unicode(context_gus),
            ReceiverConfs.active == True,
            ReceiverConfs.plugin_type == unicode(plugin_type))

        deactivate_count = 0
        for cfg in active:
            if cfg.id == keep_id:
                continue

            deactivate_count += 1
            cfg.active = False

        # just lazy debug
        print "deactivated", deactivate_count, "configuration associated with", context_gus, receiver_gus, plugin_type


    @transact
    def delete(self, conf_id, receiver_gus):
        """
        @param conf_id: configuration id that need to be deleted
        @param receiver_gus: receiver authenticated
        @return: None or Exception
        """
        store = self.getStore()

        requested = store.find(ReceiverConfs, ReceiverConfs.id == int(conf_id)).one()
        if requested == None:
            raise ReceiverConfNotFound

        if requested.creator_receiver != unicode(receiver_gus):
            raise InvalidInputFormat("Requested configuration is not in the Receiver possession")

        store.remove(requested)
        # App log
        # TODO, if requested was the active configuration, write a remind via system message for the user


    @transact
    def deactivate_by_context(self, context_gus):
        """
        @param context_gus: a context_gus removed
        @return: the number of deactivated receiver confs
        """
        pass

    @transact
    def remove_by_receiver(self, receiver_gus):
        """
        @param receiver_gus: the receiver deleted
        @return: the number of the ReceiverConf delete, previously associated with the receiver
        """
        pass

    @transact
    def remove_by_profile(self, profile_gus):
        """
        @param profile_gus: a profile that has to be deleted
        @return: the number of receiver configuration related
        """
        pass

    @transact
    def get_all(self):

        store = self.getStore()

        configurations = store.find(ReceiverConfs)

        retVal = []
        for single_c in configurations:
            retVal.append(single_c._description_dict())

        return retVal


    @transact
    def get_single(self, conf_id):

        store = self.getStore()

        try:
            requested_cfg = store.find(ReceiverConfs, ReceiverConfs.id == int(conf_id)).one()
        except NotOneError:
            raise ReceiverConfNotFound
        if requested_cfg is None:
            raise ReceiverConfNotFound

        return requested_cfg._description_dict()


    @transact
    def get_confs_by_receiver(self, receiver_gus):
        """
        @param receiver_gus: a single receiver_gus
        @return:
        """

        store = self.getStore()

        related_confs = store.find(ReceiverConfs, ReceiverConfs.creator_receiver == unicode(receiver_gus))

        retVal = []
        for single_c in related_confs:
            retVal.append(single_c._description_dict())

        return retVal


    def _import_dict(self, received_dict):

        # TODO validate the dict with profile.receiver_fields
        self.receiver_settings = received_dict['receiver_settings']
        self.active = received_dict['active']


    def _description_dict(self):

        retVal = {
            'active' : bool(self.active),
            'config_id' : int(self.id),
            'receiver_settings' : dict(self.receiver_settings),
            'receiver_gus' : unicode(self.creator_receiver),
            'context_gus' : unicode(self.context_gus),
            'profile_gus' : unicode(self.profile_gus),
            'plugin_type' : unicode(self.plugin_type),
            'creation_time' : unicode(gltime.prettyDateTime(self.creation_time)),
            'last_update' : unicode(gltime.prettyDateTime(self.last_update)),
        }

        return dict(retVal)

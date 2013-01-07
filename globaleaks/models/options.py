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
from globaleaks.rest.errors import ProfileGusNotFound, ProfileNameConflict, ReceiverConfNotFound, InvalidInputFormat
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

    # These fields are assigned at creation time and can't be changed:
    plugin_type = Unicode()
    plugin_name = Unicode()
    plugin_description = Unicode()

    profile_gus = Unicode(primary=True)

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
    id = Int(primary=True)

    receiver_gus = Unicode()
    receiver = Reference(receiver_gus, Receiver.receiver_gus)

    receiver_fields = Pickle()
    profile_gus = Unicode()
    profile = Reference(profile_gus, PluginProfiles.profile_gus)
    active = Bool()

    @transact
    def newconf(self, receiver_gus, profile_gus, settings, active):
        """
        @param receiver_gus: receiver unique identifier, already authenticated by the caller
        @param profile_gus: every ReceiverConfs Reference a PluginProfile
        @param settings: the receiver options
        @param active: True or False
        @return: None
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverConfs", "newconf")

        store = self.getStore()

        newone = ReceiverConfs()
        newone.receiver_gus = receiver_gus
        newone.receiver_fields = settings
        newone.profile_gus = profile_gus
        newone.active = active

        store.add(newone)

    @transact
    def updateconf(self, conf_id, settings, active):
        """
        @param conf_id:
            receiver_secret, receiver_gus and conf_id are required to authenticate and address
            correctly the configuration. without those three elements, it not permitted
            change a Receiver plugin configuration.
        @param settings: the receiver_fields
        @param active:
        @return:
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverConfs", "updateconf", conf_id)

        store = self.getStore()

        try:
            looked_c = store.find(ReceiverConfs, ReceiverConfs.id == conf_id).one()
        except NotOneError:
            raise ReceiverConfInvalid
        if not looked_c:
            raise ReceiverConfInvalid

        looked_c.receiver_fields = settings
        looked_c.active = active

    @transact
    def admin_get_all(self):

        log.debug("[D] %s %s " % (__file__, __name__), "ReceiverConfs admin_get_all")
        store = self.getStore()

        configurations = store.find(ReceiverConfs)

        retVal = []
        for single_c in configurations:
            retVal.append(single_c._description_dict())

        return retVal

    @transact
    def receiver_get_all(self, receiver_gus):

        log.debug("[D] %s %s " % (__file__, __name__), "ReceiverConfs receiver_get_all", receiver_gus)
        store = self.getStore()

        related_confs = store.find(ReceiverConfs, ReceiverConfs.receiver_gus == receiver_gus)

        retVal = []
        for single_c in related_confs:
            retVal.append(single_c._description_dict())

        return retVal

    def _description_dict(self):

        retVal = {
            'receiver_gus' : unicode(self.receiver_gus),
            'active' : bool(self.active),
            'config_id' : unicode(self.id),
            'receiver_fields' : list(self.receiver_fields),
            'profile_gus' : unicode(self.profile_gus)
        }
        return retVal

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
from globaleaks.rest.errors import ProfileGusNotFound, ProfileNameConflict

__all__ = [ 'PluginProfiles', 'ReceiverConfs' ]


class PluginProfiles(TXModel):
    """
    Every plugin has a series of settings, and a Node MAY have multiple
    profiles for every plugin. This table describe those profile. A profile
    can be accessed by Admin API (A4) and assigned/deassigned to a context,
    of from the /admin/context interface.
    """
    __storm_table__ = 'pluginprofiles'

    # those fields are assigned at creation time and can't be changed:
    profile_gus = Unicode(primary=True)
    plugin_type = Unicode()
    plugin_name = Unicode()
    required_fields = Pickle()
    creation_time = DateTime()

    # those fields MAY be changed when profile has been created
    external_description = Unicode()
    profile_name = Unicode()
    admin_fields = Pickle()

    # contexts_assigned = Pickle()
    # TODO - at the moment, just the context reference their Profiles and not vice-versa

    @transact
    def newprofile(self, plugtype, plugname, profname, plugreq, desc=None, settings=None):
        """
        @param plugtype:  notification|delivery|inputfilter, already checked by the caller
        @param plugname:  plugin name, already checked the existence using GLPluginManager
        @param profname:  a profile name, used to recognize a unique profile in a list
        @param plugreq: the plugins required fields for admin and receiver.
        @param desc: a descriptive string that would be presented to the receiver
        @param settings:  the admin side configuration fields for the plugin.
        @return:
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class PluginConf", "newprofile", ptype, pname)

        store = self.getStore('newprofile')

        if store.find(PluginProfiles, PluginProfiles.profile_name == profname).count() >= 1:
            raise ProfileNameConflict

        newone = PluginProfiles()
        newone.profile_gus = idops.random_plugin_gus()
        newone.profile_name = profname
        newone.creation_time = gltime.utcTimeNow()
        newone.plugin_type = plugtype
        newone.plugin_name = plugname
        newone.required_fields = plugreq

        if settings:
            newone.admin_fields = settings

        if desc:
            newone.external_description = desc

        store.add(newone)

    @transact
    def update_profile(self, profile_gus, settings=None, profname=None, desc=None):

        log.debug("[D] %s %s " % (__file__, __name__), "PluginConf update_fields", profile_gus)

        store = self.getStore('update_fields')

        if store.find(PluginProfiles, PluginProfiles.profile_name == profname).count() >= 1:
            raise ProfileNameConflict

        try:
            looked_p = store.find(PluginProfiles, PluginProfiles.profile_gus == profile_gus).one()
        except NotOneError:
            raise ProfileGusNotFound
        if not looked_p:
            raise ProfileGusNotFound

        if settings:
            looked_p.admin_fields = settings

        if profname:
            looked_p.profile_name = profname

        if desc:
            looked_p.external_description = desc


    @transact
    def admin_get_all(self, by_type=None):

        log.debug("[D] %s %s " % (__file__, __name__), "PluginConf admin_get_all", by_type)
        store = self.getStore('admin_get_all')

        if by_type:
            selected_plugins = store.find(PluginProfiles, PluginProfiles.plugin_type == by_type)
        else:
            selected_plugins = store.find(PluginProfiles)

        retVal = []
        for single_p in selected_plugins:
            retVal.append(single_p)

        return retVal


    @transact
    def admin_get_single(self, profile_gus):

        log.debug("[D] %s %s " % (__file__, __name__), "PluginConf admin_get_single", profile_gus)
        store = self.getStore('admin_get_single')

        try:
            looked_p = store.find(PluginProfiles, PluginProfiles.profile_gus == profile_gus).one()
        except NotOneError:
            raise ProfileGusNotFound
        if not looked_p:
            raise ProfileGusNotFound

        retVal = looked_p._description_dict()
        return retVal


    def _description_dict(self):

        retVal = { 'profile_gus' : self.profile_gus,
                   'plugin_type': self.plugin_type,
                   'plugin_name' : self.plugin_name,
                   'creation_time' : None,
                   'profile_name' : self.profile_name,
                   'external_description' : self.external_description,
                   'admin_fields' : self.admin_fields }

        return retVal



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

        store = self.getStore('newconf')

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

        store = self.getStore('updateconf')

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
        store = self.getStore('admin_get_all')

        configurations = store.find(ReceiverConfs)

        retVal = []
        for single_c in configurations:
            retVal.append(single_c._description_dict())

        return retVal

    @transact
    def receiver_get_all(self, receiver_gus):

        log.debug("[D] %s %s " % (__file__, __name__), "ReceiverConfs receiver_get_all", receiver_gus)
        store = self.getStore('receiver_get_all')

        related_confs = store.find(ReceiverConfs, ReceiverConfs.receiver_gus == receiver_gus)

        retVal = []
        for single_c in related_confs:
            retVal.append(single_c._description_dict())

        return retVal

    def _description_dict(self):

        retVal = {
            'receiver_gus' : self.receiver_gus,
            'active' : self.active,
            'config_id' : self.id,
            'receiver_fields' : self.receiver_fields,
            'profile_gus' : self.profile_gus
        }
        return retVal

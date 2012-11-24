from storm.twisted.transact import transact
from storm.exceptions import NotOneError
from storm.locals import Int, Pickle, Unicode, Bool, DateTime
from storm.locals import Reference

from globaleaks.utils import idops, log, gltime
from globaleaks.models.base import TXModel, ModelError
from globaleaks.models.receiver import Receiver
from globaleaks.models.context import Context

__all__ = [ 'PluginProfiles', 'ReceiverConfs' ]

class ProfileGusNotFoundError(ModelError):

    def __init__(self):
        ModelError.error_message = "Invalid Plugin Identificative for requested profile"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 400 # Bad Request

class ProfileNameConflict(ModelError):

    def __init__(self):
        ModelError.error_message = "The proposed name is already in use by another profile"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 410 # Conflict


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
    admin_settings = Pickle()

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
            store.close()
            raise ProfileNameConflict

        newone = PluginProfiles()
        newone.profile_gus = idops.random_plugin_gus()
        newone.profile_name = profname
        newone.creation_time = gltime.utcTimeNow()
        newone.plugin_type = plugtype
        newone.plugin_name = plugname
        newone.required_fields = plugreq

        if settings:
            newone.admin_settings = settings

        if desc:
            newone.external_description = desc

        store.add(newone)

        store.commit()
        store.close()

    @transact
    def update_profile(self, profile_gus, settings=None, profname=None, desc=None):

        log.debug("[D] %s %s " % (__file__, __name__), "PluginConf update_fields", profile_gus)

        store = self.getStore('update_fields')

        if store.find(PluginProfiles, PluginProfiles.profile_name == profname).count() >= 1:
            store.close()
            raise ProfileNameConflict

        try:
            looked_p = store.find(PluginProfiles, PluginProfiles.profile_gus == profile_gus).one()
        except NotOneError:
            store.close()
            raise ProfileGusNotFoundError
        if not looked_p:
            store.close()
            raise ProfileGusNotFoundError

        if settings:
            looked_p.admin_settings = settings

        if profname:
            looked_p.profile_name = profname

        if desc:
            looked_p.external_description = desc

        store.commit()
        store.close()


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

        store.close()
        return retVal


    @transact
    def admin_get_single(self, profile_gus):

        log.debug("[D] %s %s " % (__file__, __name__), "PluginConf admin_get_single", profile_gus)
        store = self.getStore('admin_get_single')

        try:
            looked_p = store.find(PluginProfiles, PluginProfiles.profile_gus == profile_gus).one()
        except NotOneError:
            store.close()
            raise ProfileGusNotFoundError
        if not looked_p:
            store.close()
            raise ProfileGusNotFoundError

        retVal = looked_p._description_dict()
        store.close()
        return retVal


    def _description_dict(self):

        retVal = { 'profile_gus' : self.profile_gus,
                   'plugin_type': self.plugin_type,
                   'plugin_name' : self.plugin_name,
                   'creation_time' : None,
                   'profile_name' : self.profile_name,
                   'external_description' : self.external_description,
                   'admin_settings' : self.admin_settings }

        return retVal


class ReceiverConfs(TXModel):

    __storm_table__ = 'receiverconfs'
    id = Int(primary=True)

    receiver_gus = Unicode()
    receiver = Reference(receiver_gus, Receiver.receiver_gus)

    configured_fields = Pickle()
    profile_gus = Unicode()
    profile = Reference(profile_gus, PluginProfiles.profile_gus)
    active = Bool()

    def newconf(self):
        pass

    def updateconf(self, receiver_secret, receiver_gus, conf_id, settings, active):
        """
        @param receiver_secret: (the tip_gus, usually)
        @param receiver_gus:
        @param conf_id:
            receiver_secret, receiver_gus and conf_id are required to authenticate and address
            correctly the configuration. without those three elements, it not permitted
            change a Receiver plugin configuration.
        @param settings: the receiver_fields
        @param active:
        @return:
        """
        pass

    def admin_get_all(self):
        pass

    def receiver_get_all(self, receiver_secret, receiver_gus):
        pass

    def _description_dict(self):
        pass

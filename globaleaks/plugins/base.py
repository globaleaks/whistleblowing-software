# -*- coding: UTF-8
# 
#   plugin/base
#   ***********
# Two helper classes used to define and handle plugins

__all__ = ['GLPluginManager', 'GLPlugin']

class GLPluginManager:
    """
    This plugin manager is temporary, perhaps https://code.google.com/p/pyplugin/
    or http://pypi.python.org/pypi/Plugins/0.5a1dev
    """

    def __init__(self):
        from globaleaks.plugins.notification.mail_plugin import MailNotification
        from globaleaks.plugins.notification.irc_plugin import IRCNotification
        from globaleaks.plugins.notification.file_plugin import FILENotification

        # only here the plugin object is instanced
        self.notification_dict = {
            'email': MailNotification(),
            # 'irc': IRCNotification(),
            'file': FILENotification()
        }
        self.delivery_dict = {}
        self.inputfilter_dict = {}

    def get_types(self, ptype):
        """
        Return the list of plugin per types
        """
        if ptype == 'notification':
            return self.notification_dict
        if ptype == 'delivery':
            return self.delivery_dict
        if ptype == 'inputfilter':
            return self.inputfilter_dict

        Exception("invalid request type in GLPluginManager")

    def get_plugin(self, pname, ptype):
        """
        Return the plugin object
        """
        plugin_registered = self.get_types(ptype)
        return plugin_registered.get(pname)

    def plugin_exists(self, pname, ptype):
        """
        return a bool, if plugin type contains a plugin with the requested name
        """
        plugin_registered = self.get_types(ptype)

        if plugin_registered.has_key(pname):
            return True
        else:
            return False


class GLPlugin:
    """
    This class is an abstract class, use to define and implement
    the Users plugins
    Almost every plugin can grow over this class, and the methods
    developed in this, are called by the documented method.

    THESE CLASSES DO NOT INTERACT WITH STORM DATABASE:
    checks variables,
    pass information in the right moment, with the right parms
    return Errors or Success

    Every plugin type has some internal methods for manage information
    defined on the inherit classes below
    """

    plugin_name = None
    plugin_type = None
    admin_fields = {}
    receiver_fields = {}

    def validate_admin_opt(self, admin_fields):
        """
        @param admin_fields: the received admin fields, before being saved
            in the database between the Plugin Profiles, is checked here
        @return: bool
        """
        Exception("Your plugin misses implementation of 'validate_admin_opt'")

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        """
        @param receiver_fields: the received Receiver fields, before being
            saved in the database between Receiver Confs, is checked here
        @param admin_fields: referenced profile settings
        @return: bool
        """
        Exception("Your plugin misses implementation of 'validate_receiver_opt'")

class Notification(GLPlugin):

    def digest_check(self, settings, stored_data, new_data):
        """
        @param settings: a list containing [ {admin_settings_dict}, {receiver_settings_dict} ]
        @param stored_data: [ 'creation_time', 'information string' ], [...]
        @param new_data: [ 'creation_time', 'information string' ]
        @return: [ 'notification_marker', [ new stored data ] ]
        """
        Exception("Your plugin misses implementation of 'digest_check'")

    def do_notify(self, settings, stored_data):
        """
        @param settings: a list containing [ {admin_settings_dict}, {receiver_settings_dict} ]
        @param stored_data: the blob returned by digest_check
        @return:
        """
        Exception("Your plugin misses implementation of 'do_notify'")


class Delivery(GLPlugin):

    def do_delivery(self):
        Exception("Your plugin misses implementation of 'do_delivery'")


# -*- coding: UTF-8
#
#   plugin/manager
#   **************
# This class instance a singleton Object, used to interact with the installed
# plugins in the GLBackend node.

__all__ = [ 'PluginManager' ]

from globaleaks.rest.errors import InvalidPluginFormat

class GLPluginManager(object):

    notification_requirement = {
        'type' : u'notification',
        'methods' : [ 'do_notify', 'digest_check' ]
    }

    #delivery_requirement = {
    #    'type' : u'delivery',
    #    'methods' : [ 'do_delivery', 'preparation_required' ]
    #}

    #fileprocess_requirement = {
    #    'type' : u'fileprocess',
    #    'methods' : [ 'do_fileprocess' ]
    #}

    def is_valid_plugin(self, instanced_plugin, requirements):

        if instanced_plugin.plugin_type != requirements['type']:
            # XXX App log
            return False

        for required_m in requirements.get('methods'):
            if getattr(instanced_plugin, required_m) is None:
                # XXX App log
                return False

        return True

    def __init__(self):
        """
        Possibile extension: just move registration and validation of the
        Plugins outside the __init__, but use a dedicated call
        """


        from globaleaks.plugins.notification import MailNotification
        email_ti = MailNotification()

        self.notification_list = [
                { 'plugin_name' : unicode(email_ti.plugin_name),
                  'plugin_description' : unicode(email_ti.plugin_description),
                  'plugin_type' : u'notification',
                  'code' : MailNotification
                }
        ]
        if not self.is_valid_plugin(email_ti, self.notification_requirement ):
            raise InvalidPluginFormat


    def _look_plugin_in(self, plugin_name, type_list):

        for pluging_descriptor in type_list:
            if pluging_descriptor['plugin_name'] == plugin_name:
                return pluging_descriptor

        return None

    def get_plugin(self, plugin_name, plugin_type=None):
        """
        Return the plugin object
        """
        if plugin_type == None or unicode(plugin_type) == u'notificaton':
            plugin = self._look_plugin_in(unicode(plugin_name),
                                          self.notification_list)
            if plugin is not None:
                return plugin

        if plugin_type == None or unicode(plugin_type) == u'delivery':
            plugin = self._look_plugin_in(unicode(plugin_name),
                                          self.delivery_list)
            if plugin is not None:
                return plugin

        if plugin_type == None or unicode(plugin_type) == u'fileprocess':
            plugin = self._look_plugin_in(unicode(plugin_name),
                                     self.fileprocess_list)
            if plugin is not None:
                return plugin

        return None

    def plugin_exists(self, plugin_name, plugin_type=None):
        """
        return a bool, if plugin type contains a plugin with the requested name
        """
        return True if self.get_plugin(plugin_name, plugin_type) else False

    def instance_plugin(self, plugin_name, plugin_type=None):

        desc = self.get_plugin(plugin_name, plugin_type)

        if desc is None:
            return None

        # Instance the class stored in 'code' and return an object
        return desc['code']()

    def get_all(self):
        """
        @return: perform serialization of Plugins available, like happen
            in the models() with get_all. Align the same fields in the
            plugins, and remove the 'code' key.
        """

        ret_list = []

        for notifip_entry in self.notification_list:

            entry_copy = dict(notifip_entry)
            del entry_copy['code']
            ret_list.append(entry_copy)

        for delivp_entry in self.delivery_list:

            entry_copy = dict(delivp_entry)
            del entry_copy['code']
            ret_list.append(entry_copy)

        for filep_entry in self.fileprocess_list:

            incomplete_entry = dict(filep_entry)
            incomplete_entry['receiver_fields'] = []
            del incomplete_entry['code']
            ret_list.append(incomplete_entry)

        return ret_list


# This is the object expored in GLBackend, instanced only once
PluginManager = GLPluginManager()

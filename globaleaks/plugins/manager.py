# -*- coding: UTF-8
# 
#   plugin/manager
#   **************
# This class instance a singleton Object, used to interact with the installed plugins
# in the GLBackend node.

__all__ = [ 'PluginManager' ]

class GLPluginManager(object):

    def __init__(self):

        from globaleaks.plugins.notification.mail_plugin import MailNotification
        from globaleaks.plugins.notification.file_plugin import FileNotification
        # from globaleaks.plugins.notification.irc_plugin import IRCNotification

        from globaleaks.plugins.fileprocess.type_validation import TypeValidation
        from globaleaks.plugins.fileprocess.virustotal import Virustotal

        from globaleaks.plugins.delivery.scp import SCPDelivery
        from globaleaks.plugins.delivery.local import LocalDelivery

        # _ti stay for temporary instance, just useful to instance the
        # self.*_list with the information returned in the REST operation.
        email_ti = MailNotification()
        file_ti = FileNotification()
        self.notification_list = [
                { 'plugin_name' : unicode(email_ti.plugin_name),
                  'plugin_description' : unicode(email_ti.plugin_description),
                  'admin_fields' : unicode(email_ti.admin_fields),
                  'receiver_fields' : unicode(email_ti.receiver_fields)
                },
                { 'plugin_name' : unicode(file_ti.plugin_name),
                  'plugin_description' : unicode(file_ti.plugin_description),
                  'admin_fields' : unicode(file_ti.admin_fields),
                  'receiver_fields' : unicode(file_ti.receiver_fields)
                }
        ]

        scp_ti = SCPDelivery()
        local_ti = LocalDelivery()
        self.delivery_list = [
                { 'plugin_name' : unicode(scp_ti.plugin_name),
                  'plugin_description' : unicode(scp_ti.plugin_description),
                  'admin_fields' : unicode(scp_ti.admin_fields),
                  'receiver_fields' : unicode(scp_ti.receiver_fields)
                },
                { 'plugin_name' : unicode(local_ti.plugin_name),
                  'plugin_description' : unicode(local_ti.plugin_description),
                  'admin_fields' : unicode(local_ti.admin_fields),
                  'receiver_fields' : unicode(local_ti.receiver_fields)
                }
        ]

        content_ti = TypeValidation()
        virust_ti = Virustotal()
        self.fileprocess_list = [
                { 'plugin_name' : unicode(content_ti.plugin_name),
                  'plugin_description' : unicode(content_ti.plugin_description),
                  'admin_fields' : unicode(content_ti.admin_fields),
                },
                { 'plugin_name' : unicode(virust_ti.plugin_name),
                  'plugin_description' : unicode(virust_ti.plugin_description),
                  'admin_fields' : unicode(virust_ti.admin_fields),
                }
        ]

    def _look_plugin_in(self, plugin_name, type_list):

        for pluging_desciptor in type_list:
            if pluging_desciptor.get('name') == plugin_name:
                return pluging_desciptor

        return None

    def get_plugin(self, plugin_name, plugin_type=None):
        """
        Return the plugin object
        """
        if plugin_type == 'notificaton' or plugin_type == None:
            p = self._look_plugin_in(plugin_name, self.notification_list)
            if p is not None:
                return p

        if plugin_type == 'delivery' or plugin_type == None:
            p = self._look_plugin_in(plugin_name, self.delivery_list)
            if p is not None:
                return p

        if plugin_type == 'fileprocess' or plugin_type == None:
            p = self._look_plugin_in(plugin_name, self.fileprocess_list)
            if p is not None:
                return p

        return None

    def plugin_exists(self, plugin_name, plugin_type=None):
        """
        return a bool, if plugin type contains a plugin with the requested name
        """
        return True if self.get_plugin(plugin_name, plugin_type) else False

    def get_all(self):

        retList = []

        retList += self.notification_list
        retList += self.delivery_list

        for filep_entry in self.fileprocess_list:

            incomplete_entry = filep_entry
            incomplete_entry['receiver_fields'] = []

            # now is complete for fit adminPluginList expected fields
            retList.append(incomplete_entry)

        return retList


# This is the object expored in GLBackend, instanced only once
PluginManager = GLPluginManager()


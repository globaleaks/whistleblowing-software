# -*- coding: UTF-8
# 
#   plugin/manager
#   **************
# This class instance a singleton Object, used to interact with the installed plugins
# in the GLBackend node.

__all__ = [ 'PluginManager' ]

from globaleaks.rest.errors import InvalidPluginFormat

class GLPluginManager(object):

    notification_requirement = {
        'type' : u'notification',
        'methods' : [ 'do_notify', 'digest_check' ]
    }

    delivery_requirement = {
        'type' : u'delivery',
        'methods' : [ 'do_delivery', 'preparation_required' ]
    }

    fileprocess_requirement = {
        'type' : u'fileprocess',
        'methods' : [ 'do_fileprocess' ]
    }

    def is_valid_plugin(self, instanced_plugin, requirements):

        if instanced_plugin.plugin_type != requirements.get('type'):
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


        # from globaleaks.plugins.notification.irc_plugin import IRCNotification
        from globaleaks.plugins.notification.mail_plugin import MailNotification
        from globaleaks.plugins.notification.file_plugin import FileNotification
        email_ti = MailNotification()
        file_ti = FileNotification()

        self.notification_list = [
                { 'plugin_name' : unicode(email_ti.plugin_name),
                  'plugin_description' : unicode(email_ti.plugin_description),
                  'admin_fields' : unicode(email_ti.admin_fields),
                  'receiver_fields' : unicode(email_ti.receiver_fields),
                  'plugin_type' : u'notification',
                  'code' : MailNotification
                },
                { 'plugin_name' : unicode(file_ti.plugin_name),
                  'plugin_description' : unicode(file_ti.plugin_description),
                  'admin_fields' : unicode(file_ti.admin_fields),
                  'receiver_fields' : unicode(file_ti.receiver_fields),
                  'plugin_type' : u'notification',
                  'code' : FileNotification
                }
        ]
        if not self.is_valid_plugin(email_ti, self.notification_requirement ):
            raise InvalidPluginFormat

        if not self.is_valid_plugin(file_ti, self.notification_requirement ):
            raise InvalidPluginFormat


        from globaleaks.plugins.delivery.scp import SCPDelivery
        from globaleaks.plugins.delivery.local import LocalDelivery
        scp_ti = SCPDelivery()
        local_ti = LocalDelivery()

        self.delivery_list = [
                { 'plugin_name' : unicode(scp_ti.plugin_name),
                  'plugin_description' : unicode(scp_ti.plugin_description),
                  'admin_fields' : unicode(scp_ti.admin_fields),
                  'receiver_fields' : unicode(scp_ti.receiver_fields),
                  'plugin_type' : u'delivery',
                  'code' : SCPDelivery
                },
                { 'plugin_name' : unicode(local_ti.plugin_name),
                  'plugin_description' : unicode(local_ti.plugin_description),
                  'admin_fields' : unicode(local_ti.admin_fields),
                  'receiver_fields' : unicode(local_ti.receiver_fields),
                  'plugin_type' : u'delivery',
                  'code' : LocalDelivery
                }
        ]
        if not self.is_valid_plugin(scp_ti, self.delivery_requirement ):
            raise InvalidPluginFormat

        if not self.is_valid_plugin(local_ti, self.delivery_requirement):
            raise InvalidPluginFormat


        from globaleaks.plugins.fileprocess.type_validation import TypeValidation
        from globaleaks.plugins.fileprocess.virustotal import Virustotal
        content_ti = TypeValidation()
        virust_ti = Virustotal()

        self.fileprocess_list = [
                { 'plugin_name' : unicode(content_ti.plugin_name),
                  'plugin_description' : unicode(content_ti.plugin_description),
                  'admin_fields' : unicode(content_ti.admin_fields),
                  'plugin_type' : u'fileprocess',
                  'code' : TypeValidation
                },
                { 'plugin_name' : unicode(virust_ti.plugin_name),
                  'plugin_description' : unicode(virust_ti.plugin_description),
                  'admin_fields' : unicode(virust_ti.admin_fields),
                  'plugin_type' : u'fileprocess',
                  'code' : Virustotal
                }
        ]
        if not self.is_valid_plugin(content_ti, self.fileprocess_requirement):
            raise InvalidPluginFormat

        if not self.is_valid_plugin(virust_ti, self.fileprocess_requirement):
            raise InvalidPluginFormat


    def _look_plugin_in(self, plugin_name, type_list):

        for pluging_desciptor in type_list:
            if pluging_desciptor.get('name') == plugin_name:
                return pluging_desciptor

        return None

    def get_plugin(self, plugin_name, plugin_type=None):
        """
        Return the plugin object
        """
        if unicode(plugin_type) == u'notificaton' or plugin_type == None:
            p = self._look_plugin_in(plugin_name, self.notification_list)
            if p is not None:
                return p

        if unicode(plugin_type) == u'delivery' or plugin_type == None:
            p = self._look_plugin_in(plugin_name, self.delivery_list)
            if p is not None:
                return p

        if unicode(plugin_type) == u'fileprocess' or plugin_type == None:
            p = self._look_plugin_in(plugin_name, self.fileprocess_list)
            if p is not None:
                return p

        return None

    def plugin_exists(self, plugin_name, plugin_type=None):
        """
        return a bool, if plugin type contains a plugin with the requested name
        """
        return True if self.get_plugin(plugin_name, plugin_type) else False

    def instance_plugin(self, plugin_name, plugin_type=None):

        desc = self.get_plugin(plugin_name, plugin_type)

        if not desc:
            return None

        # Instance the class stored in 'code' and return an object
        return desc.get('code')()

    def get_all(self):
        """
        @return: perform serialization of Plugins available, like happen
            in the models() with get_all. Align the same fields in the
            plugins, and remove the 'code' key.
        """

        retList = []

        for notifip_entry in self.notification_list:

            entry_copy = notifip_entry
            del entry_copy['code']
            retList.append(entry_copy)

        for delivp_entry in self.delivery_list:

            entry_copy = delivp_entry
            del entry_copy['code']
            retList.append(entry_copy)

        for filep_entry in self.fileprocess_list:

            incomplete_entry = filep_entry
            incomplete_entry['receiver_fields'] = []
            del incomplete_entry['code']
            retList.append(incomplete_entry)

        return retList


# This is the object expored in GLBackend, instanced only once
PluginManager = GLPluginManager()


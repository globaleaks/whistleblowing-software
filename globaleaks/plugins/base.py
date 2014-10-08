# -*- coding: UTF-8
#
#   plugin/base
#   ***********
# The base classes used to define the plugins

from collections import namedtuple

Event = namedtuple('Event',
                   ['type', 'trigger', 'notification_settings',
                    'trigger_info', 'node_info', 'receiver_info',
                    'context_info', 'fields_info', 'plugin', 'trigger_parent'])

class GLPlugin:
    def validate_admin_opt(self, admin_fields):
        """
        @param admin_fields: the received admin fields, before being saved
            in the database between the Plugin Profiles, is checked here
        @return: bool
        """
        raise NotImplementedError("Your plugin misses implementation of 'validate_admin_opt'")

    #def initialize(self, admin_fields):
    #    raise NotImplementedError("Your plugin misses implementation of 'initialize'")


class Notification(GLPlugin):

    #def digest_check(self, settings, stored_data, new_data):
    #    raise NotImplementedError("Your plugin misses implementation of 'digest_check'")

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        """
        @param receiver_fields: the received Receiver fields, before being
            saved in the database between Receiver Confs, is checked here
        @param admin_fields: referenced profile settings
        @return: bool
        """
        raise NotImplementedError("Your plugin misses implementation of 'validate_receiver_opt'")

    def do_notify(self, event):
        """
        @param settings: a dict containing
            {
                'admin_settings' : {admin_settings_dict},
                'receiver_settings' : {receiver_settings_dict}
            }
        @param data_type: one of [ 'tip', 'comment' ]
        @param stored_data: the serialized object
        @return:
        """
        raise NotImplementedError('Your plugin misses implementation of "do_notify"')


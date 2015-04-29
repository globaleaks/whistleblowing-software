# -*- coding: UTF-8
#
#   plugin/base
#   ***********
# The base classes used to define the plugins

from collections import namedtuple

Event = namedtuple('Event',
                   ['type', 'trigger', 'tip_info', 'node_info',
                    'receiver_info', 'context_info', 'steps_info',
                    'subevent_info', 'do_mail'])

class GLPlugin(object):
    def validate_admin_opt(self, admin_fields):
        """
        @param admin_fields: the received admin fields, before being saved
            in the database between the Plugin Profiles, is checked here
        @return: bool
        """
        raise NotImplementedError("Your plugin misses implementation of 'validate_admin_opt'")

class Notification(GLPlugin):
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
        """
        raise NotImplementedError('Your plugin misses implementation of "do_notify"')


# -*- coding: UTF-8
# 
#   plugin/base
#   ***********
# The base classes used to define the plugins

__all__ = [ 'Notification', 'Delivery', 'FileProcess' ]

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

    def validate_admin_opt(self, admin_fields):
        """
        @param admin_fields: the received admin fields, before being saved
            in the database between the Plugin Profiles, is checked here
        @return: bool
        """
        Exception("Your plugin misses implementation of 'validate_admin_opt'")

    def initialize(self, admin_fields):
        Exception("Your plugin misses implementation of 'initialize'")


class Notification(GLPlugin):

    def digest_check(self, settings, stored_data, new_data):
        """
        @param settings: a dict containing
            {
                'admin_settings' : {admin_settings_dict},
                'receiver_settings' : {receiver_settings_dict}
            }
        @param stored_data: [ 'creation_time', 'information string' ], [...]
        @param new_data: [ 'creation_time', 'information string' ]
        @return: [ 'notification_marker', [ new stored data ] ]
        """
        Exception("Your plugin misses implementation of 'digest_check'")

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        """
        @param receiver_fields: the received Receiver fields, before being
            saved in the database between Receiver Confs, is checked here
        @param admin_fields: referenced profile settings
        @return: bool
        """
        Exception("Your plugin misses implementation of 'validate_receiver_opt'")

    data_list = [ u'tip', u'comment' ]
    def do_notify(self, settings, data_type, stored_data):
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
        Exception("Your plugin misses implementation of 'do_notify'")


class Delivery(GLPlugin):

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        """
        @param receiver_fields: the received Receiver fields, before being
            saved in the database between Receiver Confs, is checked here
        @param admin_fields: referenced profile settings
        @return: bool
        """
        Exception("Your plugin misses implementation of 'validate_receiver_opt'")

    def preparation_required(self, fileinfo, admin_fields):
        Exception("Your plugin misses implementation of 'preparation_required'")

    def do_delivery(self, settings, data_reference):
        Exception("Your plugin misses implementation of 'do_delivery'")


class FileProcess(GLPlugin):

    def do_fileprocess(self, filepath, admin_fields):
        """
        @param filepath:
        @param admin_fields:
        @return:
        """
        Exception("Your plugin messes implementation of do_fileprocess")

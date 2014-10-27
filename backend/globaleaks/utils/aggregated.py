# -*- coding: UTF-8
#
#   aggregated 
#   **********
#
# In the Models Context and Receiver a certain amount of capability
# are described in the DB objects.
# 
# The increase of these capability enlarge the database struct seriously
# and some conflicts in the option schema will exists and need to be 
# handled.
#
# The 'aggregated' utility implements classes that masks these boolean/int
# option and return them as a dict, in this way, we've:
#
# 1) few Pickle() (or JSON) object in the Context,Receiver Models
# 2) a class able to verify integrity between the options, when are
#    loaded and set
# 3) more extensible features in the future (no DB update for boolean/int options)

from globaleaks.utils.utility import log
from globaleaks.settings import GLSetting
from globaleaks.rest.errors import ContextParameterConflict


class _CapabilityClass:

    def serialize(self):

        ret_dict = {}

        if hasattr(self, 'int_vars'):
            for int_key in self.int_vars:
                ret_dict.update({
                    int_key : getattr(self, int_key)
                })

        if hasattr(self, 'bool_vars'):
            for bool_key in self.bool_vars:
                ret_dict.update({
                    bool_key : getattr(self, bool_key)
                })

        assert ret_dict, "Invalid CapabilityClass usage"
        return ret_dict


"""
kept in context

unique_fields = Pickle()
localized_fields = Pickle()
receipt_regexp = Unicode()
last_update = DateTime()
tags = Pickle()
name = Pickle()
description = Pickle()
receiver_introduction = Pickle()
fields_introduction = Pickle()

# presentation_order = Int()

Added =>
 capability = Pickle()
   <= the ContextCapability.serialize()
"""

class ContextCapability(_CapabilityClass):

    bool_vars = [
        'selectable_receiver',
        'file_required',
        'select_all_receivers',
        'require_file_description',
        'require_pgp',
        'show_small_cards',
        'postpone_superpower',
        'can_delete_submission',
    ]

    int_vars = [
        'tip_max_access',
        'file_max_download',
        'tip_timetolive',
        'submission_timetolive',
        'maximum_selectable_receivers',
        'escalation_threshold',
        'delete_consensus_percentage',
    ]

    def __init__(self, init_data=None):

        # setting the default before loading

        self.selectable_receiver = True
        self.file_required = False
        self.select_all_receivers = True # This is the default: all selected
        self.require_file_description = False # still not implemented!
        self.require_pgp = False
        self.show_small_cards = False
        self.postpone_superpower = False
        self.can_delete_submission = False

        self.tip_max_access = 100
        self.file_max_download = 4
        self.tip_timetolive = GLSetting.defaults.tip_seconds_of_life
        self.submission_timetolive = GLSetting.defaults.submission_seconds_of_life
        self.maximum_selectable_receivers = 0
        self.escalation_threshold = 0
        self.delete_consensus_percentage = 0

        if init_data:
            for int_key in ContextCapability.int_vars:
                if init_data.has_key(int_key):
                    setattr(self, int_key, init_data[int_key])

            for bool_key in ContextCapability.bool_vars:
                if init_data.has_key(bool_key):
                    setattr(self, bool_key, init_data[bool_key])


    def integrity_check(self, context):

        if self.maximum_selectable_receivers > context.receivers.count():
            log.err("Invalid Parameter! (1)")
            raise ContextParameterConflict

        # TODO other checks need to be done here, and removed from
        # handlers.admin.context_create and .context_update
        #
        # the variable 'context' is the Storm object


"""
kept in receiver

user_id = Unicode()
name = Unicode()
description = Pickle()

gpg_key_info = Unicode()
gpg_key_fingerprint = Unicode()
gpg_key_status = Unicode()
gpg_key_armor = Unicode()

mail_address = Unicode()

last_update = DateTime()
tags = Pickle()

# presentation_order = Int()

Need to be removed:
receiver_level = Int()

"""

class ReceiverCapability(_CapabilityClass):

    bool_vars = [
        'can_delete_submission',
        'postpone_superpower',
        'tip_notification',
        'comment_notification',
        'file_notification',
        'message_notification',
        'gpg_enable_notification',
    ]

    def __init__(self, init_data=None):

        self.can_delete_submission = False
        self.postpone_superpower = False
        self.tip_notification = True
        self.comment_notification = False
        self.file_notification = True
        self.message_notification = True
        self.gpg_enable_notification = True

        if init_data:
            for bool_key in ReceiverCapability.bool_vars:
                if init_data.has_key(bool_key):
                    setattr(self, bool_key, init_data[bool_key])

    def integrity_check(self, receiver):
        pass


# class NodeSettings:
#    pass

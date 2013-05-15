# -*- coding: UTF-8
#   Requests
#   ********
#
# This file contain the specification of all the requests that can be made by a
# GLClient to a GLBackend.
# These specifications may be used with rest.validateMessage() inside of the
# handler to verify if the request is correct.

from globaleaks.rest.base import formFieldsDict, uuid_regexp

authDict = {
    'username' : unicode,
    'password' : unicode,
    'role' : unicode
}

wbSubmissionDesc = {
    'wb_fields' : dict,
    'context_gus' : uuid_regexp,
    'receivers' : [ uuid_regexp ],
    'files' : [ uuid_regexp ],
    'finalize' : bool
}

receiverReceiverDesc = {
    'name' : unicode,
    'password' : unicode,
    'old_password': unicode,
    'username' : unicode,
    'notification_fields' : dict,
    'description' : unicode,
    'gpg_key_armor': unicode,
    'gpg_key_disable': bool,
}

actorsCommentDesc = {
    'content' : unicode,
}

actorsTipOpsDesc = {
    'total_delete' : bool,
    'is_pertinent': bool
}

adminNodeDesc = {
    'name': unicode,
    'description' : unicode,
    'hidden_service' : unicode,
    'public_site' : unicode,
    'stats_update_time' : int,
    'email' : unicode,
    'password' : unicode,
    'old_password' : unicode,
}

adminNotificationDesc = {
    'server': unicode,
    'port': int,
    'security': unicode, # 'TLS' or 'SSL' only
    'username': unicode,
    'password': unicode,
    'tip_template': unicode,
    'comment_template': unicode,
    'file_template': unicode,
    'activation_template': unicode
}

adminContextDesc = {
    'name': unicode,
    'description': unicode,
    'selectable_receiver': bool,
    'tip_max_access' : int,
    'tip_timetolive' : int,
    'file_max_download' : int,
    'escalation_threshold' : int,
    'receivers' : [ uuid_regexp ],
    'fields': [ formFieldsDict ],
}

adminReceiverDesc =  {
    'password' : unicode,
    'notification_fields' : dict,
    'name' : unicode,
    'description' : unicode,
    'contexts' : [ uuid_regexp ],
    'receiver_level' : int,
    'can_delete_submission' : bool,
}

# -*- coding: UTF-8
#   Requests
#   ********
#
# This file contain the specification of all the requests that can be made by a
# GLClient to a GLBackend.
# These specifications may be used with rest.validateMessage() inside of the
# handler to verify if the request is correct.

from globaleaks.rest.base import submissionGUS, formFieldsDict, contextGUS,\
    timeType, receiverGUS, fileGUS, tipGUS, uuid_regexp

wbSubmissionDesc = {
    'wb_fields' : dict,
    'context_gus' : uuid_regexp,
    'receivers' : [ uuid_regexp ],
    'files' : [ fileGUS ],
    'finalize' : bool
}

receiverReceiverDesc = {
    'name' : unicode,
    'password' : unicode,
    'prev_password': unicode,
    'usernme' : unicode,
    'notification_fields' : dict,
    'description' : unicode,
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
    'notification_settings' : dict,
    'languages': list,
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
    'can_postpone_expiration' : bool,
    'can_configure_delivery' : bool,
    'can_configure_notification' : bool,
}

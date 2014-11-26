# -*- coding: UTF-8
#   Requests
#   ********
#
# This file contain the specification of all the requests that can be made by a
# GLClient to a GLBackend.
# These specifications may be used with rest.validateMessage() inside of the
# handler to verify if the request is correct.

uuid_regexp                       = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$'
receiver_img_regexp               = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).png$'
email_regexp                      = r'^([\w-]+\.)*[\w-]+@([\w-]+\.)+[a-z]{2,4}$|^$'
email_regexp_or_empty             = r'^([\w-]+\.)*[\w-]+@([\w-]+\.)+[a-z]{2,4}$|^$'
hidden_service_regexp             = r'^http://[0-9a-z]{16}\.onion$'
hidden_service_regexp_or_empty    = r'^http://[0-9a-z]{16}\.onion$$|^$'
https_url_regexp                  = r'^https://([0-9a-z\-]+)\.(.*)$'
https_url_regexp_or_empty         = r'^https://([0-9a-z\-]+)\.(.*)$|^$'
x_frame_options_mode_regexp       = r'^(deny)|(allow-from)$'
x_frame_options_allow_from_regexp = r'^(http(s?)://(\w+)\.(.*)$|^)?$'

dateType = r'(.*)'

# contentType = r'(application|audio|text|video|image)'
# via stackoverflow:
# /^(application|audio|example|image|message|model|multipart|text|video)\/[a-zA-Z0-9]+([+.-][a-zA-z0-9]+)*$/
contentType = r'(.*)'

fileDict = {
    'name': unicode,
    'description': unicode,
    'size': int,
    'content_type': contentType,
    'date': dateType,
    }

formFieldsDict = {
    'key': unicode,
    'presentation_order': int,
    'name': unicode,
    'required': bool,
    'preview': bool,
    'hint': unicode,
    'type': unicode,
}

authDict = {
    'username' : unicode,
    'password' : unicode,
    'role' : unicode
}

wbSubmissionDesc = {
    'wb_fields' : dict,
    'context_id' : uuid_regexp,
    'receivers' : [ uuid_regexp ],
    'files' : [ uuid_regexp ],
    'finalize' : bool,
}

receiverReceiverDesc = {
    'name' : unicode,
    'password' : unicode,
    'old_password': unicode,
    # 'username' : unicode, XXX at creation time is the same of mail_address
    'mail_address' : email_regexp,
    'description' : unicode,
    'gpg_key_armor': unicode,
    'gpg_key_remove': bool,
    "gpg_enable_notification": bool,
    "comment_notification": bool,
    "file_notification": bool,
    "tip_notification": bool,
    "message_notification": bool,
    "language": unicode,
    "timezone": unicode,
}

actorsCommentDesc = {
    'content' : unicode,
}

actorsTipOpsDesc = {
    'global_delete' : bool,
    'extend': bool,
    'is_pertinent': bool,
}

adminNodeDesc = {
    'name': unicode,
    'description' : unicode,
    'presentation' : unicode,
    'subtitle': unicode,
    'footer': unicode,
    'terms_and_conditions': unicode,
    'security_awareness_title': unicode,
    'security_awareness_text': unicode,
    'hidden_service' : hidden_service_regexp_or_empty,
    'public_site' : https_url_regexp_or_empty,
    'stats_update_time' : int,
    'email' : email_regexp_or_empty, # FIXME old versions of globaleaks have an empty value
    'password' : unicode,            # and in addition the email is not set before wizard.
    'old_password' : unicode,
    'languages_enabled': [ unicode ],
    'languages_supported': list,
    'default_language' : unicode,
    'maximum_namesize': int,
    'maximum_textsize': int,
    'maximum_filesize': int,
    'tor2web_admin': bool,
    'tor2web_submission': bool,
    'tor2web_receiver': bool,
    'tor2web_unauth': bool,
    'postpone_superpower': bool,
    'can_delete_submission': bool,
    'exception_email': email_regexp,
    'reset_css': bool,
    'reset_homepage': bool,
    'ahmia': bool,
    'anomaly_checks': bool,
    'allow_unencrypted': bool,
    'x_frame_options_mode': x_frame_options_mode_regexp,
    'x_frame_options_allow_from': x_frame_options_allow_from_regexp,
    'wizard_done': bool,
    'receipt_regexp': unicode,
    'terms_and_conditions': unicode,
    'disable_privacy_badge': bool,
    'disable_security_awareness_badge': bool,
    'disable_security_awareness_questions': bool,
    'configured': bool,
    'admin_language': unicode,
    'admin_timezone': unicode,
}

adminNotificationDesc = {
    'server': unicode,
    'port': int,
    'security': unicode, # 'TLS' or 'SSL' only
    'username': unicode,
    'password': unicode,
    'source_name' : unicode,
    'source_email' : email_regexp,
    'encrypted_tip_template': unicode,
    'encrypted_tip_mail_title': unicode,
    'plaintext_tip_template': unicode,
    'plaintext_tip_mail_title': unicode,
    'encrypted_file_template': unicode,
    'encrypted_file_mail_title': unicode,
    'plaintext_file_template': unicode,
    'plaintext_file_mail_title': unicode,
    'encrypted_comment_template': unicode,
    'encrypted_comment_mail_title': unicode,
    'plaintext_comment_template': unicode,
    'plaintext_comment_mail_title': unicode,
    'encrypted_message_template': unicode,
    'encrypted_message_mail_title': unicode,
    'plaintext_message_template': unicode,
    'plaintext_message_mail_title': unicode,
    'zip_description': unicode,
    'disable': bool,
}

adminContextDesc = {
    'name': unicode,
    'description': unicode,
    'receiver_introduction': unicode,
    'fields_introduction': unicode,
    'postpone_superpower': bool,
    'can_delete_submission': bool,
    'maximum_selectable_receivers': int,
    'require_file_description': bool,
    'delete_consensus_percentage': int,
    'require_pgp': bool,
    'selectable_receiver': bool,
    'tip_max_access' : int,
    'tip_timetolive' : int,
    'file_max_download' : int,
    'escalation_threshold' : int,
    'receivers' : [ uuid_regexp ],
    'fields': [ formFieldsDict ],
    'file_required': bool,
    'tags' : [ unicode ],
    'select_all_receivers': bool,
    'show_small_cards': bool,
    'show_receivers': bool,
    'enable_private_messages': bool, 
    'presentation_order': int,
}

adminReceiverDesc = {
    'password': unicode,
    'mail_address': email_regexp,
    'name': unicode,
    'description': unicode,
    'contexts': [ uuid_regexp ],
    'receiver_level': int,
    'can_delete_submission': bool,
    'postpone_superpower': bool,
    'tags': [ unicode ],
    'tip_notification': bool,
    'file_notification': bool,
    'comment_notification': bool,
    'message_notification': bool,
    'gpg_key_remove': bool,
    'gpg_key_fingerprint': unicode,
    'gpg_key_info': unicode,
    'gpg_key_armor': unicode,
    'gpg_key_status': unicode,
    'gpg_enable_notification': bool,
    'presentation_order': int,
    'state': unicode,
    "language": unicode,
    "timezone": unicode,
}

anonNodeDesc = {
    'name': unicode,
    'subtitle': unicode,
    'description': unicode,
    'presentation': unicode,
    'terms_and_conditions': unicode,
    'footer': unicode,
    'security_awareness_title': unicode,
    'security_awareness_text': unicode,
    'hidden_service' : hidden_service_regexp_or_empty,
    'public_site' : https_url_regexp_or_empty,
    'email' : email_regexp,
    'languages_enabled': [ unicode ],
    'languages_supported': list,
    'default_language' : unicode,
    'maximum_namesize': int,
    'maximum_textsize': int,
    'maximum_filesize': int,
    'tor2web_admin': bool,
    'tor2web_submission': bool,
    'tor2web_receiver': bool,
    'tor2web_unauth': bool,
    'postpone_superpower': bool,
    'can_delete_submission': bool,
    'ahmia': bool,
    'anomaly_checks': bool,
    'allow_unencrypted': bool,
    'wizard_done': bool,
    'configured': bool,
    'receipt_regexp': unicode,
    'disable_privacy_badge': bool,
    'disable_security_awareness_badge': bool,
    'disable_security_awareness_questions': bool
}

TipOverview = {
    'status': unicode,
    'context_id': uuid_regexp,
    'creation_lifetime': dateType,
    'receivertips': list,
    'creation_date': dateType,
    'context_name': unicode,
    'id': uuid_regexp,
    'wb_access_counter': int,
    'internalfiles': list,
    'comments': list,
    'wb_last_access': unicode,
    'expiration_date': dateType,
    'pertinence_counter': int,
}

TipsOverview = [ TipOverview ]

UserOverview = {
    'receivertips': list,
    'receiverfiles': list,
    'gpg_key_status': unicode,
    'id': uuid_regexp,
    'name': unicode,
}

UsersOverview = [ UserOverview ]

FileOverview = {
    'rfiles': int,
    'stored': bool,
    'name': unicode,
    'content_type': unicode,
    'itip': uuid_regexp,
    'path': unicode,
    'creation_date': dateType,
    'id': uuid_regexp,
    'size': int,
}

FilesOverview = [ FileOverview ]

StatsLine = {
     'file_uploaded': int,
     'new_submission': int,
     'finalized_submission': int,
     'anon_requests': int,
     'creation_date': dateType,
}

StatsCollection = [ StatsLine ]

AnomalyLine = {
     'message': unicode,
     'creation_date': dateType,
}

AnomaliesCollection = [ AnomalyLine ]

nodeReceiver = { 
    'update_date': unicode,
    'receiver_level': int,
    'name': unicode,
    'tags': [ unicode ],
    'contexts': [ uuid_regexp ],
    'description': unicode,
    'presentation_order': int,
    'gpg_key_status': unicode,
    'id': uuid_regexp,
    'creation_date': dateType,
}

nodeReceiverCollection = [ nodeReceiver ]

field = {
    'incremental_number': int,
    'name': unicode,
    'hint': unicode,
    'required': bool,
    'presentation_order': int,
    'trigger': list,
    'key': uuid_regexp,
    'preview': bool,
    'type': unicode,
}

nodeContext = {
    'select_all_receivers': bool,
    'name': unicode,
    'presentation_order': int,
    'fields': [ field ],
    'description': unicode,
    'selectable_receiver': bool,
    'tip_timetolive': int,
    'submission_introduction': unicode,
    'maximum_selectable_receivers': int,
    'show_small_cards': bool,
    'show_receivers': bool,
    'enable_private_messages': bool,
    'file_max_download': int,
    'require_pgp': bool,
    'tip_max_access': int,
    'file_required': bool,
    'id': uuid_regexp,
    'receivers': [ uuid_regexp ],
    'submission_disclaimer': unicode,
    'escalation_threshold': int,
}

nodeContextCollection = [ nodeContext ]

ahmiaDesc = {
    'description': unicode,
    'language': unicode,
    'title': unicode,
    'contactInformation': unicode,
    'relation': unicode,
    'keywords': unicode,
    'type': unicode,
}

staticFile = {
    'elapsed_time': float,
    'size': int,
    'filelocation': unicode,
    'content_type': unicode,
    'filename': unicode,
}

staticFileCollectionElem = {
    'size': int,
    'filename': unicode,
}

staticFileCollection = [ staticFileCollectionElem ]

internalTipDesc = {
    'wb_fields': dict,
    'pertinence': int,
    'receivers': [ uuid_regexp ],
    'context_id': uuid_regexp,
    'access_limit': int,
    'creation_date': dateType,
    'mark': unicode,
    'id': uuid_regexp,
    'files': [ uuid_regexp ],
    'expiration_date': dateType,
    'download_limit': int,
    'escalation_threshold': int,
}

wizardFieldDesc = {
    'incremental_number': int,
    'localized_name': dict,
    'localized_hint': dict,
    'type': unicode,
    'trigger': list,
    'defined_options': list, # can be None, I don't remember if can be other ?
}

wizardNodeDesc = {
    'presentation': dict,
    'footer': dict,
    'subtitle': dict,
    'terms_and_conditions': dict,
}

wizardFieldUpdate = {
    'version': int,
    'fields': [ wizardFieldDesc ],
    'node': wizardNodeDesc,
}

wizardFirstSetup = {
    'receiver' : adminReceiverDesc,
    'context' : adminContextDesc,
    'node' : adminNodeDesc,
    'appdata' : wizardFieldUpdate,
}

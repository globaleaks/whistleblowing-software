# -*- coding: UTF-8
#   Requests
#   ********
#
# This file contains the specification of all the requests that can be made by a
# GLClient to a GLBackend.
# These specifications may be used with rest.validateMessage() inside each of the API
# handler in order to verify if the request is correct.

uuid_regexp                       = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$'
uuid_regexp_or_empty              = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$|^$'
user_roles_regexp                 = r'^(admin|custodian|receiver)$'
user_states_regexp                = r'^(enabled|disabled)$'
receiver_img_regexp               = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).png$'
email_regexp                      = r'^([\w-]+\.)*[\w-]+@([\w-]+\.)+[a-z]{2,9}$|^$'
email_regexp_or_empty             = r'^([\w-]+\.)*[\w-]+@([\w-]+\.)+[a-z]{2,9}$|^$'
hidden_service_regexp             = r'^http://[0-9a-z]{16}\.onion$'
hidden_service_regexp_or_empty    = r'^http://[0-9a-z]{16}\.onion$$|^$'
https_url_regexp                  = r'^https://([0-9a-z\-]+)\.(.*)$'
https_url_regexp_or_empty         = r'^https://([0-9a-z\-]+)\.(.*)$|^$'
landing_page_regexp               = r'^homepage$|^submissionpage$'
tip_operation_regexp              = r'^postpone$|^label$'
token_type_regexp                 = r'^submission$'
field_type_regexp                 = (r'^('
                                     'inputbox|'
                                     'textarea|'
                                     'selectbox|'
                                     'checkbox|'
                                     'modal|'
                                     'dialog|'
                                     'tos|'
                                     'fileupload|'
                                     'number|'
                                     'email|'
                                     'date|'
                                     'fieldgroup)$')

DateType = r'(.*)'

# ContentType = r'(application|audio|text|video|image)'
# via stackoverflow:
# /^(application|audio|example|image|message|model|multipart|text|video)\/[a-zA-Z0-9]+([+.-][a-zA-z0-9]+)*$/
ContentType = r'(.*)'

FileDesc = {
    'name': unicode,
    'description': unicode,
    'size': int,
    'content_type': ContentType,
    'date': DateType
}


AuthDesc = {
    'username': unicode,
    'password': unicode,
}

ReceiptAuthDesc = {
    'receipt': unicode
}

WBStepDesc = {
    'id' : uuid_regexp,
    'hint': unicode,
    'description':unicode,
    'label': unicode,
    'children': list
}

TokenReqDesc = {
    'type': token_type_regexp
}

TokenAnswerDesc = {
    'human_captcha_answer': int,
    'graph_captcha_answer': unicode,
    'proof_of_work_answer': int
}

SubmissionDesc = {
    'context_id': uuid_regexp,
    'receivers': [uuid_regexp],
    'answers': dict
}

UserUserDesc = {
    'username': unicode,
    'name': unicode,
    'description': unicode,
    'role': user_roles_regexp,
    'password': unicode,
    'old_password': unicode,
    'password_change_needed': bool,
    'state': user_states_regexp,
    'mail_address': email_regexp,
    'pgp_key_remove': bool,
    'pgp_key_fingerprint': unicode,
    'pgp_key_expiration': unicode,
    'pgp_key_info': unicode,
    'pgp_key_public': unicode,
    'pgp_key_status': unicode,
    'language': unicode,
    'timezone': int
}

AdminUserDesc = UserUserDesc # currently the same

ReceiverReceiverDesc = {
    'username': unicode,
    'name': unicode,
    'description': unicode,
    'role': user_roles_regexp,
    'password': unicode,
    'old_password': unicode,
    'role': user_roles_regexp,
    'password_change_needed': bool,
    'mail_address': email_regexp,
    'ping_mail_address': email_regexp,
    'pgp_key_remove': bool,
    'pgp_key_fingerprint': unicode,
    'pgp_key_expiration': unicode,
    'pgp_key_info': unicode,
    'pgp_key_public': unicode,
    'pgp_key_status': unicode,
    'tip_notification': bool,
    'ping_notification': bool,
    'language': unicode,
    'timezone': int,
    'tip_expiration_threshold': int
}

ReceiverOperationDesc = {
    'operation': unicode,
    'rtips': [uuid_regexp]
}

CommentDesc = {
    'content': unicode
}

TipOpsDesc = {
    'operation': tip_operation_regexp,
    'label': unicode,
}

StepDesc = {
    'label': unicode,
    'hint': unicode,
    'description': unicode,
    'children': list,
    'context_id': uuid_regexp,
    'presentation_order': int
}

AdminNodeDesc = {
    'name': unicode,
    'description': unicode,
    'presentation': unicode,
    'footer': unicode,
    'security_awareness_title': unicode,
    'security_awareness_text': unicode,
    'whistleblowing_question': unicode,
    'whistleblowing_button': unicode,
    'hidden_service': hidden_service_regexp_or_empty,
    'public_site': https_url_regexp_or_empty,
    'email': email_regexp_or_empty, # FIXME old versions of globaleaks have an empty value
    'password': unicode,            # and in addition the email is not set before wizard.
    'old_password': unicode,
    'languages_enabled': [unicode],
    'languages_supported': list,
    'default_language': unicode,
    'default_timezone': int,
    'maximum_namesize': int,
    'maximum_textsize': int,
    'maximum_filesize': int,
    'tor2web_admin': bool,
    'tor2web_custodian': bool,
    'tor2web_whistleblower': bool,
    'tor2web_receiver': bool,
    'tor2web_unauth': bool,
    'can_postpone_expiration': bool,
    'can_delete_submission': bool,
    'ahmia': bool,
    'allow_unencrypted': bool,
    'allow_iframes_inclusion': bool,
    'wizard_done': bool,
    'disable_privacy_badge': bool,
    'disable_security_awareness_badge': bool,
    'disable_security_awareness_questions': bool,
    'disable_key_code_hint': bool,
    'configured': bool,
    'enable_simplified_login': bool,
    'enable_custom_privacy_badge': bool,
    'custom_privacy_badge_tor': unicode,
    'custom_privacy_badge_none': unicode,
    'header_title_homepage': unicode,
    'header_title_submissionpage': unicode,
    'header_title_receiptpage': unicode,
    'header_title_tippage': unicode,
    'landing_page': landing_page_regexp,
    'context_selector_label': unicode,
    'submission_minimum_delay': int,
    'submission_maximum_ttl': int,
    'show_contexts_in_alphabetical_order': bool,
    'widget_comments_title': unicode,
    'widget_messages_title': unicode,
    'widget_files_title': unicode
}

AdminNotificationDesc = {
    'server': unicode,
    'port': int,
    'security': unicode, # 'TLS' or 'SSL' only
    'username': unicode,
    'password': unicode,
    'source_name': unicode,
    'source_email': email_regexp,
    'tip_mail_template': unicode,
    'tip_mail_title': unicode,
    'file_mail_template': unicode,
    'file_mail_title': unicode,
    'comment_mail_template': unicode,
    'comment_mail_title': unicode,
    'message_mail_template': unicode,
    'message_mail_title': unicode,
    'admin_pgp_alert_mail_template': unicode,
    'admin_pgp_alert_mail_title': unicode,
    'pgp_alert_mail_template': unicode,
    'pgp_alert_mail_title': unicode,
    'zip_description': unicode,
    'ping_mail_template': unicode,
    'ping_mail_title': unicode,
    'receiver_notification_limit_reached_mail_template': unicode,
    'receiver_notification_limit_reached_mail_title': unicode,
    'notification_digest_mail_title': unicode,
    'tip_expiration_mail_template': unicode,
    'tip_expiration_mail_title': unicode,
    'admin_anomaly_mail_template': unicode,
    'admin_anomaly_mail_title': unicode,
    'admin_anomaly_activities': unicode,
    'admin_anomaly_disk_high': unicode,
    'admin_anomaly_disk_medium': unicode,
    'admin_anomaly_disk_low': unicode,
    'disable_admin_notification_emails': bool,
    'disable_receivers_notification_emails': bool,
    'send_email_for_every_event': bool,
    'notification_threshold_per_hour': int,
    'notification_suspension_time': int,
    'reset_templates': bool,
    'exception_email_address': email_regexp,
    'exception_email_pgp_key_fingerprint': unicode,
    'exception_email_pgp_key_expiration': unicode,
    'exception_email_pgp_key_info': unicode,
    'exception_email_pgp_key_public': unicode,
    'exception_email_pgp_key_status': unicode,
    'exception_email_pgp_key_remove': bool
}

AdminContextDesc = {
    'name': unicode,
    'description': unicode,
    'maximum_selectable_receivers': int,
    'tip_timetolive': int,
    'receivers': [uuid_regexp],
    'steps': list,
    'select_all_receivers': bool,
    'show_small_cards': bool,
    'show_receivers': bool,
    'enable_comments': bool,
    'enable_messages': bool,
    'enable_two_way_communication': bool,
    'enable_attachments': bool,
    'presentation_order': int,
    'show_receivers_in_alphabetical_order': bool,
    'steps_arrangement': unicode,
    'reset_steps': bool
}

AdminReceiverDesc = {
    'username': unicode,
    'role': user_roles_regexp,
    'name': unicode,
    'description': unicode,
    'password': unicode,
    'mail_address': email_regexp,
    'ping_mail_address': email_regexp,
    'contexts': [uuid_regexp],
    'can_delete_submission': bool,
    'can_postpone_expiration': bool,
    'tip_notification': bool,
    'ping_notification': bool,
    'pgp_key_remove': bool,
    'pgp_key_fingerprint': unicode,
    'pgp_key_expiration': unicode,
    'pgp_key_info': unicode,
    'pgp_key_public': unicode,
    'pgp_key_status': unicode,
    'presentation_order': int,
    'language': unicode,
    'timezone': int,
    'state': user_states_regexp,
    'configuration': unicode,
    'password_change_needed': bool,
    'tip_expiration_threshold': int
}

NodeDesc = {
    'name': unicode,
    'description': unicode,
    'presentation': unicode,
    'footer': unicode,
    'security_awareness_title': unicode,
    'security_awareness_text': unicode,
    'hidden_service': hidden_service_regexp_or_empty,
    'public_site': https_url_regexp_or_empty,
    'email': email_regexp,
    'languages_enabled': [unicode],
    'languages_supported': list,
    'default_language': unicode,
    'maximum_namesize': int,
    'maximum_textsize': int,
    'maximum_filesize': int,
    'tor2web_admin': bool,
    'tor2web_custodian': bool,
    'tor2web_whistleblower': bool,
    'tor2web_receiver': bool,
    'tor2web_unauth': bool,
    'can_postpone_expiration': bool,
    'can_delete_submission': bool,
    'ahmia': bool,
    'allow_unencrypted': bool,
    'wizard_done': bool,
    'configured': bool,
    'disable_privacy_badge': bool,
    'disable_security_awareness_badge': bool,
    'disable_security_awareness_questions': bool,
    'disable_key_code_hint': bool,
    'enable_simplified_login': bool,
    'enable_custom_privacy_badge': bool,
    'custom_privacy_badge_tor': unicode,
    'custom_privacy_badge_none': unicode,
    'widget_comments_title': unicode,
    'widget_messages_title': unicode,
    'widget_files_title': unicode
}

TipOverviewDesc = {
    'context_id': uuid_regexp,
    'creation_lifetime': DateType,
    'receivertips': list,
    'creation_date': DateType,
    'context_name': unicode,
    'id': uuid_regexp,
    'wb_access_counter': int,
    'internalfiles': list,
    'comments': list,
    'wb_last_access': unicode,
    'expiration_date': DateType
}

TipsOverviewDesc = [TipOverviewDesc]

UserOverviewDesc = {
    'receivertips': list,
    'receiverfiles': list,
    'pgp_key_status': unicode,
    'id': uuid_regexp,
    'name': unicode
}

UsersOverviewDesc = [UserOverviewDesc]

FileOverviewDesc = {
    'rfiles': int,
    'stored': bool,
    'name': unicode,
    'content_type': unicode,
    'itip': uuid_regexp,
    'path': unicode,
    'creation_date': DateType,
    'id': uuid_regexp,
    'size': int
}

FilesOverviewDesc = [FileOverviewDesc]

StatsDesc = {
     'file_uploaded': int,
     'new_submission': int,
     'finalized_submission': int,
     'anon_requests': int,
     'creation_date': DateType
}

StatsCollectionDesc = [StatsDesc]

AnomalyDesc = {
     'message': unicode,
     'creation_date': DateType
}

AnomaliesCollectionDesc = [AnomalyDesc]

ReceiverDesc = {
     'name': unicode,
     'contexts': [uuid_regexp],
     'description': unicode,
     'presentation_order': int,
     'pgp_key_status': unicode,
     'id': uuid_regexp,
     'state': user_states_regexp
}

ReceiverCollectionDesc = [ReceiverDesc]

ContextDesc = {
    'select_all_receivers': bool,
    'name': unicode,
    'presentation_order': int,
    'description': unicode,
    'tip_timetolive': int,
    'maximum_selectable_receivers': int,
    'show_small_cards': bool,
    'show_receivers': bool,
    'enable_comments': bool,
    'enable_messages': bool,
    'enable_two_way_communication': bool,
    'enable_attachments': bool,
    'id': uuid_regexp,
    'receivers': [uuid_regexp],
    'show_receivers_in_alphabetical_order': bool
}

ContextCollectionDesc = [ContextDesc]

AhmiaDesc = {
    'description': unicode,
    'language': unicode,
    'title': unicode,
    'contactInformation': unicode,
    'relation': unicode,
    'keywords': unicode,
    'type': unicode
}

StaticFileDesc = {
    'size': int,
    'filelocation': unicode,
    'content_type': unicode,
    'filename': unicode
}

InternalTipDesc = {
    'wb_steps': list,
    'receivers': [uuid_regexp],
    'context_id': uuid_regexp,
    'creation_date': DateType,
    'new': bool,
    'id': uuid_regexp,
    'files': [uuid_regexp],
    'expiration_date': DateType
}

FieldOptionDesc = {
    'id': uuid_regexp_or_empty,
    'label': unicode,
    'presentation_order': int,
    'score_points': int,
    'activated_fields': [uuid_regexp_or_empty]
}

FieldDesc = {
    'template_id': uuid_regexp_or_empty,
    'step_id': uuid_regexp_or_empty,
    'fieldgroup_id': uuid_regexp_or_empty,
    'label': unicode,
    'description': unicode,
    'hint': unicode,
    'multi_entry': bool,
    'multi_entry_hint': unicode,
    'x': int,
    'y': int,
    'width': int,
    'required': bool,
    'preview': bool,
    'stats_enabled': bool,
    'type': field_type_regexp,
    'attrs': dict,
    'options': [FieldOptionDesc],
    'children': list,
    'is_template': bool,
}

WizardStepDesc = {
    'label': dict,
    'hint': dict,
    'description': dict,
    'children': list
}

WizardNodeDesc = {
    'presentation': dict,
    'footer': dict
}

WizardAppdataDesc = {
    'version': int,
    'fields': [WizardStepDesc],
    'node': WizardNodeDesc
}

WizardFirstSetupDesc = {
    'receiver': AdminReceiverDesc,
    'context': AdminContextDesc,
    'node': AdminNodeDesc
}

ExceptionDesc = {
    'errorUrl': unicode,
    'errorMessage': unicode,
    'stackTrace': list,
    'agent': unicode
}

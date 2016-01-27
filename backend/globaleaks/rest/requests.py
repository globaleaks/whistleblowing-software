# -*- coding: UTF-8
#   Requests
#   ********
#
# This file contains the specification of all the requests that can be made by a
# GLClient to a GLBackend.
# These specifications may be used with rest.validateMessage() inside each of the API
# handler in order to verify if the request is correct.

from globaleaks import models
from globaleaks.utils.structures import get_raw_request_format

uuid_regexp                       = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$'
uuid_regexp_or_empty              = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$|^$'
user_roles_regexp                 = r'^(admin|custodian|receiver)$'
user_states_regexp                = r'^(enabled|disabled)$'
receiver_img_regexp               = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).png$'
email_regexp                      = r'^(([\w+-\.]){0,100}[\w]{1,100}@([\w+-\.]){0,100}[\w]{1,100})$'
email_regexp_or_empty             = r'^(([\w+-\.]){0,100}[\w]{1,100}@([\w+-\.]){0,100}[\w]{1,100})$|^$'
hidden_service_regexp             = r'^http://[0-9a-z]{16}\.onion$'
hidden_service_regexp_or_empty    = r'^http://[0-9a-z]{16}\.onion$$|^$'
https_url_regexp                  = r'^https://([0-9a-z\-]+)\.(.*)$'
https_url_regexp_or_empty         = r'^https://([0-9a-z\-]+)\.(.*)$|^$'
landing_page_regexp               = r'^(homepage|submissionpage)$'
tip_operation_regexp              = r'^(postpone|set)$'
shorturl_regexp                   = r'^(\/s\/[a-z0-9]{1,30})$'
longurl_regexp                    = r'^(\/[a-z0-9=_\-%?\[\]\'\"]{0,255})$'

token_regexp                      = r'([a-zA-Z0-9]{42})'
token_type_regexp                 = r'^submission$'

field_instance_regexp             = (r'^('
                                     'instance|'
                                     'reference|'
                                     'template)$')

field_type_regexp                 = (r'^('
                                     'inputbox|'
                                     'textarea|'
                                     'multichoice|'
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

field_attr_type_regexp            = (r'^('
                                     'int|'
                                     'bool|'
                                     'unicode|'
                                     'localized)$')

identityaccessreply_regexp        = (r'^('
                                     'pending|'
                                     'authorized|'
                                     'denied)$')

class SkipSpecificValidation: pass

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
    'identity_provided': bool,
    'answers': dict,
}

UserUserDesc = {
    'username': unicode,
    'name': unicode,
    'description': unicode,
    'role': user_roles_regexp,
    'password': unicode,
    'old_password': unicode,
    'password_change_needed': bool,
    'deletable': bool,
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
    'password_change_needed': bool,
    'mail_address': email_regexp,
    'pgp_key_remove': bool,
    'pgp_key_fingerprint': unicode,
    'pgp_key_expiration': unicode,
    'pgp_key_info': unicode,
    'pgp_key_public': unicode,
    'pgp_key_status': unicode,
    'tip_notification': bool,
    'language': unicode,
    'timezone': int
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
    'args': dict
}

WhisleblowerIdentityAnswers = {
    'identity_field_id': uuid_regexp,
    'identity_field_answers': dict
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
    'can_grant_permissions': bool,
    'ahmia': bool,
    'allow_unencrypted': bool,
    'allow_iframes_inclusion': bool,
    'disable_privacy_badge': bool,
    'disable_security_awareness_badge': bool,
    'disable_security_awareness_questions': bool,
    'disable_key_code_hint': bool,
    'disable_donation_panel': bool,
    'simplified_login': bool,
    'enable_captcha': bool,
    'enable_proof_of_work': bool,
    'enable_experimental_features': bool,
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
    'widget_files_title': unicode,
    'threshold_free_disk_megabytes_high': int,
    'threshold_free_disk_megabytes_medium': int,
    'threshold_free_disk_megabytes_low': int,
    'threshold_free_disk_percentage_high': int,
    'threshold_free_disk_percentage_medium': int,
    'threshold_free_disk_percentage_low': int
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
    'receiver_notification_limit_reached_mail_template': unicode,
    'receiver_notification_limit_reached_mail_title': unicode,
    'tip_expiration_mail_template': unicode,
    'tip_expiration_mail_title': unicode,
    'identity_access_authorized_mail_template': unicode,
    'identity_access_authorized_mail_title': unicode,
    'identity_access_denied_mail_template': unicode,
    'identity_access_denied_mail_title': unicode,
    'identity_access_request_mail_template': unicode,
    'identity_access_request_mail_title': unicode,
    'identity_provided_mail_template': unicode,
    'identity_provided_mail_title': unicode,
    'export_template': unicode,
    'export_message_whistleblower': unicode,
    'export_message_recipient': unicode,
    'admin_anomaly_mail_template': unicode,
    'admin_anomaly_mail_title': unicode,
    'admin_anomaly_activities': unicode,
    'admin_anomaly_disk_high': unicode,
    'admin_anomaly_disk_medium': unicode,
    'admin_anomaly_disk_low': unicode,
    'disable_admin_notification_emails': bool,
    'disable_custodian_notification_emails': bool,
    'disable_receiver_notification_emails': bool,
    'send_email_for_every_event': bool,
    'tip_expiration_threshold': int,
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

AdminFieldOptionDesc = {
    'id': uuid_regexp_or_empty,
    'label': unicode,
    'presentation_order': int,
    'score_points': int,
    'activated_fields': [uuid_regexp_or_empty],
    'activated_steps': [uuid_regexp_or_empty]
}

AdminFieldOptionDescRaw = get_raw_request_format(AdminFieldOptionDesc, models.FieldOption.localized_keys)

AdminFieldAttrDesc = {
    'id': uuid_regexp_or_empty,
    'name': unicode,
    'type': field_attr_type_regexp,
    'value': SkipSpecificValidation
}

AdminFieldAttrDescRaw = get_raw_request_format(AdminFieldAttrDesc, models.FieldAttr.localized_keys)

AdminFieldDesc = {
    'id': uuid_regexp_or_empty,
    'key': unicode,
    'instance': field_instance_regexp,
    'editable': bool,
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
    'options': [AdminFieldOptionDesc],
    'children': list
}

AdminFieldDescRaw = get_raw_request_format(AdminFieldDesc, models.Field.localized_keys)
AdminFieldDescRaw['options'] = [AdminFieldOptionDescRaw]
# AdminFieldDescRaw['attrs']; FIXME: we still miss a way for validating a hierarchy where
#                                    we have a variable dictionary like the attrs dictionary.

AdminStepDesc = {
    'id': uuid_regexp_or_empty,
    'label': unicode,
    'description': unicode,
    'children': [AdminFieldDesc],
    'context_id': uuid_regexp,
    'presentation_order': int
}

AdminStepDescRaw = get_raw_request_format(AdminStepDesc, models.Step.localized_keys)
AdminStepDescRaw['children'] = [AdminFieldDescRaw]

AdminContextDesc = {
    'id': uuid_regexp_or_empty,
    'name': unicode,
    'description': unicode,
    'maximum_selectable_receivers': int,
    'tip_timetolive': int,
    'receivers': [uuid_regexp],
    'show_context': bool,
    'select_all_receivers': bool,
    'show_recipients_details': bool,
    'allow_recipients_selection': bool,
    'show_small_cards': bool,
    'enable_comments': bool,
    'enable_messages': bool,
    'enable_two_way_comments': bool,
    'enable_two_way_messages': bool,
    'enable_attachments': bool,
    'presentation_order': int,
    'show_receivers_in_alphabetical_order': bool,
    'questionnaire_layout': unicode,
    'steps': [AdminStepDesc],
    'reset_questionnaire': bool
}

AdminContextDescRaw = get_raw_request_format(AdminContextDesc, models.Context.localized_keys)
AdminContextDescRaw['steps'] = [AdminStepDescRaw]

AdminReceiverDesc = {
    'id': uuid_regexp_or_empty,
    'contexts': [uuid_regexp],
    'can_delete_submission': bool,
    'can_postpone_expiration': bool,
    'can_grant_permissions': bool,
    'tip_notification': bool,
    'presentation_order': int,
    'configuration': unicode
}

AdminShortURLDesc = {
    'shorturl': shorturl_regexp,
    'longurl': longurl_regexp
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
    'can_grant_permissions': bool,
    'ahmia': bool,
    'allow_unencrypted': bool,
    'disable_privacy_badge': bool,
    'disable_security_awareness_badge': bool,
    'disable_security_awareness_questions': bool,
    'disable_key_code_hint': bool,
    'simplified_login': bool,
    'enable_captcha': bool,
    'enable_proof_of_work':  bool,
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

ReceiverIdentityAccessRequestDesc = {
    'request_motivation': unicode
}

CustodianIdentityAccessRequestDesc = {
    'reply': identityaccessreply_regexp,
    'reply_motivation': unicode
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
    'id': uuid_regexp,
    'name': unicode,
    'description': unicode,
    'presentation_order': int,
    'receivers': [uuid_regexp],
    'select_all_receivers': bool,
    'tip_timetolive': int,
    'show_context': bool,
    'show_recipients_details': bool,
    'allow_recipients_selection': bool,
    'show_small_cards': bool,
    'maximum_selectable_receivers': int,
    'enable_comments': bool,
    'enable_messages': bool,
    'enable_two_way_messages': bool,
    'enable_attachments': bool,
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
    'id': uuid_regexp,
    'new': bool,
    'context_id': uuid_regexp,
    'wb_steps': list,
    'receivers': [uuid_regexp],
    'files': [uuid_regexp],
    'creation_date': DateType,
    'expiration_date': DateType,
    'identity_provided': bool
}

WizardAdminDesc = {
    'password': unicode,
    'old_password': unicode,
    'mail_address': unicode
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
    'node': AdminNodeDesc,
    'admin': WizardAdminDesc,
    'receiver': AdminUserDesc,
    'context': AdminContextDesc
}

ExceptionDesc = {
    'errorUrl': unicode,
    'errorMessage': unicode,
    'stackTrace': list,
    'agent': unicode
}

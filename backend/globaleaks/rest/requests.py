# -*- coding: utf-8
#   Requests
#   ********
#
# This file contains the specification of all the requests that can be made by a
# GLClient to a GLBackend.
# These specifications may be used with rest.validateMessage() inside each of the API
# handler in order to verify if the request is correct.

import copy

from six import text_type
from globaleaks import models
from globaleaks.models.config import NotificationL10NFactory
from globaleaks.utils.sets import merge_dicts


key_regexp                        = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$|^[a-z_]{0,100}$'
key_regexp_or_empty               = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$|^[a-z_]{0,100}$|^$'
uuid_regexp                       = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$'
uuid_regexp_or_empty              = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$|^$'
user_role_regexp                  = r'^(admin|custodian|receiver)$'
user_state_regexp                 = r'^(enabled|disabled)$'
email_regexp                      = r'^(([\w+-\.]){0,100}[\w]{1,100}@([\w+-\.]){0,100}[\w]{1,100})$'
email_regexp_or_empty             = r'^(([\w+-\.]){0,100}[\w]{1,100}@([\w+-\.]){0,100}[\w]{1,100})$|^$'
onionservice_regexp_or_empty      = r'^[0-9a-z]{16}\.onion$|^$'
hostname_regexp                   = r'^[0-9a-z\-\.]+$'
hostname_regexp_or_empty          = r'^[0-9a-z\-\.]+$|^$'
subdomain_regexp                  = r'^[0-9a-z]+$'
subdomain_regexp_or_empty         = r'^[0-9a-z]+$|^$'
https_url_regexp                  = r'^https://([0-9a-z\-]+)\.(.*)$'
https_url_regexp_or_empty         = r'^https://([0-9a-z\-]+)\.(.*)$|^$'
landing_page_regexp               = r'^(homepage|submissionpage)$'
context_selector_type_regexp      = r'^(list|cards|search)$'
tip_operation_regexp              = r'^(postpone|set)$'
shorturl_regexp                   = r'^([a-z0-9_-]{1,30})$'
longurl_regexp                    = r'^(/[a-z0-9#=_&?/-]{1,255})$'
short_text_regexp                 = r'^.{1,255}$'

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
                                     'tos|'
                                     'fileupload|'
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

class SkipSpecificValidation:
    pass


def get_multilang_request_format(request_format, localized_strings):
    ret = copy.deepcopy(request_format)

    for ls in localized_strings:
        ret[ls] = dict

    return ret


DateType = r'(.*)'

# ContentType = r'(application|audio|text|video|image)'
# via stackoverflow:
# /^(application|audio|example|image|message|model|multipart|text|video)\/[a-zA-Z0-9]+([+.-][a-zA-z0-9]+)*$/
ContentType = r'(.*)'

AdminTenantDesc = {
    'label': text_type,
    'active': bool,
    'subdomain': subdomain_regexp_or_empty,
}

FileDesc = {
    'name': text_type,
    'description': text_type,
    'size': int,
    'content_type': ContentType,
    'date': DateType
}

AuthDesc = {
    'username': text_type,
    'password': text_type,
    'token': text_type
}

ReceiptAuthDesc = {
    'receipt': text_type
}


TokenReqDesc = {
    'type': token_type_regexp
}

TokenAnswerDesc = {
    'human_captcha_answer': int,
    'proof_of_work_answer': int
}

SubmissionDesc = {
    'context_id': uuid_regexp,
    'receivers': [uuid_regexp],
    'identity_provided': bool,
    'answers': dict,
    'total_score': int
}

UserUserDesc = {
    'username': text_type,
    'name': text_type,
    'description': text_type,
    'role': user_role_regexp,
    'password': text_type,
    'old_password': text_type,
    'password_change_needed': bool,
    'state': user_state_regexp,
    'mail_address': email_regexp,
    'pgp_key_remove': bool,
    'pgp_key_fingerprint': text_type,
    'pgp_key_expiration': text_type,
    'pgp_key_public': text_type,
    'language': text_type,
    'can_edit_general_settings': bool
}

AdminUserDesc = UserUserDesc # currently the same

ReceiverReceiverDesc = {
    'username': text_type,
    'name': text_type,
    'description': text_type,
    'role': user_role_regexp,
    'password': text_type,
    'old_password': text_type,
    'password_change_needed': bool,
    'mail_address': email_regexp,
    'pgp_key_remove': bool,
    'pgp_key_fingerprint': text_type,
    'pgp_key_expiration': text_type,
    'pgp_key_public': text_type,
    'tip_notification': bool,
    'language': text_type
}

ReceiverOperationDesc = {
    'operation': text_type,
    'rtips': [uuid_regexp]
}

CommentDesc = {
    'content': text_type
}

OpsDesc = {
  'operation': text_type,
  'args': dict,
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
    'name': text_type,
    'description': text_type,
    'presentation': text_type,
    'footer': text_type,
    'enable_disclaimer': bool,
    'disclaimer_title': text_type,
    'disclaimer_text': text_type,
    'rootdomain': hostname_regexp_or_empty,
    'whistleblowing_question': text_type,
    'whistleblowing_button': text_type,
    'whistleblowing_receipt_prompt': text_type,
    'tb_download_link': https_url_regexp,
    'languages_enabled': [text_type],
    'languages_supported': list,
    'default_language': text_type,
    'default_questionnaire': text_type,
    'maximum_filesize': int,
    'https_admin': bool,
    'https_custodian': bool,
    'https_whistleblower': bool,
    'https_receiver': bool,
    'can_postpone_expiration': bool,
    'can_delete_submission': bool,
    'can_grant_permissions': bool,
    'allow_indexing': bool,
    'allow_unencrypted': bool,
    'disable_encryption_warnings': bool,
    'allow_iframes_inclusion': bool,
    'disable_privacy_badge': bool,
    'disable_key_code_hint': bool,
    'disable_donation_panel': bool,
    'disable_submissions': bool,
    'simplified_login': bool,
    'enable_captcha': bool,
    'enable_proof_of_work': bool,
    'enable_experimental_features': bool,
    'enable_signup': bool,
    'signup_mode': text_type,
    'signup_fingerprint': bool,
    'signup_no_admin_user': bool,
    'signup_tos1_enable': bool,
    'signup_tos1_title': text_type,
    'signup_tos1_text': text_type,
    'signup_tos1_checkbox_label': text_type,
    'signup_tos2_enable': bool,
    'signup_tos2_title': text_type,
    'signup_tos2_text': text_type,
    'signup_tos2_checkbox_label': text_type,
    'enable_graphic_customization': bool,
    'enable_footer_customization': bool,
    'enable_custom_privacy_badge': bool,
    'custom_privacy_badge_text': text_type,
    'header_title_homepage': text_type,
    'header_title_submissionpage': text_type,
    'header_title_receiptpage': text_type,
    'header_title_tippage': text_type,
    'landing_page': landing_page_regexp,
    'context_selector_type': context_selector_type_regexp,
    'contexts_clarification': text_type,
    'show_contexts_in_alphabetical_order': bool,
    'show_small_context_cards': bool,
    'threshold_free_disk_megabytes_high': int,
    'threshold_free_disk_megabytes_low': int,
    'threshold_free_disk_percentage_high': int,
    'threshold_free_disk_percentage_low': int,
    'password_change_period': int,
    'wbtip_timetolive': int,
    'basic_auth': bool,
    'basic_auth_username': text_type,
    'basic_auth_password': text_type,
    'reachable_via_web': bool,
    'anonymize_outgoing_connections': bool,
    'enable_admin_exception_notification': bool,
    'enable_developers_exception_notification': bool,
    'ip_filter_authenticated_enable': bool,
    'ip_filter_authenticated': text_type,
    'enable_password_reset': bool,
    'enable_user_pgp_key_upload': bool
}

AdminNotificationDesc = merge_dicts({
    'smtp_server': text_type,
    'smtp_port': int,
    'smtp_security': text_type, # 'TLS' or 'SSL' only
    'smtp_authentication': bool,
    'smtp_username': text_type,
    'smtp_password': text_type,
    'smtp_source_name': text_type,
    'smtp_source_email': email_regexp,
    'disable_admin_notification_emails': bool,
    'disable_custodian_notification_emails': bool,
    'disable_receiver_notification_emails': bool,
    'tip_expiration_threshold': int,
    'notification_threshold_per_hour': int,
    'reset_templates': bool
  },
  {k: text_type for k in NotificationL10NFactory.keys}
)

AdminFieldOptionDesc = {
    'id': uuid_regexp_or_empty,
    'label': text_type,
    'presentation_order': int,
    'score_points': int,
    'trigger_field': uuid_regexp_or_empty
}

AdminFieldOptionDescRaw = get_multilang_request_format(AdminFieldOptionDesc, models.FieldOption.localized_keys)

AdminFieldAttrDesc = {
    'id': uuid_regexp_or_empty,
    'name': text_type,
    'type': field_attr_type_regexp,
    'value': SkipSpecificValidation
}

AdminFieldAttrDescRaw = get_multilang_request_format(AdminFieldAttrDesc, models.FieldAttr.localized_keys)

AdminFieldDesc = {
    'id': key_regexp_or_empty,
    'instance': field_instance_regexp,
    'editable': bool,
    'template_id': key_regexp_or_empty,
    'step_id': uuid_regexp_or_empty,
    'fieldgroup_id': key_regexp_or_empty,
    'label': text_type,
    'description': text_type,
    'hint': text_type,
    'multi_entry': bool,
    'multi_entry_hint': text_type,
    'x': int,
    'y': int,
    'width': int,
    'required': bool,
    'preview': bool,
    'stats_enabled': bool,
    'type': field_type_regexp,
    'attrs': dict,
    'options': [AdminFieldOptionDesc],
    'children': list,
    'triggered_by_score': int
}

AdminFieldDescRaw = get_multilang_request_format(AdminFieldDesc, models.Field.localized_keys)
AdminFieldDescRaw['options'] = [AdminFieldOptionDescRaw]
# AdminFieldDescRaw['attrs']; FIXME: we still miss a way for validating a hierarchy where
#                                    we have a variable dictionary like the attrs dictionary.

AdminStepDesc = {
    'id': uuid_regexp_or_empty,
    'label': text_type,
    'description': text_type,
    'children': [AdminFieldDesc],
    'questionnaire_id': key_regexp_or_empty,
    'presentation_order': int
}

AdminStepDescRaw = get_multilang_request_format(AdminStepDesc, models.Step.localized_keys)
AdminStepDescRaw['children'] = [AdminFieldDescRaw]

AdminQuestionnaireDesc = {
    'id': key_regexp_or_empty,
    'name': text_type,
    'steps': [AdminStepDesc]
}

AdminQuestionnaireDescRaw = get_multilang_request_format(AdminQuestionnaireDesc, models.Questionnaire.localized_keys)
AdminQuestionnaireDescRaw['steps'] = [AdminStepDescRaw]

AdminContextDesc = {
    'id': uuid_regexp_or_empty,
    'name': text_type,
    'description': text_type,
    'maximum_selectable_receivers': int,
    'tip_timetolive': int,
    'receivers': [uuid_regexp],
    'show_context': bool,
    'select_all_receivers': bool,
    'show_recipients_details': bool,
    'allow_recipients_selection': bool,
    'show_small_receiver_cards': bool,
    'enable_comments': bool,
    'enable_messages': bool,
    'enable_two_way_comments': bool,
    'enable_two_way_messages': bool,
    'enable_attachments': bool,
    'enable_rc_to_wb_files': bool,
    'presentation_order': int,
    'recipients_clarification': text_type,
    'status_page_message': text_type,
    'show_receivers_in_alphabetical_order': bool,
    'questionnaire_id': key_regexp_or_empty
}

AdminReceiverDesc = {
    'id': uuid_regexp_or_empty,
    'can_delete_submission': bool,
    'can_postpone_expiration': bool,
    'can_grant_permissions': bool,
    'tip_notification': bool,
    'configuration': text_type
}

AdminTLSCertFilesConfigDesc = {
    'priv_key': text_type,
    'chain': text_type,
    'cert': text_type,
}

AdminTLSCfgFileResourceDesc = {
    'name': text_type,
    'content': text_type,
}

AdminCSRFileDesc = {
    'name': short_text_regexp,
    'content': {
      'country': r'[A-Za-z]{2}',
      'province': short_text_regexp,
      'city': short_text_regexp,
      'company': short_text_regexp,
      'department': short_text_regexp,
      'email': email_regexp
    }
}

AdminShortURLDesc = {
    'shorturl': shorturl_regexp,
    'longurl': longurl_regexp
}

NodeDesc = {
    'name': text_type,
    'description': text_type,
    'presentation': text_type,
    'footer': text_type,
    'enable_disclaimer': bool,
    'disclaimer_title': text_type,
    'disclaimer_text': text_type,
    'hostname': hostname_regexp_or_empty,
    'rootdomain': hostname_regexp_or_empty,
    'tb_download_link': https_url_regexp,
    'languages_enabled': [text_type],
    'languages_supported': list,
    'default_language': text_type,
    'maximum_filesize': int,
    'https_admin': bool,
    'https_custodian': bool,
    'https_whistleblower': bool,
    'https_receiver': bool,
    'can_postpone_expiration': bool,
    'can_delete_submission': bool,
    'can_grant_permissions': bool,
    'allow_indexing': bool,
    'allow_unencrypted': bool,
    'disable_privacy_badge': bool,
    'disable_key_code_hint': bool,
    'simplified_login': bool,
    'enable_captcha': bool,
    'enable_proof_of_work':  bool,
    'enable_custom_privacy_badge': bool,
    'custom_privacy_badge_text': text_type
}

TipOverviewDesc = {
    'id': uuid_regexp,
    'context_id': uuid_regexp,
    'creation_date': DateType,
    'expiration_date': DateType
}

TipsOverviewDesc = [TipOverviewDesc]

FileOverviewDesc = {
    'id': uuid_regexp,
    'itip': uuid_regexp,
    'path': text_type
}

ReceiverIdentityAccessRequestDesc = {
    'request_motivation': text_type
}

CustodianIdentityAccessRequestDesc = {
    'reply': identityaccessreply_regexp,
    'reply_motivation': text_type
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
    'message': text_type,
    'creation_date': DateType
}

AnomalyCollectionDesc = [AnomalyDesc]

ReceiverDesc = {
    'name': text_type,
    'description': text_type,
    'id': uuid_regexp,
    'state': user_state_regexp,
    'can_delete_submission': bool,
    'can_postpone_expiration': bool,
    'can_grant_permissions': bool
}

ReceiverCollectionDesc = [ReceiverDesc]

ContextDesc = {
    'id': uuid_regexp,
    'name': text_type,
    'description': text_type,
    'presentation_order': int,
    'receivers': [uuid_regexp],
    'select_all_receivers': bool,
    'tip_timetolive': int,
    'show_context': bool,
    'show_recipients_details': bool,
    'allow_recipients_selection': bool,
    'show_small_receiver_cards': bool,
    'maximum_selectable_receivers': int,
    'enable_comments': bool,
    'enable_messages': bool,
    'enable_two_way_messages': bool,
    'enable_attachments': bool,
    'show_receivers_in_alphabetical_order': bool,
    'picture': text_type
}

ContextCollectionDesc = [ContextDesc]

PublicResourcesDesc = {
    'node': NodeDesc,
    'contexts': [ContextDesc],
    'receivers': [ReceiverDesc]
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

WizardDesc = {
    'node_language': text_type,
    'node_name': text_type,
    'admin_name': text_type,
    'admin_password': text_type,
    'admin_mail_address': text_type,
    'receiver_name': text_type,
    'receiver_mail_address': text_type,
    'profile': r'^(default)$',
    'enable_developers_exception_notification': bool
}

SignupDesc = {
    'subdomain': subdomain_regexp,
    'name': text_type,
    'surname': text_type,
    'role': text_type,
    'phone': text_type,
    'email': text_type,
    'use_case': text_type,
    'use_case_other': text_type,
    'organization_name': text_type,
    'organization_type': text_type,
    'organization_location1': text_type,
    'organization_location2': text_type,
    'organization_location3': text_type,
    'organization_location4': text_type,
    'organization_site': text_type,
    'organization_number_employees': text_type,
    'organization_number_users': text_type,
    'hear_channel': text_type,
    'tos1': bool,
    'tos2': bool
}

ExceptionDesc = {
    'errorUrl': text_type,
    'errorMessage': text_type,
    'stackTrace': list,
    'agent': text_type
}

PasswordResetDesc = {
    'username_or_email': text_type
}

GeneralSettingsDesc = {
    'name': text_type,
    'header_title_homepage': text_type,
    'presentation': text_type,
    'description': text_type,
    'whistleblowing_question': text_type,
    'whistleblowing_button': text_type,
    'footer': text_type
}

QuestionnaireDuplicationDesc = {
    'questionnaire_id': text_type,
    'new_name': text_type
}

SubmissionStatusDesc = {
    'label': text_type,
    'presentation_order': int
}

SubmissionSubStatusDesc = {
    'label': text_type,
    'presentation_order': int
}

UserTenantDesc = {
    'tenant_id': int
}

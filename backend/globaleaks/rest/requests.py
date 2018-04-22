# -*- coding: utf-8
#   Requests
#   ********
#
# This file contains the specification of all the requests that can be made by a
# GLClient to a GLBackend.
# These specifications may be used with rest.validateMessage() inside each of the API
# handler in order to verify if the request is correct.

import copy

from globaleaks import models
from globaleaks.models.config import NotificationL10NFactory
from globaleaks.utils.sets import merge_dicts


key_regexp                        = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$|^[a-z_]{0,100}$'
key_regexp_or_empty               = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$|^[a-z_]{0,100}$|^$'
uuid_regexp                       = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$'
uuid_regexp_or_empty              = r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$|^$'
user_roles_regexp                 = r'^(admin|custodian|receiver)$'
user_states_regexp                = r'^(enabled|disabled)$'
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
                                     'str|'
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
    'label': str,
    'active': bool,
    'subdomain': subdomain_regexp_or_empty,
}

FileDesc = {
    'name': str,
    'description': str,
    'size': int,
    'content_type': ContentType,
    'date': DateType
}

AuthDesc = {
    'username': str,
    'password': str,
    'token': str
}

ReceiptAuthDesc = {
    'receipt': str
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
    'username': str,
    'name': str,
    'description': str,
    'role': user_roles_regexp,
    'password': str,
    'old_password': str,
    'password_change_needed': bool,
    'state': user_states_regexp,
    'mail_address': email_regexp,
    'pgp_key_remove': bool,
    'pgp_key_fingerprint': str,
    'pgp_key_expiration': str,
    'pgp_key_public': str,
    'language': str
}

AdminUserDesc = UserUserDesc # currently the same

ReceiverReceiverDesc = {
    'username': str,
    'name': str,
    'description': str,
    'role': user_roles_regexp,
    'password': str,
    'old_password': str,
    'password_change_needed': bool,
    'mail_address': email_regexp,
    'pgp_key_remove': bool,
    'pgp_key_fingerprint': str,
    'pgp_key_expiration': str,
    'pgp_key_public': str,
    'tip_notification': bool,
    'language': str
}

ReceiverOperationDesc = {
    'operation': str,
    'rtips': [uuid_regexp]
}

CommentDesc = {
    'content': str
}

OpsDesc = {
  'operation': str,
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
    'name': str,
    'description': str,
    'presentation': str,
    'footer': str,
    'enable_disclaimer': bool,
    'disclaimer_title': str,
    'disclaimer_text': str,
    'rootdomain': hostname_regexp_or_empty,
    'whistleblowing_question': str,
    'whistleblowing_button': str,
    'whistleblowing_receipt_prompt': str,
    'tb_download_link': https_url_regexp,
    'languages_enabled': [str],
    'languages_supported': list,
    'default_language': str,
    'default_questionnaire': str,
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
    'enable_custom_privacy_badge': bool,
    'custom_privacy_badge_text': str,
    'header_title_homepage': str,
    'header_title_submissionpage': str,
    'header_title_receiptpage': str,
    'header_title_tippage': str,
    'landing_page': landing_page_regexp,
    'context_selector_type': context_selector_type_regexp,
    'contexts_clarification': str,
    'show_contexts_in_alphabetical_order': bool,
    'show_small_context_cards': bool,
    'threshold_free_disk_megabytes_high': int,
    'threshold_free_disk_megabytes_low': int,
    'threshold_free_disk_percentage_high': int,
    'threshold_free_disk_percentage_low': int,
    'wbtip_timetolive': int,
    'basic_auth': bool,
    'basic_auth_username': str,
    'basic_auth_password': str,
    'reachable_via_web': bool,
    'anonymize_outgoing_connections': bool,
    'enable_admin_exception_notification': bool,
    'enable_developers_exception_notification': bool
}

AdminNotificationDesc = merge_dicts({
    'smtp_server': str,
    'smtp_port': int,
    'smtp_security': str, # 'TLS' or 'SSL' only
    'smtp_username': str,
    'smtp_password': str,
    'smtp_source_name': str,
    'smtp_source_email': email_regexp,
    'disable_admin_notification_emails': bool,
    'disable_custodian_notification_emails': bool,
    'disable_receiver_notification_emails': bool,
    'tip_expiration_threshold': int,
    'notification_threshold_per_hour': int,
    'reset_templates': bool
  },
  {k: str for k in NotificationL10NFactory.keys}
)

AdminFieldOptionDesc = {
    'id': uuid_regexp_or_empty,
    'label': str,
    'presentation_order': int,
    'score_points': int,
    'trigger_field': uuid_regexp_or_empty
}

AdminFieldOptionDescRaw = get_multilang_request_format(AdminFieldOptionDesc, models.FieldOption.localized_keys)

AdminFieldAttrDesc = {
    'id': uuid_regexp_or_empty,
    'name': str,
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
    'label': str,
    'description': str,
    'hint': str,
    'multi_entry': bool,
    'multi_entry_hint': str,
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
    'label': str,
    'description': str,
    'children': [AdminFieldDesc],
    'questionnaire_id': key_regexp_or_empty,
    'presentation_order': int
}

AdminStepDescRaw = get_multilang_request_format(AdminStepDesc, models.Step.localized_keys)
AdminStepDescRaw['children'] = [AdminFieldDescRaw]

AdminQuestionnaireDesc = {
    'id': key_regexp_or_empty,
    'name': str,
    'steps': [AdminStepDesc]
}

AdminQuestionnaireDescRaw = get_multilang_request_format(AdminQuestionnaireDesc, models.Questionnaire.localized_keys)
AdminQuestionnaireDescRaw['steps'] = [AdminStepDescRaw]

AdminContextDesc = {
    'id': uuid_regexp_or_empty,
    'name': str,
    'description': str,
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
    'recipients_clarification': str,
    'status_page_message': str,
    'show_receivers_in_alphabetical_order': bool,
    'questionnaire_id': key_regexp_or_empty
}

AdminReceiverDesc = {
    'id': uuid_regexp_or_empty,
    'can_delete_submission': bool,
    'can_postpone_expiration': bool,
    'can_grant_permissions': bool,
    'tip_notification': bool,
    'configuration': str
}

AdminTLSCertFilesConfigDesc = {
    'priv_key': str,
    'chain': str,
    'cert': str,
}

AdminTLSCfgFileResourceDesc = {
    'name': str,
    'content': str,
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
    'name': str,
    'description': str,
    'presentation': str,
    'footer': str,
    'enable_disclaimer': bool,
    'disclaimer_title': str,
    'disclaimer_text': str,
    'hostname': hostname_regexp_or_empty,
    'rootdomain': hostname_regexp_or_empty,
    'tb_download_link': https_url_regexp,
    'languages_enabled': [str],
    'languages_supported': list,
    'default_language': str,
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
    'custom_privacy_badge_text': str
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
    'path': str
}

ReceiverIdentityAccessRequestDesc = {
    'request_motivation': str
}

CustodianIdentityAccessRequestDesc = {
    'reply': identityaccessreply_regexp,
    'reply_motivation': str
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
    'message': str,
    'creation_date': DateType
}

AnomalyCollectionDesc = [AnomalyDesc]

ReceiverDesc = {
    'name': str,
    'description': str,
    'id': uuid_regexp,
    'state': user_states_regexp,
    'can_delete_submission': bool,
    'can_postpone_expiration': bool,
    'can_grant_permissions': bool
}

ReceiverCollectionDesc = [ReceiverDesc]

ContextDesc = {
    'id': uuid_regexp,
    'name': str,
    'description': str,
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
    'picture': str
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
    'node_name': str,
    'admin_name': str,
    'admin_password': str,
    'admin_mail_address': str,
    'receiver_name': str,
    'receiver_mail_address': str,
    'profile': r'^(default)$',
    'enable_developers_exception_notification': bool
}

SignupDesc = {
    'subdomain': subdomain_regexp,
    'name': str,
    'surname': str,
    'email': str,
    'use_case': str,
    'use_case_other': str
}

ExceptionDesc = {
    'errorUrl': str,
    'errorMessage': str,
    'stackTrace': list,
    'agent': str
}

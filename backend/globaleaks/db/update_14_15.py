# -*- encoding: utf-8 -*-

"""
  Changes

    Node table:
      - introduced default_language and default_timezone

    User table:
      - introduced language and timezone

    Context table:
      - fields refactored entirely adding Field and Step table;
      - all data is migrated.

    InternalTip table:
      - changed from wb_fields to wb_steps; all data is migrated.
"""

import copy
from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import opportunistic_appdata_init
from globaleaks.models import Model, Field, FieldOption, Step, Context, db_forge_obj
from globaleaks.db.datainit import opportunistic_appdata_init
from globaleaks.utils.utility import datetime_null, uuid4

def every_language(default_text):
    return_dict = {}

    for code in LANGUAGES_SUPPORTED_CODES:
        return_dict.update({code : default_text})

    return return_dict

class Node_version_14(Model):
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    receipt_regexp = Unicode()
    languages_enabled = Pickle()
    default_language = Unicode()
    description = Pickle()
    presentation = Pickle()
    footer = Pickle()
    subtitle = Pickle()
    terms_and_conditions = Pickle()
    security_awareness_title = Pickle()
    security_awareness_text = Pickle()
    stats_update_time = Int()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    x_frame_options_mode = Unicode()
    x_frame_options_allow_from = Unicode()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    anomaly_checks = Bool()
    exception_email = Unicode()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()

class User_version_14(Model):
    __storm_table__ = 'user'
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()

class InternalTip_version_14(Model):
    __storm_table__ = 'internaltip'
    context_id = Unicode()
    wb_fields = Pickle()
    pertinence_counter = Int()
    expiration_date = DateTime()
    last_activity = DateTime()
    escalation_threshold = Int()
    access_limit = Int()
    download_limit = Int()
    mark = Unicode()

class Context_version_14(Model):
    __storm_table__ = 'context'
    unique_fields = Pickle()
    localized_fields = Pickle()
    selectable_receiver = Bool()
    escalation_threshold = Int()
    tip_max_access = Int()
    file_max_download = Int()
    file_required = Bool()
    tip_timetolive = Int()
    submission_timetolive = Int()
    last_update = DateTime()
    tags = Pickle()
    name = Pickle()
    description = Pickle()
    receiver_introduction = Pickle()
    fields_introduction = Pickle()
    select_all_receivers = Bool()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    maximum_selectable_receivers = Int()
    require_file_description = Bool()
    delete_consensus_percentage = Int()
    require_pgp = Bool()
    show_small_cards = Bool()
    show_receivers = Bool()
    enable_private_messages = Bool()
    presentation_order = Int()

class Receiver_version_14(Model):
    __storm_table__ = 'receiver'
    user_id = Unicode()
    name = Unicode()
    description = Pickle()
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()
    mail_address = Unicode()
    can_delete_submission = Bool()
    postpone_superpower = Bool()
    receiver_level = Int()
    last_update = DateTime()
    tags = Pickle()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()
    message_notification = Bool()
    presentation_order = Int()

class Notification_version_14(Model):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    encrypted_tip_template = Pickle()
    encrypted_tip_mail_title = Pickle()
    plaintext_tip_template = Pickle()
    plaintext_tip_mail_title = Pickle()
    encrypted_file_template = Pickle()
    encrypted_file_mail_title = Pickle()
    plaintext_file_template = Pickle()
    plaintext_file_mail_title = Pickle()
    encrypted_comment_template = Pickle()
    encrypted_comment_mail_title = Pickle()
    plaintext_comment_template = Pickle()
    plaintext_comment_mail_title = Pickle()
    encrypted_message_template = Pickle()
    encrypted_message_mail_title = Pickle()
    plaintext_message_template = Pickle()
    plaintext_message_mail_title = Pickle()
    zip_description = Pickle()

class Stats_version_14(Model):
    __storm_table__ = 'stats'
    content = Pickle()

class ApplicationData_version_14(Model):
    __storm_table__ = 'applicationdata'
    version = Int()
    fields = Pickle()

class Comment_version_14(Model):
    __storm_table__ = 'comment'
    internaltip_id = Unicode()
    author = Unicode()
    content = Unicode()
    system_content = Pickle()
    type = Unicode()
    mark = Unicode()

class Replacer1415(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: added default_language and default_timezone" \
              "whistleblowing_question, whistleblowing_button" % self.std_fancy

        appdata = opportunistic_appdata_init()

        old_node = self.store_old.find(self.get_right_model("Node", 14)).one()
        new_node = self.get_right_model("Node", 15)()

        for k, v in new_node._storm_columns.iteritems():

            if v.name == 'default_timezone':
                new_node.default_timezone= 0;
                continue

            if v.name == 'whistleblowing_question':
                new_node.whistleblowing_question = appdata['node']['whistleblowing_question']
                continue

            if v.name == 'whistleblowing_button':
                new_node.whistleblowing_button = appdata['node']['whistleblowing_button']
                continue

            if v.name == 'enable_custom_privacy_badge':
                new_node.enable_custom_privacy_badge = False
                continue

            if v.name == 'custom_privacy_badge_tbb':
                new_node.custom_privacy_badge_tbb = {'en': ''}
                continue

            if v.name == 'custom_privacy_badge_tor':
                new_node.custom_privacy_badge_tor = {'en': ''}
                continue

            if v.name == 'custom_privacy_badge_none':
                new_node.custom_privacy_badge_none = {'en': ''}
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_User(self):
        print "%s User migration assistant: (language, timezone," \
              "password_change_needed, password_change_date)" % self.std_fancy

        old_users = self.store_old.find(self.get_right_model("User", 14))

        for old_user in old_users:

            new_user = self.get_right_model("User", 15)()

            for k, v in new_user._storm_columns.iteritems():

                if v.name == 'language':
                    new_user.language = u'en'
                    continue

                if v.name == 'timezone':
                    new_user.timezone = 0
                    continue

                if v.name == 'password_change_needed':
                    new_user.password_change_needed = False
                    continue

                if v.name == 'password_change_date':
                    new_user.password_change_date = datetime_null()
                    continue

                setattr(new_user, v.name, getattr(old_user, v.name))

            self.store_new.add(new_user)

        self.store_new.commit()

    def migrate_Context(self):
        print "%s Context migration assistant" % self.std_fancy

        old_contexts = self.store_old.find(self.get_right_model("Context", 14))

        steps = opportunistic_appdata_init()['fields']
        tos_dict = copy.deepcopy(steps[1]['children'][0])
        tos_opt_dict = copy.deepcopy(tos_dict['options'][0])
        tos_opt_dict['number'] = 1
        print tos_opt_dict
        del tos_dict['children']
        del tos_dict['options']
        i = 1
        for step in steps:
            step['number'] = i
            del step['children']

            i += 1

        for old_context in old_contexts:

            new_context = self.get_right_model("Context", 15)()

            step1 = db_forge_obj(self.store_new, Step, steps[0])
            new_context.steps.add(step1)
            step2 = db_forge_obj(self.store_new, Step, steps[1])
            new_context.steps.add(step2)

            for k, v in new_context._storm_columns.iteritems():
                if v.name == 'steps':
                    continue

                setattr(new_context, v.name, getattr(old_context, v.name))

            for f in old_context.unique_fields:
                try:

                    field_dict = {}
                    field_dict['label'] = {}
                    field_dict['hint'] = {}
                    field_dict['description'] = {}
                    field_dict['multi_entry'] = False
                    field_dict['required'] = old_context.unique_fields[f]['required']
                    field_dict['preview'] = old_context.unique_fields[f]['preview']
                    field_dict['stats_enabled'] = False
                    field_dict['is_template'] = False
                    field_dict['x'] = 0
                    field_dict['y'] = old_context.unique_fields[f]['presentation_order']
                    if old_context.unique_fields[f]['type'] in ['email',
                                                                'phone',
                                                                'url',
                                                                'number',
                                                                'text']:
                        field_dict['type'] = 'inputbox'
                    elif old_context.unique_fields[f]['type'] in ['radio', 'select']:
                        field_dict['type'] = 'selectbox'
                    elif old_context.unique_fields[f]['type'] in ['multiple', 'checkboxes']:
                        field_dict['type'] = 'checkbox'
                    else:
                        field_dict['type'] = old_context.unique_fields[f]['type']

                    for l in old_context.localized_fields:
                        if f in old_context.localized_fields[l]:
                            field_dict['label'][l] = old_context.localized_fields[l][f]['name']
                            field_dict['hint'][l] = old_context.localized_fields[l][f]['hint']

                    field = db_forge_obj(self.store_new, Field, field_dict)

                    if field_dict['type'] in ['selectbox', 'checkbox'] and 'options' in old_context.unique_fields[f]:
                        j = 1
                        for o in old_context.unique_fields[f]['options']:
                            opt_dict = {}
                            opt_dict['number'] = j
                            opt_dict['field_id'] = field.id
                            opt_dict['attrs'] = {}
                            opt_dict['attrs']['name'] = {}
                            for lang in LANGUAGES_SUPPORTED_CODES:
                                opt_dict['attrs']['name'][lang] = o['name']
                            option = db_forge_obj(self.store_new, FieldOption, opt_dict)
                            field.options.add(option)
                            j += 1

                    step1.children.add(field)

                except:
                    continue

            tos_opt = db_forge_obj(self.store_new, FieldOption, tos_opt_dict)
            tos = db_forge_obj(self.store_new, Field, tos_dict)
            tos.options.add(tos_opt)
            step2.children.add(tos)

            self.store_new.add(new_context)

        self.store_new.commit()

    def migrate_Receiver(self):
        print "%s Receiver migration assistant: (configuration)" % self.std_fancy

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 14))

        for old_receiver in old_receivers:
            new_receiver = self.get_right_model("Receiver", 15)()

            for k, v in new_receiver._storm_columns.iteritems():

                if v.name == 'configuration':
                    new_receiver.configuration = 'default'
                    continue

                setattr(new_receiver, v.name, getattr(old_receiver, v.name) )

            self.store_new.add(new_receiver)
            self.store_new.commit()

    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant" % self.std_fancy
        steps = []

        steps.append(opportunistic_appdata_init()['fields'][0])

        i = 1
        for step in steps:
            step['number'] = i
            step['label'] = step['label']['en']
            step['hint'] = step['hint']['en']
            step['description'] = step['description']['en']
            step['children'] = []  # wipe out default fields

        old_itips = self.store_old.find(self.get_right_model("InternalTip", 14))
        context_model = self.get_right_model("Context", 14)
        for old_itip in old_itips:
            new_itip = self.get_right_model("InternalTip", 15)()
            try:
                wb_steps = copy.deepcopy(steps)
                wb_fields_copy = copy.deepcopy(old_itip.wb_fields)
                for wb_field in wb_fields_copy:
                    wb_fields_copy[wb_field]["id"] = ""
                    wb_fields_copy[wb_field]["step_id"] = ""
                    wb_fields_copy[wb_field]["fieldgroup_id"] = ""
                    wb_fields_copy[wb_field]["description"] = ""
                    wb_fields_copy[wb_field]["hint"] = ""
                    wb_fields_copy[wb_field]["multi_entry"] = False
                    wb_fields_copy[wb_field]["stats_enabled"] = False
                    wb_fields_copy[wb_field]["required"] = False
                    wb_fields_copy[wb_field]["is_template"] = False
                    wb_fields_copy[wb_field]["options"] = []
                    wb_fields_copy[wb_field]["y"] = wb_fields_copy[wb_field]['answer_order']
                    wb_fields_copy[wb_field]["x"] = 0
                    wb_fields_copy[wb_field]["preview"] = False
                    wb_fields_copy[wb_field]["children"] = []
                    wb_fields_copy[wb_field]["options"] = []
                    del wb_fields_copy[wb_field]['answer_order']
                    c = self.store_old.find(context_model, context_model.id == old_itip.context_id).one()
                    for f in c.unique_fields:
                        if f == wb_field:
                            wb_fields_copy[wb_field]['label'] = c.unique_fields[f]['name']
                            if c.unique_fields[f]['type'] in ['email',
                                                              'phone',
                                                              'url',
                                                              'number',
                                                              'text']:
                                wb_fields_copy[wb_field]['type'] = 'inputbox'
                            elif c.unique_fields[f]['type'] in ['radio', 'select']:
                                wb_fields_copy[wb_field]['type'] = 'selectbox'
                            elif c.unique_fields[f]['type'] in ['multiple', 'checkboxes']:
                                wb_fields_copy[wb_field]['type'] = 'checkbox'
                            else:
                                wb_fields_copy[wb_field]['type'] = c.unique_fields[f]['type']

                            if wb_fields_copy[wb_field]['type'] in ['selectbox', 'checkbox'] and \
                                    'options' in c.unique_fields[f]:

                                val = {}

                                j = 1
                                for o in c.unique_fields[f]['options']:
                                    opt_dict = {}
                                    opt_dict['id'] = uuid4()
                                    opt_dict['attrs'] = {}
                                    opt_dict['attrs']['name'] = o['name']
                                    opt_dict['value'] = ''

                                    wb_fields_copy[wb_field]['options'].append(opt_dict)

                                    if wb_fields_copy[wb_field]['type'] == 'checkbox':
                                        opt_name = o['name']
                                        if opt_name in wb_fields_copy[wb_field]["value"] and \
                                                wb_fields_copy[wb_field]["value"][opt_name]:
                                            opt_val = True
                                        else:
                                            opt_val = False

                                        val[opt_dict['id']] = {
                                            'order': j,
                                            'value': opt_val,
                                            'name': o['name']
                                        }
                                    j += 1

                                if wb_fields_copy[wb_field]['type'] == 'checkbox':
                                    wb_fields_copy[wb_field]["value"] = val
                                # else: it's already initialized with copy


                for f in wb_fields_copy:
                    wb_steps[0]['children'].append(wb_fields_copy[f])

                for k, v in new_itip._storm_columns.iteritems():
                    if v.name == 'wb_steps':
                        new_itip.wb_steps = wb_steps;
                        continue

                    setattr(new_itip, v.name, getattr(old_itip, v.name))
            except Exception as e:
                continue

            self.store_new.add(new_itip)

        self.store_new.commit()

    def migrate_Notification(self):
        print "%s Notification migration assistant: (admin_anomaly_template)" % self.std_fancy

        old_notification = self.store_old.find(self.get_right_model("Notification", 14)).one()
        new_notification = self.get_right_model("Notification", 15)()

        for k, v in new_notification._storm_columns.iteritems():

            if v.name == 'admin_anomaly_template':
                new_notification.admin_anomaly_template = every_language("")
                continue

            if v.name == 'pgp_expiration_alert':
                new_notification.pgp_expiration_alert = every_language("")
                continue

            if v.name == 'pgp_expiration_notice':
                new_notification.pgp_expiration_notice = every_language("")
                continue

            setattr(new_notification, v.name, getattr(old_notification, v.name) )

        self.store_new.add(new_notification)
        self.store_new.commit()

    def migrate_Stats(self):
        print "%s Stats migration assistant: trash all old stats" % self.std_fancy
        self.store_new.commit()

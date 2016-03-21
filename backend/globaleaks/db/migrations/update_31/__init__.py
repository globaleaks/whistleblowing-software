# -*- encoding: utf-8 -*-
import base64
import os
import shutil

from storm.locals import Int, Bool, Unicode, DateTime, JSON, ReferenceSet

from globaleaks.db.appdata import load_appdata
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin.field import db_import_fields
from globaleaks.handlers.admin.questionnaire import db_get_default_questionnaire_id
from globaleaks.models import Model, BaseModel, Questionnaire, Step, db_forge_obj
from globaleaks.settings import GLSettings


class Node_v_30(Model):
    __storm_table__ = 'node'
    version = Unicode()
    version_db = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    receipt_salt = Unicode()
    languages_enabled = JSON()
    default_language = Unicode()
    default_timezone = Int()
    description = JSON()
    presentation = JSON()
    footer = JSON()
    security_awareness_title = JSON()
    security_awareness_text = JSON()
    context_selector_label = JSON()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_custodian = Bool()
    tor2web_whistleblower = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    disable_encryption_warnings = Bool()
    allow_iframes_inclusion = Bool()
    submission_minimum_delay = Int()
    submission_maximum_ttl = Int()
    can_postpone_expiration = Bool()
    can_delete_submission = Bool()
    can_grant_permissions = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    disable_submissions = Bool()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()
    disable_key_code_hint = Bool()
    disable_donation_panel = Bool()
    enable_captcha = Bool()
    enable_proof_of_work = Bool()
    enable_experimental_features = Bool()
    whistleblowing_question = JSON()
    whistleblowing_button = JSON()
    simplified_login = Bool()
    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()
    header_title_homepage = JSON()
    header_title_submissionpage = JSON()
    header_title_receiptpage = JSON()
    header_title_tippage = JSON()
    widget_comments_title = JSON()
    widget_messages_title = JSON()
    widget_files_title = JSON()
    landing_page = Unicode()
    show_contexts_in_alphabetical_order = Bool()
    threshold_free_disk_megabytes_high = Int()
    threshold_free_disk_megabytes_medium = Int()
    threshold_free_disk_megabytes_low = Int()
    threshold_free_disk_percentage_high = Int()
    threshold_free_disk_percentage_medium = Int()
    threshold_free_disk_percentage_low = Int()


class User_v_30(Model):
    __storm_table__ = 'user'
    creation_date = DateTime()
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    deletable = Bool()
    name = Unicode()
    description = JSON()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    mail_address = Unicode()
    language = Unicode()
    timezone = Int()
    password_change_needed = Bool()
    password_change_date = DateTime()
    pgp_key_info = Unicode()
    pgp_key_fingerprint = Unicode()
    pgp_key_public = Unicode()
    pgp_key_expiration = DateTime()
    pgp_key_status = Unicode()


class Context_v_30(Model):
    __storm_table__ = 'context'
    show_small_cards = Bool()
    show_context = Bool()
    show_recipients_details = Bool()
    allow_recipients_selection = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    enable_comments = Bool()
    enable_messages = Bool()
    enable_two_way_comments = Bool()
    enable_two_way_messages = Bool()
    enable_attachments = Bool()
    tip_timetolive = Int()
    name = JSON()
    description = JSON()
    recipients_clarification = JSON()
    status_page_message = JSON()
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()
    questionnaire_id = Unicode()


class ReceiverTip_v_30(Model):
    __storm_table__ = 'receivertip'
    internaltip_id = Unicode()
    receiver_id = Unicode()
    last_access = DateTime()
    access_counter = Int()
    label = Unicode()
    can_access_whistleblower_identity = Bool()
    new = Int()


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for _, v in new_node._storm_columns.iteritems():
            if v.name == 'allow_indexing':
                new_node.allow_indexing = False
                continue

            if v.name == 'logo_id':
                try:
                    logo_path = os.path.join(GLSettings.static_path, 'logo.png')
                    if not os.path.exists(logo_path):
                        continue

                    logo = ''
                    with open(logo_path, 'r') as logo_file:
                        logo = logo_file.read()

                    new_node.logo =  self.model_to['Img']()
                    new_node.logo.data = base64.b64encode(logo)
                    os.remove(logo_path)

                except:
                    pass

                continue

            if v.name == 'basic_auth':
                new_node.basic_auth = False
                continue

            if v.name == 'basic_auth_username':
                new_node.basic_auth_username = u''
                continue

            if v.name == 'basic_auth_password':
                new_node.basic_auth_password = u''
                continue

            if v.name == 'contexts_clarification':
                new_node.contexts_clarification = old_node.context_selector_label
                continue

            if v.name == 'context_selector_type':
                new_node.context_selector_type = u'list'
                continue

            if v.name == 'show_small_context_cards':
                new_node.show_small_context_cards = False
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)

    def migrate_User(self):
        old_objs = self.store_old.find(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'img_id':
                    try:
                        img_path = os.path.join(GLSettings.static_path, old_obj.id + ".png")
                        if not os.path.exists(img_path):
                            continue

                        img = ''
                        with open(img_path, 'r') as img_file:
                            img = img_file.read()

                        new_node.picture =  self.model_to['Img']()
                        new_node.picture.data = base64.b64encode(img)
                        os.remove(img_path)

                    except:
                        pass

                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_Context(self):
        old_objs = self.store_old.find(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'img_id':
                    continue

                if v.name == 'show_small_receiver_cards':
                    new_obj.show_small_receiver_cards = old_obj.show_small_cards
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)


    def migrate_ReceiverTip(self):
        old_objs = self.store_old.find(self.model_from['ReceiverTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['ReceiverTip']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'enable_notifications':
                    new_obj.enable_notifications = True
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

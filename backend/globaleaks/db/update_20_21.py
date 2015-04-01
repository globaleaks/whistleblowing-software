# -*- encoding: utf-8 -*-

"""
  Changes (end2end encryption implemented)
    - Node: boolean if the system of encryption require
        file_encryption_e2e
            in migration time, if old keys are present, is set as False
            (by default, will be True)
        submission_data_e2e:
            can be disabled on demand by the admin, default True,
            but if E2E keys are missing is forge as False and submission permit
    - InternalTip:
        wb public key
        wb private key
        is_e2e_encrypted (information applied to the submission data)
    - Receiver: keep public and private key (RSA kind)
        Two new fields empty by default
    - WhistleblowerTip
        is kept 'receipt_hash' for hybrid behavior
        is add 'wb_signature' to support new
"""

from storm.locals import Int, Bool, Unicode, DateTime, JSON
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import load_appdata
from globaleaks.models import Model
from globaleaks.utils.utility import every_language



class Receiver_v_20(Model):
    """
    add below remove from comment here:
+    pgp_e2e_public
+    pgp_e2e_private
    """
    __storm_table__ = 'receiver'
    user_id = Unicode()
    name = Unicode()
    description = JSON()
    configuration = Unicode()
    pgp_key_info = Unicode()
    pgp_key_fingerprint = Unicode()
    pgp_key_public = Unicode()
    pgp_key_expiration = DateTime()
    pgp_key_status = Unicode()
    mail_address = Unicode()
    ping_mail_address = Unicode()
    can_delete_submission = Bool()
    postpone_superpower = Bool()
    last_update = DateTime()
    tip_notification = Bool()
    ping_notification = Bool()
    presentation_order = Int()


class WhistleblowerTip_v_20(Model):
    """
    added in this version 'wb_signature'
    """
    __storm_table__ = 'whistleblowertip'
    internaltip_id = Unicode()
    last_access = DateTime()
    receipt_hash = Unicode()
    access_counter = Int()


class Node_v_20(Model):
    """
    added below file_encryption_e2e, submission_data_e2e
    """
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    receipt_regexp = Unicode()
    languages_enabled = JSON()
    default_language = Unicode()
    default_timezone = Int()
    description = JSON()
    presentation = JSON()
    footer = JSON()
    security_awareness_title = JSON()
    security_awareness_text = JSON()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    allow_iframes_inclusion = Bool()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()
    disable_key_code_hint = Bool()
    whistleblowing_question = JSON()
    whistleblowing_button = JSON()
    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()
    header_title_homepage = JSON()
    header_title_submissionpage = JSON()
    header_title_receiptpage = JSON()
    landing_page = Unicode()
    exception_email = Unicode()

class InternalTip_v_20(Model):
    """
    add below remove from comment here:
+    wb_e2e_public
+    wb_e2e_private
+    is_e2e_encrypted
    """
    __storm_table__ = 'internaltip'
    context_id = Unicode()
    wb_steps = JSON()
    expiration_date = DateTime()
    last_activity = DateTime()
    new = Int()


class Replacer2021(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: Integrate E2E (disabled for old node)" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 20)).one()
        new_node = self.get_right_model("Node", 21)()

        for _, v in new_node._storm_columns.iteritems():

            if v.name == 'file_encryption_e2e':
                new_node.file_encryption_e2e = False
                continue

            if v.name == 'submission_data_e2e':
                new_node.submission_data_e2e = False
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant: Support E2E" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("InternalTip", 20))

        for old_obj in old_objs:

            new_obj = self.get_right_model("InternalTip", 21)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'wb_e2e_public':
                    new_obj.wb_e2e_public = None
                    continue

                if v.name == 'wb_e2e_private':
                    new_obj.wb_e2e_private = None
                    continue

                if v.name == 'is_e2e_encrypted':
                    new_obj.is_e2e_encrypted = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()


    def migrate_Receiver(self):
        print "%s Receiver migration assistant: Support E2E " % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Receiver", 20))

        for old_obj in old_objs:

            new_obj = self.get_right_model("Receiver", 21)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'pgp_e2e_public':
                    new_obj.pgp_e2e_public = None
                    continue

                if v.name == 'pgp_e2e_private':
                    new_obj.pgp_e2e_private = None
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

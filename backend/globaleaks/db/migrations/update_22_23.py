# -*- encoding: utf-8 -*-

import copy
import json

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference, ReferenceSet

from globaleaks.db.base_updater import TableReplacer
from globaleaks.handlers.admin.field import db_update_fieldattr
from globaleaks.handlers.submission import db_save_questionnaire_answers, \
    extract_answers_preview
from globaleaks.models import Model, ArchivedSchema
from globaleaks.security import sha256
from globaleaks.settings import GLSetting


class InternalFile_v_22(Model):
    __storm_table__ = 'internalfile'
    creation_date = DateTime()
    internaltip_id = Unicode()
    name = Unicode()
    file_path = Unicode()
    content_type = Unicode()
    size = Int()
    new = Int()


class Comment_v_22(Model):
    __storm_table__ = 'comment'
    creation_date = DateTime()
    internaltip_id = Unicode()
    author = Unicode()
    content = Unicode()
    system_content = JSON()
    type = Unicode()
    new = Int(default=True)


class Context_v_22(Model):
    __storm_table__ = 'context'
    show_small_cards = Bool()
    show_receivers = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    enable_comments = Bool()
    enable_private_messages = Bool()
    tip_timetolive = Int()
    last_update = DateTime()
    name = JSON()
    description = JSON()
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()


class Field_v_22(Model):
    __storm_table__ = 'field'
    label = JSON()
    description = JSON()
    hint = JSON()
    multi_entry = Bool()
    required = Bool()
    preview = Bool()
    stats_enabled = Bool()
    is_template = Bool()
    x = Int()
    y = Int()
    type = Unicode()


class FieldOption_v_22(Model):
    __storm_table__ = 'fieldoption'
    field_id = Unicode()
    presentation_order = Int()
    attrs = JSON()


Field_v_22.options = ReferenceSet(
    Field_v_22.id,
    FieldOption_v_22.field_id
)


class InternalTip_v_22(Model):
    __storm_table__ = 'internaltip'
    creation_date = DateTime()
    context_id = Unicode()
    wb_steps = JSON()
    preview = JSON()
    progressive = Int()
    tor2web = Bool()
    expiration_date = DateTime()
    last_activity = DateTime()
    new = Int()


class Notification_v_22(Model):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    torify = Int()
    admin_pgp_alert_mail_title = JSON()
    admin_pgp_alert_mail_template = JSON()
    admin_anomaly_mail_template = JSON()
    admin_anomaly_mail_title = JSON()
    admin_anomaly_disk_low = JSON()
    admin_anomaly_disk_medium = JSON()
    admin_anomaly_disk_high = JSON()
    admin_anomaly_activities = JSON()
    tip_mail_template = JSON()
    tip_mail_title = JSON()
    file_mail_template = JSON()
    file_mail_title = JSON()
    comment_mail_template = JSON()
    comment_mail_title = JSON()
    message_mail_template = JSON()
    message_mail_title = JSON()
    tip_expiration_mail_template = JSON()
    tip_expiration_mail_title = JSON()
    pgp_alert_mail_title = JSON()
    pgp_alert_mail_template = JSON()
    receiver_notification_limit_reached_mail_template = JSON()
    receiver_notification_limit_reached_mail_title = JSON()
    zip_description = JSON()
    ping_mail_template = JSON()
    ping_mail_title = JSON()
    notification_digest_mail_title = JSON()
    disable_admin_notification_emails = Bool()
    disable_receivers_notification_emails = Bool()
    send_email_for_every_event = Bool()
    tip_expiration_threshold = Int()
    notification_threshold_per_hour = Int()
    notification_suspension_time=Int()


class Anomalies_v_22(Model):
    __storm_table__ = 'anomalies'
    stored_when = Unicode()
    alarm = Int()
    events = JSON()


class Replacer2223(TableReplacer):
    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant" % self.std_fancy

        def extract_answers_from_wb_field(wb_field, answers):
            answers[wb_field['id']] = {'0': {'0': wb_field['value']}}

            del wb_field['value']

            for c in wb_field['children']:
                extract_answers_from_wb_field(c, answers)

        def extract_answers_from_wb_steps(wb_steps):
            answers = {}

            for s in wb_steps:
                for f in s['children']:
                    answers[f['id']] = {'0': {'0': f['value']}}
                    del f['value']
                    for c in f['children']:
                        extract_answers_from_wb_field(c, answers)

            return wb_steps, answers

        def handle_internaltip_fixes(store, new_obj, old_obj):
            old_node = self.store_old.find(self.get_right_model("Node", 22)).one()

            questionnaire, answers = extract_answers_from_wb_steps(old_obj.wb_steps)

            new_obj.questionnaire_hash = sha256(json.dumps(questionnaire))

            aqs = store.find(ArchivedSchema,
                             ArchivedSchema.hash == unicode(new_obj.questionnaire_hash),
                             ArchivedSchema.type == u'questionnaire',
                             ArchivedSchema.language == unicode(old_node.default_language)).one()

            if not aqs:
                for lang in old_node.languages_enabled:
                    aqs = ArchivedSchema()
                    aqs.hash = new_obj.questionnaire_hash
                    aqs.type = u'questionnaire'
                    aqs.language = lang
                    aqs.schema = questionnaire
                    store.add(aqs)

                    preview = []
                    for s in aqs.schema:
                        for f in s['children']:
                            if f['preview']:
                                preview.append(f)

                    aqsp = ArchivedSchema()
                    aqsp.hash = new_obj.questionnaire_hash
                    aqsp.type = u'preview'
                    aqsp.language = lang
                    aqsp.schema = preview
                    store.add(aqsp)

            db_save_questionnaire_answers(store, new_obj, answers)

            new_obj.preview = extract_answers_preview(questionnaire, answers)

        old_objs = self.store_old.find(self.get_right_model("InternalTip", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("InternalTip", 23)()

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'questionnaire_hash' or v.name == 'preview':
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            handle_internaltip_fixes(self.store_new, new_obj, old_obj)

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_InternalFile(self):
        print "%s InternalFile migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("InternalFile", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("InternalFile", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'processing_attempts':
                    new_obj.processing_attempts = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Comment(self):
        print "%s Comment migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Comment", 22))

        for old_obj in old_objs:
            if old_obj.type == u'system':
                continue

            new_obj = self.get_right_model("Comment", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Context(self):
        print "%s Context migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Context", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("Context", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'steps_arrangement':
                    new_obj.steps_arrangement = 'horizontal'
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Field(self):
        print "%s Field migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Field", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("Field", 23)()

            if old_obj.type == 'inputbox' or old_obj.type == 'textarea':
                db_update_fieldattr(self.store_new, old_obj.id, {'name': u'min_len', 'type': u'int', 'value':'0'})
                db_update_fieldattr(self.store_new, old_obj.id, {'name': u'max_len', 'type': u'int', 'value':'-1'})
                db_update_fieldattr(self.store_new, old_obj.id, {'name': u'regexp', 'type': u'unicode', 'value':''})

            if old_obj.type == 'tos':
                db_update_fieldattr(self.store_new, old_obj.id, {'name': u'clause', 'type': u'localized', 'value': '{"en": ""}'})
                db_update_fieldattr(self.store_new, old_obj.id, {'name': u'agreement_statement', 'type':u'localized', 'value':'{"en": ""}'})

            for _, v in new_obj._storm_columns.iteritems():
                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_FieldOption(self):
        print "%s FieldOption migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("FieldOption", 22))

        for old_obj in old_objs:
            skip_add = False
            new_obj = self.get_right_model("FieldOption", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'score_points':
                    new_obj.score_points = 0
                    continue

                if v.name == 'label':
                    if 'name' in old_obj.attrs:
                        new_obj.label = old_obj.attrs['name']
                        continue
                    if 'clause' in old_obj.attrs:
                        db_update_fieldattr(self.store_new, old_obj.field_id, {'name': u'clause', 'type': u'localized', 'value': old_obj.attrs['clause']})
                        skip_add = True
                        break
                    if 'agreement_statement' in old_obj.attrs:
                        db_update_fieldattr(self.store_new, old_obj.field_id, {'name': u'clause', 'type': u'localized', 'value': old_obj.attrs['agreement_statement']})
                        skip_add = True
                        break
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            if not skip_add:
                self.store_new.add(new_obj)

        self.store_new.commit()

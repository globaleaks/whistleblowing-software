# -*- encoding: utf-8 -*-

import json

import os
from storm.locals import Int, Bool, Unicode, DateTime, JSON, ReferenceSet
from globaleaks.db.base_updater import TableReplacer
from globaleaks.handlers.admin.field import db_update_fieldattr
from globaleaks.handlers.submission import db_save_questionnaire_answers, \
    extract_answers_preview
from globaleaks.models import Model, ArchivedSchema
from globaleaks.security import sha256
from globaleaks.settings import GLSettings
from globaleaks.third_party.rstr import xeger


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


class Replacer2223(TableReplacer):
    def fix_field_answer_id(self, f):
        if f['id'] == '':
            xxx = self.store_old.find(self.get_right_model("Field", 22))
            for x in xxx:
                try:
                    if isinstance(x.label, dict):
                        for k, v in x.label.iteritems():
                            if unicode(v).find(unicode(f['label'])) != -1:
                                f['id'] = x.id
                                break
                    elif unicode(x.label).find(unicode(f['label'])) != -1:
                        f['id'] = x.id
                        break
                except:
                    pass

        return f['id']

    def extract_answers_from_wb_field(self, f):
        answers = {}

        if f['type'] == 'fieldgroup':
            for c in f['children']:
                self.fix_field_answer_id(c)
                if c['id'] != '':
                    answers[c['id']] = self.extract_answers_from_wb_field(c)
        elif f['type'] == 'checkbox':
            if 'value' in f:
                try:
                    for oid, ovalue in f['value'].iteritems():
                        if 'value' in ovalue:
                            answers[oid] = ovalue['value']
                        else:
                            answers[oid] = 'False'
                except:
                    pass
        else:
            if 'value' in f:
                answers['value'] = f['value']
            else:
                answers['value'] = ''

        if 'value' in f:
            del f['value']

        return [answers]

    def extract_answers_from_wb_steps(self, wb_steps):
        answers = {}

        for s in wb_steps:
            for f in s['children']:
                self.fix_field_answer_id(f)
                if f['id'] != '':
                    answers[f['id']] = self.extract_answers_from_wb_field(f)

        return wb_steps, answers

    def handle_internaltip_fixes(self, new_obj, old_obj):
        old_node = self.store_old.find(self.get_right_model("Node", 22)).one()

        questionnaire, answers = self.extract_answers_from_wb_steps(old_obj.wb_steps)

        new_obj.questionnaire_hash = sha256(json.dumps(questionnaire))

        aqs = self.store_new.find(self.get_right_model("ArchivedSchema", 23),
                                  self.get_right_model("ArchivedSchema", 23).hash == unicode(new_obj.questionnaire_hash),
                                  self.get_right_model("ArchivedSchema", 23).type == u'questionnaire',
                                  self.get_right_model("ArchivedSchema", 23).language == unicode(old_node.default_language)).one()

        if not aqs:
            for lang in old_node.languages_enabled:
                aqs = self.get_right_model("ArchivedSchema", 23)()
                aqs.hash = new_obj.questionnaire_hash
                aqs.type = u'questionnaire'
                aqs.language = lang
                aqs.schema = questionnaire
                self.store_new.add(aqs)

                preview = []
                for s in aqs.schema:
                    for f in s['children']:
                        if f['preview']:
                            preview.append(f)

                aqsp = self.get_right_model("ArchivedSchema", 23)()
                aqsp.hash = new_obj.questionnaire_hash
                aqsp.type = u'preview'
                aqsp.language = lang
                aqsp.schema = preview
                self.store_new.add(aqsp)

        db_save_questionnaire_answers(self.store_new, new_obj.id, answers)

        new_obj.preview = extract_answers_preview(questionnaire, answers)

    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("InternalTip", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("InternalTip", 23)()

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'questionnaire_hash' or v.name == 'preview':
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.handle_internaltip_fixes(new_obj, old_obj)

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

                if v.name == 'file_path':
                    new_obj.file_path = os.path.join(GLSettings.submission_path, "%s.aes" % xeger(r'[A-Za-z0-9]{16}'))
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Comment(self):
        print "%s Comment migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Comment", 22))

        for old_obj in old_objs:
            if old_obj.type == u'system':
                self.entries_count['Comment'] -= 1
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
                db_update_fieldattr(self.store_new, old_obj.id, u'min_len', {'name': u'min_len', 'type': u'int', 'value':'0'}, 'en')
                db_update_fieldattr(self.store_new, old_obj.id, u'max_len', {'name': u'max_len', 'type': u'int', 'value':'-1'}, 'en')
                db_update_fieldattr(self.store_new, old_obj.id, u'regex', {'name': u'regexp', 'type': u'unicode', 'value':''}, 'en')

            if old_obj.type == 'tos':
                db_update_fieldattr(self.store_new, old_obj.id, u'clause', {'name': u'clause', 'type': u'localized', 'value': '{"en": ""}'}, 'en')
                db_update_fieldattr(self.store_new, old_obj.id, u'agreement_statement', {'name': u'agreement_statement', 'type':u'localized', 'value':'{"en": ""}'}, 'en')

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'template_id':
                    # simply skip so to inizialize to NULL
                    continue

                if v.name == 'width':
                    new_obj.width = 0
                    continue

                if v.name == 'multi_entry_hint':
                    new_obj.multi_entry_hint = {'en': ''}
                    continue

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
                        db_update_fieldattr(self.store_new, old_obj.field_id, 'clause', {'name': u'clause', 'type': u'localized', 'value': old_obj.attrs['clause']}, 'en')
                        skip_add = True
                    if 'agreement_statement' in old_obj.attrs:
                        db_update_fieldattr(self.store_new, old_obj.field_id, 'agreement_statement', {'name': u'agreement_statement', 'type': u'localized', 'value': old_obj.attrs['agreement_statement']}, 'en')
                        skip_add = True
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            if skip_add:
                self.entries_count['FieldOption'] -= 1
                continue

            self.store_new.add(new_obj)

        self.store_new.commit()

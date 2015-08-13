# -*- encoding: utf-8 -*-

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference, ReferenceSet
from globaleaks.db.base_updater import TableReplacer
from globaleaks.handlers.admin.field import db_update_fieldattr
from globaleaks.models import BaseModel, Model, Step, Receiver, ReceiverContext



class InternalFile_v_22(Model):
    __storm_table__ = 'internalfile'
    internaltip_id = Unicode()
    name = Unicode()
    file_path = Unicode()
    content_type = Unicode()
    size = Int()
    new = Int()


class Comment_v_22(Model):
    __storm_table__ = 'comment'
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

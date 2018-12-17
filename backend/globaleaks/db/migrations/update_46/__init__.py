# -*- coding: UTF-8
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.db.migrations.update import MigrationBase

class Context_v_45(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    show_steps_navigation_interface = Column(Boolean, default=True, nullable=False)
    show_small_receiver_cards = Column(Boolean, default=False, nullable=False)
    show_context = Column(Boolean, default=True, nullable=False)
    show_recipients_details = Column(Boolean, default=False, nullable=False)
    allow_recipients_selection = Column(Boolean, default=False, nullable=False)
    maximum_selectable_receivers = Column(Integer, default=0, nullable=False)
    select_all_receivers = Column(Boolean, default=True, nullable=False)
    enable_comments = Column(Boolean, default=True, nullable=False)
    enable_messages = Column(Boolean, default=False, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_two_way_messages = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_rc_to_wb_files = Column(Boolean, default=False, nullable=False)
    tip_timetolive = Column(Integer, default=30, nullable=False)
    name = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    recipients_clarification = Column(JSON, default=dict, nullable=False)
    status_page_message = Column(JSON, default=dict, nullable=False)
    show_receivers_in_alphabetical_order = Column(Boolean, default=True, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    questionnaire_id = Column(UnicodeText(36), default=u'default', nullable=False)
    additional_questionnaire_id = Column(UnicodeText(36))


class FieldOption_v_45(Model):
    __tablename__ = 'fieldoption'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(UnicodeText(36), nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    score_points = Column(Integer, default=0, nullable=False)
    trigger_field = Column(UnicodeText(36))


class Field_v_45(Model):
    __tablename__ = 'field'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    x = Column(Integer, default=0, nullable=False)
    y = Column(Integer, default=0, nullable=False)
    width = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    hint = Column(JSON, nullable=False)
    required = Column(Boolean, default=False, nullable=False)
    preview = Column(Boolean, default=False, nullable=False)
    multi_entry = Column(Boolean, default=False, nullable=False)
    multi_entry_hint = Column(JSON, nullable=False)
    triggered_by_score = Column(Integer, default=0, nullable=False)
    step_id = Column(UnicodeText(36))
    fieldgroup_id = Column(UnicodeText(36))
    type = Column(UnicodeText, default=u'inputbox', nullable=False)
    instance = Column(UnicodeText, default=u'instance', nullable=False)
    editable = Column(Boolean, default=True, nullable=False)
    template_id = Column(UnicodeText(36))
    template_override_id = Column(UnicodeText(36))
    encrypt = Column(Boolean, default=True, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_Field(self):
        old_objs = self.session_old.query(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.type == 'multichoice':
                new_obj.type = 'selectbox'

            self.session_new.add(new_obj)

    def migrate_FieldOption(self):
        old_objs = self.session_old.query(self.model_from['FieldOption'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldOption']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'score_type':
                    if old_obj.score_points != 0:
                        new_obj.score_type = 1
                    continue
                elif key in ['trigger_step', 'trigger_field_inverted', 'trigger_step_inverted']:
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def epilogue(self):
        tenants = self.session_new.query(self.model_from['Tenant'])
        for t in tenants:
            m = self.model_from['Config']
            a = self.session_new.query(m.value).filter(m.tid == t.id, m.var_name == u'ip_filter_authenticated_enable').one_or_none()
            b = self.session_new.query(m.value).filter(m.tid == t.id, m.var_name == u'ip_filter_authenticated').one_or_none()

            if a is None or b is None:
                continue

            for c in ['admin', 'custodian', 'receiver']:
                self.session_new.add(self.model_to['Config'](t.id, u'ip_filter_' + c + '_enable', a[0]))
                self.session_new.add(self.model_to['Config'](t.id, u'ip_filter_' + c, b[0]))
                self.entries_count['Config'] += 2

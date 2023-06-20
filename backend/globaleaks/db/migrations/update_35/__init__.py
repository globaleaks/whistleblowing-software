# -*- coding: utf-8
from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.properties import *
from globaleaks.settings import Settings
from globaleaks.utils.utility import datetime_now, datetime_null


class Context_v_34(models.Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    show_small_receiver_cards = Column(Boolean, default=False)
    show_context = Column(Boolean, default=True)
    show_recipients_details = Column(Boolean, default=False)
    allow_recipients_selection = Column(Boolean, default=False)
    maximum_selectable_receivers = Column(Integer, default=0)
    select_all_receivers = Column(Boolean, default=True)
    enable_two_way_comments = Column(Boolean, default=True)
    enable_attachments = Column(Boolean, default=True)
    tip_timetolive = Column(Integer, default=15)
    name = Column(JSON)
    description = Column(JSON)
    recipients_clarification = Column(JSON)
    status_page_message = Column(JSON)
    show_receivers_in_alphabetical_order = Column(Boolean, default=False)
    presentation_order = Column(Integer, default=0)
    questionnaire_id = Column(UnicodeText(36))
    img_id = Column(UnicodeText(36))


class WhistleblowerTip_v_34(models.Model):
    __tablename__ = 'whistleblowertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(UnicodeText(36))
    receipt_hash = Column(UnicodeText)
    access_counter = Column(Integer, default=0)


class InternalTip_v_34(models.Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    update_date = Column(DateTime, default=datetime_now)
    context_id = Column(UnicodeText(36))
    questionnaire_hash = Column(UnicodeText)
    preview = Column(JSON)
    progressive = Column(Integer, default=0)
    tor2web = Column(Boolean, default=False)
    total_score = Column(Integer, default=0)
    expiration_date = Column(DateTime)
    identity_provided = Column(Boolean, default=False)
    identity_provided_date = Column(DateTime, default=datetime_null)
    enable_two_way_comments = Column(Boolean, default=True)
    enable_attachments = Column(Boolean, default=True)
    enable_whistleblower_identity = Column(Boolean, default=False)
    wb_last_access = Column(DateTime, default=datetime_now)


class MigrationScript(MigrationBase):
    def migrate_Context(self):
        for old_obj in self.session_old.query(self.model_from['Context']):
            new_obj = self.model_to['Context']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'tip_timetolive':
                    tip_ttl = 5 * 365
                    if old_obj.tip_timetolive > tip_ttl:
                        # If data retention was larger than 5 years the intended goal was
                        # probably to keep the submission around forever.
                        new_obj.tip_timetolive = -1
                    elif old_obj.tip_timetolive < -1:
                        new_obj.tip_timetolive = -1
                    else:
                        new_obj.tip_timetolive = old_obj.tip_timetolive
                    continue

                elif key == 'enable_rc_to_wb_files':
                    new_obj.enable_rc_to_wb_files = False

                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_User(self):
        default_language = self.session_new.query(self.model_to['Config']).filter(self.model_to['Config'].var_name == 'default_language').one().value['v']
        enabled_languages = [r[0] for r in self.session_old.query(self.model_to['EnabledLanguage'].name)]

        for old_obj in self.session_old.query(self.model_from['User']):
            new_obj = self.model_to['User']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key in ['pgp_key_public', 'pgp_key_fingerprint'] and getattr(old_obj, key) is None:
                    setattr(new_obj, key, '')

                elif key in ['pgp_key_expiration'] and getattr(old_obj, key) is None:
                    setattr(new_obj, key, datetime_null())

                elif key == 'language' and getattr(old_obj, key) not in enabled_languages:
                    # fix users that have configured a language that has never been there
                    setattr(new_obj, key, default_language)

                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_WhistleblowerTip(self):
        for old_obj in self.session_old.query(self.model_from['WhistleblowerTip']):
            new_obj = self.model_to['WhistleblowerTip']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'id':
                    new_obj.id = old_obj.internaltip_id
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def epilogue(self):
        c = self.session_new.query(self.model_to['Config']).filter(self.model_to['Config'].var_name == 'wbtip_timetolive').one()
        if int(c.value['v']) < 5:
            c.value['v'] = 90
        elif int(c.value['v']) > 365 * 2:
            c.value['v'] = 365 * 2

        self.session_new.commit()

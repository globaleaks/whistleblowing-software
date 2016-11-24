# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.config import NodeFactory, NotificationFactory
from globaleaks.models.l10n import EnabledLanguage
from globaleaks.settings import GLSettings
from globaleaks.models import *


class Context_v_34(ModelWithID):
    __storm_table__ = 'context'
    show_small_receiver_cards = Bool(default=False)
    show_context = Bool(default=True)
    show_recipients_details = Bool(default=False)
    allow_recipients_selection = Bool(default=False)
    maximum_selectable_receivers = Int(default=0)
    select_all_receivers = Bool(default=True)
    enable_comments = Bool(default=True)
    enable_messages = Bool(default=False)
    enable_two_way_comments = Bool(default=True)
    enable_two_way_messages = Bool(default=True)
    enable_attachments = Bool(default=True)
    tip_timetolive = Int(default=15)
    name = JSON(validator=shortlocal_v)
    description = JSON(validator=longlocal_v)
    recipients_clarification = JSON()
    status_page_message = JSON()
    show_receivers_in_alphabetical_order = Bool(default=False)
    presentation_order = Int(default=0)
    questionnaire_id = Unicode()
    img_id = Unicode()

    localized_keys = ['name', 'description', 'recipients_clarification', 'status_page_message']


class WhistleblowerTip_v_34(ModelWithID):
    __storm_table__ = 'whistleblowertip'
    internaltip_id = Unicode()
    receipt_hash = Unicode()
    access_counter = Int(default=0)


class InternalTip_v_34(ModelWithID):
    __storm_table__ = 'internaltip'
    creation_date = DateTime(default_factory=datetime_now)
    update_date = DateTime(default_factory=datetime_now)
    context_id = Unicode()
    questionnaire_hash = Unicode()
    preview = JSON()
    progressive = Int(default=0)
    tor2web = Bool(default=False)
    total_score = Int(default=0)
    expiration_date = DateTime()
    identity_provided = Bool(default=False)
    identity_provided_date = DateTime(default_factory=datetime_null)
    enable_two_way_comments = Bool(default=True)
    enable_two_way_messages = Bool(default=True)
    enable_attachments = Bool(default=True)
    enable_whistleblower_identity = Bool(default=False)
    wb_last_access = DateTime(default_factory=datetime_now)


class MigrationScript(MigrationBase):
    # Trim a Config validator to fall within the range of the range_v object
    # This ensures that future update to the config dictionary will not fail
    # because an old value was set outside of the acceptable range.
    def trim_value_to_range(self, factory, name):
        cfg_v = factory.get_val(name)
        cfg_d = factory.group_desc[name]
        if cfg_v > cfg_d.validator.stop:
            nf.set_val(name, cfg_d.validator.stop)
        if cfg_v < cfg_d.validator.start:
            GLSettings.print_msg('[Warning!] Found field with negative value %s reseting to default' % s)
            nf.set_val(name, cfg_d.default)

    def prologue(self):
       nf = NodeFactory(self.store_old)
       self.trim_value_to_range(nf, 'wbtip_timetolive')
       self.trim_value_to_range(nf, 'submission_maximum_ttl')
       self.store_old.commit()

       # TODO include fix for PGP KEYS

    def migrate_Context(self):
        old_objs = self.store_old.find(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'tip_timetolive':
                    # NOTE hardcoded policy. . . .
                    tip_ttl = 5*365
                    if old_obj.tip_timetolive > tip_ttl:
                        GLSettings.print_msg('[WARNING] Found an expiration date longer than 5 years! Configuring tips to never expire.')
                        # If data retention was larger than 5 years the intended goal was 
                        # probably to keep the submission around forever.
                        new_obj.tip_timetolive = -1
                    elif old_obj.tip_timetolive < -1:
                        GLSettings.print_msg('[WARNING] Found a negative tip expiration! Configuring tips to never expire.')
                        new_obj.tip_timetolive = -1
                    else:
                        new_obj.tip_timetolive = old_obj.tip_timetolive
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_User(self):
        default_language = NodeFactory(self.store_old).get_val('default_language')
        enabled_languages = EnabledLanguage.list(self.store_old)

        old_objs = self.store_old.find(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name in ['pgp_key_public', 'pgp_key_fingerprint']:
                    if getattr(old_obj, v.name) is None:
                        setattr(new_obj, v.name, '')
                        continue

                elif v.name in ['pgp_key_expiration']:
                    if getattr(old_obj, v.name) is None:
                        setattr(new_obj, v.name, datetime_null())
                        continue

                elif v.name == 'language' and getattr(old_obj, v.name) not in enabled_languages:
                    # fix users that have configured a language that has never been there
                    setattr(new_obj, v.name, default_language)
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_WhistleblowerTip(self):
        old_objs = self.store_old.find(self.model_from['WhistleblowerTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['WhistleblowerTip']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'id':
                    new_obj.id = old_obj.internaltip_id
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

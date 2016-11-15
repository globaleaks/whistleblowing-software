# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.config import NodeFactory, NotificationFactory
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
                        GLSettings.print_msg('[WARNING] This update changes the servers submission retention policy')
                        # If data retention was larger than 5 years the intended goal was 
                        # probably to keep the submission around forever.
                        new_obj.tip_timetolive = -1
                    elif old_obj.tip_timetolive < -1:
                        GLSettings.print_msg('[WARNING] Found tip_ttl with negative value %s reseting to default')
                        new_obj.tip_timetolive = Context.tip_timetolive.default
                    else:
                        new_obj.tip_timetolive = old_obj.tip_timetolive
                    continue
                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

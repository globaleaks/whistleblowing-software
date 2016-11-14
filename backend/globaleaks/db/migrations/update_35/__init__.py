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

    tip_timetolive = Int(default=15) # in days
    # localized strings
    name = JSON(validator=shortlocal_v)
    description = JSON(validator=longlocal_v)
    recipients_clarification = JSON(validator=longlocal_v)

    status_page_message = JSON(validator=longlocal_v)

    show_receivers_in_alphabetical_order = Bool(default=False)

    presentation_order = Int(default=0)

    questionnaire_id = Unicode()

    img_id = Unicode()

    unicode_keys = ['questionnaire_id']


class MigrationScript(MigrationBase):

   def trim_value_to_range(factory, name):
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

       ntfn = NotificationFactory(self.store_old)
       self.trim_value_to_range(ntfn, 'tip_expiration_threshold')

       ctx = self.old_store.find(Context_v_34).one()

       # NOTE hardcoded policy. . . .
       tip_ttl = 5*365 #TODO
       if ctx.tip_timetolive > tip_ttl:
           GLSettings.print_msg('[WARNING] This update changes the servers submission retention policy')
           # If data retention was larger than 5 years the intended goal was 
           # probably to keep the submission around forever.
           ctx.tip_timetolive = -1
       if ctx.tip_timetolive < -1:
           GLSettings.print_msg('[WARNING] Found tip_ttl with negative value %s reseting to default')
           ctx.tip_timetolive = 15 # TODO reset to default

       self.old_store.commit()

       # TODO include fix for PGP KEYS

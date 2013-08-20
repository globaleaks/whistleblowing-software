# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, Context
from storm.locals import Bool, Pickle, Unicode, Int, DateTime

"""
The goal of this thing is to migrate something like this:


[
    {"name": {"en": "Short title"},
     "hint": {"en": "Describe your tip-off with a line/title"},
     "required": true,
     "presentation_order": 1,
     "value": "", 
     "key": "Short title",
     "type": "text"
    }, 
    {"name": {"en": "Full description"},
     "hint": {"en": "Describe the details of your tip-off"},
     "required": true,
     "presentation_order": 2,
     "value": "",
     "key": "Full description",
     "type": "text"},
    {"name": {"en": "Files description"},
     "hint": {"en": "Describe the submitted files"},
     "required": false, "presentation_order": 3,
     "value": "",
     "key": "Files description",
     "type": "text"}
]


to This

{'en':
    [{"name": "Short title",
     "hint": "Describe your tip-off with a line/title",
     "required": true,
     "presentation_order": 1,
     "value": "", 
     "key": "Short title",
     "type": "text"
    }, 
    {"name": "Full description"},
     "hint": "Describe the details of your tip-off",
     "required": true,
     "presentation_order": 2,
     "value": "",
     "key": "Full description",
     "type": "text"},
    {"name": "Files description"},
     "hint": "Describe the submitted files",
     "required": false,
     "presentation_order": 3,
     "value": "",
     "key": "Files description",
     "type": "text"}
    ]
}

"""

class Receiver_version_2(Model):
    __storm_table__ = 'receiver'

    name = Unicode()
    description = Pickle()
    username = Unicode()
    password = Unicode()
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()
    gpg_enable_files = Bool()
    notification_fields = Pickle()
    can_delete_submission = Bool()
    receiver_level = Int()
    failed_login = Int()
    last_update = DateTime()
    last_access = DateTime()
    tags = Pickle()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()

def get_all_languages(fields):
    all_languages = set()
    for field in fields:
        languages = field['name'].keys()
        for language in languages:
            all_languages.add(language)
    return all_languages

def fields_conversion(old_fields):

    default_language = 'en'
    all_languages = get_all_languages(old_fields)
    new_fields = {}
    for language in all_languages:
        import copy
        new_fields[language] = copy.deepcopy(old_fields)
        for idx, _ in enumerate(new_fields[language]):
            try:
                new_fields[language][idx]['name'] = unicode(old_fields[idx]['name'][language])
            except KeyError:
                new_fields[language][idx]['name'] = unicode(old_fields[idx]['name'][default_language])
            try:
                new_fields[language][idx]['hint'] = unicode(old_fields[idx]['hint'][language])
            except KeyError:
                new_fields[language][idx]['hint'] = unicode(old_fields[idx]['hint'][default_language])

    return new_fields

class Replacer23(TableReplacer):

    def migrate_Context(self):

        print "%s Context migration assistant, changing fields format: #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("Context", 2)).count() )

        # Remind: commonly here is searched for Context_version_$OLD, but in this rare case
        # there is not a change in the Model (only in the content of a single field)
        old_contexts = self.store_old.find(self.get_right_model("Context", 2))

        for ocntx in old_contexts:

            new_obj = self.get_right_model("Context", 3)()

            # the only conversion in this revision, its here:
            new_obj.fields = fields_conversion(ocntx.fields)

            new_obj.id = ocntx.id
            new_obj.creation_date = ocntx.creation_date
            new_obj.selectable_receiver = ocntx.selectable_receiver
            new_obj.escalation_threshold = ocntx.escalation_threshold
            new_obj.tip_max_access = ocntx.tip_max_access
            new_obj.file_max_download = ocntx.file_max_download
            new_obj.file_required = ocntx.file_required
            new_obj.tip_timetolive = ocntx.tip_timetolive
            new_obj.submission_timetolive = ocntx.submission_timetolive
            new_obj.last_update = ocntx.last_update
            new_obj.receipt_regexp = ocntx.receipt_regexp
            new_obj.file_required = ocntx.file_required
            new_obj.name = ocntx.name
            new_obj.description = ocntx.description
            new_obj.receipt_description = ocntx.receipt_description
            new_obj.submission_introduction =  ocntx.submission_introduction
            new_obj.submission_disclaimer = ocntx.submission_disclaimer
            new_obj.tags = ocntx.tags

            self.store_new.add(new_obj)
        self.store_new.commit()

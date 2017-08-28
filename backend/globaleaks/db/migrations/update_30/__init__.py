# -*- encoding: utf-8 -*-
import os
from storm.locals import Int, Bool, Unicode, JSON, ReferenceSet

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin.field import db_create_field
from globaleaks.models import ModelWithID, Model, db_forge_obj
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import read_json_file


class Node_v_29(ModelWithID):
    __storm_table__ = 'node'
    version = Unicode()
    version_db = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    receipt_salt = Unicode()
    languages_enabled = JSON()
    default_language = Unicode()
    default_timezone = Int()
    description = JSON()
    presentation = JSON()
    footer = JSON()
    security_awareness_title = JSON()
    security_awareness_text = JSON()
    context_selector_label = JSON()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_custodian = Bool()
    tor2web_whistleblower = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    allow_iframes_inclusion = Bool()
    submission_minimum_delay = Int()
    submission_maximum_ttl = Int()
    can_postpone_expiration = Bool()
    can_delete_submission = Bool()
    can_grant_permissions = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    disable_submissions = Bool()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()
    disable_key_code_hint = Bool()
    disable_donation_panel = Bool()
    enable_captcha = Bool()
    enable_proof_of_work = Bool()
    enable_experimental_features = Bool()
    whistleblowing_question = JSON()
    whistleblowing_button = JSON()
    simplified_login = Bool()
    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()
    header_title_homepage = JSON()
    header_title_submissionpage = JSON()
    header_title_receiptpage = JSON()
    header_title_tippage = JSON()
    widget_comments_title = JSON()
    widget_messages_title = JSON()
    widget_files_title = JSON()
    landing_page = Unicode()
    show_contexts_in_alphabetical_order = Bool()
    threshold_free_disk_megabytes_high = Int()
    threshold_free_disk_megabytes_medium = Int()
    threshold_free_disk_megabytes_low = Int()
    threshold_free_disk_percentage_high = Int()
    threshold_free_disk_percentage_medium = Int()
    threshold_free_disk_percentage_low = Int()


class Context_v_29(ModelWithID):
    __storm_table__ = 'context'
    show_small_cards = Bool()
    show_context = Bool()
    show_steps_navigation_bar = Bool()
    steps_navigation_requires_completion = Bool()
    show_recipients_details = Bool()
    allow_recipients_selection = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    enable_comments = Bool()
    enable_messages = Bool()
    enable_two_way_comments = Bool()
    enable_two_way_messages = Bool()
    enable_attachments = Bool()
    enable_whistleblower_identity = Bool()
    tip_timetolive = Int()
    name = JSON()
    description = JSON()
    recipients_clarification = JSON()
    questionnaire_layout = Unicode()
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()


class Step_v_29(ModelWithID):
    __storm_table__ = 'step'
    context_id = Unicode()
    label = JSON()
    description = JSON()
    presentation_order = Int()
    triggered_by_score = Int()


class FieldAnswer_v_29(ModelWithID):
    __storm_table__ = 'fieldanswer'
    internaltip_id = Unicode()
    key = Unicode(default=u'')
    is_leaf = Bool(default=True)
    value = Unicode(default=u'')


class FieldAnswerGroup_v_29(ModelWithID):
    __storm_table__ = 'fieldanswergroup'
    number = Int(default=0)
    fieldanswer_id = Unicode()


class FieldAnswerGroupFieldAnswer_v_29(Model):
    __storm_table__ = 'fieldanswergroup_fieldanswer'
    __storm_primary__ = 'fieldanswergroup_id', 'fieldanswer_id'

    fieldanswergroup_id = Unicode()
    fieldanswer_id = Unicode()


FieldAnswerGroup_v_29.fieldanswers = ReferenceSet(
    FieldAnswerGroup_v_29.id,
    FieldAnswerGroupFieldAnswer_v_29.fieldanswergroup_id,
    FieldAnswerGroupFieldAnswer_v_29.fieldanswer_id,
    FieldAnswer_v_29.id
)


class MigrationScript(MigrationBase):
    def prologue(self):
        default_questionnaire = read_json_file(os.path.join(GLSettings.questionnaires_path, 'default.json'))

        steps = default_questionnaire.pop('steps')

        questionnaire = db_forge_obj(self.store_new, self.model_to['Questionnaire'], default_questionnaire)
        questionnaire.key = u'default'

        for step in steps:
            f_children = step.pop('children')
            s = db_forge_obj(self.store_new, self.model_to['Step'], step)
            for child in f_children:
                child['step_id'] = s.id
                db_create_field(self.store_new, child, None)
            s.questionnaire_id = questionnaire.id

        self.store_new.commit()

    def migrate_Node(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for _, v in new_node._storm_columns.iteritems():
            if v.name == 'disable_encryption_warnings':
                new_node.disable_encryption_warnings = False
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)

    def migrate_FieldAnswer(self):
        old_objs = self.store_old.find(self.model_from['FieldAnswer'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldAnswer']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'fieldanswergroup_id':
                    old_ref = self.store_old.find(FieldAnswerGroupFieldAnswer_v_29,
                                                  FieldAnswerGroupFieldAnswer_v_29.fieldanswer_id == old_obj.id).one()
                    if old_ref is not None:
                        new_obj.fieldanswergroup_id = old_ref.fieldanswergroup_id
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_Context(self):
        # Migrated in the epilogue
        pass

    def migrate_Step(self):
        # Migrated in the epilogue
        pass

    def epilogue(self):
        self.fail_on_count_mismatch['Step'] = False
        self.fail_on_count_mismatch['Field'] = False
        self.fail_on_count_mismatch['FieldOption'] = False
        self.fail_on_count_mismatch['FieldAttr'] = False

        # Add the required references
        Context_v_29.steps = ReferenceSet(Context_v_29.id, Step_v_29.context_id)
        Step_v_29.children = ReferenceSet(Step_v_29.id, self.model_from['Field'].step_id)

        default_language = self.store_old.find(self.model_from['Node']).one().default_language

        old_contexts = self.store_old.find(self.model_from['Context'])
        for old_context in old_contexts:
            map_on_default = False
            new_questionnaire_id = None

            for old_step in old_context.steps:
                if old_step.children.count() != 4:
                    break

                for field in old_step.children:
                    if 'en' in field.label and field.label['en'] == 'Short title':
                        map_on_default = True
                        break

                if map_on_default:
                   break

            if not map_on_default:
                new_questionnaire = self.model_to['Questionnaire']()
                new_questionnaire.name = old_context.name[default_language] if default_language in old_context.name else ''
                new_questionnaire.layout = old_context.questionnaire_layout
                new_questionnaire.show_steps_navigation_bar = old_context.show_steps_navigation_bar
                new_questionnaire.steps_navigation_requires_completion = old_context.steps_navigation_requires_completion
                new_questionnaire.enable_whistleblower_identity = old_context.enable_whistleblower_identity
                self.store_new.add(new_questionnaire)
                new_questionnaire_id = new_questionnaire.id

                for old_step in old_context.steps:
                    new_step = self.model_to['Step']()
                    for _, v in new_step._storm_columns.iteritems():
                        if v.name == 'questionnaire_id':
                            new_step.questionnaire_id = new_questionnaire.id
                            continue

                        setattr(new_step, v.name, getattr(old_step, v.name))

                    self.store_new.add(new_step)

            new_context = self.model_to['Context']()
            for _, v in new_context._storm_columns.iteritems():
                if v.name == 'status_page_message':
                    new_context.status_page_message = ''
                    continue

                if v.name == 'questionnaire_id':
                    new_context.questionnaire_id = u'default' if new_questionnaire_id is None else new_questionnaire_id
                    continue

                setattr(new_context, v.name, getattr(old_context, v.name))

            self.store_new.add(new_context)

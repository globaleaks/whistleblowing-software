# -*- coding: UTF-8
#
# submission
# **********
#
# Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

import copy
import json

from storm.expr import And, In
from twisted.internet import defer

from globaleaks import models
from globaleaks.handlers.admin.context import db_get_context_steps
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.security import hash_password, sha256, generateRandomReceipt
from globaleaks.settings import GLSettings
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.utils.token import TokenList
from globaleaks.utils.utility import log, get_expiration, \
    datetime_now, datetime_never, datetime_to_ISO8601


def get_submission_sequence_number(itip):
    return "%s-%d" % (itip.creation_date.strftime("%Y%m%d"), itip.progressive)


def db_assign_submission_progressive(store):
    counter = store.find(models.Counter, models.Counter.key == u'submission_sequence').one()
    if not counter:
        counter = models.Counter({'key': u'submission_sequence'})
        store.add(counter)
    else:
        now = datetime_now()
        update = counter.update_date
        if ((now > counter.update_date) and (not((now.year == update.year) and
                                                     (now.month == update.month) and
                                                     (now.day == update.day)))):
            counter.counter = 1
        else:
            counter.counter += 1

        counter.update_date = now

    return counter.counter


def _db_get_archived_field_recursively(field, language):
    for key, value in field.get('attrs', {}).iteritems():
        if key not in field['attrs']: continue
        if 'type' not in field['attrs'][key]: continue

        if field['attrs'][key]['type'] == u'localized':
            if language in field['attrs'][key].get('value', []):
                field['attrs'][key]['value'] = field['attrs'][key]['value'][language]
            else:
                field['attrs'][key]['value'] = ""

    for o in field.get('options', []):
        get_localized_values(o, o, models.FieldOption.localized_keys, language)

    for c in field.get('children', []):
        _db_get_archived_field_recursively(c, language)

    return get_localized_values(field, field, models.Field.localized_keys, language)


def _db_get_archived_questionnaire_schema(store, hash, type, language):
    aqs = store.find(models.ArchivedSchema,
                     models.ArchivedSchema.hash == hash,
                     models.ArchivedSchema.type == type).one()

    if not aqs:
        log.err("Unable to find questionnaire schema with hash %s" % hash)
        questionnaire = []
    else:
        questionnaire = copy.deepcopy(aqs.schema)

    if type == 'questionnaire':
        for step in questionnaire:
            for field in step['children']:
                _db_get_archived_field_recursively(field, language)

            get_localized_values(step, step, models.Step.localized_keys, language)

    elif type == 'preview':
        for field in questionnaire:
            _db_get_archived_field_recursively(field, language)

    return questionnaire


def db_get_archived_questionnaire_schema(store, hash, language):
    return _db_get_archived_questionnaire_schema(store, hash, u'questionnaire', language)


def db_get_archived_preview_schema(store, hash, language):
    return _db_get_archived_questionnaire_schema(store, hash, u'preview', language)


def db_serialize_questionnaire_answers_recursively(answers):
    ret = {}

    for answer in answers:
        if answer.is_leaf:
            ret[answer.key] = answer.value
        else:
            ret[answer.key] = [db_serialize_questionnaire_answers_recursively(group.fieldanswers)
                               for group in answer.groups.order_by(models.FieldAnswerGroup.number)]
    return ret


def db_serialize_questionnaire_answers(store, usertip):
    internaltip = usertip.internaltip

    questionnaire = db_get_archived_questionnaire_schema(store, internaltip.questionnaire_hash, GLSettings.memory_copy.default_language)

    answers_ids = []
    filtered_answers_ids = []
    for s in questionnaire:
        for f in s['children']:
            if 'key' in f and f['key'] == 'whistleblower_identity':
                if isinstance(usertip, models.WhistleblowerTip) or \
                   f['attrs']['visibility_subject_to_authorization']['value'] == False or \
                   (isinstance(usertip, models.ReceiverTip) and usertip.can_access_whistleblower_identity):
                    answers_ids.append(f['id'])
                else:
                    filtered_answers_ids.append(f['id'])
            else:
                answers_ids.append(f['id'])

    answers = store.find(models.FieldAnswer, And(models.FieldAnswer.internaltip_id == internaltip.id,
                                                 In(models.FieldAnswer.key, answers_ids)))

    return db_serialize_questionnaire_answers_recursively(answers)


def db_save_questionnaire_answers(store, internaltip_id, entries):
    ret = []

    for key, value in entries.iteritems():
        field_answer = models.FieldAnswer({
            'internaltip_id': internaltip_id,
            'key': key
        })
        store.add(field_answer)
        if isinstance(value, list):
            field_answer.is_leaf = False
            field_answer.value = ""
            n = 0
            for entries in value:
                group = models.FieldAnswerGroup({
                  'fieldanswer_id': field_answer.id,
                  'number': n
                })
                store.add(group)
                group_elems = db_save_questionnaire_answers(store, internaltip_id, entries)
                for group_elem in group_elems:
                    group.fieldanswers.add(group_elem)
                n += 1
        else:
            field_answer.is_leaf = True
            field_answer.value = unicode(value)
        ret.append(field_answer)

    return ret


def extract_answers_preview(questionnaire, answers):
    preview = {}

    preview.update({f['id']: copy.deepcopy(answers[f['id']])
    for s in questionnaire for f in s['children'] if f['preview'] and f['id'] in answers})

    return preview


def db_archive_questionnaire_schema(store, questionnaire, questionnaire_hash):
    if store.find(models.ArchivedSchema,
                  models.ArchivedSchema.hash == questionnaire_hash).count() <= 0:

        aqs = models.ArchivedSchema()
        aqs.hash = questionnaire_hash
        aqs.type = u'questionnaire'
        aqs.schema = questionnaire
        store.add(aqs)

        aqsp = models.ArchivedSchema()
        aqsp.hash = questionnaire_hash
        aqsp.type = u'preview'
        aqsp.schema = [f for s in aqs.schema for f in s['children'] if f['preview']]
        store.add(aqsp)


def db_get_itip_receiver_list(store, itip, language):
    return [{
        "id": rtip.receiver.id,
        "name": rtip.receiver.user.public_name,
        "pgp_key_public": rtip.receiver.user.pgp_key_public,
        "last_access": datetime_to_ISO8601(rtip.last_access),
        "access_counter": rtip.access_counter,
    } for rtip in itip.receivertips]


def serialize_itip(store, internaltip, language):
    context = internaltip.context
    mo = Rosetta(context.localized_keys)
    mo.acquire_storm_object(context)

    return {
        'id': internaltip.id,
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'update_date': datetime_to_ISO8601(internaltip.update_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'progressive': internaltip.progressive,
        'sequence_number': get_submission_sequence_number(internaltip),
        'context_id': internaltip.context_id,
        'context_name': mo.dump_localized_key('name', language),
        'questionnaire': db_get_archived_questionnaire_schema(store, internaltip.questionnaire_hash, language),
        'receivers': db_get_itip_receiver_list(store, internaltip, language),
        'tor2web': internaltip.tor2web,
        'timetolive': context.tip_timetolive,
        'enable_comments': context.enable_comments,
        'enable_messages': context.enable_messages,
        'enable_two_way_comments': internaltip.enable_two_way_comments,
        'enable_two_way_messages': internaltip.enable_two_way_messages,
        'enable_attachments': internaltip.enable_attachments,
        'enable_whistleblower_identity': internaltip.enable_whistleblower_identity,
        'identity_provided': internaltip.identity_provided,
        'identity_provided_date': datetime_to_ISO8601(internaltip.identity_provided_date),
        'show_recipients_details': context.show_recipients_details,
        'status_page_message': mo.dump_localized_key('status_page_message', language),
        'wb_last_access': datetime_to_ISO8601(internaltip.wb_last_access),
        'wb_access_revoked': internaltip.is_wb_access_revoked()
    }


def serialize_usertip(store, usertip, language):
    internaltip = usertip.internaltip

    ret = serialize_itip(store, internaltip, language)
    ret['id'] = usertip.id
    ret['internaltip_id'] = internaltip.id
    ret['answers'] = db_serialize_questionnaire_answers(store, usertip)
    ret['total_score'] = usertip.internaltip.total_score

    return ret


def db_create_receivertip(store, receiver, internaltip):
    """
    Create models.ReceiverTip for the required tier of models.Receiver.
    """
    log.debug('Creating receivertip for receiver: %s' % receiver.id)

    receivertip = models.ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.receiver_id = receiver.id

    store.add(receivertip)

    return receivertip.id

def db_create_whistleblowertip(store, internaltip):
    """
    The plaintext receipt is returned only now, and then is
    stored hashed in the WBtip table
    """
    receipt = unicode(generateRandomReceipt())

    wbtip = models.WhistleblowerTip()
    wbtip.id = internaltip.id
    wbtip.receipt_hash = hash_password(receipt, GLSettings.memory_copy.private.receipt_salt)
    store.add(wbtip)

    return receipt, wbtip


@transact
def create_whistleblowertip(*args):
    return db_create_whistleblowertip(*args)[0] # here is exported only the receipt


def db_create_submission(store, request, uploaded_files, client_using_tor, language):
    answers = request['answers']

    context = store.find(models.Context, models.Context.id == request['context_id']).one()
    if not context:
        raise errors.ContextIdNotFound

    submission = models.InternalTip()

    submission.progressive = db_assign_submission_progressive(store)

    if context.tip_timetolive > -1:
        submission.expiration_date = get_expiration(context.tip_timetolive)
    else:
        submission.expiration_date = datetime_never()

    # this is get from the client as it the only possibility possible
    # that would fit with the end to end submission.
    # the score is only an indicator and not a critical information so we can accept to
    # be fooled by the malicious user.
    submission.total_score = request['total_score']

    # The status tor2web is used to keep track of the security level adopted by the whistleblower
    submission.tor2web = not client_using_tor

    submission.context_id = context.id

    submission.enable_two_way_comments = context.enable_two_way_comments
    submission.enable_two_way_messages = context.enable_two_way_messages
    submission.enable_attachments = context.enable_attachments
    submission.enable_whistleblower_identity = context.questionnaire.enable_whistleblower_identity

    if submission.enable_whistleblower_identity and request['identity_provided']:
        submission.identity_provided = True
        submission.identity_provided_date = datetime_now()

    try:
        questionnaire = db_get_context_steps(store, context.id, None)
        questionnaire_hash = unicode(sha256(json.dumps(questionnaire)))

        submission.questionnaire_hash = questionnaire_hash
        submission.preview = extract_answers_preview(questionnaire, answers)

        store.add(submission)

        db_archive_questionnaire_schema(store, questionnaire, questionnaire_hash)

        db_save_questionnaire_answers(store, submission.id, answers)
    except Exception as excep:
        log.err("Submission create: fields validation fail: %s" % excep)
        raise excep

    try:
        for filedesc in uploaded_files:
            new_file = models.InternalFile()
            new_file.name = filedesc['name']
            new_file.description = ""
            new_file.content_type = filedesc['type']
            new_file.size = filedesc['size']
            new_file.internaltip_id = submission.id
            new_file.submission = filedesc['submission']
            new_file.file_path = filedesc['path']
            store.add(new_file)
            log.debug("=> file associated %s|%s (%d bytes)" % (
                new_file.name, new_file.content_type, new_file.size))
    except Exception as excep:
        log.err("Submission create: unable to create db entry for files: %s" % excep)
        raise excep

    receipt, wbtip = db_create_whistleblowertip(store, submission)

    if submission.context.maximum_selectable_receivers > 0 and \
                    len(request['receivers']) > submission.context.maximum_selectable_receivers:
        raise errors.SubmissionValidationFailure("selected an invalid number of recipients")

    rtips = []
    for receiver in store.find(models.Receiver, In(models.Receiver.id, request['receivers'])):
        if submission.context not in receiver.contexts:
            continue

        if not GLSettings.memory_copy.allow_unencrypted and len(receiver.user.pgp_key_public) == 0:
            continue

        rtips.append(db_create_receivertip(store, receiver, submission))

    if len(rtips) == 0:
        raise errors.SubmissionValidationFailure("need at least one recipient")

    log.debug("The finalized submission had created %d models.ReceiverTip(s)" % len(rtips))

    submission_dict = serialize_usertip(store, wbtip, language)

    submission_dict.update({'receipt': receipt})

    return submission_dict


@transact
def create_submission(store, request, uploaded_files, client_using_tor, language):
    return db_create_submission(store, request, uploaded_files, client_using_tor, language)


class SubmissionInstance(BaseHandler):
    """
    The interface that creates, populates and finishes a submission.
    """
    check_roles = 'unauthenticated'

    def put(self, token_id):
        """
        Parameter: token_id
        Request: SubmissionDesc
        Response: SubmissionDesc

        PUT finalize the submission
        """
        request = self.validate_message(self.request.content.read(), requests.SubmissionDesc)

        # The get and use method will raise if the token is invalid
        token = TokenList.get(token_id)
        token.use()

        submission = create_submission(request,
                                       token.uploaded_files,
                                       self.request.client_using_tor,
                                       self.request.language)

        # Delete the token only when a valid submission has been stored in the DB
        TokenList.delete(token_id)

        return submission

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
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin.context import db_get_context_steps
from globaleaks.handlers.authentication import transport_security_check, unauthenticated, get_tor2web_header
from globaleaks.utils.token import TokenList
from globaleaks.rest import errors, requests
from globaleaks.security import hash_password, sha256
from globaleaks.settings import transact, GLSettings
from globaleaks.third_party import rstr
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.utility import log, utc_future_date, datetime_now, datetime_to_ISO8601

def _db_get_archived_fieldattr(fieldattr, language):
    return get_localized_values(fieldattr, fieldattr, models.FieldAttr.localized_strings, language)

def _db_get_archived_fieldoption(fieldoption, language):
    return get_localized_values(fieldoption, fieldoption, models.FieldOption.localized_strings, language)

def _db_get_archived_field_recursively(field, language):
    for key, value in field['attrs'].iteritems():
        if field['attrs'][key]['type'] == u'localized':
             if language in field['attrs'][key]['value']:
                 field['attrs'][key]['value'] = field['attrs'][key]['value'][language]
             else:
                 field['attrs'][key]['value'] = ""

    for o in field['options']:
        _db_get_archived_fieldoption(o, language)

    for c in field['children']:
        _db_get_archived_field_recursively(c, language)

    return get_localized_values(field, field, models.Field.localized_strings, language)


def _db_get_archived_questionnaire_schema(store, hash, type, language):
    aqs = store.find(models.ArchivedSchema,
                     models.ArchivedSchema.hash == hash,
                     models.ArchivedSchema.type == type).one()

    if not aqs:
        log.err("Unable to find questionnaire schema with hash %s" % hash)
        questionnaire = []
    else:
        questionnaire = copy.deepcopy(aqs.schema)

    for step in questionnaire:
        for field in step['children']:
            _db_get_archived_field_recursively(field, language)
        get_localized_values(step, step, models.Step.localized_strings, language)

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


def db_serialize_questionnaire_answers(store, internaltip):
    questionnaire = db_get_archived_questionnaire_schema(store, internaltip.questionnaire_hash, GLSettings.memory_copy.default_language)

    answers_ids = [f['id'] for s in questionnaire for f in s['children']]

    answers = store.find(models.FieldAnswer, And(models.FieldAnswer.internaltip_id == internaltip.id,
                                          In(models.FieldAnswer.key, answers_ids)))

    return db_serialize_questionnaire_answers_recursively(answers)


def db_save_questionnaire_answers_recursively(store, internaltip_id, entries):
    ret = []

    for key, value in entries.iteritems():
        field_answer = models.FieldAnswer()
        field_answer.internaltip_id = internaltip_id
        field_answer.key = key
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
                group_elems = db_save_questionnaire_answers_recursively(store, internaltip_id, entries)
                for group_elem in group_elems:
                    group.fieldanswers.add(group_elem)
                n += 1
        else:
            field_answer.is_leaf = True
            field_answer.value = unicode(value)
        ret.append(field_answer)

    return ret


def db_save_questionnaire_answers(store, internaltip, answers):
    return db_save_questionnaire_answers_recursively(store, internaltip.id, answers)


def extract_answers_preview(questionnaire, answers):
    preview = {}

    preview.update({f['id']: copy.deepcopy(answers[f['id']])
        for s in questionnaire for f in s['children'] if f['preview'] and f['id'] in answers})

    return preview


def wb_serialize_internaltip(store, internaltip):
    return {
        'id': internaltip.id,
        'context_id': internaltip.context_id,
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'whistleblower_provided_identity': internaltip.whistleblower_provided_identity,
        'answers': db_serialize_questionnaire_answers(store, internaltip),
        'files': [f.id for f in internaltip.internalfiles],
        'receivers': [r.id for r in internaltip.receivers]
    }


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


def db_create_receivertip(store, receiver, internaltip):
    """
    Create models.ReceiverTip for the required tier of models.Receiver.
    """
    log.debug('Creating models.ReceiverTip for receiver: %s' % receiver.id)

    receivertip = models.ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.receiver_id = receiver.id

    store.add(receivertip)

    return receivertip.id

def db_create_whistleblower_tip(store, internaltip):
    """
    The plaintext receipt is returned only now, and then is
    stored hashed in the WBtip table
    """
    wbtip = models.WhistleblowerTip()

    receipt = unicode(rstr.xeger(GLSettings.receipt_regexp))

    wbtip.receipt_hash = hash_password(receipt, GLSettings.memory_copy.receipt_salt)
    wbtip.access_counter = 0
    wbtip.internaltip_id = internaltip.id

    store.add(wbtip)

    created_rtips = [db_create_receivertip(store, receiver, internaltip) for receiver in internaltip.receivers]

    internaltip.new = False

    if len(created_rtips):
        log.debug("The finalized submissions had created %d models.ReceiverTip(s)" % len(created_rtips))

    return receipt


@transact
def create_whistleblower_tip(*args):
    return db_create_whistleblower_tip(*args)


def import_receivers(store, submission, receiver_id_list):
    context = submission.context

    if not len(receiver_id_list):
        log.err("models.Receivers required to be selected, not empty")
        raise errors.SubmissionValidationFailure("needed almost one receiver selected")

    if context.maximum_selectable_receivers and \
                    len(receiver_id_list) > context.maximum_selectable_receivers:
        raise errors.InvalidInputFormat("provided an invalid number of receivers")

    for receiver in store.find(models.Receiver, In(models.Receiver.id, receiver_id_list)):
        if context not in receiver.contexts:
            raise errors.InvalidInputFormat("forged receiver selection, you fuzzer! <:")

        try:
            if not GLSettings.memory_copy.allow_unencrypted and \
                            receiver.pgp_key_status != u'enabled':
                log.err("Encrypted only submissions are supported. Cannot select [%s]" % receiver.id)
                continue
            submission.receivers.add(receiver)
        except Exception as excep:
            log.err("models.Receiver %s can't be assigned to the tip [%s]" % (receiver.id, excep))
            continue

        log.debug("+receiver [%s] In tip (%s) #%d" % \
                  (receiver.user.name, submission.id, submission.receivers.count() ))
    if submission.receivers.count() == 0:
        log.err("models.Receivers required to be selected, not empty")
        raise errors.SubmissionValidationFailure("needed at least one receiver selected [2]")


def db_create_submission(store, token_id, request, t2w, language):
    # the .get method raise an exception if the token is invalid
    token = TokenList.get(token_id)

    token.use()

    answers = request['answers']

    context = store.find(models.Context, models.Context.id == request['context_id']).one()
    if not context:
        # this can happen only if the context is removed
        # between submission POST and PUT.. :) that's why is better just
        # ignore this check, take che cached and wait the reference below fault
        log.err("models.Context requested: [%s] not found!" % request['context_id'])
        raise errors.models.ContextIdNotFound

    submission = models.InternalTip()

    submission.whistleblower_provided_identity = request['whistleblower_provided_identity']

    submission.expiration_date = utc_future_date(seconds=context.tip_timetolive)
    submission.context_id = context.id
    submission.creation_date = datetime_now()

    # Tor2Web is spot in the handler and passed here, is done to keep track of the
    # security level adopted by the whistleblower
    submission.tor2web = t2w

    submission.enable_comments = context.enable_comments
    submission.enable_messages = context.enable_messages
    submission.enable_two_way_communication = context.enable_two_way_communication
    submission.enable_attachments = context.enable_attachments

    try:
        questionnaire = db_get_context_steps(store, context.id, None)
        questionnaire_hash = unicode(sha256(json.dumps(questionnaire)))

        submission.questionnaire_hash = questionnaire_hash
        submission.preview = extract_answers_preview(questionnaire, answers)

        store.add(submission)

        db_archive_questionnaire_schema(store, questionnaire, questionnaire_hash)

        db_save_questionnaire_answers(store, submission, answers)
    except Exception as excep:
        log.err("Submission create: fields validation fail: %s" % excep)
        raise excep

    try:
        import_receivers(store, submission, request['receivers'])
    except Exception as excep:
        log.err("Submission create: receivers import fail: %s" % excep)
        raise excep

    try:
        for filedesc in token.uploaded_files:
            associated_f = models.InternalFile()
            associated_f.name = filedesc['filename']
            associated_f.description = ""
            associated_f.content_type = filedesc['content_type']
            associated_f.size = filedesc['body_len']
            associated_f.internaltip_id = submission.id
            associated_f.file_path = filedesc['encrypted_path']
            store.add(associated_f)

            log.debug("=> file associated %s|%s (%d bytes)" % (
                associated_f.name, associated_f.content_type, associated_f.size))

    except Exception as excep:
        log.err("Unable to create a DB entry for file! %s" % excep)
        raise excep

    receipt = db_create_whistleblower_tip(store, submission)

    submission_dict = wb_serialize_internaltip(store, submission)

    submission_dict.update({'receipt': receipt})

    return submission_dict


@transact
def create_submission(store, token_id, request, t2w, language):
    return db_create_submission(store, token_id, request, t2w, language)


class SubmissionInstance(BaseHandler):
    """
    This is the interface for create, populate and complete a submission.
    """
    @transport_security_check('whistleblower')
    @unauthenticated
    @defer.inlineCallbacks
    def put(self, token_id):
        """
        Parameter: token_id
        Request: SubmissionDesc
        Response: SubmissionDesc

        PUT finalize the submission
        """
        request = self.validate_message(self.request.body, requests.SubmissionDesc)

        status = yield create_submission(token_id, request,
                                         get_tor2web_header(self.request.headers),
                                         self.request.language)
        self.set_status(202)  # Updated, also if submission if effectively created (201)
        self.finish(status)

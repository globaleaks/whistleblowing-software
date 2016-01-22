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
from globaleaks.orm import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin.context import db_get_context_steps
from globaleaks.handlers.authentication import transport_security_check, unauthenticated, get_tor2web_header
from globaleaks.utils.token import TokenList
from globaleaks.rest import errors, requests
from globaleaks.security import hash_password, sha256, generateRandomReceipt
from globaleaks.settings import GLSettings
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.utils.utility import log, utc_future_date, datetime_now, datetime_to_ISO8601, ISO8601_to_datetime


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
        if ((now > counter.update_date) and (not((now.year == update.year) and \
                                                 (now.month == update.month) and \
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

    for step in questionnaire:
        for field in step['children']:
            _db_get_archived_field_recursively(field, language)

        get_localized_values(step, step, models.Step.localized_keys, language)

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
        'show_recipients_details': context.show_recipients_details
    }

def serialize_internalfile(ifile):
    ifile_dict = {
        'id': ifile.id,
        'creation_date': datetime_to_ISO8601(ifile.internaltip.creation_date),
        'internaltip_id': ifile.internaltip_id,
        'name': ifile.name,
        'file_path': ifile.file_path,
        'content_type': ifile.content_type,
        'size': ifile.size,
    }

    return ifile_dict

def serialize_receiverfile(rfile):
    rfile_dict = {
        'id' : rfile.id,
        'creation_date': datetime_to_ISO8601(rfile.internaltip.creation_date),
        'internaltip_id': rfile.internaltip_id,
        'internalfile_id': rfile.internalfile_id,
        'receiver_id': rfile.receiver_id,
        'receivertip_id': rfile.receivertip_id,
        'file_path': rfile.file_path,
        'size': rfile.size,
        'downloads': rfile.downloads,
        'last_access': rfile.last_access,
        'status': rfile.status,
    }

    return rfile_dict


def serialize_usertip(store, usertip, language):
    internaltip = usertip.internaltip

    ret = serialize_itip(store, internaltip, language)
    ret['id'] = usertip.id
    ret['answers'] = db_serialize_questionnaire_answers(store, usertip)
    ret['last_access'] = datetime_to_ISO8601(usertip.last_access)
    ret['access_counter'] = usertip.access_counter

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

def db_create_whistleblower_tip(store, internaltip):
    """
    The plaintext receipt is returned only now, and then is
    stored hashed in the WBtip table
    """
    wbtip = models.WhistleblowerTip()

    receipt = unicode(generateRandomReceipt())

    wbtip.receipt_hash = hash_password(receipt, GLSettings.memory_copy.receipt_salt)
    wbtip.access_counter = 0
    wbtip.internaltip_id = internaltip.id

    store.add(wbtip)

    created_rtips = [db_create_receivertip(store, receiver, internaltip) for receiver in internaltip.receivers]

    internaltip.new = False

    if len(created_rtips):
        log.debug("The finalized submissions had created %d models.ReceiverTip(s)" % len(created_rtips))

    return receipt, wbtip


@transact
def create_whistleblower_tip(*args):
    return db_create_whistleblower_tip(*args)[0] # here is exported only the receipt


def import_receivers(store, submission, receiver_id_list):
    context = submission.context

    if not len(receiver_id_list):
        raise errors.SubmissionValidationFailure("needed almost one receiver selected [1]")

    if context.maximum_selectable_receivers and \
                    len(receiver_id_list) > context.maximum_selectable_receivers:
        raise errors.InvalidInputFormat("provided an invalid number of receivers")

    for receiver in store.find(models.Receiver, In(models.Receiver.id, receiver_id_list)):
        if context not in receiver.contexts:
            raise errors.InvalidInputFormat("forged receiver selection, you fuzzer! <:")

        if not GLSettings.memory_copy.allow_unencrypted and receiver.user.pgp_key_status != u'enabled':
            raise errors.SubmissionValidationFailure("the platform does not allow selection of receivers with encryption disabled")
            continue

        submission.receivers.add(receiver)

        log.debug("+receiver [%s] In tip (%s) #%d" % \
                  (receiver.user.name, submission.id, submission.receivers.count() ))
    if submission.receivers.count() == 0:
        raise errors.SubmissionValidationFailure("needed almost one receiver selected [2]")


def db_create_submission(store, token_id, request, t2w, language):
    # the .get method raise an exception if the token is invalid
    token = TokenList.get(token_id)

    token.use()

    answers = request['answers']

    context = store.find(models.Context, models.Context.id == request['context_id']).one()
    if not context:
        raise errors.ContextIdNotFound

    submission = models.InternalTip()

    submission.progressive = db_assign_submission_progressive(store)

    submission.expiration_date = utc_future_date(seconds=context.tip_timetolive)

    # The use of Tor2Web is detected by the basehandler and the status forwared  here;
    # The status is used to keep track of the security level adopted by the whistleblower
    submission.tor2web = t2w

    submission.context_id = context.id

    submission.enable_two_way_comments = context.enable_two_way_comments
    submission.enable_two_way_messages = context.enable_two_way_messages
    submission.enable_attachments = context.enable_attachments
    submission.enable_whistleblower_identity = context.enable_whistleblower_identity

    if context.enable_whistleblower_identity and request['identity_provided']:
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
        log.err("Submission create: unable to create db entry for files: %s" % excep)
        raise excep

    receipt, wbtip = db_create_whistleblower_tip(store, submission)

    submission_dict = serialize_usertip(store, wbtip, language)

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

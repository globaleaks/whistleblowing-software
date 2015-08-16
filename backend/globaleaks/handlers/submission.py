# -*- coding: UTF-8
#
# submission
# **********
#
# Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

import copy

import json

from storm.expr import In

from twisted.internet.defer import inlineCallbacks

from globaleaks.models import Node, Context, Receiver, \
    InternalTip, ReceiverTip, WhistleblowerTip, \
    InternalFile, FieldAnswer, ArchivedSchema
from globaleaks.anomaly import Alarm
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin import db_get_context_steps
from globaleaks.handlers.authentication import transport_security_check, unauthenticated, get_tor2web_header
from globaleaks.utils.token import Token, TokenList
from globaleaks.rest import errors, requests
from globaleaks.security import hash_password, sha256
from globaleaks.settings import transact, GLSetting
from globaleaks.third_party import rstr
from globaleaks.utils.utility import log, utc_future_date, datetime_now, datetime_to_ISO8601


def _db_get_archived_questionnaire_schema(store, hash, type, language):
    aqs = store.find(ArchivedSchema,
                     ArchivedSchema.hash == hash,
                     ArchivedSchema.type == type,
                     ArchivedSchema.language == unicode(language)).one()

    if not aqs:
        aqs = store.find(ArchivedSchema,
                         ArchivedSchema.hash == hash,
                         ArchivedSchema.type == type,
                         ArchivedSchema.language == unicode(GLSetting.memory_copy.default_language)).one()

    if not aqs:
        log.err("Unable to find questionnaire schema with hash %s" % hash)
        questionnaire = []
    else:
        questionnaire = aqs.schema

    return questionnaire


def db_get_archived_questionnaire_schema(store, hash, language):
    return _db_get_archived_questionnaire_schema(store, hash, u'questionnaire', language)


def db_get_archived_preview_schema(store, hash, language):
    return _db_get_archived_questionnaire_schema(store, hash, u'preview', language)


def db_serialize_questionnaire_answers(store, answers):
    ret = {}
    for answer in answers:
        if answer.field_id not in ret:
            ret[answer.field_id] = {}

        if answer.n not in ret[answer.field_id]:
            ret[answer.field_id][answer.n] = {}

        ret[answer.field_id][answer.n][answer.key] = answer.answer

    return ret


def db_save_questionnaire_answers(store, internaltip, answers):
    for id, entries in answers.iteritems():
        field_answer = FieldAnswer()
        for n, entry_n in entries.iteritems():
            for key, value in entry_n.iteritems():
                field_answer.internaltip_id = internaltip.id
                field_answer.field_id = id
                field_answer.n = int(n)
                field_answer.key = key
                field_answer.answer = unicode(value)
                store.add(field_answer)


def extract_answers_preview(questionnaire, answers):
    preview = {}
    for s in questionnaire:
        for f in s['children']:
            if f['preview'] and f['id'] in answers:
                preview[f['id']] = {}
                for n, entry_n in answers[f['id']].iteritems():
                    preview[f['id']][n] = {}
                    for key, value in entry_n.iteritems():
                        preview[f['id']][n][key] = value
    return preview


def wb_serialize_internaltip(store, internaltip):
    response = {
        'id': internaltip.id,
        'context_id': internaltip.context_id,
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'answers': db_serialize_questionnaire_answers(store, internaltip.answers),
        'files': [f.id for f in internaltip.internalfiles],
        'receivers': [r.id for r in internaltip.receivers]
    }

    return response


def db_archive_questionnaire_schema(store, submission):
    if (store.find(ArchivedSchema, 
                   ArchivedSchema.hash == submission.questionnaire_hash).count() <= 0):

        for lang in GLSetting.memory_copy.languages_enabled:
            aqs = ArchivedSchema()
            aqs.hash = submission.questionnaire_hash
            aqs.type = u'questionnaire'
            aqs.language = lang
            aqs.schema = db_get_context_steps(store, submission.context_id, lang)
            store.add(aqs)

            preview = []
            for s in aqs.schema:
                for f in s['children']:
                    if f['preview']:
                        preview.append(f)

            aqsp = ArchivedSchema()
            aqsp.hash = submission.questionnaire_hash
            aqsp.type = u'preview'
            aqsp.language = lang
            aqsp.schema = preview
            store.add(aqsp)


def db_create_receivertip(store, receiver, internaltip):
    """
    Create ReceiverTip for the required tier of Receiver.
    """
    log.debug('Creating ReceiverTip for receiver: %s' % receiver.id)

    receivertip = ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.receiver_id = receiver.id

    store.add(receivertip)

    return receivertip.id

def db_create_whistleblower_tip(store, internaltip):
    """
    The plaintext receipt is returned only now, and then is
    stored hashed in the WBtip table
    """
    wbtip = WhistleblowerTip()

    node = store.find(Node).one()

    receipt = unicode(rstr.xeger(GLSetting.receipt_regexp))

    wbtip.receipt_hash = hash_password(receipt, node.receipt_salt)
    wbtip.access_counter = 0
    wbtip.internaltip_id = internaltip.id

    store.add(wbtip)

    created_rtips = []

    for receiver in internaltip.receivers:
        rtip_id = db_create_receivertip(store, receiver, internaltip)

    internaltip.new = False

    if len(created_rtips):
        log.debug("The finalized submissions had created %d ReceiverTip(s)" % len(created_rtips))

    return receipt


@transact
def create_whistleblower_tip(*args):
    return db_create_whistleblower_tip(*args)


def import_receivers(store, submission, receiver_id_list):
    context = submission.context

    if not len(receiver_id_list):
        log.err("Receivers required to be selected, not empty")
        raise errors.SubmissionValidationFailure("needed almost one receiver selected")

    if context.maximum_selectable_receivers and \
                    len(receiver_id_list) > context.maximum_selectable_receivers:
        raise errors.InvalidInputFormat("provided an invalid number of receivers")

    for receiver in store.find(Receiver, In(Receiver.id, receiver_id_list)):
        if context not in receiver.contexts:
            raise errors.InvalidInputFormat("forged receiver selection, you fuzzer! <:")

        try:
            if not GLSetting.memory_copy.allow_unencrypted and \
                            receiver.pgp_key_status != u'enabled':
                log.err("Encrypted only submissions are supported. Cannot select [%s]" % receiver.id)
                continue
            submission.receivers.add(receiver)
        except Exception as excep:
            log.err("Receiver %s can't be assigned to the tip [%s]" % (receiver.id, excep))
            continue

        log.debug("+receiver [%s] In tip (%s) #%d" % \
                  (receiver.name, submission.id, submission.receivers.count() ))
    if submission.receivers.count() == 0:
        log.err("Receivers required to be selected, not empty")
        raise errors.SubmissionValidationFailure("needed at least one receiver selected [2]")


def verify_fields_recursively(fields, wb_fields):
    for f in fields:
        if f not in wb_fields:
            raise errors.SubmissionValidationFailure("missing field (no structure present): %s" % f)

        if fields[f]['required'] and ('value' not in wb_fields[f] or
                                              wb_fields[f]['value'] == ''):
            raise errors.SubmissionValidationFailure("missing required field (no value provided): %s" % f)

        if isinstance(wb_fields[f]['value'], unicode):
            if len(wb_fields[f]['value']) > GLSetting.memory_copy.maximum_textsize:
                raise errors.InvalidInputFormat("field value overcomes size limitation")

        indexed_fields = {}
        for f_c in fields[f]['children']:
            indexed_fields[f_c['id']] = copy.deepcopy(f_c)

        indexed_wb_fields = {}
        for f_c in wb_fields[f]['children']:
            indexed_wb_fields[f_c['id']] = copy.deepcopy(f_c)

        verify_fields_recursively(indexed_fields, indexed_wb_fields)

    for wbf in wb_fields:
        if wbf not in fields:
            raise errors.SubmissionValidationFailure("provided unexpected field %s" % wbf)

def db_create_submission(store, token_id, request, t2w, language):
    # the .get method raise an exception if the token is invalid
    token = TokenList.get(token_id)

    if not token.context_associated == request['context_id']:
        raise errors.InvalidInputFormat("Token context does not match the one specified in submission payload")

    token.validate(request)

    TokenList.delete(token_id)

    answers = request['answers']

    context = store.find(Context, Context.id == token.context_associated).one()
    if not context:
        # this can happen only if the context is removed
        # between submission POST and PUT.. :) that's why is better just
        # ignore this check, take che cached and wait the reference below fault
        log.err("Context requested: [%s] not found!" % token.context_associated)
        raise errors.ContextIdNotFound

    submission = InternalTip()

    submission.expiration_date = utc_future_date(seconds=context.tip_timetolive)
    submission.context_id = context.id
    submission.creation_date = datetime_now()

    # Tor2Web is spot in the handler and passed here, is done to keep track of the
    # security level adopted by the whistleblower
    submission.tor2web = t2w

    try:
        questionnaire = db_get_context_steps(store, context.id, GLSetting.memory_copy.default_language)
        questionnaire_hash = sha256(json.dumps(questionnaire))


        submission.questionnaire_hash = questionnaire_hash
        submission.preview = extract_answers_preview(questionnaire, answers)

        store.add(submission)

        db_archive_questionnaire_schema(store, submission)

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
            associated_f = InternalFile()
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


class SubmissionCreate(BaseHandler):
    """
    This class Request a token to create a submission.
    We keep the naming with "Create" suffix for internal globaleaks convention,
    but this handler do not interact with Database, InternalTip, Submissions, etc.
    """

    @transport_security_check('wb')
    @unauthenticated
    def post(self):
        """
        Request: None
        Response: SubmissionDesc (Token)
        Errors: ContextIdNotFound, InvalidInputFormat, SubmissionValidationFailure

        This API create a Token, a temporary memory only object able to keep
        track of the submission. If the system is under stress, complete the
        submission will require some actions to be performed before the
        submission can be concluded (e.g. hashcash and captchas).
        """
        if not GLSetting.memory_copy.accept_submissions:
            raise errors.SubmissionDisabled

        request = self.validate_message(self.request.body, requests.SubmissionDesc)

        token = Token('submission', request['context_id'])
        token.set_difficulty(Alarm().get_token_difficulty())
        token_answer = token.serialize_token()

        token_answer.update({'id': token_answer['token_id']})
        token_answer.update({'context_id': request['context_id']})
        token_answer.update({'receivers': []})
        token_answer.update({'answers': {}})
        token_answer.update({'human_captcha_answer': 0})
        token_answer.update({'graph_captcha_answer': ""})
        token_answer.update({'proof_of_work': 0})

        self.set_status(201)  # Created
        self.finish(token_answer)


class SubmissionInstance(BaseHandler):
    """
    This is the interface for create, populate and complete a submission.
    Relay in the client-server update and exchange of the submissionStatus message.
    """

    @transport_security_check('wb')
    @unauthenticated
    @inlineCallbacks
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

# -*- coding: utf-8 -*-
#
# Handlerse dealing with submission interface
import base64
import copy
import json
import os

from globaleaks import models
from globaleaks.handlers.admin.questionnaire import db_get_questionnaire
from globaleaks.handlers.base import connection_check, BaseHandler
from globaleaks.models import get_localized_values
from globaleaks.orm import db_get, transact
from globaleaks.rest import errors, requests
from globaleaks.state import State
from globaleaks.utils.crypto import sha256, Base64Encoder, GCE
from globaleaks.utils.json import JSONEncoder
from globaleaks.utils.utility import get_expiration, datetime_null, uuid4


class TempSubmission(object):
    id = None

    def __init__(self):
        self.id = uuid4()
        self.files = []

    def expireCallback(self):
        for f in self.files:
            try:
                os.path.remove(os.path.abspath(os.path.join(State.settings.tmp_path, f['filename'])))
            except Exception:
                pass


def initialize_submission():
    temp_submission = TempSubmission()
    State.TempSubmissions[temp_submission.id] = temp_submission
    return {'id': temp_submission.id}


def decrypt_tip(user_key, tip_prv_key, tip):
    tip_key = GCE.asymmetric_decrypt(user_key, tip_prv_key)

    for questionnaire in tip['questionnaires']:
        questionnaire['answers'] = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(questionnaire['answers'].encode())).decode())

    for k in ['whistleblower_identity']:
        if k in tip['data'] and tip['data'][k]:
            tip['data'][k] = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(tip['data'][k].encode())).decode())

            if k == 'whistleblower_identity' and isinstance(tip['data'][k], list):
                # Fix for issue: https://github.com/globaleaks/GlobaLeaks/issues/2612
                # The bug is due to the fact that the data was initially saved as an array of one entry
                tip['data'][k] = tip['data'][k][0]

    for x in tip['comments'] + tip['messages']:
        x['content'] = GCE.asymmetric_decrypt(tip_key, base64.b64decode(x['content'].encode())).decode()

    for x in tip['wbfiles'] + tip['rfiles']:
        for k in ['name', 'description', 'type', 'size']:
            if k in x:
                x[k] = GCE.asymmetric_decrypt(tip_key, base64.b64decode(x[k].encode())).decode()
                if k == 'size':
                    x[k] = int(x[k])

    return tip


def db_set_internaltip_answers(session, itip_id, questionnaire_hash, answers):
    x = session.query(models.InternalTipAnswers) \
               .filter(models.InternalTipAnswers.internaltip_id == itip_id,
                       models.InternalTipAnswers.questionnaire_hash == questionnaire_hash).one_or_none()

    if x is not None:
        return

    ita = models.InternalTipAnswers()
    ita.internaltip_id = itip_id
    ita.questionnaire_hash = questionnaire_hash
    ita.answers = answers
    session.add(ita)


def db_set_internaltip_data(session, itip_id, key, value):
    x = session.query(models.InternalTipData) \
               .filter(models.InternalTipData.internaltip_id == itip_id,
                       models.InternalTipData.key == key).one_or_none()

    if x is not None:
        return

    itd = models.InternalTipData()
    itd.internaltip_id = itip_id
    itd.key = key
    itd.value = value
    session.add(itd)


def db_assign_submission_progressive(session, tid):
    counter = session.query(models.Config).filter(models.Config.tid == tid, models.Config.var_name == 'counter_submissions').one()
    counter.value += 1
    return counter.value


def _db_serialize_archived_field_recursively(field, language):
    for key, _ in field.get('attrs', {}).items():
        if key not in field['attrs']:
            continue

        if 'type' not in field['attrs'][key]:
            continue

        if field['attrs'][key]['type'] == 'localized':
            if language in field['attrs'][key].get('value', []):
                field['attrs'][key]['value'] = field['attrs'][key]['value'][language]
            else:
                field['attrs'][key]['value'] = ""

    for o in field.get('options', []):
        get_localized_values(o, o, models.FieldOption.localized_keys, language)

    for c in field.get('children', []):
        _db_serialize_archived_field_recursively(c, language)

    return get_localized_values(field, field, models.Field.localized_keys, language)


def db_serialize_archived_questionnaire_schema(questionnaire_schema, language):
    questionnaire = copy.deepcopy(questionnaire_schema)

    for step in questionnaire:
        for field in step['children']:
            _db_serialize_archived_field_recursively(field, language)

        get_localized_values(step, step, models.Step.localized_keys, language)

    return questionnaire


def db_archive_questionnaire_schema(session, questionnaire):
    hash = str(sha256(json.dumps(questionnaire, sort_keys=True)))
    if session.query(models.ArchivedSchema).filter(models.ArchivedSchema.hash == hash).count():
        return hash

    aqs = models.ArchivedSchema()
    aqs.hash = hash
    aqs.schema = questionnaire
    session.add(aqs)

    return hash


def db_get_itip_receiver_list(session, itip):
    ret = []

    for rtip in session.query(models.ReceiverTip).filter(models.ReceiverTip.internaltip_id == itip.id):
        ret.append({
            "id": rtip.receiver_id,
            "last_access": rtip.last_access,
            "access_counter": rtip.access_counter,
        })

    return ret


def serialize_itip(session, internaltip, language):
    x = session.query(models.InternalTipAnswers, models.ArchivedSchema) \
               .filter(models.ArchivedSchema.hash == models.InternalTipAnswers.questionnaire_hash,
                       models.InternalTipAnswers.internaltip_id == internaltip.id)

    questionnaires = []
    for ita, aqs in x:
        questionnaires.append({
            'steps': db_serialize_archived_questionnaire_schema(aqs.schema, language),
            'answers': ita.answers
        })

    return {
        'id': internaltip.id,
        'creation_date': internaltip.creation_date,
        'update_date': internaltip.update_date,
        'expiration_date': internaltip.expiration_date,
        'progressive': internaltip.progressive,
        'context_id': internaltip.context_id,
        'questionnaires': questionnaires,
        'receivers': db_get_itip_receiver_list(session, internaltip),
        'https': internaltip.https,
        'mobile': internaltip.mobile,
        'enable_two_way_comments': internaltip.enable_two_way_comments,
        'enable_two_way_messages': internaltip.enable_two_way_messages,
        'enable_attachments': internaltip.enable_attachments,
        'enable_whistleblower_identity': internaltip.enable_whistleblower_identity,
        'wb_last_access': internaltip.wb_last_access,
        'score': internaltip.total_score,
        'status': internaltip.status,
        'substatus': internaltip.substatus
    }


def serialize_usertip(session, usertip, itip, language):
    ret = serialize_itip(session, itip, language)
    ret['id'] = usertip.id
    ret['internaltip_id'] = itip.id
    ret['data'] = {}

    for itd in session.query(models.InternalTipData).filter(models.InternalTipData.internaltip_id == itip.id):
        ret['data'][itd.key] = itd.value

    return ret


def db_create_receivertip(session, receiver, internaltip, can_access_whistleblower_identity, enc_key):
    """
    Create a receiver tip for the specified receiver
    """
    receivertip = models.ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.receiver_id = receiver.id
    receivertip.can_access_whistleblower_identity = can_access_whistleblower_identity
    receivertip.crypto_tip_prv_key = Base64Encoder.encode(enc_key)
    session.add(receivertip)


def db_create_submission(session, tid, request, temp_submission, client_using_tor):
    encryption = db_get(session, models.Config, (models.Config.tid == tid, models.Config.var_name == 'encryption'))

    crypto_is_available = encryption.value

    tenant = db_get(session, models.Tenant, models.Tenant.id == tid)

    context, questionnaire = db_get(session,
                                    (models.Context, models.Questionnaire),
                                    (models.Context.id == request['context_id'],
                                     models.Questionnaire.id == models.Context.questionnaire_id))

    answers = request['answers']
    steps = db_get_questionnaire(session, tid, questionnaire.id, None)['steps']
    questionnaire_hash = db_archive_questionnaire_schema(session, steps)

    crypto_tip_pub_key = ''

    receivers = []
    for r in session.query(models.User).filter(models.User.id.in_(request['receivers'])):
        if crypto_is_available:
            if r.crypto_pub_key:
                # This is the regular condition of systems setup on Globaleaks 4
                # Since this version, encryption is enabled by default and
                # users need to perform their first access before they
                # could receive reports.
                receivers.append(r)
            elif encryption.update_date != datetime_null():
                # This is the exceptional condition of systems setup when
                # encryption was implemented via PGP.
                # For continuity reason of those production systems
                # encryption could not be enforced.
                receivers.append(r)
                crypto_is_available = False
        else:
                receivers.append(r)

    if not receivers:
        raise errors.InputValidationError("Unable to deliver the submission to at least one recipient")

    if 0 < context.maximum_selectable_receivers < len(request['receivers']):
        raise errors.InputValidationError("The number of recipients selected exceed the configured limit")

    if crypto_is_available:
        crypto_tip_prv_key, crypto_tip_pub_key = GCE.generate_keypair()

    itip = models.InternalTip()
    itip.tid = tid
    itip.status = 'new'
    itip.crypto_tip_pub_key = crypto_tip_pub_key

    itip.progressive = db_assign_submission_progressive(session, tid)

    if context.tip_timetolive > 0:
        itip.expiration_date = get_expiration(context.tip_timetolive)

    # Evaluate the score level
    itip.total_score = request['total_score']

    # The status https is used to keep track of the security level adopted by the whistleblower
    itip.https = not client_using_tor
    itip.mobile = request['mobile']

    itip.context_id = context.id
    itip.enable_two_way_comments = context.enable_two_way_comments
    itip.enable_two_way_messages = context.enable_two_way_messages
    itip.enable_attachments = context.enable_attachments

    x = session.query(models.Field, models.FieldAttr.value) \
               .filter(models.Field.template_id == 'whistleblower_identity',
                       models.Field.step_id == models.Step.id,
                       models.Step.questionnaire_id == context.questionnaire_id,
                       models.FieldAttr.field_id == models.Field.id,
                       models.FieldAttr.name == 'visibility_subject_to_authorization').one_or_none()

    whistleblower_identity = None
    can_access_whistleblower_identity = True

    if x:
        whistleblower_identity = x[0]
        can_access_whistleblower_identity = not x[1]

    itip.enable_whistleblower_identity = whistleblower_identity is not None

    session.add(itip)
    session.flush()

    # Evaluate if the whistleblower tip should be generated
    if ((not State.tenant_cache[tid].enable_scoring_system) or
        (context.score_threshold_receipt == 0) or
        (context.score_threshold_receipt == 1 and itip.total_score >= 2) or
        (context.score_threshold_receipt == 2 and itip.total_score == 3)):

        receipt = GCE.generate_receipt()
        receipt_salt = State.tenant_cache[tid].receipt_salt

        wbtip = models.WhistleblowerTip()
        wbtip.id = itip.id
        wbtip.tid = tid
        wbtip.hash_alg = 'ARGON2'
        wbtip.receipt_hash = GCE.hash_password(receipt, receipt_salt)

        # Evaluate if the whistleblower tip should be encrypted
        if crypto_is_available:
            crypto_tip_prv_key, itip.crypto_tip_pub_key = GCE.generate_keypair()
            wb_key = GCE.derive_key(receipt.encode(), receipt_salt)
            wb_prv_key, wb_pub_key = GCE.generate_keypair()
            wbtip.crypto_prv_key = Base64Encoder.encode(GCE.symmetric_encrypt(wb_key, wb_prv_key))
            wbtip.crypto_pub_key = wb_pub_key
            wbtip.crypto_tip_prv_key = Base64Encoder.encode(GCE.asymmetric_encrypt(wb_pub_key, crypto_tip_prv_key))

        session.add(wbtip)
    else:
        receipt = ''


    # Apply special handling to the whistleblower identity question
    if itip.enable_whistleblower_identity and request['identity_provided'] and answers[whistleblower_identity.id]:
        if crypto_is_available:
            wbi = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, json.dumps(answers[whistleblower_identity.id][0]).encode())).decode()
        else:
            wbi = answers[whistleblower_identity.id][0]

        answers[whistleblower_identity.id] = ''

        db_set_internaltip_data(session, itip.id, 'whistleblower_identity', wbi)

    if crypto_is_available:
        answers = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, json.dumps(answers, cls=JSONEncoder).encode())).decode()

    db_set_internaltip_answers(session, itip.id, questionnaire_hash, answers)

    for uploaded_file in temp_submission.files:
        if not itip.enable_attachments:
            break

        if uploaded_file['id'] in request['removed_files']:
            continue

        if crypto_is_available:
            for k in ['name', 'type', 'size']:
                uploaded_file[k] = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, str(uploaded_file[k])))

        new_file = models.InternalFile()
        new_file.tid = tid
        new_file.name = uploaded_file['name']
        new_file.content_type = uploaded_file['type']
        new_file.size = uploaded_file['size']
        new_file.internaltip_id = itip.id
        new_file.filename = uploaded_file['filename']
        new_file.submission = uploaded_file['submission']
        session.add(new_file)

    for user in receivers:
        if crypto_is_available:
            _tip_key = GCE.asymmetric_encrypt(user.crypto_pub_key, crypto_tip_prv_key)
        else:
            _tip_key = b''

        db_create_receivertip(session, user, itip, can_access_whistleblower_identity, _tip_key)

    State.log(tid=tid,  type='whistleblower_new_report')

    return {
        'receipt': receipt,
        'score': itip.total_score
    }


@transact
def create_submission(session, tid, request, temp_session, client_using_tor):
    return db_create_submission(session, tid, request, temp_session, client_using_tor)


class SubmissionInstance(BaseHandler):
    """
    The interface that creates, populates and finishes a submission.
    """
    check_roles = 'any'
    require_token = [b'GET']

    def get(self):
        return initialize_submission()

    def put(self, submission_id):
        """
        Finalize the submission
        """
        temp_submission = self.state.TempSubmissions.pop(submission_id, None)
        if temp_submission is None:
            return

        connection_check(self.request.tid, self.request.client_ip, 'whistleblower', self.request.client_using_tor)

        if not self.state.accept_submissions or self.state.tenant_cache[self.request.tid]['disable_submissions']:
            raise errors.SubmissionDisabled

        request = self.validate_message(self.request.content.read(), requests.SubmissionDesc)

        request['mobile'] = self.request.client_mobile

        return create_submission(self.request.tid,
                                 request,
                                 temp_submission,
                                 self.request.client_using_tor)

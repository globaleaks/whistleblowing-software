# -*- coding: utf-8 -*-
#
# Handlerse dealing with submission interface
import base64
import copy
import json

from six import text_type

from globaleaks import models
from globaleaks.handlers.admin.questionnaire import db_get_questionnaire
from globaleaks.handlers.admin.submission_statuses import db_get_id_for_system_status
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import get_localized_values
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.state import State
from globaleaks.utils.crypto import sha256, GCE
from globaleaks.utils.log import log
from globaleaks.utils.utility import get_expiration, \
    datetime_never, datetime_to_ISO8601


def decrypt_tip(user_key, tip_prv_key, tip):
    tip_key = GCE.asymmetric_decrypt(user_key, tip_prv_key)

    for questionnaire in tip['questionnaires']:
        questionnaire['answers'] = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(questionnaire['answers'].encode())).decode())

    for k in ['whistleblower_identity']:
        if k in tip['data'] and tip['data'][k]['encrypted'] and tip['data'][k]['value']:
            tip['data'][k]['value'] = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(tip['data'][k]['value'].encode())).decode())

    for x in tip['comments'] + tip['messages']:
        x['content'] = GCE.asymmetric_decrypt(tip_key, base64.b64decode(x['content'].encode())).decode()

    return tip


def db_set_internaltip_answers(session, itip_id, questionnaire_hash, answers, encrypted):
    ita = session.query(models.InternalTipAnswers) \
                 .filter(models.InternalTipAnswers.internaltip_id == itip_id, models.InternalTipAnswers.questionnaire_hash == questionnaire_hash).one_or_none()

    if ita is None:
        ita = models.InternalTipAnswers()

    ita.internaltip_id = itip_id
    ita.questionnaire_hash = questionnaire_hash
    ita.encrypted = encrypted
    ita.answers = answers
    session.add(ita)


def db_set_internaltip_data(session, itip_id, key, value, encrypted):
    itd = session.query(models.InternalTipData) \
                 .filter(models.InternalTipData.internaltip_id == itip_id, models.InternalTipData.key == key).one_or_none()

    if itd is None:
        itd = models.InternalTipData()

    itd.internaltip_id = itip_id
    itd.key = key
    itd.encrypted = encrypted

    itd.value = value
    session.add(itd)


def db_assign_submission_progressive(session, tid):
    counter = session.query(models.Config).filter(models.Config.tid == tid, models.Config.var_name == u'counter_submissions').one()
    counter.value += 1
    return counter.value


def _db_serialize_archived_field_recursively(field, language):
    for key, _ in field.get('attrs', {}).items():
        if key not in field['attrs']:
            continue

        if 'type' not in field['attrs'][key]:
            continue

        if field['attrs'][key]['type'] == u'localized':
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


def db_serialize_archived_preview_schema(preview_schema, language):
    preview = copy.deepcopy(preview_schema)

    for field in preview:
        _db_serialize_archived_field_recursively(field, language)

    return preview


def db_save_questionnaire_answers(session, tid, internaltip_id, entries):
    ret = []

    for key, value in entries.items():
        field_answer = models.FieldAnswer({
            'internaltip_id': internaltip_id,
            'key': key,
            'tid': tid,
        })

        session.add(field_answer)
        session.flush()

        if isinstance(value, list):
            field_answer.is_leaf = False
            field_answer.value = ""
            n = 0
            for elem in value:
                group = models.FieldAnswerGroup({
                  'fieldanswer_id': field_answer.id,
                  'number': n,
                  'tid': tid,
                })

                session.add(group)
                session.flush()

                group_elems = db_save_questionnaire_answers(session, tid, internaltip_id, elem)
                for group_elem in group_elems:
                    group_elem.fieldanswergroup_id = group.id

                n += 1
        else:
            field_answer.is_leaf = True
            field_answer.value = text_type(value)

        ret.append(field_answer)

    return ret


def extract_answers_preview(questionnaire, answers):
    preview = {}

    preview.update({f['id']: copy.deepcopy(answers[f['id']])
        for s in questionnaire for f in s['children'] if f['preview'] and f['id'] in answers})

    return preview


def db_archive_questionnaire_schema(session, questionnaire):
    hash = text_type(sha256(json.dumps(questionnaire, sort_keys=True)))
    if session.query(models.ArchivedSchema).filter(models.ArchivedSchema.hash == hash).count():
        return hash

    aqs = models.ArchivedSchema()
    aqs.hash = hash

    aqs.schema = questionnaire
    aqs.preview = [f for s in questionnaire for f in s['children'] if f['preview']]

    session.add(aqs)

    return hash


def db_get_itip_receiver_list(session, itip):
    ret = []

    for rtip, user in session.query(models.ReceiverTip, models.User).filter(models.ReceiverTip.internaltip_id == itip.id,
                                                                            models.User.id == models.ReceiverTip.receiver_id):
        ret.append({
            "id": rtip.receiver_id,
            "name": user.name,
            "pgp_key_public": user.pgp_key_public,
            "last_access": datetime_to_ISO8601(rtip.last_access),
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

    wb_access_revoked = session.query(models.WhistleblowerTip).filter(models.WhistleblowerTip.id == internaltip.id).count() == 0

    return {
        'id': internaltip.id,
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'update_date': datetime_to_ISO8601(internaltip.update_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'progressive': internaltip.progressive,
        'context_id': internaltip.context_id,
        'additional_questionnaire_id': internaltip.additional_questionnaire_id,
        'questionnaires': questionnaires,
        'receivers': db_get_itip_receiver_list(session, internaltip),
        'https': internaltip.https,
        'enable_two_way_comments': internaltip.enable_two_way_comments,
        'enable_two_way_messages': internaltip.enable_two_way_messages,
        'enable_attachments': internaltip.enable_attachments,
        'enable_whistleblower_identity': internaltip.enable_whistleblower_identity,
        'wb_last_access': datetime_to_ISO8601(internaltip.wb_last_access),
        'wb_access_revoked': wb_access_revoked,
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
        ret['data'][itd.key] = {
            'value': itd.value,
            'encrypted': itd.encrypted
        }

    return ret


def db_create_receivertip(session, receiver, internaltip, can_access_whistleblower_identity, enc_key):
    """
    Create a receiver tip for the specified receiver
    """
    receivertip = models.ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.receiver_id = receiver.id
    receivertip.can_access_whistleblower_identity = can_access_whistleblower_identity
    receivertip.crypto_tip_prv_key = enc_key

    session.add(receivertip)


def db_create_submission(session, tid, request, token, client_using_tor):
    if not request['receivers']:
        raise errors.InputValidationError("need at least one recipient")

    answers = request['answers']

    context, questionnaire = session.query(models.Context, models.Questionnaire) \
                                    .filter(models.Context.id == request['context_id'],
                                            models.Questionnaire.id == models.Context.questionnaire_id,
                                            models.Questionnaire.tid.in_(set([1, tid]))).one_or_none()

    if not context:
        raise errors.ModelNotFound(models.Context)

    steps = db_get_questionnaire(session, tid, questionnaire.id, None)['steps']
    questionnaire_hash = db_archive_questionnaire_schema(session, steps)

    itip = models.InternalTip()
    itip.tid = tid
    itip.status = db_get_id_for_system_status(session, tid, u'new')

    itip.progressive = db_assign_submission_progressive(session, tid)

    itip.additional_questionnaire_id = context.additional_questionnaire_id

    if context.tip_timetolive > 0:
        itip.expiration_date = get_expiration(context.tip_timetolive)

    # Evaluate the score level
    itip.total_score = request['total_score']

    # The status https is used to keep track of the security level adopted by the whistleblower
    itip.https = not client_using_tor

    itip.context_id = context.id
    itip.enable_two_way_comments = context.enable_two_way_comments
    itip.enable_two_way_messages = context.enable_two_way_messages
    itip.enable_attachments = context.enable_attachments

    x = session.query(models.Field, models.FieldAttr.value) \
               .filter(models.Field.template_id == u'whistleblower_identity',
                       models.Field.step_id == models.Step.id,
                       models.Step.questionnaire_id == context.questionnaire_id,
                       models.FieldAttr.field_id == models.Field.id,
                       models.FieldAttr.name == u'visibility_subject_to_authorization').one_or_none()

    whistleblower_identity = None
    can_access_whistleblower_identity = True

    if x:
        whistleblower_identity = x[0]
        can_access_whistleblower_identity = not x[1]

    itip.enable_whistleblower_identity = whistleblower_identity is not None

    itip.preview = extract_answers_preview(steps, answers)

    session.add(itip)
    session.flush()

    crypto_is_available = State.tenant_cache[1].encryption

    # Evaluate if encryption is available
    if crypto_is_available:
        users_count = session.query(models.User) \
                             .filter(models.User.id.in_(request['receivers']),
                                     models.User.crypto_prv_key != b'').count()

        crypto_is_available = users_count == len(request['receivers'])

        if crypto_is_available:
            crypto_tip_prv_key, itip.crypto_tip_pub_key = GCE.generate_keypair()

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
        wbtip.hash_alg = GCE.HASH
        wbtip.receipt_hash = GCE.hash_password(receipt, receipt_salt)

        # Evaluate if the whistleblower tip should be encrypted
        if crypto_is_available:
            crypto_tip_prv_key, itip.crypto_tip_pub_key = GCE.generate_keypair()
            wb_key = GCE.derive_key(receipt.encode(), receipt_salt)
            wb_prv_key, wb_pub_key = GCE.generate_keypair()
            wbtip.crypto_prv_key = GCE.symmetric_encrypt(wb_key, wb_prv_key)
            wbtip.crypto_pub_key = wb_pub_key
            wbtip.crypto_tip_prv_key = GCE.asymmetric_encrypt(wb_pub_key, crypto_tip_prv_key)

        session.add(wbtip)
    else:
        receipt = ''

    # Apply special handling to the whistleblower identity question
    if itip.enable_whistleblower_identity and request['identity_provided'] and answers[whistleblower_identity.id]:
        if crypto_is_available:
            wbi = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, json.dumps(answers[whistleblower_identity.id][0]).encode())).decode()
            answers[whistleblower_identity.id] = ''
        else:
            wbi = answers[whistleblower_identity.id][0]

        db_set_internaltip_data(session, itip.id, 'identity_provided', True, False)
        db_set_internaltip_data(session, itip.id, 'whistleblower_identity', wbi, crypto_is_available)

    if crypto_is_available:
        answers = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, json.dumps(answers).encode())).decode()
    else:
        db_save_questionnaire_answers(session, tid, itip.id, answers)

    db_set_internaltip_answers(session,
                               itip.id,
                               questionnaire_hash,
                               answers,
                               crypto_is_available)

    for filedesc in token.uploaded_files:
        new_file = models.InternalFile()
        new_file.tid = tid
        new_file.encrypted = crypto_is_available
        new_file.name = filedesc['name']
        new_file.description = ""
        new_file.content_type = filedesc['type']
        new_file.size = filedesc['size']
        new_file.internaltip_id = itip.id
        new_file.submission = filedesc['submission']
        new_file.filename = filedesc['filename']
        session.add(new_file)
        log.debug("=> file associated %s|%s (%d bytes)",
                  new_file.name, new_file.content_type, new_file.size)

    if context.maximum_selectable_receivers > 0 and \
                    len(request['receivers']) > context.maximum_selectable_receivers:
        raise errors.InputValidationError("selected an invalid number of recipients")

    for user in session.query(models.User).filter(models.User.id.in_(request['receivers'])):
        if not crypto_is_available and not user.pgp_key_public and not State.tenant_cache[tid].allow_unencrypted:
            continue

        _tip_key = b''
        if crypto_is_available:
            _tip_key = GCE.asymmetric_encrypt(user.crypto_pub_key, crypto_tip_prv_key)

        db_create_receivertip(session, user, itip, can_access_whistleblower_identity, _tip_key)

    return {
        'receipt': receipt,
        'score': itip.total_score
    }


@transact
def create_submission(session, tid, request, token, client_using_tor):
    return db_create_submission(session, tid, request, token, client_using_tor)


class SubmissionInstance(BaseHandler):
    """
    The interface that creates, populates and finishes a submission.
    """
    check_roles = 'unauthenticated'

    def put(self, token_id):
        """
        Finalize the submission
        """
        request = self.validate_message(self.request.content.read(), requests.SubmissionDesc)

        token = self.state.tokens.pop(token_id)

        # The get and use method will raise if the token is invalid
        token.use()

        return create_submission(self.request.tid,
                                 request,
                                 token,
                                 self.request.client_using_tor)

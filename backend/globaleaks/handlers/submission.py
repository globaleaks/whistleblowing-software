# -*- coding: utf-8 -*-
#
# Handlerse dealing with submission interface
import base64
import copy
import json
import os

from six import binary_type, text_type

from globaleaks import models
from globaleaks.handlers.admin.questionnaire import db_get_questionnaire
from globaleaks.handlers.admin.submission_statuses import db_get_id_for_system_status
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.state import State
from globaleaks.utils.crypto import sha256, GCE
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.utility import get_expiration, \
    datetime_now, datetime_never, datetime_to_ISO8601
from globaleaks.utils.log import log


def decrypt_tip(user_key, tip_prv_key, tip):
    tip_key = GCE.asymmetric_decrypt(user_key, tip_prv_key)

    for k in ['answers', 'whistleblower_identity']:
        if k in tip['data'] and tip['data'][k]['encrypted'] and tip['data'][k]['value']:
            tip['data'][k]['value'] = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(tip['data'][k]['value'].encode())).decode())

    for x in tip['comments'] + tip['messages']:
        x['content'] = GCE.asymmetric_decrypt(tip_key, base64.b64decode(x['content'].encode())).decode()

    return tip


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


def db_serialize_questionnaire_answers_recursively(session, answers, answers_by_group, groups_by_answer):
    ret = {}

    for answer in answers:
        if answer.is_leaf:
            ret[answer.key] = answer.value
        else:
            ret[answer.key] = [db_serialize_questionnaire_answers_recursively(session, answers_by_group.get(group.id, []), answers_by_group, groups_by_answer)
                                  for group in groups_by_answer.get(answer.id, [])]

    return ret


def db_serialize_questionnaire_answers(session, tid, usertip, internaltip):
    aqs = session.query(models.ArchivedSchema).filter(models.ArchivedSchema.hash == internaltip.questionnaire_hash).one()
    questionnaire = db_serialize_archived_questionnaire_schema(aqs.schema, State.tenant_cache[tid].default_language)

    answers = []
    answers_by_group = {}
    groups_by_answer = {}
    all_answers_ids = []
    root_answers_ids = []

    for s in questionnaire:
        for f in s['children']:
            if f.get('template_id', '') == 'whistleblower_identity':
                if isinstance(usertip, models.InternalTip) or \
                   f['attrs']['visibility_subject_to_authorization']['value'] is False or \
                   (isinstance(usertip, models.ReceiverTip) and usertip.can_access_whistleblower_identity):
                    root_answers_ids.append(f['id'])
            else:
                root_answers_ids.append(f['id'])

    for answer in session.query(models.FieldAnswer) \
                       .filter(models.FieldAnswer.internaltip_id == internaltip.id):
        all_answers_ids.append(answer.id)

        if answer.key in root_answers_ids:
            answers.append(answer)

        if answer.fieldanswergroup_id not in answers_by_group:
            answers_by_group[answer.fieldanswergroup_id] = []

        answers_by_group[answer.fieldanswergroup_id].append(answer)

    if all_answers_ids:
        for group in session.query(models.FieldAnswerGroup) \
                            .filter(models.FieldAnswerGroup.fieldanswer_id.in_(all_answers_ids)) \
                            .order_by(models.FieldAnswerGroup.number):

            if group.fieldanswer_id not in groups_by_answer:
                groups_by_answer[group.fieldanswer_id] = []

            groups_by_answer[group.fieldanswer_id].append(group)

    return db_serialize_questionnaire_answers_recursively(session, answers, answers_by_group, groups_by_answer)


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


def db_archive_questionnaire_schema(session, questionnaire, questionnaire_hash):
    if session.query(models.ArchivedSchema).filter(models.ArchivedSchema.hash == questionnaire_hash).count():
        return

    aqs = models.ArchivedSchema()
    aqs.hash = questionnaire_hash

    aqs.schema = questionnaire
    aqs.preview = [f for s in questionnaire for f in s['children'] if f['preview']]

    session.add(aqs)


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
    aq = session.query(models.ArchivedSchema).filter(models.ArchivedSchema.hash == internaltip.questionnaire_hash).one()

    wb_access_revoked = session.query(models.WhistleblowerTip).filter(models.WhistleblowerTip.id == internaltip.id).count() == 0

    return {
        'id': internaltip.id,
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'update_date': datetime_to_ISO8601(internaltip.update_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'progressive': internaltip.progressive,
        'context_id': internaltip.context_id,
        'questionnaire': db_serialize_archived_questionnaire_schema(aq.schema, language),
        'receivers': db_get_itip_receiver_list(session, internaltip),
        'https': internaltip.https,
        'enable_two_way_comments': internaltip.enable_two_way_comments,
        'enable_two_way_messages': internaltip.enable_two_way_messages,
        'enable_attachments': internaltip.enable_attachments,
        'enable_whistleblower_identity': internaltip.enable_whistleblower_identity,
        'identity_provided': internaltip.identity_provided,
        'identity_provided_date': datetime_to_ISO8601(internaltip.identity_provided_date),
        'wb_last_access': datetime_to_ISO8601(internaltip.wb_last_access),
        'wb_access_revoked': wb_access_revoked,
        'total_score': internaltip.total_score,
        'status': internaltip.status,
        'substatus': internaltip.substatus
    }


def serialize_usertip(session, usertip, itip, language):
    ret = serialize_itip(session, itip, language)
    ret['id'] = usertip.id
    ret['internaltip_id'] = itip.id

    ret['data'] = {}
    ret['data']['answers'] = {
        'value': db_serialize_questionnaire_answers(session, itip.tid, usertip, itip),
        'encrypted': False
    }

    for itd in session.query(models.InternalTipData).filter(models.InternalTipData.internaltip_id == itip.id):
        ret['data'][itd.key] = {
            'value': itd.value,
            'encrypted': itd.encrypted
        }

    return ret


def db_create_receivertip(session, receiver, internaltip, enc_key):
    """
    Create models.ReceiverTip for the required tier of models.Receiver.
    """
    log.debug("Creating receivertip for receiver: %s", receiver.id)

    receivertip = models.ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.receiver_id = receiver.id
    receivertip.crypto_tip_prv_key = enc_key

    session.add(receivertip)


def db_create_submission(session, tid, request, token, client_using_tor):
    answers = request['answers']

    context, questionnaire = session.query(models.Context, models.Questionnaire) \
                                    .filter(models.Context.id == request['context_id'],
                                            models.Questionnaire.id == models.Context.questionnaire_id,
                                            models.Questionnaire.tid.in_(set([1, tid]))).one_or_none()
    if not context:
        raise errors.ModelNotFound(models.Context)

    steps = db_get_questionnaire(session, tid, questionnaire.id, None)['steps']
    questionnaire_hash = text_type(sha256(json.dumps(steps)))
    db_archive_questionnaire_schema(session, steps, questionnaire_hash)

    itip = models.InternalTip()
    itip.tid = tid
    itip.status = db_get_id_for_system_status(session, tid, u'new')

    itip.progressive = db_assign_submission_progressive(session, tid)

    if context.tip_timetolive > 0:
        itip.expiration_date = get_expiration(context.tip_timetolive)
    else:
        itip.expiration_date = datetime_never()

    # this is get from the client as it the only possibility possible
    # that would fit with the end to end submission.
    # the score is only an indicator and not a critical information so we can accept to
    # be fooled by the malicious user.
    itip.total_score = request['total_score']

    # The status https is used to keep track of the security level adopted by the whistleblower
    itip.https = not client_using_tor

    itip.context_id = context.id
    itip.enable_two_way_comments = context.enable_two_way_comments
    itip.enable_two_way_messages = context.enable_two_way_messages
    itip.enable_attachments = context.enable_attachments

    whistleblower_identity = session.query(models.Field) \
                                    .filter(models.Field.template_id == u'whistleblower_identity',
                                            models.Field.step_id == models.Step.id,
                                            models.Step.questionnaire_id == context.questionnaire_id).one_or_none()

    itip.enable_whistleblower_identity = whistleblower_identity is not None

    if itip.enable_whistleblower_identity and request['identity_provided']:
        itip.identity_provided = True
        itip.identity_provided_date = datetime_now()

    itip.questionnaire_hash = questionnaire_hash
    itip.preview = extract_answers_preview(steps, answers)

    session.add(itip)
    session.flush()

    receipt = text_= GCE.generate_receipt()
    receipt_salt = State.tenant_cache[tid].receipt_salt

    wbtip = models.WhistleblowerTip()
    wbtip.id = itip.id
    wbtip.tid = tid
    wbtip.hash_alg = GCE.HASH
    wbtip.receipt_hash = GCE.hash_password(receipt, receipt_salt)

    crypto_is_available = State.tenant_cache[tid].encryption
    if crypto_is_available:
        users_count = session.query(models.User) \
                             .filter(models.Receiver.id.in_(request['receivers']),
                                     models.ReceiverContext.receiver_id == models.Receiver.id,
                                     models.ReceiverContext.context_id == context.id,
                                     models.User.id == models.Receiver.id,
                                     models.User.crypto_prv_key != b'',
                                     models.UserTenant.user_id == models.User.id,
                                     models.UserTenant.tenant_id == tid).count()

        crypto_is_available = users_count == len(request['receivers'])

    if crypto_is_available:
        crypto_tip_prv_key, itip.crypto_tip_pub_key = GCE.generate_keypair()
        wb_key = GCE.derive_key(receipt.encode(), receipt_salt)
        wb_prv_key, wb_pub_key = GCE.generate_keypair()
        wbtip.crypto_prv_key = GCE.symmetric_encrypt(wb_key, wb_prv_key)
        wbtip.crypto_pub_key = wb_pub_key
        wbtip.crypto_tip_prv_key = GCE.asymmetric_encrypt(wb_pub_key, crypto_tip_prv_key)

        itd = models.InternalTipData()
        itd.internaltip_id = itip.id
        itd.key = u'answers'
        itd.value = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, json.dumps(answers).encode())).decode()
        itd.encrypted = True
        session.add(itd)

    else:
        db_save_questionnaire_answers(session, tid, itip.id, answers)

    session.add(wbtip)

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

    rtips_count = 0
    for receiver, user in session.query(models.Receiver, models.User) \
                                 .filter(models.Receiver.id.in_(request['receivers']),
                                         models.ReceiverContext.receiver_id == models.Receiver.id,
                                         models.ReceiverContext.context_id == context.id,
                                         models.User.id == models.Receiver.id,
                                         models.UserTenant.user_id == models.User.id,
                                         models.UserTenant.tenant_id == tid):
        if not crypto_is_available and not user.pgp_key_public and not State.tenant_cache[tid].allow_unencrypted:
            continue

        _tip_key = b''
        if crypto_is_available:
            _tip_key = GCE.asymmetric_encrypt(user.crypto_pub_key, crypto_tip_prv_key)

        db_create_receivertip(session, receiver, itip, _tip_key)
        rtips_count += 1

    if not rtips_count:
        raise errors.InputValidationError("need at least one recipient")

    log.debug("The finalized submission had created %d models.ReceiverTip(s)", rtips_count)

    return {'receipt': receipt}


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

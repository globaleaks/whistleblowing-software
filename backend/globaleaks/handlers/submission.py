# -*- coding: utf-8 -*-
#
# Handlerse dealing with submission interface
import copy
import json

from globaleaks import models
from globaleaks.handlers.admin.questionnaire import db_get_questionnaire
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.utils.security import hash_password, sha256, generateRandomReceipt
from globaleaks.state import State
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.token import TokenList
from globaleaks.utils.utility import log, get_expiration, \
    datetime_now, datetime_never, datetime_to_ISO8601


def get_submission_sequence_number(itip):
    return "%s-%d" % (itip.creation_date.strftime("%Y%m%d"), itip.progressive)


def db_assign_submission_progressive(session, tid):
    counter = session.query(models.Counter).filter(models.Counter.key == u'submission_sequence', models.Counter.tid == tid).one_or_none()
    if counter is None:
        counter = models.Counter({'key': u'submission_sequence', 'tid': tid})
        session.add(counter)
    else:
        now = datetime_now()
        update = counter.update_date
        if ((now > update) and
            (not((now.year == update.year) and (now.month == update.month) and (now.day == update.day)))):
            counter.counter = 0

        counter.counter += 1
        counter.update_date = now

    return counter.counter


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


def db_serialize_archived_questionnaire_schema(session, questionnaire_schema, language):
    questionnaire = copy.deepcopy(questionnaire_schema)

    for step in questionnaire:
        for field in step['children']:
            _db_serialize_archived_field_recursively(field, language)

        get_localized_values(step, step, models.Step.localized_keys, language)


    return questionnaire


def db_serialize_archived_preview_schema(session, preview_schema, language):
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
    questionnaire = db_serialize_archived_questionnaire_schema(session, aqs.schema, State.tenant_cache[tid].default_language)

    answers = []
    answers_by_group = {}
    groups_by_answer = {}
    all_answers_ids = []
    root_answers_ids = []

    for s in questionnaire:
        for f in s['children']:
            if f['template_id'] == 'whistleblower_identity':
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
            field_answer.value = unicode(value)

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
    session.flush()


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

    return {
        'id': internaltip.id,
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'update_date': datetime_to_ISO8601(internaltip.update_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'sequence_number': get_submission_sequence_number(internaltip),
        'context_id': internaltip.context_id,
        'questionnaire': db_serialize_archived_questionnaire_schema(session, aq.schema, language),
        'receivers': db_get_itip_receiver_list(session, internaltip),
        'https': internaltip.https,
        'enable_two_way_comments': internaltip.enable_two_way_comments,
        'enable_two_way_messages': internaltip.enable_two_way_messages,
        'enable_attachments': internaltip.enable_attachments,
        'enable_whistleblower_identity': internaltip.enable_whistleblower_identity,
        'identity_provided': internaltip.identity_provided,
        'identity_provided_date': datetime_to_ISO8601(internaltip.identity_provided_date),
        'wb_last_access': datetime_to_ISO8601(internaltip.wb_last_access),
        'wb_access_revoked': internaltip.receipt_hash == None,
        'total_score': internaltip.total_score
    }


def serialize_usertip(session, usertip, itip, language):
    ret = serialize_itip(session, itip, language)
    ret['id'] = usertip.id
    ret['internaltip_id'] = itip.id
    ret['progressive'] = itip.progressive
    ret['answers'] = db_serialize_questionnaire_answers(session, itip.tid, usertip, itip)
    return ret


def db_create_receivertip(session, receiver, internaltip):
    """
    Create models.ReceiverTip for the required tier of models.Receiver.
    """
    log.debug("Creating receivertip for receiver: %s", receiver.id)

    receivertip = models.ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.receiver_id = receiver.id

    session.add(receivertip)

    return receivertip.id


def db_create_submission(session, tid, request, uploaded_files, client_using_tor):
    answers = request['answers']

    context, questionnaire = session.query(models.Context, models.Questionnaire) \
                                    .filter(models.Context.id == request['context_id'],
                                            models.Questionnaire.id == models.Context.questionnaire_id,
                                            models.Questionnaire.tid.in_(set([1, tid]))).one_or_none()
    if not context:
        raise errors.ModelNotFound(models.Context)

    steps = db_get_questionnaire(session, tid, questionnaire.id, None)['steps']
    questionnaire_hash = unicode(sha256(json.dumps(steps)))
    db_archive_questionnaire_schema(session, steps, questionnaire_hash)

    submission = models.InternalTip()
    submission.tid = tid

    submission.progressive = db_assign_submission_progressive(session, tid)

    if context.tip_timetolive > -1:
        submission.expiration_date = get_expiration(context.tip_timetolive)
    else:
        submission.expiration_date = datetime_never()

    # this is get from the client as it the only possibility possible
    # that would fit with the end to end submission.
    # the score is only an indicator and not a critical information so we can accept to
    # be fooled by the malicious user.
    submission.total_score = request['total_score']

    # The status https is used to keep track of the security level adopted by the whistleblower
    submission.https = not client_using_tor

    submission.context_id = context.id
    submission.enable_two_way_comments = context.enable_two_way_comments
    submission.enable_two_way_messages = context.enable_two_way_messages
    submission.enable_attachments = context.enable_attachments
    submission.enable_whistleblower_identity = questionnaire.enable_whistleblower_identity

    if submission.enable_whistleblower_identity and request['identity_provided']:
        submission.identity_provided = True
        submission.identity_provided_date = datetime_now()

    submission.questionnaire_hash = questionnaire_hash
    submission.preview = extract_answers_preview(steps, answers)

    receipt = unicode(generateRandomReceipt())

    submission.receipt_hash = hash_password(receipt, State.tenant_cache[tid].receipt_salt)

    session.add(submission)
    session.flush()

    db_save_questionnaire_answers(session, tid, submission.id, answers)

    for filedesc in uploaded_files:
        new_file = models.InternalFile()
        new_file.tid = tid
        new_file.name = filedesc['name']
        new_file.description = ""
        new_file.content_type = filedesc['type']
        new_file.size = filedesc['size']
        new_file.internaltip_id = submission.id
        new_file.submission = filedesc['submission']
        new_file.file_path = filedesc['path']
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
                                         models.User.tid == tid):
        if user.pgp_key_public or State.tenant_cache[tid].allow_unencrypted:
            db_create_receivertip(session, receiver, submission)
            rtips_count += 1

    if rtips_count == 0:
        raise errors.InputValidationError("need at least one recipient")

    log.debug("The finalized submission had created %d models.ReceiverTip(s)", rtips_count)

    return {'receipt': receipt}


@transact
def create_submission(session, tid, request, uploaded_files, client_using_tor):
    return db_create_submission(session, tid, request, uploaded_files, client_using_tor)


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

        # The get and use method will raise if the token is invalid
        token = TokenList.get(token_id)
        token.use()

        submission = create_submission(self.request.tid,
                                       request,
                                       token.uploaded_files,
                                       self.request.client_using_tor)

        # Delete the token only when a valid submission has been stored in the DB
        TokenList.delete(token_id)

        return submission

# -*- coding: utf-8
#
# submission
# **********
#
# Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI
import copy
import json
from storm.expr import In

from globaleaks import models
from globaleaks.handlers.admin.questionnaire import db_get_questionnaire
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.security import hash_password, sha256, generateRandomReceipt
from globaleaks.state import State
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.token import TokenList
from globaleaks.utils.utility import log, get_expiration, \
    datetime_now, datetime_never, datetime_to_ISO8601


def get_submission_sequence_number(itip):
    return "%s-%d" % (itip.creation_date.strftime("%Y%m%d"), itip.progressive)


def db_assign_submission_progressive(store, tid):
    counter = store.find(models.Counter, key=u'submission_sequence', tid=tid).one()
    if counter is None:
        counter = models.Counter({'key': u'submission_sequence', 'tid': tid})
        store.add(counter)
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


def _db_serialize_archived_questionnaire_schema(store, aqs, language):
    questionnaire = copy.deepcopy(aqs.schema)

    if aqs.type == 'questionnaire':
        for step in questionnaire:
            for field in step['children']:
                _db_serialize_archived_field_recursively(field, language)

            get_localized_values(step, step, models.Step.localized_keys, language)

    elif aqs.type == 'preview':
        for field in questionnaire:
            _db_serialize_archived_field_recursively(field, language)

    return questionnaire


def db_serialize_archived_questionnaire_schema(store, hash, language):
    aqs = store.find(models.ArchivedSchema, hash=hash, type=u'questionnaire').one()

    return _db_serialize_archived_questionnaire_schema(store, aqs, language)


def db_serialize_archived_preview_schema(store, aqs, language):
    return _db_serialize_archived_questionnaire_schema(store, aqs, language)


def db_serialize_questionnaire_answers_recursively(store, answers, answers_by_group, groups_by_answer):
    ret = {}

    for answer in answers:
        if answer.is_leaf:
            ret[answer.key] = answer.value
        else:
            ret[answer.key] = [db_serialize_questionnaire_answers_recursively(store, answers_by_group.get(group.id, []), answers_by_group, groups_by_answer)
                                  for group in groups_by_answer.get(answer.id, [])]

    return ret


def db_serialize_questionnaire_answers(store, tid, usertip, internaltip):
    questionnaire = db_serialize_archived_questionnaire_schema(store, internaltip.questionnaire_hash, State.tenant_cache[tid].default_language)

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

    for answer in store.find(models.FieldAnswer, internaltip_id=internaltip.id, tid=tid):
        all_answers_ids.append(answer.id)

        if answer.key in root_answers_ids:
            answers.append(answer)

        if answer.fieldanswergroup_id not in answers_by_group:
            answers_by_group[answer.fieldanswergroup_id] = []

        answers_by_group[answer.fieldanswergroup_id].append(answer)

    for group in store.find(models.FieldAnswerGroup,
                            In(models.FieldAnswerGroup.fieldanswer_id, all_answers_ids), tid=tid).order_by(models.FieldAnswerGroup.number):
        if group.fieldanswer_id not in groups_by_answer:
            groups_by_answer[group.fieldanswer_id] = []

        groups_by_answer[group.fieldanswer_id].append(group)

    return db_serialize_questionnaire_answers_recursively(store, answers, answers_by_group, groups_by_answer)


def db_save_questionnaire_answers(store, tid, internaltip_id, entries):
    ret = []

    for key, value in entries.items():
        field_answer = models.FieldAnswer({
            'internaltip_id': internaltip_id,
            'key': key,
            'tid': tid,
        })

        store.add(field_answer)

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

                store.add(group)

                group_elems = db_save_questionnaire_answers(store, tid, internaltip_id, elem)
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


def db_archive_questionnaire_schema(store, tid, questionnaire, questionnaire_hash):
    if store.find(models.ArchivedSchema, hash=questionnaire_hash).count():
        return

    for type in [u'questionnaire', u'preview']:
        aqs = models.ArchivedSchema()
        aqs.hash = questionnaire_hash

        if type == u'questionnaire':
            aqs.type = u'questionnaire'
            aqs.schema = questionnaire
        else:
            aqs.type = u'preview'
            aqs.schema = [f for s in questionnaire for f in s['children'] if f['preview']]

        store.add(aqs)


def db_get_itip_receiver_list(store, itip):
    ret = []

    for rtip, user in store.find((models.ReceiverTip, models.User),
                                 models.ReceiverTip.internaltip_id == itip.id,
                                 models.User.id == models.ReceiverTip.receiver_id):

        ret.append({
            "id": rtip.receiver_id,
            "name": user.public_name,
            "pgp_key_public": user.pgp_key_public,
            "last_access": datetime_to_ISO8601(rtip.last_access),
            "access_counter": rtip.access_counter,
        })

    return ret


def serialize_itip(store, internaltip, language):
    wb_access_revoked = internaltip.receipt_hash == None

    return {
        'id': internaltip.id,
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'update_date': datetime_to_ISO8601(internaltip.update_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'sequence_number': get_submission_sequence_number(internaltip),
        'context_id': internaltip.context_id,
        'questionnaire': db_serialize_archived_questionnaire_schema(store, internaltip.questionnaire_hash, language),
        'receivers': db_get_itip_receiver_list(store, internaltip),
        'tor2web': internaltip.tor2web,
        'enable_two_way_comments': internaltip.enable_two_way_comments,
        'enable_two_way_messages': internaltip.enable_two_way_messages,
        'enable_attachments': internaltip.enable_attachments,
        'enable_whistleblower_identity': internaltip.enable_whistleblower_identity,
        'identity_provided': internaltip.identity_provided,
        'identity_provided_date': datetime_to_ISO8601(internaltip.identity_provided_date),
        'wb_last_access': datetime_to_ISO8601(internaltip.wb_last_access),
        'wb_access_revoked': wb_access_revoked,
        'total_score': internaltip.total_score
    }


def serialize_usertip(store, usertip, itip, language):
    ret = serialize_itip(store, itip, language)
    ret['id'] = usertip.id
    ret['internaltip_id'] = itip.id
    ret['progressive'] = itip.progressive
    ret['answers'] = db_serialize_questionnaire_answers(store, itip.tid, usertip, itip)
    return ret


def db_create_receivertip(store, receiver, internaltip):
    """
    Create models.ReceiverTip for the required tier of models.Receiver.
    """
    log.debug("Creating receivertip for receiver: %s", receiver.id)

    receivertip = models.ReceiverTip()
    receivertip.tid = receiver.tid
    receivertip.internaltip_id = internaltip.id
    receivertip.receiver_id = receiver.id

    store.add(receivertip)

    return receivertip.id


def db_create_submission(store, tid, request, uploaded_files, client_using_tor):
    answers = request['answers']

    context, questionnaire = store.find((models.Context, models.Questionnaire),
                                        models.Context.id == request['context_id'],
                                        models.Questionnaire.id == models.Context.questionnaire_id,
                                        models.Questionnaire.tid == tid).one()
    if not context:
        raise errors.ModelNotFound(models.Context)

    steps = db_get_questionnaire(store, tid, questionnaire.id, None)['steps']
    questionnaire_hash = unicode(sha256(json.dumps(steps)))

    submission = models.InternalTip()
    submission.tid = tid

    submission.progressive = db_assign_submission_progressive(store, tid)

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
    submission.enable_whistleblower_identity = questionnaire.enable_whistleblower_identity

    if submission.enable_whistleblower_identity and request['identity_provided']:
        submission.identity_provided = True
        submission.identity_provided_date = datetime_now()

    submission.questionnaire_hash = questionnaire_hash
    submission.preview = extract_answers_preview(steps, answers)

    receipt = unicode(generateRandomReceipt())

    submission.receipt_hash = hash_password(receipt, State.tenant_cache[tid].private.receipt_salt)

    store.add(submission)

    db_archive_questionnaire_schema(store, tid, steps, questionnaire_hash)
    db_save_questionnaire_answers(store, tid, submission.id, answers)

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
        store.add(new_file)
        log.debug("=> file associated %s|%s (%d bytes)",
                  new_file.name, new_file.content_type, new_file.size)

    if context.maximum_selectable_receivers > 0 and \
                    len(request['receivers']) > context.maximum_selectable_receivers:
        raise errors.SubmissionValidationFailure("selected an invalid number of recipients")

    rtips_count = 0
    for receiver, user, in store.find((models.Receiver, models.User),
                                      In(models.Receiver.id, request['receivers']),
                                      models.ReceiverContext.receiver_id == models.Receiver.id,
                                      models.ReceiverContext.context_id == context.id,
                                      models.User.id == models.Receiver.id,
                                      models.User.tid == tid):
        if user.pgp_key_public or State.tenant_cache[tid].allow_unencrypted:
            db_create_receivertip(store, receiver, submission)
            rtips_count += 1

    if rtips_count == 0:
        raise errors.SubmissionValidationFailure("need at least one recipient")

    log.debug("The finalized submission had created %d models.ReceiverTip(s)", rtips_count)

    return {'receipt': receipt}


@transact
def create_submission(store, tid, request, uploaded_files, client_using_tor):
    return db_create_submission(store, tid, request, uploaded_files, client_using_tor)


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

        submission = create_submission(self.request.tid,
                                       request,
                                       token.uploaded_files,
                                       self.request.client_using_tor)

        # Delete the token only when a valid submission has been stored in the DB
        TokenList.delete(token_id)

        return submission

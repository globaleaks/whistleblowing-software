# -*- coding: utf-8
import copy
import os

from globaleaks import models
from globaleaks.models.config import ConfigFactory
from globaleaks.state import State
from sqlalchemy import or_, and_


def serialize_archived_field_recursively(field, language):
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
        models.get_localized_values(o, o, models.FieldOption.localized_keys, language)

    for c in field.get('children', []):
        serialize_archived_field_recursively(c, language)

    return models.get_localized_values(field, field, models.Field.localized_keys, language)


def serialize_archived_questionnaire_schema(questionnaire_schema, language):
    questionnaire = copy.deepcopy(questionnaire_schema)

    for step in questionnaire:
        for field in step['children']:
            serialize_archived_field_recursively(field, language)

        models.get_localized_values(step, step, models.Step.localized_keys, language)

    return questionnaire


def serialize_identityaccessrequest(session, identityaccessrequest):
    itip, request_user = session.query(models.InternalTip, models.User) \
                                .filter(models.InternalTip.id == identityaccessrequest.internaltip_id,
                                        models.User.id == identityaccessrequest.request_user_id).one()

    reply_user = session.query(models.User) \
                        .filter(models.User.id == identityaccessrequest.reply_user_id).one_or_none()

    return {
        'id': identityaccessrequest.id,
        'internaltip_id': identityaccessrequest.internaltip_id,
        'request_date': identityaccessrequest.request_date,
        'request_user_name': request_user.name,
        'request_motivation': identityaccessrequest.request_motivation,
        'reply_date': identityaccessrequest.reply_date,
        'reply_user_name': reply_user.id if reply_user is not None else '',
        'reply': identityaccessrequest.reply,
        'reply_motivation': identityaccessrequest.reply_motivation,
        'submission_progressive': itip.progressive,
        'submission_date': itip.creation_date
    }

def serialize_comment(session, comment):
    """
    Transaction returning a serialized descriptor of a comment

    :param session: An ORM session
    :param comment: A model to be serialized
    :return: A serialized description of the model specified
    """
    return {
        'id': comment.id,
        'creation_date': comment.creation_date,
        'content': comment.content,
        'author_id': comment.author_id,
        'visibility': comment.visibility
    }


def serialize_ifile(session, ifile):
    """
    Transaction for serializing ifiles

    :param session: An ORM session
    :param ifile: The ifile to be serialized
    :return: The serialized ifile
    """
    return {
        'id': ifile.id,
        'creation_date': ifile.creation_date,
        'name': ifile.name,
        'size': ifile.size,
        'type': ifile.content_type,
        'reference_id': ifile.reference_id
    }


def serialize_wbfile(session, ifile, wbfile):
    """
    Transaction for serializing wbfile

    :param session: An ORM session
    :param ifile: The ifile to be serialized
    :param wbfile: The wbfile to be serialized
    :return: The serialized wbfile
    """
    error = not os.path.exists(os.path.join(State.settings.attachments_path, ifile.id)) and \
        not os.path.exists(os.path.join(State.settings.attachments_path, wbfile.id))

    return {
        'id': wbfile.id,
        'ifile_id': ifile.id,
        'creation_date': ifile.creation_date,
        'name': ifile.name,
        'size': ifile.size,
        'type': ifile.content_type,
        'reference_id': ifile.reference_id,
        'error': error
    }


def serialize_rfile(session, rfile):
    """
    Transaction for serializing rfile

    :param session: An ORM session
    :param rfile: The rfile to be serialized
    :return: The serialized rfile
    """
    error = not os.path.exists(os.path.join(State.settings.attachments_path, rfile.id))

    return {
        'id': rfile.id,
        'creation_date': rfile.creation_date,
        'name': rfile.name,
        'size': rfile.size,
        'type': rfile.content_type,
        'description': rfile.description,
        'visibility': rfile.visibility,
        'error': error
    }


def serialize_itip(session, internaltip, language):
    x = session.query(models.InternalTipAnswers, models.ArchivedSchema) \
               .filter(models.ArchivedSchema.hash == models.InternalTipAnswers.questionnaire_hash,
                       models.InternalTipAnswers.internaltip_id == internaltip.id) \
               .order_by(models.InternalTipAnswers.creation_date.asc())

    questionnaires = []
    for ita, aqs in x:
        questionnaires.append({
            'steps': serialize_archived_questionnaire_schema(aqs.schema, language),
            'answers': ita.answers
        })

    ret = {
        'id': internaltip.id,
        'creation_date': internaltip.creation_date,
        'update_date': internaltip.update_date,
        'expiration_date': internaltip.expiration_date,
        'context_id': internaltip.context_id,
        'questionnaires': questionnaires,
        'tor': internaltip.tor,
        'mobile': internaltip.mobile,
        'reminder_date' : internaltip.reminder_date,
        'enable_two_way_comments': internaltip.enable_two_way_comments,
        'enable_attachments': internaltip.enable_attachments,
        'enable_whistleblower_identity': internaltip.enable_whistleblower_identity,
        'last_access': internaltip.last_access,
        'score': internaltip.score,
        'status': internaltip.status,
        'substatus': internaltip.substatus,
        'receivers': [],
        'comments': [],
        'wbfiles': [],
        'rfiles': [],
        'data': {}
    }

    for itd in session.query(models.InternalTipData).filter(models.InternalTipData.internaltip_id == internaltip.id):
        ret['data'][itd.key] = itd.value
        ret['data'][itd.key + "_date"] = itd.creation_date

    return ret



def serialize_rtip(session, itip, rtip, language):
    """
    Transaction returning a serialized descriptor of a tip

    :param session: An ORM session
    :param rtip: A model to be serialized
    :param itip: A itip object referenced by the model to be serialized
    :param language: A language of the serialization
    :return: A serialized description of the model specified
    """
    user_id = rtip.receiver_id

    ret = serialize_itip(session, itip, language)

    ret['id'] = itip.id
    ret['progressive'] = itip.progressive
    ret['receiver_id'] = user_id
    ret['custodian'] = State.tenants[itip.tid].cache['custodian']
    ret['important'] = itip.important
    ret['label'] = itip.label
    ret['enable_notifications'] = rtip.enable_notifications

    iar = session.query(models.IdentityAccessRequest) \
                 .filter(models.IdentityAccessRequest.internaltip_id == itip.id) \
                 .order_by(models.IdentityAccessRequest.request_date.desc()).first()

    if iar:
        ret['iar'] = serialize_identityaccessrequest(session, iar)

    for receiver in session.query(models.User) \
                           .filter(models.User.id == models.ReceiverTip.receiver_id,
                                   models.ReceiverTip.internaltip_id == itip.id):
        ret['receivers'].append({
          'id': receiver.id,
          'name': receiver.name
        })

    if 'whistleblower_identity' in ret['data']:
        ret['data']['whistleblower_identity_provided'] = True

        if 'iar' not in ret or ret['iar']['reply'] == 'denied':
            del ret['data']['whistleblower_identity']


    for ifile, wbfile in session.query(models.InternalFile, models.WhistleblowerFile) \
                               .filter(models.InternalFile.id == models.WhistleblowerFile.internalfile_id,
                                       models.WhistleblowerFile.receivertip_id == rtip.id):
        ret['wbfiles'].append(serialize_wbfile(session, ifile, wbfile))

    for rfile in session.query(models.ReceiverFile) \
                         .filter(models.ReceiverFile.internaltip_id == itip.id,
                                 or_(models.ReceiverFile.visibility == 0,
                                     models.ReceiverFile.visibility == 1,
                                     and_(models.ReceiverFile.visibility == 2,
                                          models.ReceiverFile.author_id == user_id))):
        ret['rfiles'].append(serialize_rfile(session, rfile))

    for comment in session.query(models.Comment) \
                          .filter(models.Comment.internaltip_id == itip.id,
                                  or_(models.Comment.visibility == 0,
                                      models.Comment.visibility == 1,
                                      and_(models.Comment.visibility == 2,
                                           models.Comment.author_id == user_id))):
        ret['comments'].append(serialize_comment(session, comment))

    return ret


def serialize_wbtip(session, itip, language):
    ret = serialize_itip(session, itip, language)

    for receiver in session.query(models.User) \
                           .filter(models.User.id == models.ReceiverTip.receiver_id,
                                   models.ReceiverTip.internaltip_id == itip.id):
        ret['receivers'].append({
          'id': receiver.id,
          'name': receiver.public_name
        })

    for ifile in session.query(models.InternalFile) \
                        .filter(models.InternalFile.internaltip_id == itip.id):
        ret['wbfiles'].append(serialize_ifile(session, ifile))

    for rfile in session.query(models.ReceiverFile) \
                         .filter(models.ReceiverFile.internaltip_id == itip.id,
                                 models.ReceiverFile.visibility == 0):
        ret['rfiles'].append(serialize_rfile(session, rfile))

    for comment in session.query(models.Comment) \
                          .filter(models.Comment.internaltip_id == itip.id,
                                  models.Comment.visibility == 0):
        ret['comments'].append(serialize_comment(session, comment))


    return ret


def serialize_redirect(redirect):
    """
    Transact for serializing a redirect

    :param redirect: The redirect to be serialized
    :return: The serialized redirect
    """
    return {
        'id': redirect.id,
        'path1': redirect.path1,
        'path2': redirect.path2
    }


def serialize_signup(signup):
    """
    Transaction serializing the signup descriptor

    :param signup: A signup model
    :return: A serialization of the provided model
    """
    return {
        'name': signup.name,
        'surname': signup.surname,
        'role': signup.role,
        'email': signup.email,
        'phone': signup.phone,
        'subdomain': signup.subdomain,
        'language': signup.language,
        'activation_token': signup.activation_token,
        'registration_date': signup.registration_date,
        'organization_name': signup.organization_name,
        'organization.tax_code': signup.organization_tax_code,
        'organization_vat_code': signup.organization_vat_code,
        'organization_location': signup.organization_location,
        'tos1': signup.tos1,
        'tos2': signup.tos2
    }


def serialize_tenant(session, tenant):
    ret = {
      'id': tenant.id,
      'creation_date': tenant.creation_date,
      'active': tenant.active
    }

    ret.update(ConfigFactory(session, tenant.id).serialize('tenant'))

    return ret

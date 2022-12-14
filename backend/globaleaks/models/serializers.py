# -*- coding: utf-8
import copy
from globaleaks import models
from globaleaks.models.config import ConfigFactory
from globaleaks.state import State


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
    itip, user = session.query(models.InternalTip, models.User) \
                      .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                              models.ReceiverTip.id == identityaccessrequest.receivertip_id,
                              models.User.id == models.ReceiverTip.receiver_id).one()

    reply_user = session.query(models.User) \
                        .filter(models.User.id == identityaccessrequest.reply_user_id).one_or_none()

    return {
        'id': identityaccessrequest.id,
        'receivertip_id': identityaccessrequest.receivertip_id,
        'request_date': identityaccessrequest.request_date,
        'request_user_name': user.name,
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
        'type': comment.type,
        'creation_date': comment.creation_date,
        'content': comment.content,
        'author': comment.author_id
    }


def serialize_message(session, message):
    """
    Transaction returning a serialized descriptor of a message

    :param session: An ORM session
    :param message: A model to be serialized
    :return: A serialized description of the model specified
    """
    receiver_involved_id = session.query(models.ReceiverTip.receiver_id) \
                                  .filter(models.ReceiverTip.id == models.Message.receivertip_id,
                                          models.Message.id == message.id).one()

    return {
        'id': message.id,
        'type': message.type,
        'creation_date': message.creation_date,
        'content': message.content,
        'receiver_involved_id': receiver_involved_id
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
        'filename': ifile.filename
    }


def serialize_rfile(session, ifile, rfile):
    """
    Transaction for serializing rfile

    :param session: An ORM session
    :param ifile: The ifile to be serialized
    :param rfile: The rfile to be serialized
    :return: The serialized rfile
    """
    return {
        'id': rfile.id,
        'creation_date': ifile.creation_date,
        'name': ifile.name,
        'size': ifile.size,
        'type': ifile.content_type,
        'filename': rfile.filename
    }


def serialize_wbfile(session, wbfile):
    """
    Transaction for serializing wbfile

    :param session: An ORM session
    :param wbfile: The wbfile to be serialized
    :return: The serialized wbfile
    """
    return {
        'id': wbfile.id,
        'creation_date': wbfile.creation_date,
        'name': wbfile.name,
        'size': wbfile.size,
        'type': wbfile.content_type,
        'description': wbfile.description,
        'filename': wbfile.filename
    }


def serialize_itip(session, internaltip, language):
    x = session.query(models.InternalTipAnswers, models.ArchivedSchema) \
               .filter(models.ArchivedSchema.hash == models.InternalTipAnswers.questionnaire_hash,
                       models.InternalTipAnswers.internaltip_id == internaltip.id) \
               .order_by(models.InternalTipAnswers.creation_date.desc())

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
        'progressive': internaltip.progressive,
        'context_id': internaltip.context_id,
        'questionnaires': questionnaires,
        'tor': internaltip.tor,
        'mobile': internaltip.mobile,
        'reminder_date_soft' : internaltip.reminder_date_soft,
        'reminder_date_hard' : internaltip.reminder_date_hard,
        'enable_two_way_comments': internaltip.enable_two_way_comments,
        'enable_two_way_messages': internaltip.enable_two_way_messages,
        'enable_attachments': internaltip.enable_attachments,
        'enable_whistleblower_identity': internaltip.enable_whistleblower_identity,
        'last_access': internaltip.last_access,
        'score': internaltip.score,
        'status': internaltip.status,
        'substatus': internaltip.substatus,
        'receivers': [],
        'messages': [],
        'comments': [],
        'rfiles': [],
        'wbfiles': [],
        'data': {}
    }

    for comment in session.query(models.Comment) \
                          .filter(models.Comment.internaltip_id == internaltip.id):
        ret['comments'].append(serialize_comment(session, comment))

    for wbfile in session.query(models.WhistleblowerFile) \
                         .filter(models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                                 models.ReceiverTip.internaltip_id == internaltip.id):
        ret['wbfiles'].append(serialize_wbfile(session, wbfile))

    for itd in session.query(models.InternalTipData).filter(models.InternalTipData.internaltip_id == internaltip.id):
        ret['data'][itd.key] = itd.value

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

    ret['id'] = rtip.id
    ret['internaltip_id'] = itip.id
    ret['receiver_id'] = user_id
    ret['custodian'] = State.tenants[itip.tid].cache['enable_custodian']
    ret['important'] = itip.important
    ret['label'] = itip.label
    ret['reminder_notification_status'] = itip.reminder_notification_status

    ret['enable_notifications'] = rtip.enable_notifications

    iar = session.query(models.IdentityAccessRequest) \
                 .filter(models.IdentityAccessRequest.receivertip_id == rtip.id) \
                 .order_by(models.IdentityAccessRequest.request_date.desc()).first()

    if iar:
        ret['iar'] = serialize_identityaccessrequest(session, iar)
    else:
        ret['iar'] = None

    for receiver in session.query(models.User) \
                           .filter(models.User.id == models.ReceiverTip.receiver_id,
                                   models.ReceiverTip.internaltip_id == itip.id):
        ret['receivers'].append({
          'id': receiver.id,
          'name': receiver.name
        })

    for message in session.query(models.Message) \
                          .filter(models.Message.receivertip_id == rtip.id):
        ret['messages'].append(serialize_message(session, message))

    if 'whistleblower_identity' in ret['data']:
        ret['data']['whistleblower_identity_provided'] = True

        if ret['iar'] is None or ret['iar']['reply'] == 'denied':
            del ret['data']['whistleblower_identity']

    for ifile, rfile in session.query(models.InternalFile, models.ReceiverFile) \
                               .filter(models.InternalFile.id == models.ReceiverFile.internalfile_id,
                                       models.ReceiverFile.receivertip_id == rtip.id):
        ret['rfiles'].append(serialize_rfile(session, ifile, rfile))

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

    for message in session.query(models.Message) \
                          .filter(models.Message.receivertip_id == models.ReceiverTip.id,
                                  models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                  models.InternalTip.id == itip.id):
        ret['messages'].append(serialize_message(session, message))

    for ifile in session.query(models.InternalFile) \
                        .filter(models.InternalFile.internaltip_id == itip.id):
        ret['rfiles'].append(serialize_ifile(session, ifile))

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

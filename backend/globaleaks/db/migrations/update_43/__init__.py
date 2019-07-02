# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_never, datetime_now, datetime_null


class InternalTip_v_42(Model):
    __tablename__ = 'internaltip'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    encrypted = Column(Boolean, default=False, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)
    questionnaire_hash = Column(UnicodeText(64), nullable=False)
    preview = Column(JSON, nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    identity_provided = Column(Boolean, default=False, nullable=False)
    identity_provided_date = Column(DateTime, default=datetime_null, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_two_way_messages = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)

    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    wb_access_counter = Column(Integer, default=0, nullable=False)

    status = Column(UnicodeText(36), nullable=False)
    substatus = Column(UnicodeText(36), nullable=True)


class ReceiverTip_v_42(Model):
    __tablename__ = 'receivertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tip_key = Column(UnicodeText, default=u'', nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    receiver_id = Column(UnicodeText(36), nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    access_counter = Column(Integer, default=0, nullable=False)
    label = Column(UnicodeText, default=u'', nullable=False)
    can_access_whistleblower_identity = Column(Boolean, default=True, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)


class Signup_v_42(Model):
    __tablename__ = 'signup'

    id = Column(Integer, primary_key=True, nullable=False)
    tid = Column(Integer, nullable=False)
    subdomain = Column(UnicodeText, unique=True, nullable=False)
    language = Column(UnicodeText, nullable=False)
    name = Column(UnicodeText, nullable=False)
    surname = Column(UnicodeText, nullable=False)
    role = Column(UnicodeText, default=u'', nullable=False)
    phone = Column(UnicodeText, default=u'', nullable=False)
    email = Column(UnicodeText, nullable=False)
    use_case = Column(UnicodeText, default=u'', nullable=False)
    use_case_other = Column(UnicodeText, default=u'', nullable=False)
    organization_name = Column(UnicodeText, default=u'', nullable=False)
    organization_type = Column(UnicodeText, default=u'', nullable=False)
    organization_location1 = Column(UnicodeText, default=u'', nullable=False)
    organization_location2 = Column(UnicodeText, default=u'', nullable=False)
    organization_location3 = Column(UnicodeText, default=u'', nullable=False)
    organization_location4 = Column(UnicodeText, default=u'', nullable=False)
    organization_site = Column(UnicodeText, default=u'', nullable=False)
    organization_number_employees = Column(UnicodeText, default=u'', nullable=False)
    organization_number_users = Column(UnicodeText, default=u'', nullable=False)
    hear_channel = Column(UnicodeText, default=u'', nullable=False)
    activation_token = Column(UnicodeText, nullable=False)

    password_admin = Column(UnicodeText, default=u'', nullable=False)
    password_recipient = Column(UnicodeText, default=u'', nullable=False)

    client_ip_address = Column(UnicodeText, default=u'', nullable=False)
    client_user_agent = Column(UnicodeText, default=u'', nullable=False)
    registration_date = Column(DateTime, default=datetime_now, nullable=False)
    tos1 = Column(UnicodeText, default=u'', nullable=False)
    tos2 = Column(UnicodeText, default=u'', nullable=False)


class User_v_42(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default=u'', nullable=False)
    password = Column(UnicodeText, default=u'', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
    name = Column(UnicodeText, default=u'', nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    role = Column(UnicodeText, default=u'receiver', nullable=False)
    state = Column(UnicodeText, default=u'enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default=u'', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)
    auth_token = Column(UnicodeText, default=u'', nullable=False)
    enc_prv_key = Column(UnicodeText, default=u'', nullable=False)
    enc_pub_key = Column(UnicodeText, default=u'', nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    change_email_address = Column(UnicodeText, default=u'', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_never, nullable=False)
    reset_password_token = Column(UnicodeText, unique=True, nullable=True)
    reset_password_date = Column(UnicodeText, default=datetime_never, nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_public = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class WhistleblowerTip_v_42(Model):
    __tablename__ = 'whistleblowertip'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    receipt_hash = Column(UnicodeText(128), nullable=False)

    wb_prv_key = Column(UnicodeText, default=u'', nullable=False)
    wb_pub_key = Column(UnicodeText, default=u'', nullable=False)
    wb_tip_key = Column(UnicodeText, default=u'', nullable=False)
    enc_data = Column(UnicodeText, default=u'', nullable=False)


class MigrationScript(MigrationBase):
    pass

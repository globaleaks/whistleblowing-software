# -*- coding: utf-8 -*-
import importlib
import os
import shutil
import sys
from collections import OrderedDict

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from globaleaks import __version__, models, \
    DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED, LANGUAGES_SUPPORTED_CODES
from globaleaks.db.appdata import load_appdata, db_load_defaults
from globaleaks.orm import db_log

from globaleaks.db.migrations.update_31 import Node_v_30, Context_v_30, \
    User_v_30, ReceiverTip_v_30, Notification_v_30
from globaleaks.db.migrations.update_32 import Node_v_31, Comment_v_31, \
    Message_v_31, User_v_31
from globaleaks.db.migrations.update_33 import Node_v_32, \
    WhistleblowerTip_v_32, InternalTip_v_32, User_v_32
from globaleaks.db.migrations.update_34 import Node_v_33, Notification_v_33
from globaleaks.db.migrations.update_35 import Context_v_34, InternalTip_v_34, \
    WhistleblowerTip_v_34
from globaleaks.db.migrations.update_38 import Field_v_37, Questionnaire_v_37
from globaleaks.db.migrations.update_39 import \
    Anomalies_v_38, ArchivedSchema_v_38, Comment_v_38, Config_v_38, \
    ConfigL10N_v_38, Context_v_38, CustomTexts_v_38, EnabledLanguage_v_38, \
    Field_v_38, FieldAnswer_v_38, FieldAnswerGroup_v_38, FieldAttr_v_38, \
    FieldOption_v_38, File_v_38, IdentityAccessRequest_v_38, \
    InternalFile_v_38, InternalTip_v_38, Mail_v_38, Message_v_38, \
    Questionnaire_v_38, Receiver_v_38, ReceiverContext_v_38, \
    ReceiverFile_v_38, ReceiverTip_v_38, \
    Step_v_38, User_v_38, WhistleblowerFile_v_38, WhistleblowerTip_v_38
from globaleaks.db.migrations.update_40 import \
    FieldAnswer_v_39, FieldAnswerGroup_v_39
from globaleaks.db.migrations.update_41 import InternalFile_v_40, \
    InternalTip_v_40, ReceiverFile_v_40, ReceiverTip_v_40, \
    User_v_40, WhistleblowerFile_v_40
from globaleaks.db.migrations.update_42 import InternalTip_v_41
from globaleaks.db.migrations.update_43 import InternalTip_v_42, \
    User_v_42
from globaleaks.db.migrations.update_45 import Context_v_44, Field_v_44, \
    InternalTip_v_44, Receiver_v_44, ReceiverFile_v_44, \
    ReceiverTip_v_44, Step_v_44, User_v_44, WhistleblowerFile_v_44, \
    WhistleblowerTip_v_44
from globaleaks.db.migrations.update_46 import Config_v_45, ConfigL10N_v_45, \
    Context_v_45, Field_v_45, FieldOption_v_45, InternalFile_v_45, \
    InternalTip_v_45, Receiver_v_45, User_v_45, WhistleblowerFile_v_45
from globaleaks.db.migrations.update_47 import Context_v_46, FieldOption_v_46, \
    InternalTip_v_46, SubmissionStatus_v_46, SubmissionSubStatus_v_46
from globaleaks.db.migrations.update_48 import Field_v_47, FieldOption_v_47
from globaleaks.db.migrations.update_49 import InternalTip_v_48
from globaleaks.db.migrations.update_50 import SubmissionStatus_v_49, \
    SubmissionSubStatus_v_49, User_v_49
from globaleaks.db.migrations.update_51 import Field_v_50, InternalFile_v_50, \
    User_v_50
from globaleaks.db.migrations.update_52 import Context_v_51, \
    Field_v_51, FieldAttr_v_51, FieldOption_v_51, \
    InternalTip_v_51, InternalTipData_v_51, \
    Message_v_51, ReceiverFile_v_51, Step_v_51, \
    ReceiverContext_v_51, \
    SubmissionStatus_v_51, SubmissionSubStatus_v_51, User_v_51
from globaleaks.db.migrations.update_53 import InternalTip_v_52, \
    ReceiverTip_v_52, Subscriber_v_52, \
    Tenant_v_52, User_v_52
from globaleaks.db.migrations.update_54 import ContextImg_v_53, File_v_53, UserImg_v_53
from globaleaks.db.migrations.update_55 import SubmissionStatusChange_v_54, User_v_54
from globaleaks.db.migrations.update_57 import User_v_56
from globaleaks.db.migrations.update_58 import InternalTip_v_57, \
    ReceiverFile_v_57, ReceiverTip_v_57, WhistleblowerFile_v_57
from globaleaks.db.migrations.update_59 import ReceiverTip_v_58
from globaleaks.db.migrations.update_60 import InternalTip_v_59, ReceiverTip_v_59, WhistleblowerTip_v_59
from globaleaks.db.migrations.update_62 import AuditLog_v_61, Context_v_61, ReceiverTip_v_61, User_v_61
from globaleaks.db.migrations.update_63 import Subscriber_v_62
from globaleaks.db.migrations.update_64 import Context_v_63, InternalTip_v_63

from globaleaks.orm import get_engine, get_session, make_db_uri
from globaleaks.models import config, Base
from globaleaks.settings import Settings
from globaleaks.utils.fs import srm
from globaleaks.utils.log import log
from globaleaks.utils.utility import datetime_now


migration_mapping = OrderedDict([
    ('ArchivedSchema', [ArchivedSchema_v_38, 0, 0, 0, 0, 0, 0, 0, 0, models._ArchivedSchema, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('AuditLog', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, AuditLog_v_61, 0, 0, 0, 0, 0, 0, 0, models._AuditLog, 0, 0, 0]),
    ('Comment', [Comment_v_31, 0, Comment_v_38, 0, 0, 0, 0, 0, 0, models._Comment, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Config', [-1, -1, -1, -1, Config_v_38, 0, 0, 0, 0, Config_v_45, 0, 0, 0, 0, 0, 0, models._Config, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ConfigL10N', [-1, -1, -1, -1, ConfigL10N_v_38, 0, 0, 0, 0, ConfigL10N_v_45, 0, 0, 0, 0, 0, 0, models._ConfigL10N, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Context', [Context_v_30, Context_v_34, 0, 0, 0, 0, 0, 0, 0, Context_v_44, 0, 0, 0, 0, 0, Context_v_45, Context_v_46, Context_v_51, 0, 0, 0, 0, Context_v_61, 0, 0, 0, 0, 0, 0, 0, 0, 0, Context_v_63, 0, models._Context, 0]),
    ('ContextImg', [-1, -1, -1, -1, -1, -1, -1, -1, -1, ContextImg_v_53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('CustomTexts', [-1, -1, CustomTexts_v_38, 0, 0, 0, 0, 0, 0, models._CustomTexts, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('EnabledLanguage', [-1, -1, -1, -1, EnabledLanguage_v_38, 0, 0, 0, 0, models._EnabledLanguage, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Field', [Field_v_37, 0, 0, 0, 0, 0, 0, 0, Field_v_38, Field_v_44, 0, 0, 0, 0, 0, Field_v_45, Field_v_47, 0, Field_v_50, 0, 0, Field_v_51, models._Field, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('FieldAnswer', [FieldAnswer_v_38, 0, 0, 0, 0, 0, 0, 0, 0, FieldAnswer_v_39, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('FieldAnswerGroup', [FieldAnswerGroup_v_38, 0, 0, 0, 0, 0, 0, 0, 0, FieldAnswerGroup_v_39, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('FieldAttr', [FieldAttr_v_38, 0, 0, 0, 0, 0, 0, 0, 0, FieldAttr_v_51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models._FieldAttr, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('FieldOption', [FieldOption_v_38, 0, 0, 0, 0, 0, 0, 0, 0, FieldOption_v_45, 0, 0, 0, 0, 0, 0, FieldOption_v_46, FieldOption_v_47, FieldOption_v_51, 0, 0, 0, models._FieldOption, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('FieldOptionTriggerField', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models._FieldOptionTriggerField, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('FieldOptionTriggerStep', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models._FieldOptionTriggerStep, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('File', [-1, File_v_38, 0, 0, 0, 0, 0, 0, 0, File_v_53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models._File, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('IdentityAccessRequest', [IdentityAccessRequest_v_38, 0, 0, 0, 0, 0, 0, 0, 0, models._IdentityAccessRequest, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('InternalFile', [InternalFile_v_38, 0, 0, 0, 0, 0, 0, 0, 0, InternalFile_v_40, 0, InternalFile_v_45, 0, 0, 0, 0, InternalFile_v_50, 0, 0, 0, 0, models._InternalFile, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('InternalTip', [InternalTip_v_32, 0, 0, InternalTip_v_34, 0, InternalTip_v_38, 0, 0, 0, InternalTip_v_40, 0, InternalTip_v_41, InternalTip_v_42, InternalTip_v_44, 0, InternalTip_v_45, InternalTip_v_46, InternalTip_v_48, 0, InternalTip_v_51, 0, 0, InternalTip_v_52, InternalTip_v_57, 0, 0, 0, 0, InternalTip_v_59, 0, InternalTip_v_63, 0, 0, 0, models._InternalTip, 0]),
    ('InternalTipAnswers', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models._InternalTipAnswers, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('InternalTipData', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, InternalTipData_v_51, 0, 0, 0, 0, 0, 0, models._InternalTipData, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Mail', [Mail_v_38, 0, 0, 0, 0, 0, 0, 0, 0, models._Mail, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Message', [Message_v_31, 0, Message_v_38, 0, 0, 0, 0, 0, 0, Message_v_51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, Message_v_64, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1]),
    ('Node', [Node_v_30, Node_v_31, Node_v_32, Node_v_33, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('Notification', [Notification_v_30, Notification_v_33, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('Questionnaire', [Questionnaire_v_37, 0, 0, 0, 0, 0, 0, 0, Questionnaire_v_38, models._Questionnaire, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Receiver', [Receiver_v_38, 0, 0, 0, 0, 0, 0, 0, 0, Receiver_v_44, 0, 0, 0, 0, 0, Receiver_v_45, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('ReceiverContext', [ReceiverContext_v_38, 0, 0, 0, 0, 0, 0, 0, 0, ReceiverContext_v_51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models._ReceiverContext, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ReceiverFile', [ReceiverFile_v_38, 0, 0, 0, 0, 0, 0, 0, 0, ReceiverFile_v_40, 0, ReceiverFile_v_44, 0, 0, 0, ReceiverFile_v_51, 0, 0, 0, 0, 0, 0, ReceiverFile_v_57, 0, 0, 0, 0, 0, models._ReceiverFile, 0, 0, 0, 0, 0, 0, 0]),
    ('ReceiverTip', [ReceiverTip_v_30, ReceiverTip_v_38, 0, 0, 0, 0, 0, 0, 0, ReceiverTip_v_40, 0, ReceiverTip_v_44, 0, 0, 0, ReceiverTip_v_52, 0, 0, 0, 0, 0, 0, 0, ReceiverTip_v_57, 0, 0, 0, 0, ReceiverTip_v_58, ReceiverTip_v_59, ReceiverTip_v_61, 0, models._ReceiverTip, 0, 0, 0]),
    ('Redirect', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models._Redirect, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('SubmissionStatus', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, SubmissionStatus_v_46, 0, 0, 0, 0, SubmissionStatus_v_49, 0, 0, SubmissionStatus_v_51, 0, models._SubmissionStatus, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('SubmissionSubStatus', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, SubmissionSubStatus_v_46, 0, 0, 0, 0, SubmissionSubStatus_v_49, 0, 0, SubmissionSubStatus_v_51, 0, models._SubmissionSubStatus, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('SubmissionStatusChange', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, SubmissionStatusChange_v_54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('Step', [Step_v_38, 0, 0, 0, 0, 0, 0, 0, 0, Step_v_44, 0, 0, 0, 0, 0, Step_v_51, 0, 0, 0, 0, 0, 0, models._Step, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -0, 0]),
    ('Subscriber', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, Subscriber_v_52, 0, 0, 0, 0, 0, 0, 0, 0, Subscriber_v_62, 0, 0, 0, 0, 0, 0, 0, 0, 0, models._Subscriber, 0, 0]),
    ('Tenant', [0, 0, 0, 0, 0, 0, 0, 0, 0, Tenant_v_52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models._Tenant, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('User', [User_v_30, User_v_31, User_v_32, User_v_38, 0, 0, 0, 0, 0, User_v_40, 0, User_v_42, 0, User_v_44, 0, User_v_45, User_v_49, 0, 0, 0, User_v_50, User_v_51, User_v_52, User_v_54, 0, User_v_56, 0, User_v_61, 0, 0, 0, 0, models._User, 0, 0, 0]),
    ('UserImg', [-1, -1, -1, -1, -1, -1, -1, -1, -1, UserImg_v_53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('WhistleblowerFile', [-1, -1, -1, -1, -1, WhistleblowerFile_v_38, 0, 0, 0, WhistleblowerFile_v_40, 0, WhistleblowerFile_v_44, 0, 0, 0, WhistleblowerFile_v_45, WhistleblowerFile_v_57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models._WhistleblowerFile, 0, 0, 0, 0, 0, 0, 0]),
    ('WhistleblowerTip', [WhistleblowerTip_v_32, 0, 0, WhistleblowerTip_v_34, 0, WhistleblowerTip_v_38, 0, 0, 0, -1, -1, -1, WhistleblowerTip_v_44, 0, 0, WhistleblowerTip_v_59, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1])
])


def get_right_model(migration_mapping, model_name, version):
    """
    Utility function to retrieve the model corresponding to a specific model name in a specific database version
    :param migration_mapping: The model mappung table
    :param model_name: The model name
    :param version: The database version
    :return: The model corresponding to a specific model name in a specific database version
    """
    table_index = (version - FIRST_DATABASE_VERSION_SUPPORTED)

    if migration_mapping[model_name][table_index] == -1:
        return None

    while table_index >= 0:
        if migration_mapping[model_name][table_index] != 0:
            return migration_mapping[model_name][table_index]
        table_index -= 1

    return None


def perform_data_update(db_file):
    """
    Update the database including up-to-date application data
    :param db_file: The database file path
    """
    now = datetime_now()

    appdata = load_appdata()

    session = get_session(make_db_uri(db_file), foreign_keys = False)

    enabled_languages = [lang.name for lang in session.query(models.EnabledLanguage)]

    removed_languages = list(set(enabled_languages) - set(LANGUAGES_SUPPORTED_CODES))

    if removed_languages:
        removed_languages.sort()
        removed_languages = ', '.join(removed_languages)
        raise Exception("FATAL: cannot complete the upgrade because the support for some of the enabled languages is currently incomplete (%s)\n" % removed_languages)

    try:
        original_version = config.ConfigFactory(session, 1).get_val('version')
        if original_version != __version__:
            for tid in [t[0] for t in session.query(models.Tenant.id)]:
                config.update_defaults(session, tid, appdata)

            db_load_defaults(session)

            session.query(models.Config).filter_by(var_name='version') \
                   .update({'value': __version__, 'update_date': now})

            session.query(models.Config).filter_by(var_name='latest_version') \
                   .update({'value': __version__, 'update_date': now})

            session.query(models.Config).filter_by(var_name='version_db') \
                   .update({'value': DATABASE_VERSION, 'update_date': now})

            db_log(session, tid=1, type='version_update', user_id='system', data={'from': original_version, 'to': __version__})

        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def perform_migration(version):
    """
    Utility function for performing a database migration
    :param version: The current version of the database to update
    """
    if version < FIRST_DATABASE_VERSION_SUPPORTED:
        log.info("Migrations from DB version lower than %d are no longer supported!" % FIRST_DATABASE_VERSION_SUPPORTED)
        sys.exit(1)

    tmpdir = os.path.abspath(os.path.join(Settings.tmp_path, 'tmp'))
    if version < 41:
        orig_db_file = os.path.abspath(os.path.join(Settings.working_path, 'db', 'glbackend-%d.db' % version))
    else:
        orig_db_file = os.path.abspath(os.path.join(Settings.working_path, 'globaleaks.db'))

    final_db_file = os.path.abspath(os.path.join(Settings.working_path, 'globaleaks.db'))

    shutil.rmtree(tmpdir, True)
    os.mkdir(tmpdir)
    shutil.copy(orig_db_file, os.path.join(tmpdir, 'old.db'))

    new_db_file = None

    try:
        while version < DATABASE_VERSION:
            old_db_file = os.path.abspath(os.path.join(tmpdir, 'old.db'))
            new_db_file = os.path.abspath(os.path.join(tmpdir, 'new.db'))

            if os.path.exists(new_db_file):
                shutil.move(new_db_file, old_db_file)

            Settings.db_file = new_db_file
            Settings.enable_input_length_checks = False

            log.info("Updating DB from version %d to version %d" %
                     (version, version + 1))

            j = version - FIRST_DATABASE_VERSION_SUPPORTED
            session_old = get_session(make_db_uri(old_db_file))

            engine = get_engine(make_db_uri(new_db_file), foreign_keys=False, orm_lockdown=False)
            if FIRST_DATABASE_VERSION_SUPPORTED + j + 1 == DATABASE_VERSION:
                Base.metadata.create_all(engine)
            else:
                Bases[j+1].metadata.create_all(engine)

            session_new = sessionmaker(bind=engine)()

            # Here is instanced the migration script
            MigrationModule = importlib.import_module("globaleaks.db.migrations.update_%d" % (version + 1))
            migration_script = MigrationModule.MigrationScript(migration_mapping, version, session_old, session_new)

            log.info("Migrating table:")

            try:
                try:
                    migration_script.prologue()
                except Exception as exception:
                    log.err("Failure while executing migration prologue: %s" % exception)
                    raise exception

                for model_name, _ in migration_mapping.items():
                    if migration_script.model_from[model_name] is not None and migration_script.model_to[model_name] is not None:
                        try:
                            migration_script.migrate_model(model_name)

                            # Commit at every table migration in order to be able to detect
                            # the precise migration that may fail.
                            migration_script.commit()
                        except Exception as exception:
                            log.err("Failure while migrating table %s: %s " % (model_name, exception))
                            raise exception
                try:
                    migration_script.epilogue()
                    migration_script.commit()
                except Exception as exception:
                    log.err("Failure while executing migration epilogue: %s " % exception)
                    raise exception

            finally:
                # the database should be always closed before leaving the application
                # in order to not keep leaking journal files.
                migration_script.close()

            log.info("Migration stats:")

            # we open a new db in order to verify integrity of the generated file
            session_verify = get_session(make_db_uri(new_db_file))

            for model_name, _ in migration_mapping.items():
                if migration_script.model_from[model_name] is not None and migration_script.model_to[model_name] is not None:
                    count = session_verify.query(migration_script.model_to[model_name]).count()
                    if migration_script.entries_count[model_name] != count:
                        if migration_script.skip_count_check.get(model_name, False):
                            log.info(" * %s table migrated (entries count changed from %d to %d)" %
                                     (model_name, migration_script.entries_count[model_name], count))
                        else:
                            raise AssertionError("Integrity check failed on count equality for table %s: %d != %d" %
                                                 (model_name, count, migration_script.entries_count[model_name]))
                    else:
                        log.info(" * %s table migrated (%d entry(s))" %
                                             (model_name, migration_script.entries_count[model_name]))

            version += 1

            session_verify.close()

        perform_data_update(new_db_file)
    except:
        raise
    else:
        # in case of success first copy the new migrated db, then as last action delete the original db file
        shutil.copy(new_db_file, final_db_file)

        if orig_db_file != final_db_file:
            srm(orig_db_file)

        path = os.path.join(Settings.working_path, 'db')
        if os.path.exists(path):
            shutil.rmtree(path)
    finally:
        # Always cleanup the temporary directory used for the migration
        for f in os.listdir(tmpdir):
            srm(os.path.join(tmpdir, f))

        shutil.rmtree(tmpdir)


mp = OrderedDict()
Bases = {}
for i in range(DATABASE_VERSION - FIRST_DATABASE_VERSION_SUPPORTED + 1):
    Bases[i] = declarative_base()
    for k in migration_mapping:
        if k not in mp:
            mp[k] = []

        x = get_right_model(migration_mapping, k,
                            FIRST_DATABASE_VERSION_SUPPORTED + i)
        if x is not None:
            class y(x, Bases[i]):
                pass

            mp[k].append(y)
        else:
            mp[k].append(None)


migration_mapping = mp

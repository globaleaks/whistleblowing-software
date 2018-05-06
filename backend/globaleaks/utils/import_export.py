# -*- coding: utf-8 -*-
# Functions related to importing/exporting the data from a GL instance

import os

from globaleaks import models
from globaleaks.db import get_db_file, make_db_uri
from globaleaks.models import Base
from globaleaks.settings import Settings
from globaleaks.orm import get_engine, get_session

# Allows for easy testing as a new root tenant
EXPORTED_TENANT_ID = 0

# Direct TID references are, as the name suggests things that
# directly connect to a tenant and need to be serialized in full
DIRECT_TID_REFERENCES = [
    ('anomalies', models.Anomalies),
    ('config', models.Config),
    ('config_l10n', models.ConfigL10N),
    ('context', models.Context),
    ('counters', models.Counter),
    ('custom_texts', models.CustomTexts),
    ('enabledlanguages', models.EnabledLanguage),
    ('field', models.Field),
    ('file', models.File),
    ('internaltip', models.InternalTip),
    ('mail', models.Mail),
    ('questionaire', models.Questionnaire),
    ('signup', models.Signup),
    ('shorturl', models.ShortURL),
    ('stats', models.Stats),
    ('user', models.User),
    ('usertenant', models.UserTenant)
]

IMPORT_ORDER = [
    'anomalies',
    'config',
    'config_l10n',
    'context',
    'counters',
    'custom_texts',
    'enabledlanguages',
    'field',
    'file',
    'internaltip',
    'mail',
    'questionaire',
    'signup',
    'shorturl',
    'stats',
    'user',
    'usertenant',
    'comment',
    'contextimg',
    'fieldanswer',
    'fieldanswergroup',
    'fieldattr',
    'fieldoption',
    'internalfile',
    'receiver',
    'receivercontext',
    'receivertip',
    'identityaccessrequest',
    'step',
    'userimg',
    'whistleblowerfile'
]

def row_serializator(session, rowset, output_list):
    '''Serializes and expunges a row for import into a clean DB'''
    for row in rowset:
        session.expunge(row)
        if hasattr(row, 'tid'):
            row.tid = EXPORTED_TENANT_ID
        if hasattr(row, 'tenant_id'):
            row.tenant_id = EXPORTED_TENANT_ID
        output_list.append(row)

def build_id_list(dataset, column_name):
    id_list = []
    for row in dataset:
        id_list.append(row.__dict__[column_name])

    return id_list

def collect_pk_relation(session, model, pks, filter_column):
    data = []
    for pk in pks:
        filter_dict = { filter_column: pk}
        rows = session.query(model).filter_by(**filter_dict)
        for row in rows:
            session.expunge(row)
            data.append(row)

    return data

def collect_all_tenant_data(db_file, tid):
    '''Collects the tenant data into dictionary form ready for serialization
       into a new database instance detaching the information from SQLAlchemy'''

    tenant_data = {}

    # First recover the base tenant data
    session = get_session(make_db_uri(db_file))
    tenant = session.query(models.Tenant).filter_by(id=tid).first()
    print("Exporting Tenant: " + tenant.label)
    session.expunge(tenant)

    # Zero out the PK to note that this is special
    tenant.id = EXPORTED_TENANT_ID
    tenant_data['tenant'] = tenant

    ## DIRECT REFERENCES TO TIDs GO HERE; WE'LL GET RELATED DATA BELOW!

    for element in DIRECT_TID_REFERENCES:
        tenant_data[element[0]] = []

        # HACK: see if we can change the column name
        if element[0] == 'usertenant':
            rows = session.query(element[1]).filter_by(tenant_id=tid)
        else:
            rows = session.query(element[1]).filter_by(tid=tid)

        row_serializator(session, rows, tenant_data[element[0]])
        print("  Serialized " + element[0] + " (" + str(len(tenant_data[element[0]])) + " rows)")

    # At thie point, things get more complex because we need to reference the existing data, and
    # go fishing for what we actually need.

    # We'll get a list of IDs we need from the primary data
    context_ids = build_id_list(tenant_data['context'], 'id')
    field_ids = build_id_list(tenant_data['field'], 'id')
    internaltip_ids = build_id_list(tenant_data['internaltip'], 'id')
    user_ids = build_id_list(tenant_data['user'], 'id')
    questionaire_id = build_id_list(tenant_data['questionaire'], 'id')

    # Comment
    tenant_data['comment'] = collect_pk_relation(session, models.Comment, internaltip_ids, 'internaltip_id')
    print("  Serialized comment (" + str(len(tenant_data['comment'])) + " rows)")

    # ContextImg
    tenant_data['contextimg'] = collect_pk_relation(session, models.ContextImg, context_ids, 'id')
    print("  Serialized contextimg (" + str(len(tenant_data['contextimg'])) + " rows)")

    # FieldAnswer
    tenant_data['fieldanswer'] = collect_pk_relation(session, models.FieldAnswer, internaltip_ids, 'internaltip_id')
    print("  Serialized fieldanswer (" + str(len(tenant_data['fieldanswer'])) + " rows)")

    # FieldAnswerGroup
    fieldanswer_ids = build_id_list(tenant_data['fieldanswer'], 'id')
    tenant_data['fieldanswergroup'] = collect_pk_relation(session, models.FieldAnswerGroup, fieldanswer_ids, 'id')
    print("  Serialized fieldanswergroup (" + str(len(tenant_data['fieldanswergroup'])) + " rows)")

    # FieldAttr
    tenant_data['fieldattr'] = collect_pk_relation(session, models.FieldAttr, field_ids, 'field_id')
    print("  Serialized fieldattr (" + str(len(tenant_data['fieldattr'])) + " rows)")

    # FieldOption
    tenant_data['fieldoption'] = collect_pk_relation(session, models.FieldOption, field_ids, 'field_id')
    print("  Serialized fieldoption (" + str(len(tenant_data['fieldoption'])) + " rows)")

    # InternalFile
    tenant_data['internalfile'] = collect_pk_relation(session, models.InternalFile, field_ids, 'internaltip_id')
    print("  Serialized internalfile (" + str(len(tenant_data['internalfile'])) + " rows)")
    
    # Receivers
    tenant_data['receiver'] = collect_pk_relation(session, models.Receiver, user_ids, 'id')
    print("  Serialized receiver (" + str(len(tenant_data['receiver'])) + " rows)")

    # ReceiverContext
    tenant_data['receivercontext'] = collect_pk_relation(session, models.ReceiverContext, context_ids, 'context_id')
    print("  Serialized receivercontext (" + str(len(tenant_data['receivercontext'])) + " rows)")

    # ReceiverTip
    tenant_data['receivertip'] = collect_pk_relation(session, models.ReceiverTip, internaltip_ids, 'internaltip_id')
    print("  Serialized receivertip (" + str(len(tenant_data['receivertip'])) + " rows)")

    # IdentityAccessRequest
    receivertip_ids = build_id_list(tenant_data['receivertip'], 'receivertip_id')
    tenant_data['identityaccessrequest'] = collect_pk_relation(session, models.IdentityAccessRequest, receivertip_ids, 'id')
    print("  Serialized identityaccessrequest (" + str(len(tenant_data['identityaccessrequest'])) + " rows)")

    # Step
    tenant_data['step'] = collect_pk_relation(session, models.Step, questionaire_id, 'questionnaire_id')
    print("  Serialized step (" + str(len(tenant_data['step'])) + " rows)")

    # UserImg
    tenant_data['userimg'] = collect_pk_relation(session, models.UserImg, user_ids, 'id')
    print("  Serialized userimg (" + str(len(tenant_data['userimg'])) + " rows)")


    # WhistleblowerFile
    tenant_data['whistleblowerfile'] = collect_pk_relation(session, models.WhistleblowerFile, receivertip_ids, 'receivertip_id')
    print("  Serialized whistleblowerfile (" + str(len(tenant_data['whistleblowerfile'])) + " rows)")

    session.close()
    return tenant_data

def write_tenant_to_fresh_db(tenant_data):
    '''Writes the tenant data to a fresh database'''
    
    # Now we need to initialize a fresh database
    db_path = '/tmp/globaleaks.db'

    # FIXME: Remove testing code for proper temp db
    try:
        os.remove(db_path)
    except FileNotFoundError:
        pass

    # Need the engine to initialize all the base classes
    engine = get_engine(make_db_uri(db_path))
    engine.execute('PRAGMA foreign_keys = ON')
    engine.execute('PRAGMA secure_delete = ON')
    engine.execute('PRAGMA auto_vacuum = FULL')

    Base.metadata.create_all(engine)
    print("Initialized empty GlobaLeaks database at " + db_path)

    session = get_session(make_db_uri(db_path))

    # Create the root tenant object
    session.merge(tenant_data['tenant'])

    # Replay the tenant data
    for element in IMPORT_ORDER:
        for row in tenant_data[element]:
            session.merge(row)

    print("Export Complete!")
    session.commit()
    session.close()

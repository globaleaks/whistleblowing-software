# -*- coding: utf-8 -*-
# Functions related to importing/exporting the data from a GL instance

from globaleaks import models

from globaleaks.db import get_db_file, make_db_uri
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
    user_ids = build_id_list(tenant_data['user'], 'id')

    # Receivers
    tenant_data['receiver'] = collect_pk_relation(session, models.Receiver, user_ids, 'id')
    print("  Serialized receiver (" + str(len(tenant_data['receiver'])) + " rows)")

    # UserImg
    tenant_data['userimg'] = collect_pk_relation(session, models.UserImg, user_ids, 'id')
    print("  Serialized userimg (" + str(len(tenant_data['userimg'])) + " rows)")

    #import pprint
    #pprint.pprint(tenant_data)
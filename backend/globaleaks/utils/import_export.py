# -*- coding: utf-8 -*-
# Functions related to importing/exporting the data from a GL instance

import copy
import io
import os
import shutil
import tarfile
import tempfile

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
    'archivedschema',
    'anomalies',
    'enabledlanguages',
    'config',
    'config_l10n',
    'questionaire',
    'context',
    'step',
    'counters',
    'custom_texts',
    'field',
    'file',
    'internaltip',
    'mail',
    'signup',
    'shorturl',
    'stats',
    'user',
    'usertenant',
    'comment',
    'contextimg',
    'fieldanswer_nulled', # See below for this ugly hack
    'fieldanswergroup',
    'fieldanswer',
    'fieldattr',
    'fieldoption',
    'internalfile',
    'receiver',
    'receivercontext',
    'receivertip',
    'receiverfile',
    'identityaccessrequest',
    'userimg',
    'whistleblowerfile'
]

def row_serializator(session, rowset, output_list):
    '''Serializes and expunges a row for import into a clean DB'''
    for row in rowset:
        session.expunge(row)
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

def collect_all_tenant_data(session, tid):
    '''Collects the tenant data into dictionary form ready for serialization
       into a new database instance detaching the information from SQLAlchemy'''

    tenant_data = {}

    # First recover the base tenant data
    tenant = session.query(models.Tenant).filter_by(id=tid).first()

    if tid == EXPORTED_TENANT_ID:
        print("Importing Tenant: " + tenant.label)
    else:
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
    questionairehash_id = build_id_list(tenant_data['internaltip'], 'questionnaire_hash')

    # ArchivedSchema
    tenant_data['archivedschema'] = collect_pk_relation(session, models.ArchivedSchema, questionairehash_id, 'hash')
    print("  Serialized archivedschema (" + str(len(tenant_data['archivedschema'])) + " rows)")
    
    # Comment
    tenant_data['comment'] = collect_pk_relation(session, models.Comment, internaltip_ids, 'internaltip_id')
    print("  Serialized comment (" + str(len(tenant_data['comment'])) + " rows)")

    # ContextImg
    tenant_data['contextimg'] = collect_pk_relation(session, models.ContextImg, context_ids, 'id')
    print("  Serialized contextimg (" + str(len(tenant_data['contextimg'])) + " rows)")

    # FieldAnswer
    tenant_data['fieldanswer'] = collect_pk_relation(session, models.FieldAnswer, internaltip_ids, 'internaltip_id')
    print("  Serialized fieldanswer (" + str(len(tenant_data['fieldanswer'])) + " rows)")

    # HACK ALERT: fieldanswer has a circular dependency on fieldanswergroup. To allow this to fly, we need
    # to create a version of fieldanswer with the FK nulled out, import that, and then override it
    tenant_data['fieldanswer_nulled'] = copy.deepcopy(tenant_data['fieldanswer'])
    for fieldanswer in tenant_data['fieldanswer_nulled']:
        fieldanswer.fieldanswergroup_id = None

    # FieldAnswerGroup
    fieldanswer_ids = build_id_list(tenant_data['fieldanswer'], 'id')
    tenant_data['fieldanswergroup'] = collect_pk_relation(session, models.FieldAnswerGroup, fieldanswer_ids, 'fieldanswer_id')
    print("  Serialized fieldanswergroup (" + str(len(tenant_data['fieldanswergroup'])) + " rows)")

    # FieldAttr
    tenant_data['fieldattr'] = collect_pk_relation(session, models.FieldAttr, field_ids, 'field_id')
    print("  Serialized fieldattr (" + str(len(tenant_data['fieldattr'])) + " rows)")

    # FieldOption
    tenant_data['fieldoption'] = collect_pk_relation(session, models.FieldOption, field_ids, 'field_id')
    print("  Serialized fieldoption (" + str(len(tenant_data['fieldoption'])) + " rows)")

    # InternalFile
    tenant_data['internalfile'] = collect_pk_relation(session, models.InternalFile, internaltip_ids, 'internaltip_id')
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

    # ReceiverFiles
    internalfile_ids = build_id_list(tenant_data['internalfile'], 'id')
    tenant_data['receiverfile'] = collect_pk_relation(session, models.ReceiverFile, internalfile_ids, 'internalfile_id')
    print("  Serialized receiverfile (" + str(len(tenant_data['receiverfile'])) + " rows)")

    # IdentityAccessRequest
    receivertip_ids = build_id_list(tenant_data['receivertip'], 'id')
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

def write_tenant_to_fresh_db(tenant_data, db_path):
    '''Writes the tenant data to a fresh database'''

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
    merge_tenant_data(session, tenant_data, EXPORTED_TENANT_ID)

def write_tenant_to_preexisting_db(tenant_data, db_path):
    '''Writes the tenant data to a pre-existing DB'''
    session = get_session(make_db_uri(db_path))
    merge_tenant_data(session, tenant_data, None)

def merge_tenant_data(session, tenant_data, tid=None):
    '''Merges the tenant data into a new and/or existing database

    tid is None means an autoincremented one is take from the database
    '''

    if tid is None:
        tenant_data['tenant'].id = None
        tenant_obj = session.merge(tenant_data['tenant'])
        session.flush()
        tid = tenant_obj.id
    else:
        tenant_data['tenant'].id = tid
        session.merge(tenant_data['tenant'])

    # Correct the TID in all rows
    for datatype, rowset in tenant_data.items():
        if datatype is 'tenant':
            continue

        for row in rowset:
            if hasattr(row, 'tid'):
                row.tid = tid
            if hasattr(row, 'tenant_id'):
                row.tenant_id = tid

def write_tenant_to_preexisting_db(tenant_data, db_path):
    '''Writes the tenant data to a pre-existing DB'''
    session = get_session(make_db_uri(db_path))
    merge_tenant_data(session, tenant_data, None)

def merge_tenant_data(session, tenant_data, tid=None):
    '''Merges the tenant data into a new and/or existing database

    tid is None means an autoincremented one is take from the database
    '''

    if tid is None:
        tenant_data['tenant'].id = None
        tenant_obj = session.merge(tenant_data['tenant'])
        session.flush()
        tid = tenant_obj.id
    else:
        tenant_data['tenant'].id = tid
        session.merge(tenant_data['tenant'])

    # Correct the TID in all rows
    for datatype, rowset in tenant_data.items():
        if datatype is 'tenant':
            continue

        for row in rowset:
            if hasattr(row, 'tid'):
                row.tid = tid
            if hasattr(row, 'tenant_id'):
                row.tenant_id = tid

    # Replay the tenant data
    for element in IMPORT_ORDER:
        if element == 'fieldanswer':
            # fieldanswer needs to deNULL the above
            for fieldanswer in tenant_data['fieldanswer']:
                nulled_field = session.query(models.FieldAnswer).filter_by(id=fieldanswer.id).first()
                nulled_field.fieldanswergroup_id = fieldanswer.fieldanswergroup_id
        else:
            for row in tenant_data[element]:
                session.merge(row)

    session.commit()
    session.close()

def create_export_tarball(session, tid):
    '''Creates an export tarball, either as a file on disk, or in memory as a variable'''

    # Collect tenant data
    tenant_data = collect_all_tenant_data(session, tid)

    try:
        dirpath = tempfile.mkdtemp()

        # Create the export database
        write_tenant_to_fresh_db(tenant_data, dirpath + "/globaleaks.db")

        # Write out a export format version marker
        with open(dirpath + "/EXPORT_FORMAT", 'w') as f:
            f.write(str(1))

        output_file = io.BytesIO()

        with tarfile.open(fileobj=output_file, mode='w:gz') as export_tarball:
            export_tarball.add(dirpath + "/EXPORT_FORMAT", arcname="EXPORT_FORMAT")
            export_tarball.add(dirpath + "/globaleaks.db", arcname="globaleaks.db")

            def process_files_for_tarball(fileset):
                for receiverfile in fileset:
                    tarball_file = "attachments/"+receiverfile.filename
                    file_to_read = os.path.join(Settings.attachments_path, receiverfile.filename)
                    try:
                        export_tarball.add(file_to_read, arcname=tarball_file)
                    except FileNotFoundError:
                        # Reference files might not exist if the system successfully encrypted 
                        # them for all receivers
                        if receiverfile.status == u'reference':
                            print("Reference file " + file_to_read + " not found, skipping.")

            process_files_for_tarball(tenant_data['receiverfile'])
            process_files_for_tarball(tenant_data['whistleblowerfile'])

    finally:
        shutil.rmtree(dirpath)

    return output_file.getvalue()

def read_import_tarball(gl_session, tarball_blob):
    '''Reads a tarball in and imports it's tenant'''

    try:
        dirpath = tempfile.mkdtemp()

        # Extract the bits and start getting things going
        export_tarball = io.BytesIO(tarball_blob)
        with tarfile.open(fileobj=export_tarball, mode='r:gz') as export_tarball:
            export_tarball.extractall(path=dirpath)

        tenant_session = get_session(make_db_uri(dirpath + "/globaleaks.db"))
        tenant_data = collect_all_tenant_data(tenant_session, EXPORTED_TENANT_ID)
        merge_tenant_data(gl_session, tenant_data, tid=None)

    finally:
        shutil.rmtree(dirpath)

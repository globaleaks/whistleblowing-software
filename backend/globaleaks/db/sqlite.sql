PRAGMA foreign_keys = ON;
PRAGMA auto_vacuum = FULL;

CREATE TABLE tenant (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    label TEXT NOT NULL,
    active BOOL NOT NULL,
    subdomain TEXT NOT NULL,
    creation_date TEXT NOT NULL
);

CREATE TABLE enabledlanguage (
    tid INTEGER NOT NULL DEFAULT 1,
    name TEXT NOT NULL,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, name)
);

CREATE TABLE config (
    tid INTEGER NOT NULL DEFAULT 1,
    var_group TEXT NOT NULL,
    var_name TEXT NOT NULL,
    customized BOOL NOT NULL,
    value BLOB NOT NULL,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, var_group, var_name)
);

CREATE TABLE config_l10n (
    tid INTEGER NOT NULL DEFAULT 1,
    lang TEXT NOT NULL,
    var_group TEXT NOT NULL,
    var_name TEXT NOT NULL,
    value TEXT NOT NULL,
    customized BOOL NOT NULL,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, lang) REFERENCES enabledlanguage(tid, name) ON DELETE CASCADE,
    PRIMARY KEY (tid, lang, var_group, var_name)
);

CREATE TABLE user (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'receiver', 'custodian')),
    state TEXT NOT NULL CHECK (state IN ('disabled', 'enabled')),
    name TEXT NOT NULL,
    description BLOB NOT NULL,
    public_name TEXT NOT NULL,
    last_login TEXT NOT NULL,
    mail_address TEXT NOT NULL,
    language TEXT NOT NULL,
    password_change_needed INTEGER DEFAULT 0 NOT NULL,
    password_change_date TEXT DEFAULT '1970-01-01 00:00:00.000000' NOT NULL,
    pgp_key_fingerprint TEXT NOT NULL,
    pgp_key_public TEXT NOT NULL,
    pgp_key_expiration INTEGER NOT NULL,
    UNIQUE(id),
    UNIQUE (tid, username),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, language) REFERENCES enabledlanguage(tid, name),
    PRIMARY KEY (tid, id)
);

CREATE TABLE userimg (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    data TEXT NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, id) REFERENCES user(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE message (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    receivertip_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('receiver', 'whistleblower')),
    content TEXT NOT NULL,
    new INTEGER NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, receivertip_id) REFERENCES receivertip(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE comment (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    author_id TEXT,
    internaltip_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('receiver', 'whistleblower')),
    content TEXT NOT NULL,
    new INTEGER NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, internaltip_id) REFERENCES internaltip(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES user(id) ON DELETE SET NULL,
    PRIMARY KEY (tid, id)
);

CREATE TABLE context (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    name BLOB NOT NULL,
    description BLOB NOT NULL,
    recipients_clarification BLOB NOT NULL,
    tip_timetolive INTEGER NOT NULL,
    select_all_receivers INTEGER NOT NULL,
    maximum_selectable_receivers INTEGER,
    show_small_receiver_cards INTEGER NOT NULL,
    show_context INTEGER NOT NULL,
    show_recipients_details INTEGER NOT NULL,
    allow_recipients_selection INTEGER NOT NULL,
    enable_comments INTEGER NOT NULL,
    enable_messages INTEGER NOT NULL,
    enable_two_way_comments INTEGER NOT NULL,
    enable_two_way_messages INTEGER NOT NULL,
    enable_attachments INTEGER NOT NULL,
    enable_rc_to_wb_files INTEGER NOT NULL,
    status_page_message BLOB NOT NULL,
    presentation_order INTEGER,
    show_receivers_in_alphabetical_order INTEGER NOT NULL,
    questionnaire_id TEXT NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, questionnaire_id) REFERENCES questionnaire(tid, id),
    PRIMARY KEY (tid, id)
);

CREATE TABLE contextimg (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    data TEXT NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, id) REFERENCES context(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE internalfile (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_path TEXT,
    name TEXT NOT NULL,
    size INTEGER NOT NULL,
    new INTEGER NOT NULL,
    submission INTEGER NOT NULL,
    processing_attempts INTEGER NOT NULL,
    internaltip_id TEXT NOT NULL,
    UNIQUE(id),
    UNIQUE(file_path),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, internaltip_id) REFERENCES internaltip(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE receiverfile (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    file_path TEXT,
    size INTEGER NOT NULL,
    downloads INTEGER NOT NULL,
    last_access TEXT,
    internalfile_id TEXT NOT NULL,
    receivertip_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'reference', 'encrypted', 'unavailable', 'nokey')),
    new INTEGER  NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, internalfile_id) REFERENCES internalfile(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid, receivertip_id) REFERENCES receivertip(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE whistleblowerfile (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    content_type TEXT NOT NULL,
    receivertip_id TEXT NOT NULL,
    name TEXT NOT NULL,
    file_path TEXT,
    size INTEGER NOT NULL,
    downloads INTEGER NOT NULL,
    create_date TEXT,
    last_access TEXT,
    description TEXT,
    UNIQUE(id),
    UNIQUE(file_path),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, receivertip_id) REFERENCES receivertip(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE internaltip (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    update_date TEXT NOT NULL,
    expiration_date TEXT NOT NULL,
    questionnaire_hash TEXT NOT NULL,
    preview BLOB NOT NULL,
    progressive INTEGER NOT NULL,
    context_id TEXT NOT NULL,
    tor2web INTEGER NOT NULL,
    total_score INTEGER NOT NULL,
    enable_two_way_comments INTEGER NOT NULL,
    enable_two_way_messages INTEGER NOT NULL,
    enable_attachments INTEGER NOT NULL,
    enable_whistleblower_identity INTEGER NOT NULL,
    identity_provided INTEGER NOT NULL,
    identity_provided_date TEXT NOT NULL,
    wb_access_counter INTEGER NOT NULL,
    wb_last_access TEXT NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, context_id) REFERENCES context(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE identityaccessrequest (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    receivertip_id TEXT NOT NULL,
    request_date TEXT NOT NULL,
    request_motivation TEXT NOT NULL,
    reply_date TEXT NOT NULL,
    reply_user_id TEXT NOT NULL,
    reply_motivation TEXT NOT NULL,
    reply TEXT NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, receivertip_id) REFERENCES receivertip(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE mail (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    address TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    processing_attempts INTEGER NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE receiver (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    configuration TEXT NOT NULL CHECK (configuration IN ('default', 'forcefully_selected', 'unselectable')),
    can_delete_submission INTEGER NOT NULL,
    can_postpone_expiration INTEGER NOT NULL,
    can_grant_permissions INTEGER NOT NULL,
    tip_notification INTEGER NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, id) REFERENCES user(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE receiver_context (
    tid INTEGER NOT NULL DEFAULT 1,
    context_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    presentation_order INTEGER NOT NULL,
    UNIQUE (tid, context_id, presentation_order),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, context_id) REFERENCES context(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid, receiver_id) REFERENCES receiver(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, context_id, receiver_id)
);

CREATE TABLE receivertip (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    last_access TEXT,
    access_counter INTEGER NOT NULL,
    receiver_id TEXT NOT NULL,
    label TEXT NOT NULL,
    can_access_whistleblower_identity INTEGER NOT NULL,
    enable_notifications INTEGER NOT NULL,
    new INTEGER NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, internaltip_id) REFERENCES internaltip(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid, receiver_id) REFERENCES receiver(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE whistleblowertip (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    receipt_hash TEXT NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, id) REFERENCES internaltip(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE anomalies (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    date TEXT NOT NULL,
    alarm INTEGER NOT NULL,
    events BLOB NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE stats (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    start TEXT NOT NULL,
    summary BLOB NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE field (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    fieldgroup_id TEXT,
    step_id TEXT,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    hint TEXT DEFAULT '' NOT NULL,
    multi_entry INTEGER DEFAULT 0 NOT NULL,
    multi_entry_hint BLOB NOT NULL,
    required INTEGER DEFAULT 0 NOT NULL,
    preview INTEGER NOT NULL,
    stats_enabled INTEGER DEFAULT 0 NOT NULL,
    template_id TEXT,
    triggered_by_score INTEGER DEFAULT 0 NOT NULL,
    x INTEGER DEFAULT 0 NOT NULL,
    y INTEGER DEFAULT 0 NOT NULL,
    width INTEGER DEFAULT 0 NOT NULL CHECK (width >= 0 AND width <= 12),
    type TEXT NOT NULL CHECK (type IN ('inputbox',
                                       'textarea',
                                       'multichoice',
                                       'selectbox',
                                       'checkbox',
                                       'modal',
                                       'dialog',
                                       'tos',
                                       'fileupload',
                                       'number',
                                       'date',
                                       'email',
                                       'fieldgroup')),
    instance TEXT NOT NULL CHECK (instance IN ('instance',
                                               'reference',
                                               'template')),
    editable INT NOT NULL,
    FOREIGN KEY (tid, fieldgroup_id) REFERENCES field(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid, step_id) REFERENCES step(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid, template_id) REFERENCES field(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id),
    CONSTRAINT check_parent CHECK ((instance IS 'instance' AND template_id IS NULL AND
                                                               ((step_id IS NOT NULL AND fieldgroup_id IS NULL) OR
                                                               (step_id IS NULL AND fieldgroup_id IS NOT NULL))) OR
                                   (instance IS 'reference' AND template_id is NOT NULL AND
                                                                ((step_id IS NOT NULL AND fieldgroup_id IS NULL) OR
                                                                 (step_id IS NULL AND fieldgroup_id IS NOT NULL))) OR
                                   (instance IS 'template' AND template_id IS NULL AND
                                                               (step_id IS NULL OR fieldgroup_id IS NULL)))
);

CREATE TABLE fieldattr (
    tid INTEGER NOT NULL DEFAULT 1,

    id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (TYPE IN ('int',
                                       'bool',
                                       'unicode',
                                       'localized')),
    value TEXT NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid, field_id) REFERENCES field(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE fieldoption (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    label TEXT NOT NULL,
    presentation_order INTEGER NOT NULL,
    score_points INTEGER NOT NULL CHECK (score_points >= 0 AND score_points <= 1000),
    trigger_field TEXT,
    UNIQUE(id),
    FOREIGN KEY (tid, field_id) REFERENCES field(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid, trigger_field) REFERENCES field(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE questionnaire (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    show_steps_navigation_bar INTEGER NOT NULL,
    steps_navigation_requires_completion INTEGER NOT NULL,
    enable_whistleblower_identity INTEGER NOT NULL,
    editable INTEGER NOT NULL,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE step (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    questionnaire_id TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    presentation_order INTEGER NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (tid, questionnaire_id) REFERENCES questionnaire(tid, id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE fieldanswer (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    fieldanswergroup_id TEXT,
    key TEXT NOT NULL,
    is_leaf INTEGER NOT NULL,
    value TEXT NOT NULL,
    UNIQUE(id),
    FOREIGN KEY (tid, internaltip_id) REFERENCES internaltip(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid, fieldanswergroup_id) REFERENCES fieldanswergroup(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE fieldanswergroup (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    fieldanswer_id TEXT NOT NULL,
    number INTEGER NOT NULL,
    UNIQUE(id),
    UNIQUE (tid, id, fieldanswer_id, number),
    FOREIGN KEY (tid, fieldanswer_id) REFERENCES fieldanswer(tid, id) ON DELETE CASCADE,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE archivedschema (
    tid INTEGER NOT NULL DEFAULT 1,
    hash TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('questionnaire',
                                       'preview')),
    schema BLOB NOT NULL,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, hash, type)
);

CREATE TABLE securefiledelete (
    id TEXT NOT NULL,
    filepath TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE counter (
    tid INTEGER NOT NULL DEFAULT 1,
    key TEXT NOT NULL,
    counter INTEGER NOT NULL,
    update_date TEXT NOT NULL,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, key)
);

CREATE TABLE shorturl (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    shorturl TEXT NOT NULL,
    longurl TEXT NOT NULL,
    UNIQUE (shorturl),
    UNIQUE(id),
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE file (
    tid INTEGER NOT NULL DEFAULT 1,
    id TEXT NOT NULL,
    data TEXT NOT NULL,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, id)
);

CREATE TABLE customtexts (
    tid INTEGER NOT NULL DEFAULT 1,
    lang TEXT NOT NULL,
    texts BLOB NOT NULL,
    FOREIGN KEY (tid) REFERENCES tenant(id) ON DELETE CASCADE,
    PRIMARY KEY (tid, lang)
);

PRAGMA foreign_keys = ON;
PRAGMA auto_vacuum = FULL;

CREATE TABLE tenant (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    label TEXT NOT NULL,
    active BOOL NOT NULL,
    creation_date TEXT NOT NULL
);

CREATE TABLE enabledlanguage (
    name TEXT NOT NULL,
    PRIMARY KEY (name)
);

CREATE TABLE config (
    var_group TEXT NOT NULL,
    var_name TEXT NOT NULL,
    customized BOOL NOT NULL,
    value BLOB NOT NULL,
    PRIMARY KEY (var_group, var_name)
);

CREATE TABLE config_l10n (
    lang TEXT NOT NULL,
    var_group TEXT NOT NULL,
    var_name TEXT NOT NULL,
    value TEXT NOT NULL,
    customized BOOL NOT NULL,
    FOREIGN KEY (lang) REFERENCES enabledlanguage(name) ON DELETE CASCADE,
    PRIMARY KEY (lang, var_group, var_name)
);

CREATE TABLE user (
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    salt TEXT NOT NULL,
    deletable INTEGER NOT NULL,
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
    img_id TEXT,
    UNIQUE (username),
    FOREIGN KEY (language) REFERENCES enabledlanguage(name),
    FOREIGN KEY (img_id) REFERENCES file(id) ON DELETE SET NULL,
    PRIMARY KEY (id)
);

CREATE TABLE message (
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    receivertip_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('receiver', 'whistleblower')),
    content TEXT NOT NULL,
    new INTEGER NOT NULL,
    FOREIGN KEY (receivertip_id) REFERENCES receivertip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE comment (
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    author_id TEXT,
    internaltip_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('receiver', 'whistleblower')),
    content TEXT NOT NULL,
    new INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user(id) ON DELETE SET NULL,
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE context (
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
    img_id TEXT,
    FOREIGN KEY (questionnaire_id) REFERENCES questionnaire(id),
    FOREIGN KEY (img_id) REFERENCES file(id) ON DELETE SET NULL,
    PRIMARY KEY (id)
);

CREATE TABLE internalfile (
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
    UNIQUE(file_path),
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE receiverfile (
    id TEXT NOT NULL,
    file_path TEXT,
    size INTEGER NOT NULL,
    downloads INTEGER NOT NULL,
    last_access TEXT,
    internalfile_id TEXT NOT NULL,
    receivertip_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'reference', 'encrypted', 'unavailable', 'nokey')),
    new INTEGER  NOT NULL,
    FOREIGN KEY (internalfile_id) REFERENCES internalfile(id) ON DELETE CASCADE,
    FOREIGN KEY (receivertip_id) REFERENCES receivertip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE whistleblowerfile (
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
    UNIQUE(file_path),
    FOREIGN KEY (receivertip_id) REFERENCES receivertip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE internaltip (
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
    FOREIGN KEY (context_id) REFERENCES context(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE identityaccessrequest (
    id TEXT NOT NULL,
    receivertip_id TEXT NOT NULL,
    request_date TEXT NOT NULL,
    request_motivation TEXT NOT NULL,
    reply_date TEXT NOT NULL,
    reply_user_id TEXT,
    reply_motivation TEXT NOT NULL,
    reply TEXT NOT NULL,
    FOREIGN KEY (receivertip_id) REFERENCES receivertip(id) ON DELETE CASCADE,
    FOREIGN KEY (reply_user_id) REFERENCES user(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE mail (
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    address TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    processing_attempts INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE receiver (
    id TEXT NOT NULL,
    configuration TEXT NOT NULL CHECK (configuration IN ('default', 'forcefully_selected', 'unselectable')),
    can_delete_submission INTEGER NOT NULL,
    can_postpone_expiration INTEGER NOT NULL,
    can_grant_permissions INTEGER NOT NULL,
    tip_notification INTEGER NOT NULL,
    presentation_order INTEGER,
    FOREIGN KEY (id) REFERENCES user(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE receiver_context (
    context_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    FOREIGN KEY (context_id) REFERENCES context(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    PRIMARY KEY (context_id, receiver_id)
);

CREATE TABLE receivertip (
    id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    last_access TEXT,
    access_counter INTEGER NOT NULL,
    receiver_id TEXT NOT NULL,
    label TEXT NOT NULL,
    can_access_whistleblower_identity INTEGER NOT NULL,
    enable_notifications INTEGER NOT NULL,
    new INTEGER NOT NULL,
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE whistleblowertip (
    id TEXT NOT NULL,
    receipt_hash TEXT NOT NULL,
    FOREIGN KEY (id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE anomalies (
    id TEXT NOT NULL,
    date TEXT NOT NULL,
    alarm INTEGER NOT NULL,
    events BLOB NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE stats (
    id TEXT NOT NULL,
    start TEXT NOT NULL,
    free_disk_space INTEGER NOT NULL,
    summary BLOB NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE field (
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
    FOREIGN KEY (fieldgroup_id) REFERENCES field(id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES step(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES field(id) ON DELETE CASCADE,
    PRIMARY KEY (id),
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
    id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (TYPE IN ('int',
                                       'bool',
                                       'unicode',
                                       'localized')),
    value TEXT NOT NULL,
    FOREIGN KEY (field_id) REFERENCES field(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE fieldoption (
    id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    label TEXT NOT NULL,
    presentation_order INTEGER NOT NULL,
    score_points INTEGER NOT NULL CHECK (score_points >= 0 AND score_points <= 1000),
    trigger_field TEXT,
    trigger_step TEXT,
    FOREIGN KEY (field_id) REFERENCES field(id) ON DELETE CASCADE,
    FOREIGN KEY (trigger_field) REFERENCES field(id) ON DELETE CASCADE,
    FOREIGN KEY (trigger_step) REFERENCES step(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE questionnaire (
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    show_steps_navigation_bar INTEGER NOT NULL,
    steps_navigation_requires_completion INTEGER NOT NULL,
    enable_whistleblower_identity INTEGER NOT NULL,
    editable INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE step (
    id TEXT NOT NULL,
    questionnaire_id TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    presentation_order INTEGER NOT NULL,
    triggered_by_score INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (questionnaire_id) REFERENCES questionnaire(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE fieldanswer (
    id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    fieldanswergroup_id TEXT,
    key TEXT NOT NULL,
    is_leaf INTEGER NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    FOREIGN KEY (fieldanswergroup_id) REFERENCES fieldanswergroup(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE fieldanswergroup (
    id TEXT NOT NULL,
    fieldanswer_id TEXT NOT NULL,
    number INTEGER NOT NULL,
    UNIQUE (id, fieldanswer_id, number),
    FOREIGN KEY (fieldanswer_id) REFERENCES fieldanswer(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE archivedschema (
    hash TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('questionnaire',
                                       'preview')),
    schema BLOB NOT NULL,
    UNIQUE (hash, type),
    PRIMARY KEY (hash, type)
);

CREATE TABLE securefiledelete (
    id TEXT NOT NULL,
    filepath TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE counter (
    key TEXT NOT NULL,
    counter INTEGER NOT NULL,
    update_date TEXT NOT NULL,
    PRIMARY KEY (key)
);

CREATE TABLE shorturl (
    id TEXT NOT NULL,
    shorturl TEXT NOT NULL,
    longurl TEXT NOT NULL,
    UNIQUE (shorturl),
    PRIMARY KEY (id)
);

CREATE TABLE file (
    id TEXT NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE customtexts (
    lang TEXT NOT NULL,
    texts BLOB NOT NULL,
    PRIMARY KEY (lang)
);

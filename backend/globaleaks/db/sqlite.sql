PRAGMA foreign_keys = ON;

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
    last_login TEXT NOT NULL,
    mail_address TEXT NOT NULL,
    language TEXT NOT NULL,
    timezone INTEGER DEFAULT 0,
    password_change_needed INTEGER NOT NULL DEFAULT 0,
    password_change_date TEXT NOT NULL DEFAULT '1970-01-01 00:00:00.000000',
    pgp_key_status TEXT NOT NULL CHECK (pgp_key_status IN ('disabled', 'enabled')) DEFAULT 'disabled',
    pgp_key_info TEXT,
    pgp_key_fingerprint TEXT,
    pgp_key_public TEXT,
    pgp_key_expiration INTEGER,
    UNIQUE (username),
    PRIMARY KEY (id)
);

CREATE TABLE message (
    id TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    author TEXT NOT NULL,
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
    author TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('receiver', 'whistleblower')),
    content TEXT NOT NULL,
    new INTEGER NOT NULL,
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
    show_small_cards INTEGER NOT NULL,
    show_context INTEGER NOT NULL,
    show_recipients_details INTEGER NOT NULL,
    allow_recipients_selection INTEGER NOT NULL,
    enable_comments INTEGER NOT NULL,
    enable_messages INTEGER NOT NULL,
    enable_two_way_comments INTEGER NOT NULL,
    enable_two_way_messages INTEGER NOT NULL,
    enable_attachments INTEGER NOT NULL,
    enable_whistleblower_identity INTEGER NOT NULL,
    presentation_order INTEGER,
    show_receivers_in_alphabetical_order INTEGER NOT NULL,
    questionnaire_layout TEXT NOT NULL CHECK (questionnaire_layout IN ('vertical', 'horizontal')) DEFAULT 'horizontal',
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
    receiver_id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    receivertip_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'reference', 'encrypted', 'unavailable', 'nokey')),
    new INTEGER  NOT NULL,
    FOREIGN KEY (internalfile_id) REFERENCES internalfile(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
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
    new INTEGER NOT NULL,
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

CREATE TABLE node (
    id TEXT NOT NULL,
    version TEXT NOT NULL,
    version_db TEXT NOT NULL,
    description BLOB NOT NULL,
    presentation BLOB NOT NULL,
    footer BLOB NOT NULL,
    security_awareness_title BLOB NOT NULL,
    security_awareness_text BLOB NOT NULL,
    context_selector_label BLOB NOT NULL,
    whistleblowing_question BLOB NOT NULL,
    whistleblowing_button BLOB NOT NULL,
    hidden_service TEXT NOT NULL,
    languages_enabled BLOB NOT NULL,
    default_language TEXT NOT NULL,
    default_timezone INTEGER,
    name TEXT NOT NULL,
    receipt_salt TEXT NOT NULL,
    public_site TEXT NOT NULL,
    maximum_namesize INTEGER NOT NULL,
    maximum_textsize INTEGER NOT NULL,
    maximum_filesize INTEGER NOT NULL,
    tor2web_admin INTEGER NOT NULL,
    tor2web_custodian INTEGER NOT NULL,
    tor2web_whistleblower INTEGER NOT NULL,
    tor2web_receiver INTEGER NOT NULL,
    tor2web_unauth INTEGER NOT NULL,
    submission_minimum_delay INTEGER NOT NULL,
    submission_maximum_ttl INTEGER NOT NULL,
    can_postpone_expiration INTEGER NOT NULL,
    can_delete_submission INTEGER NOT NULL,
    can_grant_permissions INTEGER NOT NULL,
    ahmia INTEGER NOT NULL,
    wizard_done INTEGER NOT NULL,
    allow_unencrypted INTEGER NOT NULL,
    allow_iframes_inclusion INTEGER NOT NULL,
    disable_privacy_badge INTEGER NOT NULL,
    disable_security_awareness_badge INTEGER NOT NULL,
    disable_security_awareness_questions INTEGER NOT NULL,
    disable_key_code_hint INTEGER NOT NULL,
    disable_donation_panel INTEGER NOT NULL,
    enable_captcha INTEGER NOT NULL,
    enable_proof_of_work INTEGER NOT NULL,
    enable_experimental_features INTEGER NOT NULL,
    simplified_login INTEGER NOT NULL,
    enable_custom_privacy_badge INTEGER NOT NULL,
    custom_privacy_badge_tor BLOB NOT NULL,
    custom_privacy_badge_none BLOB NOT NULL,
    header_title_homepage BLOB NOT NULL,
    header_title_submissionpage BLOB NOT NULL,
    header_title_receiptpage BLOB NOT NULL,
    header_title_tippage BLOB NOT NULL,
    widget_comments_title BLOB NOT NULL,
    widget_messages_title BLOB NOT NULL,
    widget_files_title BLOB NOT NULL,
    landing_page TEXT NOT NULL CHECK (landing_page IN ('homepage', 'submissionpage')),
    show_contexts_in_alphabetical_order INTEGER NOT NULL,
    threshold_free_disk_megabytes_high INTEGER NOT NULL,
    threshold_free_disk_megabytes_medium INTEGER NOT NULL,
    threshold_free_disk_megabytes_low INTEGER NOT NULL,
    threshold_free_disk_percentage_high INTEGER NOT NULL,
    threshold_free_disk_percentage_medium INTEGER NOT NULL,
    threshold_free_disk_percentage_low INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE notification (
    id TEXT NOT NULL,
    server TEXT,
    port INTEGER,
    password TEXT,
    username TEXT,
    source_name TEXT NOT NULL,
    source_email TEXT NOT NULL,
    security TEXT NOT NULL CHECK (security IN ('TLS', 'SSL')),
    torify INTEGER,
    tip_mail_template BLOB,
    tip_mail_title BLOB,
    file_mail_template BLOB,
    file_mail_title BLOB,
    message_mail_template BLOB,
    message_mail_title BLOB,
    comment_mail_template BLOB,
    comment_mail_title BLOB,
    tip_expiration_mail_template BLOB,
    tip_expiration_mail_title BLOB,
    admin_anomaly_mail_template BLOB,
    admin_anomaly_mail_title BLOB,
    admin_anomaly_disk_low BLOB,
    admin_anomaly_disk_medium BLOB,
    admin_anomaly_disk_high BLOB,
    admin_anomaly_activities BLOB,
    admin_pgp_alert_mail_template BLOB,
    admin_pgp_alert_mail_title BLOB,
    pgp_alert_mail_template BLOB,
    pgp_alert_mail_title BLOB,
    notification_digest_mail_title BLOB,
    identity_access_authorized_mail_template BLOB,
    identity_access_authorized_mail_title BLOB,
    identity_access_denied_mail_template BLOB,
    identity_access_denied_mail_title BLOB,
    identity_access_request_mail_template BLOB,
    identity_access_request_mail_title BLOB,
    identity_provided_mail_template BLOB,
    identity_provided_mail_title BLOB,
    export_template BLOB,
    export_message_whistleblower BLOB,
    export_message_recipient BLOB,
    receiver_notification_limit_reached_mail_template BLOB,
    receiver_notification_limit_reached_mail_title BLOB,
    tip_expiration_threshold INTEGER NOT NULL,
    notification_threshold_per_hour INTEGER NOT NULL,
    notification_suspension_time INTEGER NOT NULL,
    disable_admin_notification_emails INTEGER NOT NULL,
    disable_custodian_notification_emails INTEGER NOT NULL,
    disable_receiver_notification_emails INTEGER NOT NULL,
    send_email_for_every_event INTEGER NOT NULL,
    exception_email_address TEXT NOT NULL,
    exception_email_pgp_key_status TEXT NOT NULL CHECK (exception_email_pgp_key_status IN ('disabled', 'enabled')) DEFAULT 'disabled',
    exception_email_pgp_key_info TEXT,
    exception_email_pgp_key_fingerprint TEXT,
    exception_email_pgp_key_public TEXT,
    exception_email_pgp_key_expiration INTEGER,
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

CREATE TABLE custodian (
    id TEXT NOT NULL,
    FOREIGN KEY (id) REFERENCES user(id) ON DELETE CASCADE,
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

CREATE TABLE receiver_internaltip (
    receiver_id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    FOREIGN KEY (receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (receiver_id, internaltip_id)
);

CREATE TABLE receivertip (
    id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    last_access TEXT,
    access_counter INTEGER NOT NULL,
    receiver_id TEXT NOT NULL,
    label TEXT NOT NULL,
    can_access_whistleblower_identity INTEGER NOT NULL,
    new INTEGER NOT NULL,
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE whistleblowertip (
    id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    last_access TEXT,
    access_counter INTEGER NOT NULL,
    receipt_hash TEXT NOT NULL,
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE applicationdata (
    id TEXT NOT NULL,
    version INTEGER NOT NULL,
    default_questionnaire BLOB NOT NULL,
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
    key TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    hint TEXT NOT NULL DEFAULT '',
    multi_entry INTEGER NOT NULL DEFAULT 0,
    multi_entry_hint BLOB NOT NULL,
    required INTEGER NOT NULL DEFAULT 0,
    preview INTEGER NOT NULL,
    stats_enabled INTEGER NOT NULL DEFAULT 0,
    template_id TEXT,
    activated_by_score INTEGER NOT NULL DEFAULT 0,
    x INTEGER NOT NULL DEFAULT 0,
    y INTEGER NOT NULL DEFAULT 0,
    width INTEGER NOT NULL DEFAULT 0 CHECK (width >= 0 AND width <= 12),
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
    FOREIGN KEY (template_id) REFERENCES field(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
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
    score_points INTEGER NOT NULL,
    FOREIGN KEY (field_id) REFERENCES field(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE optionactivatefield (
    option_id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    FOREIGN KEY (option_id) REFERENCES fieldoption(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES field(id) ON DELETE CASCADE,
    PRIMARY KEY (option_id, field_id)
);

CREATE TABLE optionactivatestep (
    option_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    FOREIGN KEY (option_id) REFERENCES fieldoption(id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES step(id) ON DELETE CASCADE,
    PRIMARY KEY (option_id, step_id)
);

CREATE TABLE step (
    id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    presentation_order INTEGER NOT NULL,
    FOREIGN KEY (context_id) REFERENCES context(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE field_field (
    parent_id TEXT NOT NULL,
    child_id TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES field(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES field(id) ON DELETE CASCADE,
    PRIMARY KEY (parent_id, child_id)
);

CREATE TABLE step_field (
    step_id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    UNIQUE (field_id),
    FOREIGN KEY (step_id) REFERENCES step(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES field(id) ON DELETE CASCADE,
    PRIMARY KEY (step_id, field_id)
);

CREATE TABLE fieldanswer (
    id TEXT NOT NULL,
    internaltip_id TEXT NOT NULL,
    key TEXT NOT NULL,
    is_leaf INTEGER NOT NULL,
    value TEXT NOT NULL,
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

CREATE TABLE fieldanswergroup_fieldanswer (
    fieldanswergroup_id TEXT NOT NULL,
    fieldanswer_id TEXT NOT NULL,
    FOREIGN KEY (fieldanswergroup_id) REFERENCES fieldanswergroup(id) ON DELETE CASCADE,
    FOREIGN KEY (fieldanswer_id) REFERENCES fieldanswer(id) ON DELETE CASCADE,
    PRIMARY KEY (fieldanswergroup_id, fieldanswer_id)
);

CREATE TABLE archivedschema (
    id TEXT NOT NULL,
    hash TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('questionnaire',
                                       'preview')),
    schema BLOB NOT NULL,
    UNIQUE (hash, type),
    PRIMARY KEY (id)
);

CREATE TABLE securefiledelete (
    id TEXT NOT NULL,
    filepath TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE counter (
    id TEXT NOT NULL,
    key TEXT NOT NULL,
    counter INTEGER NOT NULL,
    update_date TEXT NOT NULL,
    UNIQUE (key),
    PRIMARY KEY (id)
);

CREATE TABLE shorturl (
    id TEXT NOT NULL,
    shorturl TEXT NOT NULL,
    longurl TEXT NOT NULL,
    UNIQUE (shorturl),
    PRIMARY KEY (id)
);

CREATE INDEX field__template_id_index ON field(template_id);
CREATE INDEX fieldattr__field_id_index ON fieldattr(field_id);
CREATE INDEX fieldoption__field_id_index ON fieldoption(field_id);
CREATE INDEX optionactivatefield__field_id_index ON optionactivatefield(field_id);
CREATE INDEX optionactivatestep__step_id_index ON optionactivatestep(step_id);
CREATE INDEX step__context_id_index ON step(context_id);
CREATE INDEX fieldanswer__internaltip_id_index ON fieldanswer(internaltip_id);

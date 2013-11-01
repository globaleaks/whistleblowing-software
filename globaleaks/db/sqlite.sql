PRAGMA foreign_keys = ON;

CREATE TABLE user (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    salt VARCHAR NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('admin', 'receiver')),
    state VARCHAR NOT NULL CHECK (state IN ('disabled', 'to_be_activated', 'enabled')),
    last_login VARCHAR NOT NULL,
    last_update VARCHAR,
    failed_login_count INTEGER NOT NULL, 
    PRIMARY KEY (id),
    UNIQUE (username)
);

CREATE TABLE comment (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    type VARCHAR NOT NULL CHECK (type IN ('receiver', 'whistleblower', 'system')),
    mark VARCHAR NOT NULL CHECK (mark IN ('not notified', 'notified', 'unable to notify', 'disabled', 'skipped')),
    content VARCHAR NOT NULL,
    system_content BLOB,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE context (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    description BLOB NOT NULL,
    escalation_threshold INTEGER,
    unique_fields BLOB NOT NULL,
    localized_fields BLOB NOT NULL,
    file_max_download INTEGER NOT NULL,
    file_required INTEGER NOT NULL,
    last_update VARCHAR,
    name BLOB NOT NULL,
    selectable_receiver INTEGER NOT NULL,
    tip_max_access INTEGER NOT NULL,
    tip_timetolive INTEGER NOT NULL,
    submission_timetolive INTEGER NOT NULL,
    receipt_regexp VARCHAR NOT NULL,
    receipt_description BLOB NOT NULL,
    submission_introduction BLOB NOT NULL,
    submission_disclaimer BLOB NOT NULL,
    tags BLOB,
    select_all_receivers INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE internalfile (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    content_type VARCHAR NOT NULL,
    file_path VARCHAR,
    mark VARCHAR NOT NULL CHECK (mark IN ('not processed', 'locked', 'ready', 'delivered')),
    name VARCHAR NOT NULL,
    sha2sum VARCHAR,
    size INTEGER NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE receiverfile (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    file_path VARCHAR,
    size INTEGER NOT NULL,
    downloads INTEGER NOT NULL,
    last_access VARCHAR,
    internalfile_id VARCHAR NOT NULL,
    receiver_id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    receiver_tip_id VARCHAR NOT NULL,
    mark VARCHAR NOT NULL CHECK (mark IN ('not notified', 'notified', 'unable to notify', 'disabled', 'skipped')),
    status VARCHAR NOT NULL CHECK (status IN ('cloned', 'reference', 'encrypted', 'unavailable')),
    FOREIGN KEY(internalfile_id) REFERENCES internalfile(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE internaltip (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    access_limit INTEGER NOT NULL,
    download_limit INTEGER NOT NULL,
    escalation_threshold INTEGER,
    expiration_date VARCHAR NOT NULL,
    wb_fields BLOB,
    last_activity VARCHAR,
    mark VARCHAR NOT NULL CHECK (mark IN ('submission', 'finalize', 'first', 'second')),
    pertinence_counter INTEGER NOT NULL,
    context_id VARCHAR NOT NULL,
    FOREIGN KEY(context_id) REFERENCES context(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE node (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    description BLOB NOT NULL,
    presentation BLOB NOT NULL,
    footer BLOB NOT NULL,
    email VARCHAR NOT NULL,
    hidden_service VARCHAR NOT NULL,
    languages_enabled BLOB NOT NULL,
    languages_supported BLOB NOT NULL,
    default_language VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    receipt_salt VARCHAR NOT NULL,
    public_site VARCHAR NOT NULL,
    stats_update_time INTEGER NOT NULL,
    last_update VARCHAR,
    maximum_namesize INTEGER NOT NULL,
    maximum_textsize INTEGER NOT NULL,
    maximum_filesize INTEGER NOT NULL,
    tor2web_admin INTEGER NOT NULL,
    tor2web_submission INTEGER NOT NULL,
    tor2web_tip INTEGER NOT NULL,
    tor2web_receiver INTEGER NOT NULL,
    tor2web_unauth INTEGER NOT NULL,
    postpone_superpower INTEGER,
    exception_email VARCHAR NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE notification (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    server VARCHAR,
    port INTEGER,
    password VARCHAR,
    username VARCHAR,
    source_name VARCHAR NOT NULL,
    source_email VARCHAR NOT NULL,
    security VARCHAR NOT NULL CHECK (security IN ('TLS', 'SSL')),
    tip_template BLOB,
    tip_mail_title BLOB,
    file_template BLOB,
    file_mail_title BLOB,
    comment_template BLOB,
    comment_mail_title BLOB,
    activation_template BLOB,
    activation_mail_title BLOB,
    PRIMARY KEY (id)
);

CREATE TABLE receiver (
    id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    can_delete_submission INTEGER NOT NULL,
    description BLOB NOT NULL,
    last_update VARCHAR,
    name VARCHAR NOT NULL,
    tags BLOB,
    comment_notification INTEGER NOT NULL,
    file_notification INTEGER NOT NULL,
    tip_notification INTEGER NOT NULL,
    notification_fields BLOB NOT NULL,
    gpg_key_status VARCHAR NOT NULL CHECK (gpg_key_status IN ('Disabled', 'Enabled')),
    gpg_key_info VARCHAR,
    gpg_key_fingerprint VARCHAR,
    gpg_key_armor VARCHAR,
    gpg_enable_notification INTEGER,
    gpg_enable_files INTEGER,
    receiver_level INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE

);

CREATE TABLE receiver_context (
    context_id VARCHAR NOT NULL,
    receiver_id VARCHAR NOT NULL,
    PRIMARY KEY (context_id, receiver_id),
    FOREIGN KEY (context_id) REFERENCES context(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES receiver(id) ON DELETE CASCADE
);

CREATE TABLE receiver_internaltip (
    receiver_id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    PRIMARY KEY (receiver_id, internaltip_id),
    FOREIGN KEY (receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    FOREIGN KEY (internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE
);

CREATE TABLE receivertip (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    access_counter INTEGER NOT NULL,
    expressed_pertinence INTEGER NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    last_access VARCHAR,
    notification_date VARCHAR,
    mark VARCHAR NOT NULL CHECK (mark IN ('not notified', 'notified', 'unable to notify', 'disabled', 'skipped')),
    receiver_id VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES receiver(id) ON DELETE CASCADE
);

CREATE TABLE whistleblowertip (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    access_counter INTEGER NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    last_access VARCHAR,
    receipt_hash VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE
);

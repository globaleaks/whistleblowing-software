PRAGMA foreign_keys = ON;

CREATE TABLE user (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    salt VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    state VARCHAR NOT NULL,
    last_login VARCHAR NOT NULL,
    last_update VARCHAR,
    PRIMARY KEY (id),
    UNIQUE (username),
    CHECK (role IN ('admin', 'receiver')),
    CHECK (state IN ('disabled', 'to_be_activated', 'enabled'))
);

CREATE TABLE message (
    id VARCHAR NOT NULL,
    visualized INT NOT NULL,
    creation_date VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    receivertip_id VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    mark VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    FOREIGN KEY(receivertip_id) REFERENCES receivertip(id) ON DELETE CASCADE,
    PRIMARY KEY (id),
    CHECK (type IN ('receiver', 'whistleblower' )),
    CHECK (mark IN ('not notified', 'notified', 'unable to notify', 'disabled', 'skipped'))
);

CREATE TABLE comment (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    mark VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    system_content BLOB,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id),
    CHECK (type IN ('receiver', 'whistleblower', 'system')),
    CHECK (mark IN ('not notified', 'notified', 'unable to notify', 'disabled', 'skipped'))
);

CREATE TABLE context (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    description BLOB NOT NULL,
    escalation_threshold INT,
    unique_fields BLOB NOT NULL,
    localized_fields BLOB NOT NULL,
    file_max_download INT NOT NULL,
    file_required INT NOT NULL,
    last_update VARCHAR,
    name BLOB NOT NULL,
    selectable_receiver INT NOT NULL,
    tip_max_access INT NOT NULL,
    tip_timetolive INT NOT NULL,
    submission_timetolive INT NOT NULL,
    receipt_regexp VARCHAR NOT NULL,
    receiver_introduction BLOB NOT NULL,
    fields_introduction BLOB NOT NULL,
    tags BLOB,
    select_all_receivers INT NOT NULL,
    postpone_superpower INT NOT NULL,
    can_delete_submission INT NOT NULL,
    maximum_selectable_receivers INT,
    require_file_description INT NOT NULL,
    delete_consensus_percentage INT,
    require_pgp INT NOT NULL,
    show_small_cards INT NOT NULL,
    presentation_order INT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE internalfile (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    content_type VARCHAR NOT NULL,
    file_path VARCHAR,
    mark VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    sha2sum VARCHAR,
    size INT NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id),
    CHECK (mark IN ('not processed', 'locked', 'ready', 'delivered'))
);

CREATE TABLE receiverfile (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    file_path VARCHAR,
    size INT NOT NULL,
    downloads INT NOT NULL,
    last_access VARCHAR,
    internalfile_id VARCHAR NOT NULL,
    receiver_id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    receiver_tip_id VARCHAR NOT NULL,
    mark VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    FOREIGN KEY(internalfile_id) REFERENCES internalfile(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id),
    CHECK (mark IN ('not notified', 'notified', 'unable to notify', 'disabled', 'skipped')),
    CHECK (status IN ('cloned', 'reference', 'encrypted', 'unavailable'))
);

CREATE TABLE internaltip (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    access_limit INT NOT NULL,
    download_limit INT NOT NULL,
    escalation_threshold INT,
    expiration_date VARCHAR NOT NULL,
    wb_fields BLOB,
    last_activity VARCHAR,
    mark VARCHAR NOT NULL,
    pertinence_counter INT NOT NULL,
    context_id VARCHAR NOT NULL,
    FOREIGN KEY(context_id) REFERENCES context(id) ON DELETE CASCADE,
    PRIMARY KEY (id),
    CHECK (mark IN ('submission', 'finalize', 'first', 'second'))
);

CREATE TABLE node (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    description BLOB NOT NULL,
    presentation BLOB NOT NULL,
    subtitle BLOB NOT NULL,
    footer BLOB NOT NULL,
    email VARCHAR NOT NULL,
    hidden_service VARCHAR NOT NULL,
    languages_enabled BLOB NOT NULL,
    default_language VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    receipt_salt VARCHAR NOT NULL,
    public_site VARCHAR NOT NULL,
    stats_update_time INT NOT NULL,
    last_update VARCHAR,
    maximum_namesize INT NOT NULL,
    maximum_textsize INT NOT NULL,
    maximum_filesize INT NOT NULL,
    tor2web_admin INT NOT NULL,
    tor2web_submission INT NOT NULL,
    tor2web_receiver INT NOT NULL,
    tor2web_unauth INT NOT NULL,
    postpone_superpower INT NOT NULL,
    can_delete_submission INT NOT NULL,
    ahmia INT NOT NULL,
    wizard_done INT NOT NULL,
    anomaly_checks INT NOT NULL,
    exception_email VARCHAR NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE notification (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    server VARCHAR,
    port INT,
    password VARCHAR,
    username VARCHAR,
    source_name VARCHAR NOT NULL,
    source_email VARCHAR NOT NULL,
    security VARCHAR NOT NULL,
    encrypted_tip_template BLOB,
    encrypted_tip_mail_title BLOB,
    plaintext_tip_template BLOB,
    plaintext_tip_mail_title BLOB,
    encrypted_file_template BLOB,
    encrypted_file_mail_title BLOB,
    plaintext_file_template BLOB,
    plaintext_file_mail_title BLOB,
    encrypted_message_template BLOB,
    encrypted_message_mail_title BLOB,
    plaintext_message_template BLOB,
    plaintext_message_mail_title BLOB,
    encrypted_comment_template BLOB,
    encrypted_comment_mail_title BLOB,
    plaintext_comment_template BLOB,
    plaintext_comment_mail_title BLOB,
    zip_description BLOB,
    PRIMARY KEY (id),
    CHECK (security IN ('TLS', 'SSL'))
);

CREATE TABLE receiver (
    id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    can_delete_submission INT NOT NULL,
    postpone_superpower INT NOT NULL,
    description BLOB NOT NULL,
    last_update VARCHAR,
    name VARCHAR NOT NULL,
    tags BLOB,
    comment_notification INT NOT NULL,
    file_notification INT NOT NULL,
    tip_notification INT NOT NULL,
    message_notification INT NOT NULL,
    mail_address VARCHAR NOT NULL,
    gpg_key_status VARCHAR NOT NULL,
    gpg_key_info VARCHAR,
    gpg_key_fingerprint VARCHAR,
    gpg_key_armor VARCHAR,
    gpg_enable_notification INT,
    receiver_level INT NOT NULL,
    presentation_order INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE,
    CHECK (gpg_key_status IN ('Disabled', 'Enabled'))
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
    access_counter INT NOT NULL,
    expressed_pertinence INT NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    last_access VARCHAR,
    notification_date VARCHAR,
    mark VARCHAR NOT NULL,
    receiver_id VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    CHECK (mark IN ('not notified', 'notified', 'unable to notify', 'disabled', 'skipped'))
);

CREATE TABLE whistleblowertip (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    access_counter INT NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    last_access VARCHAR,
    receipt_hash VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE
);

CREATE TABLE applicationdata (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    fields_version INT NOT NULL,
    fields BLOB,
    PRIMARY KEY (id)
);

CREATE TABLE stats (
    id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    content BLOB,
    PRIMARY KEY (id)
);

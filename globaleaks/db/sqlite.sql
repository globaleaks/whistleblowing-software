PRAGMA foreign_keys = ON;

CREATE TABLE comment (
    author VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    message VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE
);

CREATE TABLE context (
    creation_date VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    escalation_threshold INTEGER,
    fields BLOB NOT NULL,
    file_max_download INTEGER NOT NULL,
    id VARCHAR NOT NULL,
    last_update VARCHAR,
    name VARCHAR NOT NULL,
    selectable_receiver INTEGER NOT NULL,
    tip_max_access INTEGER NOT NULL,
    tip_timetolive INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE internalfile (
    content_type VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    mark VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    sha2sum VARCHAR NOT NULL,
    size INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE
);

CREATE TABLE internaltip (
    access_limit INTEGER NOT NULL,
    context_id VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    download_limit INTEGER NOT NULL,
    escalation_threshold INTEGER,
    expiration_date VARCHAR NOT NULL,
    fields BLOB NOT NULL,
    files BLOB NOT NULL,
    id VARCHAR NOT NULL,
    last_activity VARCHAR,
    mark VARCHAR NOT NULL,
    pertinence_counter INTEGER NOT NULL,
    receivers BLOB NOT NULL,
--    whistleblower_tip_id VARCHAR,
--    FOREIGN KEY(whistleblower_tip_id) REFERENCES whistleblower(id),
    PRIMARY KEY (id)
);

CREATE TABLE node (
    creation_date VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    hidden_service VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    languages BLOB NOT NULL,
    name VARCHAR NOT NULL,
    notification_settings BLOB NOT NULL,
    password VARCHAR NOT NULL,
    public_site VARCHAR NOT NULL,
    stats_update_time INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE receiver (
    can_configure_delivery INTEGER NOT NULL,
    can_configure_notification INTEGER NOT NULL,
    can_delete_submission INTEGER NOT NULL,
    can_postpone_expiration INTEGER NOT NULL,
    creation_date VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    last_access VARCHAR,
    last_update VARCHAR,
    name VARCHAR NOT NULL,
    notification_fields BLOB NOT NULL,
    password VARCHAR,
    receiver_level INTEGER NOT NULL,
    username VARCHAR NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE receiver_context (
    context_id VARCHAR NOT NULL,
    receiver_id VARCHAR NOT NULL,
    PRIMARY KEY (context_id, receiver_id),
    FOREIGN KEY(context_id) REFERENCES context(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES receiver(id) ON DELETE CASCADE
);

CREATE TABLE receivertip (
    access_counter INTEGER NOT NULL,
    creation_date VARCHAR NOT NULL,
    expressed_pertinence INTEGER NOT NULL,
    id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    last_access VARCHAR,
    notification_date VARCHAR NOT NULL,
    notification_mark VARCHAR NOT NULL,
    receiver_id VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES receiver(id) ON DELETE CASCADE
);

CREATE TABLE whistleblowertip (
    access_counter INTEGER NOT NULL,
    creation_date VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    last_access VARCHAR,
    receipt VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE
);


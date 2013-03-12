PRAGMA foreign_keys = ON;

CREATE TABLE comment (
    author VARCHAR NOT NULL,
    creation_date VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    type VARCHAR NOT NULL CHECK (type IN ('receiver', 'whistleblower', 'system')),
    mark VARCHAR NOT NULL CHECK (mark IN ('not notified', 'notified', 'unable to notify')),
    content VARCHAR NOT NULL,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
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
    creation_date VARCHAR,
    file_path VARCHAR,
    mark VARCHAR NOT NULL CHECK (mark IN ('not processed', 'ready', 'blocked', 'stored')),
    name VARCHAR NOT NULL,
    sha2sum VARCHAR,
    size INTEGER NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE receiverfile (
    file_path VARCHAR,
    downloads INTEGER NOT NULL,
    creation_date VARCHAR NOT NULL,
    last_access VARCHAR,
    id VARCHAR NOT NULL,
    internalfile_id VARCHAR NOT NULL,
    receiver_id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    mark VARCHAR NOT NULL CHECK (mark IN ('not notified', 'notified', 'unable to notify')),
    FOREIGN KEY(internalfile_id) REFERENCES internalfile(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES receiver(id) ON DELETE CASCADE,
    FOREIGN KEY(internaltip_id) REFERENCES internaltip(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE internaltip (
    access_limit INTEGER NOT NULL,
    creation_date VARCHAR NOT NULL,
    download_limit INTEGER NOT NULL,
    escalation_threshold INTEGER,
    expiration_date VARCHAR NOT NULL,
    wb_fields BLOB,
    last_activity VARCHAR,
    mark VARCHAR NOT NULL CHECK (mark IN ('submission', 'finalize', 'first', 'second')),
    pertinence_counter INTEGER NOT NULL,
    context_id VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    FOREIGN KEY(context_id) REFERENCES context(id) ON DELETE CASCADE,
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
    password VARCHAR NOT NULL,
    public_site VARCHAR NOT NULL,
    stats_update_time INTEGER NOT NULL,
    last_update VARCHAR,
    PRIMARY KEY (id)
);

CREATE TABLE notification (
    creation_date VARCHAR NOT NULL,
    server VARCHAR,
    port INTEGER,
    password VARCHAR,
    username VARCHAR,
    security VARCHAR NOT NULL CHECK (security IN ('TLS', 'SSL')),
    tip_template VARCHAR,
    file_template VARCHAR,
    comment_template VARCHAR,
    activation_template VARCHAR,
    id VARCHAR NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE receiver (
    can_delete_submission INTEGER NOT NULL,
    creation_date VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    last_access VARCHAR,
    last_update VARCHAR,
    name VARCHAR NOT NULL,
    notification_fields BLOB NOT NULL,
    password VARCHAR,
    failed_login INTEGER NOT NULL,
    receiver_level INTEGER NOT NULL,
    username VARCHAR NOT NULL,
    PRIMARY KEY (id)
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
    access_counter INTEGER NOT NULL,
    creation_date VARCHAR NOT NULL,
    expressed_pertinence INTEGER NOT NULL,
    id VARCHAR NOT NULL,
    internaltip_id VARCHAR NOT NULL,
    last_access VARCHAR,
    notification_date VARCHAR,
    mark VARCHAR NOT NULL CHECK (mark IN ('not notified', 'notified', 'unable to notify')),
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



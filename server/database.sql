create table root_key
(
    id           int auto_increment
        primary key,
    pubkey         text(255)   not null,
    private_key    text(255)   not null,
    cert           text(4096)  not null,
    created        timestamp   not null,
    constraint root_key_pk
        unique (pubkey(255))
);

create table user_register
(
    id           bigint auto_increment
        primary key,
    fio          text(255)     not null,
    phone_number text(16)      not null,
    pubkey       text(255)     not null,
    ip           text(20)      not null,
    time         timestamp     not null,
    tries        int default 0 not null,
    verif_code   text(6)       not null,
    request_id   text(255)     not null,
    constraint user_register_pk_2
        unique (phone_number(16)),
    constraint user_register_pk_3
        unique (pubkey(255))
);

create table users
(
    id           bigint auto_increment
        primary key,
    fio          text(255)     not null,
    phone_number text(16)      not null,
    pubkey       text(255)     not null,
    time_register timestamp    not null,
    cert         text(4096)    not null,
    token text(128) not null,
    constraint users_pk_2
        unique (phone_number(16)),
    constraint users_pk_3
        unique (pubkey(255)),
    constraint users_pk_4
        unique (token(128))
);

create table auth
(
    id           bigint auto_increment
        primary key,
    phone_number text(16)  not null,
    trs          text(128) not null,
    timestamp    timestamp not null,
    pubkey text(255) not null,
    constraint auth_pk_2
        unique (phone_number(16))
);

create table revoke_requests
(
    id           bigint auto_increment
        primary key,
    phone_number text(16)      not null,
    pubkey       text(255)     not null,
    ip           text(20)      not null,
    time         timestamp     not null,
    tries        int default 0 not null,
    verif_code   text(6)       not null,
    request_id   text(255)     not null,
    constraint revoke_requests_pk_2
        unique (phone_number(16)),
    constraint revoke_requests_pk_3
        unique (pubkey(255))
);

create table revoked_keys
(
    id           bigint auto_increment
        primary key,
    phone_number text(16)      not null,
    pubkey       text(255)     not null,
    ip           text(20)      not null,
    time         timestamp     not null,
    constraint revoke_keys_pk_2
        unique (pubkey(255))
);

create table documents
(
    timeuuid     CHAR(36)      not null,
    path         VARCHAR(255)  not null,
    filename     VARCHAR(255)  not null,
    user_id      bigint        not null,
    created      timestamp     not null,
    sign         VARCHAR(4096),
    sign_verified BOOLEAN      not null DEFAULT FALSE,
    sha256       CHAR(64)      not null,
    can_access   varchar(255),
    PRIMARY KEY (timeuuid),
    UNIQUE (path),
    UNIQUE (sha256),
    INDEX (user_id)
);

create table new_docs_available
(
    id           bigint auto_increment
        primary key,
    user_id      bigint        not null,
    timeuuid     CHAR(36)      not null,
    filename     VARCHAR(255)  not null,
    created      timestamp     not null,
    sign         VARCHAR(4096),
    sha256       CHAR(64)      not null,
    INDEX (user_id),
    INDEX (timeuuid)
);


CREATE TABLE first_launch (yes INT);
CREATE TABLE items (id INT AUTO_INCREMENT PRIMARY KEY, find_val VARCHAR(255));
INSERT INTO items (find_val) VALUES ('bruh');



/*
 * Copyright (c) 2024 DjamikTea.
 * Created by Dzhamal on 2024-12-2.
 * All rights reserved.
 */

#INSERT INTO user_register (fio, phone_number, pubkey, ip, time, verif_code, request_id)
#VALUES ('шими я шими я шими я', '996555555555', 'pubkey', '8.8.8.8', NOW(), '123456', 'request_id');
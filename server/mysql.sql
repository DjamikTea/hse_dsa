/*
 * Copyright (c) 2024 DjamikTea.
 * Created by Dzhamal on 2024-12-1.
 * All rights reserved.
 */

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
    time_register         timestamp     not null,
    constraint users_pk_2
        unique (phone_number(16)),
    constraint users_pk_3
        unique (pubkey(255))
);

INSERT INTO user_register (fio, phone_number, pubkey, ip, time, verif_code, request_id)
VALUES ('шими я шими я шими я', '996555555555', 'pubkey', '8.8.8.8', NOW(), '123456', 'request_id');
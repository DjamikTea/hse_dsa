#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-1.
#  All rights reserved.
import asyncio
import os
from http.client import responses

from fastapi.testclient import TestClient
from mysql.connector import ProgrammingError

from server.app.database import connection_pool
from server.app.main import app
from server.app.telegram_gateway import TelegramGatewayAPI
client = TestClient(app)

#TODO: мокировать TelegramGatewayAPI

def test_first_launch():
    db = connection_pool.get_connection()
    cursor = db.cursor()
    first_launch_flag: bool = False
    try:
        cursor.execute("SELECT * FROM first_launch")
        first_launch_flag = True
    except ProgrammingError as e:
        print(e)

    if not first_launch_flag:
        print("First launch flag not found")
        print("Creating tables...")

        # create table user_register
        # (
        #     id           bigint auto_increment
        #         primary key,
        #     fio          text(255)     not null,
        #     phone_number text(16)      not null,
        #     pubkey       text(255)     not null,
        #     ip           text(20)      not null,
        #     time         timestamp     not null,
        #     tries        int default 0 not null,
        #     verif_code   text(6)       not null,
        #     request_id   text(255)     not null,
        #     constraint user_register_pk_2
        #         unique (phone_number(16)),
        #     constraint user_register_pk_3
        #         unique (pubkey(255))
        # );

        cursor.execute("CREATE TABLE user_register (id BIGINT AUTO_INCREMENT PRIMARY KEY, fio TEXT(255) NOT NULL, phone_number TEXT(16) NOT NULL, pubkey TEXT(255) NOT NULL, ip TEXT(20) NOT NULL, time TIMESTAMP NOT NULL, tries INT DEFAULT 0 NOT NULL, verif_code TEXT(6) NOT NULL, request_id TEXT(255) NOT NULL, CONSTRAINT user_register_pk_2 UNIQUE (phone_number(16)), CONSTRAINT user_register_pk_3 UNIQUE (pubkey(255)))")
        # create table users
        # (
        #     id           bigint auto_increment
        #         primary key,
        #     fio          text(255)     not null,
        #     phone_number text(16)      not null,
        #     pubkey       text(255)     not null,
        #     time_register         timestamp     not null,
        #     constraint users_pk_2
        #         unique (phone_number(16)),
        #     constraint users_pk_3
        #         unique (pubkey(255))
        # );
        cursor.execute("CREATE TABLE users (id BIGINT AUTO_INCREMENT PRIMARY KEY, fio TEXT(255) NOT NULL, phone_number TEXT(16) NOT NULL, pubkey TEXT(255) NOT NULL, time_register TIMESTAMP NOT NULL, CONSTRAINT users_pk_2 UNIQUE (phone_number(16)), CONSTRAINT users_pk_3 UNIQUE (pubkey(255)))")
        cursor.execute("CREATE TABLE first_launch (yes INT)")
        cursor.execute("CREATE TABLE items (id INT AUTO_INCREMENT PRIMARY KEY, find_val VARCHAR(255))")
        cursor.execute("INSERT INTO items (find_val) VALUES ('bruh')")
        db.commit()
        print("Table first_launch created")
        first_launch_flag = True

    assert first_launch_flag == True

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {'message': 'hello world'}

def test_mysql_select():
    response = client.get("/test/items", params={"item_id": "bruh"})
    assert response.status_code == 200
    assert response.json() == {'find_val': 'bruh', 'id': 1}

async def test_telegram_gateway():
    tg_gateway = TelegramGatewayAPI()
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")
    if not test_phone_number:
        print("Telegram test phone number not found")
        assert False

    response = await tg_gateway.check_send_ability(test_phone_number)
    print(response)
    assert response['ok'] == True
    assert response['result']['phone_number'] == test_phone_number
    assert response['result']['request_cost'] == 0
    await asyncio.sleep(5)

    response = await tg_gateway.send_verification_message(test_phone_number, code="123456")
    print(response)
    assert response['ok'] == True
    await asyncio.sleep(1)

    response = await tg_gateway.check_verification_status(response['result']['request_id'])
    print(response)
    assert response['ok'] == True
    assert response['result']['delivery_status']['status'] == 'sent'
    await asyncio.sleep(1)

    response = await tg_gateway.revoke_verification_message(response['result']['request_id'])
    print(response)
    assert response['ok'] == True
    assert response['result'] == True
    await asyncio.sleep(60)

def test_register():
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")
    response = client.get("/login/register", params={"phone_number": test_phone_number, "fio": "Test User", "public_key": "1234567890"})
    assert response.json() == {"message": "Verification code sent"}
    assert response.status_code == 200

    response = client.get("/login/register", params={"phone_number": test_phone_number, "fio": "Test User", "public_key": "1234567890"})
    assert response.json() == {"detail": "Too many requests, try again later"}
    assert response.status_code == 400

def test_verify():
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")
    response = client.get("/login/verify", params={"phone_number": test_phone_number, "code": "123456"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid verification code"}

    db = connection_pool.get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_register WHERE phone_number = %s", (test_phone_number,))
    user = cursor.fetchone()
    assert user is not None

    code = user['verif_code']
    response = client.get("/login/verify", params={"phone_number": test_phone_number, "code": code})
    assert response.status_code == 200
    assert response.json() == {"message": "User registered"}

    response = client.get("/login/verify", params={"phone_number": test_phone_number, "code": code})
    assert response.status_code == 400
    assert response.json() == {"detail": "Register not found"}


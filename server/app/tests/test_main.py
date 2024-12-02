#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-1.
#  All rights reserved.
import asyncio
import os
import pytest
from aioresponses import aioresponses

from fastapi.testclient import TestClient
from mysql.connector import ProgrammingError

from server.app.database import connection_pool
from server.app.main import app
from server.app.telegram_gateway import TelegramGatewayAPI, mock_http
client = TestClient(app)

auth_token = ""

@pytest.fixture
def mocked_aiohttp():
    with aioresponses() as mock:
        yield mock

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

        sql = open("server/database.sql", "r").read()  # Updated path
        for query in sql.split(";"):
            if query != '':
                if str(query).replace("\n", "")[0] != '#':
                    cursor.execute(query.replace("\n", ""))

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

async def test_telegram_gateway(mocked_aiohttp):
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")
    tg_gateway = TelegramGatewayAPI()
    if not test_phone_number:
        print("Telegram test phone number not found")
        assert False

    mock_http(mocked_aiohttp, test_phone_number)

    response = await tg_gateway.check_send_ability(test_phone_number)
    assert response['ok'] == True
    assert response['result']['phone_number'] == test_phone_number
    assert response['result']['request_cost'] == 0

    response = await tg_gateway.send_verification_message(test_phone_number, code="123456")
    assert response['ok'] == True

    response = await tg_gateway.check_verification_status(response['result']['request_id'])
    assert response['ok'] == True
    assert response['result']['delivery_status']['status'] == 'sent'

    response = await tg_gateway.revoke_verification_message(response['result']['request_id'])
    assert response['ok'] == True
    assert response['result'] == True

def test_register(mocked_aiohttp):
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")

    mock_http(mocked_aiohttp, test_phone_number)

    response = client.post("/login/register", params={"phone_number": test_phone_number, "fio": "Test User", "public_key": "1234567890"})
    assert response.json() == {"message": "Verification code sent"}
    assert response.status_code == 200

    response = client.post("/login/register", params={"phone_number": test_phone_number, "fio": "Test User", "public_key": "1234567890"})
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
    global auth_token
    auth_token = response.json()['token']

    response = client.get("/login/verify", params={"phone_number": test_phone_number, "code": code})
    assert response.status_code == 400
    assert response.json() == {"detail": "Register not found"}
#
# def test_auth():
#     response = client.get("/login/auth", headers={"Authorization": f"Bearer {auth_token}"})
#     assert response.status_code == 200
#     assert response.json() == {"message": "User authenticated"}
#
#     response = client.get("/login/auth", headers={"Authorization": "Bearer 123456"})
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Invalid token"}
#
#     response = client.get("/login/auth")
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Not authenticated"}
#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-1.
#  All rights reserved.
import asyncio
import os
from datetime import datetime, timezone
import json

import pytest
from aioresponses import aioresponses

from hsecrypto import GostDSA
from utils.csr import generate_csr, check_csr_root

from fastapi.testclient import TestClient
from mysql.connector import ProgrammingError

from app.database import connection_pool
from app.main import app
from app.telegram_gateway import TelegramGatewayAPI, mock_http
client = TestClient(app)

auth_token = ""
crypto = GostDSA()

private_key, public_key = crypto.generate_key_pair()

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

        sql = open("database.sql", "r").read()  # Updated path
        for query in sql.split(";"):
            if query != '':
                if str(query).replace("\n", "")[0] != '#':
                    cursor.execute(query.replace("\n", ""))
        db.commit()

        crypto2 = GostDSA()
        privkeyroot, pubkeyroot = crypto2.generate_key_pair()
        root_ca = {
            "root_ca": {
                "country": "RU",
                "organization": "DjamikTea",
                "email": "abakarovda@edu.hse.ru",
                "public_key": pubkeyroot,
                "domain": "secr.gopass.dev",
                "date_generation": datetime.now(timezone.utc).isoformat()
            }
        }

        cert_sign = crypto2.sign(str(root_ca).encode(), privkeyroot)
        root_ca['root_sign'] = cert_sign

        cursor.execute("INSERT INTO root_key (pubkey, private_key, cert, created) VALUES (%s, %s, %s, NOW())", (pubkeyroot, privkeyroot, json.dumps(root_ca)))
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

    response = client.get("/test/items", params={"item_id": "bruh1"})
    assert response.status_code == 404

async def test_telegram_gateway(mocked_aiohttp):
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")
    tg_gateway = TelegramGatewayAPI()

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

    response = client.post("/login/register", params={"phone_number": test_phone_number, "fio": "Test User", "public_key": public_key})
    assert response.json() == {"message": "Verification code sent"}
    assert response.status_code == 200

    response = client.post("/login/register", params={"phone_number": test_phone_number, "fio": "Test User", "public_key": public_key})
    assert response.json() == {"detail": "Too many requests, try again later"}
    assert response.status_code == 400

def test_verify():
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")

    country = "RU"
    organization = "DjamikTea"
    ip = "testclient"
    fio = "Dzhamal Dzhamalovich"

    csr = generate_csr(private_key, public_key, country, organization, test_phone_number, ip, fio)

    response = client.get("/login/verify", params={"phone_number": test_phone_number, "code": "123456", "csr": json.dumps(csr)})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid verification code"}

    db = connection_pool.get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM user_register WHERE phone_number = %s", (test_phone_number,))
    user = cursor.fetchone()
    assert user is not None

    code = user['verif_code']

    csrfalse = {
        "client": {
            "public_key": public_key,
            "country": country,
            "organization": organization,
            "phone_number": test_phone_number,
            "fio": fio,
            "ip": ip,
            "date_generation": datetime.now(timezone.utc).isoformat()
        },
        "client_sign_time": datetime.now(timezone.utc).isoformat()
    }
    falspriv, falspub = crypto.generate_key_pair()
    csrfalse['client_sign'] = crypto.sign(str(csr).encode(), falspriv)

    response = client.get("/login/verify", params={"phone_number": test_phone_number, "code": code, "csr": json.dumps(csrfalse)})
    assert response.status_code == 400
    assert response.json() == {"detail": "CSR client signature is invalid"}

    response = client.get("/login/verify", params={"phone_number": test_phone_number, "code": code, "csr": json.dumps(csr)})
    assert response.status_code == 200
    global auth_token
    auth_token = response.json()['token']

    csr = json.loads(response.json()['csr'])
    assert check_csr_root(csr, "secr.gopass.dev")

    response = client.get("/login/verify", params={"phone_number": test_phone_number, "code": code, "csr": json.dumps(csr)})
    assert response.status_code == 400
    assert response.json() == {"detail": "Register not found"}

def test_auth():
    response = client.get("/login/get_auth", params={"phone": os.getenv("TELEGRAM_TEST_PHONE")})
    assert response.status_code == 200
    trs = response.json()['trs']

    response = client.get("/login/get_auth", params={"phone": os.getenv("TELEGRAM_TEST_PHONE")})
    assert response.status_code == 400
    assert response.json() == {"detail": "Too many requests, try again later"}

    signed_trs = crypto.sign(str(trs).encode(), private_key=private_key)
    response = client.get("/login/auth", params={"phone": os.getenv("TELEGRAM_TEST_PHONE"), "signed_trs": signed_trs})
    assert response.status_code == 200

    response = client.get("/login/auth", params={"phone": os.getenv("TELEGRAM_TEST_PHONE"), "signed_trs": signed_trs})
    assert response.status_code == 400
    assert response.json() == {"detail": "User not found"}

def test_revoke(mocked_aiohttp):
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")
    mock_http(mocked_aiohttp, test_phone_number)


    response = client.post("/revoke", params={"phone": "799999999"})
    assert response.json() == {"detail": "User not found"}

    response = client.post("/revoke", params={"phone": test_phone_number})
    assert response.json() == {"message": "Verification code sent"}

    response = client.post("/revoke", params={"phone": test_phone_number})
    assert response.json() == {"detail": "Too many requests, try again later"}

    response = client.get("/revoke/verify", params={"phone": test_phone_number, "code": "123456"})
    assert response.json() == {"detail": "Invalid verification code"}

    db = connection_pool.get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM revoke_requests WHERE phone_number = %s", (test_phone_number,))
    request = cursor.fetchone()
    assert request is not None

    code = request['verif_code']

    response = client.get("/revoke/check", params={"public_key": request['pubkey']})
    assert response.json() == {"revoked": False,"message": "Key not revoked"}

    response = client.get("/revoke/verify", params={"phone": test_phone_number, "code": code})
    assert response.json() == {"message": "Key revoked and user deleted"}

    response = client.get("/revoke/check", params={"public_key": request['pubkey']})
    assert response.json() == {"revoked": True,"message": "Key revoked"}

    response = client.get("/revoke/verify", params={"phone": test_phone_number, "code": code})
    assert response.json() == {"detail": "Request not found"}
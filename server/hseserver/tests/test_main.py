#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-1.
#  All rights reserved.
import hashlib
import os
from datetime import datetime, timezone
import json

import pytest
from aioresponses import aioresponses
from mysql.connector import pooling

from hsecrypto import GostDSA
from hseserver.utils.csr import generate_csr, check_csr_root

from fastapi.testclient import TestClient
from mysql.connector import ProgrammingError

from hseserver.app.database import dbconfig
from hseserver.app.main import app
from hseserver.app.telegram_gateway import TelegramGatewayAPI, mock_http
from hseserver.utils.sign import sign_document

client = TestClient(app)

auth_token = ""
timeuuid_file = ""
cert = {}

auth_token_sec = ""
cert_sec = {}

first_launch_patch = False

crypto = GostDSA()
private_key, public_key = crypto.generate_key_pair()
private_key_sec, public_key_sec = crypto.generate_key_pair()


@pytest.fixture
def mocked_aiohttp():
    with aioresponses() as mock:
        yield mock


@pytest.fixture(scope="session", autouse=True)
def check_first_launch():
    try:
        test_first_launch()
    except Exception as e:
        pytest.skip(f"Skipping all tests because test_first_launch failed: {e}")


def test_first_launch():
    global first_launch_patch
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mypool", pool_size=5, **dbconfig
    )
    db = connection_pool.get_connection()
    cursor = db.cursor()
    first_launch_flag: bool = False
    try:
        cursor.execute("SELECT * FROM first_launch")
        cursor.fetchall()
        first_launch_flag = True
    except ProgrammingError as e:
        print(e)

    if not first_launch_flag:
        print("First launch flag not found")
        print("Creating tables...")

        sql = open("database.sql", "r").read()  # Updated path
        for query in sql.split(";"):
            if query != "":
                if str(query).replace("\n", "")[0] != "#":
                    cursor.execute(query.replace("\n", ""))
        db.commit()

        crypto2 = GostDSA()
        privkeyroot, pubkeyroot = crypto2.generate_key_pair()
        root_ca = {
            "root_ca": {
                "country": "RU",
                "organization": os.getenv("ORGANIZATION", "DjamikTea"),
                "email": os.getenv("EMAIL", "daabakarov@edu.hse.ru"),
                "public_key": pubkeyroot,
                "domain": os.getenv("DOMAIN", "hse.gopass.dev"),
                "date_generation": datetime.now(timezone.utc).isoformat(),
            }
        }

        cert_sign = crypto2.sign(str(root_ca).encode(), privkeyroot)
        root_ca["root_sign"] = cert_sign

        cursor.execute(
            "INSERT INTO root_key (pubkey, private_key, cert, created) VALUES (%s, %s, %s, NOW())",
            (pubkeyroot, privkeyroot, json.dumps(root_ca)),
        )
        db.commit()
        print("Table first_launch created")
        # create .test_lock file
        with open(".test_lock", "w") as f:
            f.write("1")
        first_launch_flag = True
    else:
        if not first_launch_patch:
            raise Exception("First launch flag found. skip...")

    first_launch_patch = first_launch_flag
    assert first_launch_flag == True
    db.close()


def test_read_main(check_first_launch):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}


def test_mysql_select(check_first_launch):
    response = client.get("/test/items", params={"item_id": "bruh"})
    assert response.status_code == 200
    assert response.json() == {"find_val": "bruh", "id": 1}

    response = client.get("/test/items", params={"item_id": "bruh1"})
    assert response.status_code == 404


async def test_telegram_gateway(check_first_launch, mocked_aiohttp):
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")
    tg_gateway = TelegramGatewayAPI()

    mock_http(mocked_aiohttp, test_phone_number)

    response = await tg_gateway.check_send_ability(test_phone_number)
    assert response["ok"] == True
    assert response["result"]["phone_number"] == test_phone_number
    assert response["result"]["request_cost"] == 0

    response = await tg_gateway.send_verification_message(
        test_phone_number, code="123456"
    )
    assert response["ok"] == True

    response = await tg_gateway.check_verification_status(
        response["result"]["request_id"]
    )
    assert response["ok"] == True
    assert response["result"]["delivery_status"]["status"] == "sent"

    response = await tg_gateway.revoke_verification_message(
        response["result"]["request_id"]
    )
    assert response["ok"] == True
    assert response["result"] == True


def test_register(check_first_launch, mocked_aiohttp):
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")

    mock_http(mocked_aiohttp, test_phone_number)

    response = client.post(
        "/login/register",
        params={
            "phone_number": test_phone_number,
            "fio": "Test User",
            "public_key": public_key,
        },
    )
    assert response.json() == {"message": "Verification code sent"}
    assert response.status_code == 200

    response = client.post(
        "/login/register",
        params={
            "phone_number": test_phone_number,
            "fio": "Test User",
            "public_key": public_key,
        },
    )
    assert response.json() == {"detail": "Too many requests, try again later"}
    assert response.status_code == 400


def test_verify(check_first_launch):
    global cert
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")

    country = "RU"
    organization = "DjamikTea"
    ip = "testclient"
    fio = "Dzhamal Dzhamalovich"

    csr = generate_csr(
        private_key, public_key, country, organization, test_phone_number, ip, fio
    )

    response = client.get(
        "/login/verify",
        params={
            "phone_number": test_phone_number,
            "code": "123457",
            "csr": json.dumps(csr),
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid verification code"}

    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mypool", pool_size=5, **dbconfig
    )
    db = connection_pool.get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM user_register WHERE phone_number = %s", (test_phone_number,)
    )
    user = cursor.fetchone()
    assert user is not None

    code = user["verif_code"]

    csrfalse = {
        "client": {
            "public_key": public_key,
            "country": country,
            "organization": organization,
            "phone_number": test_phone_number,
            "fio": fio,
            "ip": ip,
            "date_generation": datetime.now(timezone.utc).isoformat(),
        },
        "client_sign_time": datetime.now(timezone.utc).isoformat(),
    }
    falspriv, falspub = crypto.generate_key_pair()
    csrfalse["client_sign"] = crypto.sign(str(csr).encode(), falspriv)

    response = client.get(
        "/login/verify",
        params={
            "phone_number": test_phone_number,
            "code": code,
            "csr": json.dumps(csrfalse),
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "CSR client signature is invalid"}

    response = client.get(
        "/login/verify",
        params={
            "phone_number": test_phone_number,
            "code": code,
            "csr": json.dumps(csr),
        },
    )
    assert response.status_code == 200
    global auth_token
    auth_token = response.json()["token"]

    csr = json.loads(response.json()["cert"])
    cert = csr
    assert check_csr_root(csr, os.getenv("DOMAIN", "hse.gopass.dev"))

    response = client.get(
        "/login/verify",
        params={
            "phone_number": test_phone_number,
            "code": code,
            "csr": json.dumps(csr),
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Register not found"}
    db.close()


def test_auth(check_first_launch):
    global auth_token
    response = client.get(
        "/login/get_auth", params={"phone": os.getenv("TELEGRAM_TEST_PHONE")}
    )
    assert response.status_code == 200
    trs = response.json()["trs"]

    response = client.get(
        "/login/get_auth", params={"phone": os.getenv("TELEGRAM_TEST_PHONE")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Too many requests, try again later"}

    signed_trs = crypto.sign(str(trs).encode(), private_key=private_key)
    response = client.get(
        "/login/auth",
        params={"phone": os.getenv("TELEGRAM_TEST_PHONE"), "signed_trs": signed_trs},
    )
    assert response.status_code == 200
    auth_token = response.json()["token"]

    response = client.get(
        "/login/auth",
        params={"phone": os.getenv("TELEGRAM_TEST_PHONE"), "signed_trs": signed_trs},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "User not found"}


def test_upload_file(check_first_launch):
    global auth_token, timeuuid_file

    sha256_file = hashlib.sha256(
        open("hseserver/utils/test.txt", "rb").read()
    ).hexdigest()

    response = client.put(
        "/docs/upload",
        headers={"Authorization": "bruh", "sha256": sha256_file},
        files={"file": ("test.txt", open("hseserver/utils/test.txt", "rb"))},
    )
    assert response.status_code == 401

    response = client.put(
        "/docs/upload",
        headers={"Authorization": auth_token, "sha256": sha256_file},
        files={"file": ("test.txt", open("hseserver/utils/test.txt", "rb"))},
    )
    assert response.status_code == 200
    timeuuid_file = response.json()["timeuuid"]

    response = client.put(
        "/docs/upload",
        headers={"Authorization": auth_token, "sha256": "bruh"},
        files={"file": ("test.txt", open("hseserver/utils/test.txt", "rb"))},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": f"Hashes do not match: {sha256_file}"}


def test_sign_file(check_first_launch):
    global auth_token, timeuuid_file

    response = client.post("/docs/sign/bruh", headers={"Authorization": auth_token})
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}

    sign = sign_document(
        timeuuid_file,
        hashlib.sha256(open("hseserver/utils/test.txt", "rb").read()).hexdigest(),
        private_key,
        cert,
    )
    response = client.post(
        f"/docs/sign/{timeuuid_file}",
        headers={"Authorization": auth_token, "signature": json.dumps(sign)},
    )
    assert response.status_code == 200

    sign = sign_document(
        timeuuid_file,
        hashlib.sha256(open("hseserver/utils/test.txt", "rb").read()).hexdigest(),
        "7233096205a1014b9c14a334e0b608e6a1fd47abc126568ec862151c43fbd161",
        cert,
    )
    response = client.post(
        f"/docs/sign/{timeuuid_file}",
        headers={"Authorization": auth_token, "signature": json.dumps(sign)},
    )
    assert response.status_code == 400


def test_download_file(check_first_launch):
    global auth_token, timeuuid_file

    response = client.get("/docs/download/bruh", headers={"Authorization": auth_token})
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}

    response = client.get(
        f"/docs/download/{timeuuid_file}", headers={"Authorization": auth_token}
    )
    assert response.status_code == 200
    assert response.content == open("hseserver/utils/test.txt", "rb").read()


def test_get_list(check_first_launch):
    global auth_token

    response = client.get("/docs/list", headers={"Authorization": auth_token})
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1


def test_register_second(check_first_launch, mocked_aiohttp):
    test_phone_number = "79999999999"

    mock_http(mocked_aiohttp, test_phone_number)

    response = client.post(
        "/login/register",
        params={
            "phone_number": test_phone_number,
            "fio": "Test User",
            "public_key": public_key_sec,
        },
    )
    assert response.json() == {"message": "Verification code sent"}
    assert response.status_code == 200

    response = client.post(
        "/login/register",
        params={
            "phone_number": test_phone_number,
            "fio": "Test User",
            "public_key": public_key_sec,
        },
    )
    assert response.json() == {"detail": "Too many requests, try again later"}
    assert response.status_code == 400


def test_verify_second(check_first_launch):
    global cert_sec, auth_token_sec
    test_phone_number = "79999999999"

    country = "RU"
    organization = "DjamikTea"
    ip = "testclient"
    fio = "Dzhamal Dzhamalovich"

    csr = generate_csr(
        private_key_sec,
        public_key_sec,
        country,
        organization,
        test_phone_number,
        ip,
        fio,
    )
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mypool", pool_size=5, **dbconfig
    )
    db = connection_pool.get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM user_register WHERE phone_number = %s", (test_phone_number,)
    )
    user = cursor.fetchone()
    assert user is not None

    code = user["verif_code"]

    response = client.get(
        "/login/verify",
        params={
            "phone_number": test_phone_number,
            "code": code,
            "csr": json.dumps(csr),
        },
    )
    assert response.status_code == 200
    auth_token_sec = response.json()["token"]

    csr = json.loads(response.json()["cert"])
    cert_sec = csr
    assert check_csr_root(csr, os.getenv("DOMAIN", "hse.gopass.dev"))


def test_send_document(check_first_launch):
    global auth_token, auth_token_sec, timeuuid_file

    response = client.get(
        f"/docs/download/{timeuuid_file}", headers={"Authorization": auth_token_sec}
    )
    assert response.status_code == 403

    response = client.post(
        f"/docs/sign/{timeuuid_file}", headers={"Authorization": auth_token_sec}
    )
    assert response.status_code == 403

    response = client.post(
        f"/docs/send/{timeuuid_file}",
        headers={"Authorization": auth_token, "phone": "79999999999"},
    )
    assert response.status_code == 200

    response = client.post(
        f"/docs/send/{timeuuid_file}",
        headers={"Authorization": auth_token, "phone": "79999999998"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Reciver not registered"}

    response = client.post(
        f"/docs/send/{timeuuid_file}",
        headers={"Authorization": auth_token_sec, "phone": "79999999999"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}

    response = client.post(
        "/docs/send/bruh",
        headers={"Authorization": auth_token, "phone_number": "79999999999"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_recive_document(check_first_launch):
    global auth_token_sec, timeuuid_file

    response = client.get("/docs/available", headers={"Authorization": auth_token_sec})
    assert response.status_code == 200
    file_info = response.json()["documents"]
    assert len(file_info) == 1
    assert file_info[0]["timeuuid"] == timeuuid_file

    response = client.get(
        f"/docs/download/{timeuuid_file}", headers={"Authorization": auth_token_sec}
    )
    assert response.status_code == 200
    assert file_info[0]["sha256"] == hashlib.sha256(response.content).hexdigest()

    response = client.post(
        f"/docs/accept/{timeuuid_file}", headers={"Authorization": auth_token_sec}
    )
    assert response.status_code == 200

    response = client.post(
        f"/docs/accept/{timeuuid_file}", headers={"Authorization": auth_token_sec}
    )
    assert response.status_code == 404


def test_delete_document(check_first_launch):
    global auth_token, auth_token_sec, timeuuid_file

    response = client.delete("/docs/delete/bruh", headers={"Authorization": auth_token})
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}

    response = client.delete(
        f"/docs/delete/{timeuuid_file}", headers={"Authorization": auth_token_sec}
    )
    assert response.status_code == 403

    response = client.delete(
        f"/docs/delete/{timeuuid_file}", headers={"Authorization": auth_token}
    )
    assert response.status_code == 200

    response = client.delete(
        f"/docs/delete/{timeuuid_file}", headers={"Authorization": auth_token}
    )
    assert response.status_code == 404


def test_revoke(check_first_launch, mocked_aiohttp):
    test_phone_number = os.getenv("TELEGRAM_TEST_PHONE")
    mock_http(mocked_aiohttp, test_phone_number)

    response = client.post("/revoke", params={"phone": "799999998"})
    assert response.json() == {"detail": "User not found"}

    response = client.post("/revoke", params={"phone": test_phone_number})
    assert response.json() == {"message": "Verification code sent"}

    response = client.post("/revoke", params={"phone": test_phone_number})
    assert response.json() == {"detail": "Too many requests, try again later"}

    response = client.get(
        "/revoke/verify", params={"phone": test_phone_number, "code": "123458"}
    )
    assert response.json() == {"detail": "Invalid verification code"}

    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mypool", pool_size=5, **dbconfig
    )
    db = connection_pool.get_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

    cursor.execute(
        "SELECT * FROM revoke_requests WHERE phone_number = %s", (test_phone_number,)
    )
    request = cursor.fetchone()
    assert request is not None

    code = request["verif_code"]

    response = client.get("/revoke/check", params={"public_key": request["pubkey"]})
    assert response.json() == {"revoked": False, "message": "Key not revoked"}

    response = client.get(
        "/revoke/verify", params={"phone": test_phone_number, "code": code}
    )
    assert response.json() == {"message": "Key revoked and user deleted"}

    response = client.get("/revoke/check", params={"public_key": request["pubkey"]})
    assert response.json() == {"revoked": True, "message": "Key revoked"}

    response = client.get(
        "/revoke/verify", params={"phone": test_phone_number, "code": code}
    )
    assert response.json() == {"detail": "Request not found"}

    mock_http(mocked_aiohttp, "79999999999")

    response = client.post("/revoke", params={"phone": "79999999999"})
    assert response.json() == {"message": "Verification code sent"}

    cursor.execute(
        "SELECT * FROM revoke_requests WHERE phone_number = %s", ("79999999999",)
    )
    request = cursor.fetchone()
    assert request is not None

    code = request["verif_code"]

    response = client.get(
        "/revoke/verify", params={"phone": "79999999999", "code": code}
    )
    assert response.json() == {"message": "Key revoked and user deleted"}

    cursor.execute("DELETE FROM documents WHERE timeuuid = %s", (timeuuid_file,))
    cursor.execute(
        "DELETE FROM user_register WHERE phone_number = %s", (test_phone_number,)
    )
    db.commit()

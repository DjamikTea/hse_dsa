import json
import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from random import randint

from hsecrypto import GostDSA

from hseserver.app.database import get_db
from hseserver.app.greensms import Otp
from hseserver.app.telegram_gateway import TelegramGatewayAPI
import secrets

from hseserver.utils.csr import sign_csr

router = APIRouter()
logger = logging.getLogger(__name__)
tg = TelegramGatewayAPI()
grsms = Otp()


def generate_bearer_token():
    return secrets.token_urlsafe(64)


def generate_trs():
    return {
        "rand": secrets.token_urlsafe(64),
        "timestamp": datetime.now(timezone.utc).timestamp(),
    }


@router.post("/register")
async def register(
        phone_number: str, fio: str, public_key: str, request: Request, db=Depends(get_db)
):
    """
    Регистрация пользователя
    :param phone_number:
    :param fio:
    :param public_key:
    :param request:
    :param db:
    :return: {"message": "Verification code sent"}
    """
    cursor, conn = db
    ip = request.headers.get("X-Real-IP")

    if ip is None:
        ip = request.client.host

    cursor.execute(
        "SELECT * FROM user_register WHERE phone_number = %s", (phone_number,)
    )
    user = cursor.fetchone()
    if user is not None:
        if user["time"].replace(tzinfo=timezone.utc) > datetime.now(
                timezone.utc
        ) - timedelta(minutes=5):
            raise HTTPException(
                status_code=400, detail="Too many requests, try again later"
            )
        else:
            cursor.execute(
                "DELETE FROM user_register WHERE phone_number = %s", (phone_number,)
            )
            conn.commit()
    cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone_number,))
    user = cursor.fetchone()
    if user is not None:
        raise HTTPException(status_code=400, detail="User already exists")
    cursor.execute("SELECT * FROM revoked_keys WHERE pubkey = %s", (public_key,))
    user = cursor.fetchone()
    if user is not None:
        raise HTTPException(status_code=400, detail="Public key revoked")

    if os.getenv("OTP", "GREEN_SMS") == "TG":
        verif_code = randint(100000, 999999)
        resp = await tg.send_verification_message(phone_number, code=str(verif_code))
        if not resp["ok"]:
            raise HTTPException(
                status_code=400, detail="Failed to send verification message"
            )
    else:
        verif_code = await grsms.send_otp(phone_number)
        resp = {"result": {"request_id": "green_sms"}}
    cursor.execute(
        "INSERT INTO user_register (fio, phone_number, pubkey, ip, time, verif_code, request_id) "
        "VALUES (%s, %s, %s, %s, NOW(), %s, %s)",
        (fio, phone_number, public_key, ip, verif_code, resp["result"]["request_id"]),
    )
    conn.commit()
    return {"message": "Verification code sent"}


@router.get("/verify")
async def verify(
        phone_number: str, code: str, csr: str, request: Request, db=Depends(get_db)
):
    """
    Проверка кода верификации
    :param phone_number: Phone number
    :param code: Verification code
    :param csr: Certificate Signing Request
    :param request:
    :return: {"message": "User registered", "token": token, "cert": json.dumps(signed_csr)}
    """
    cursor, conn = db
    cursor.execute(
        "SELECT * FROM user_register WHERE phone_number = %s", (phone_number,)
    )
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=400, detail="Register not found")

    if user["time"].replace(tzinfo=timezone.utc) < datetime.now(
            timezone.utc
    ) - timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="Verification code expired")
    ip = request.headers.get("X-Real-IP")

    if ip is None:
        ip = request.client.host

    if user["ip"] != ip:
        raise HTTPException(status_code=400, detail="IP address mismatch")
    if user["tries"] >= 3:
        raise HTTPException(status_code=400, detail="Too many tries, try again later")
    if user["verif_code"] != code:
        cursor.execute(
            "UPDATE user_register SET tries = %s WHERE phone_number = %s",
            (
                user["tries"] + 1,
                phone_number,
            ),
        )
        conn.commit()
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # get root keys
    cursor.execute("SELECT * FROM root_key WHERE id = 1")
    root = cursor.fetchone()
    if root is None:
        raise HTTPException(status_code=500, detail="Server error K01")
    root_ca = json.loads(root["cert"])
    csr_loaded = json.loads(csr)

    try:
        signed_csr = sign_csr(csr_loaded, root["private_key"], root_ca, phone_number)
    except ValueError:
        raise HTTPException(status_code=400, detail="CSR client signature is invalid")
    token = generate_bearer_token()
    cursor.execute(
        "INSERT INTO users (fio, phone_number, pubkey, time_register, token, cert) "
        "VALUES (%s, %s, %s, NOW(), %s, %s)",
        (
            user["fio"],
            user["phone_number"],
            user["pubkey"],
            token,
            json.dumps(signed_csr),
        ),
    )
    cursor.execute("DELETE FROM user_register WHERE phone_number = %s", (phone_number,))
    conn.commit()
    return {
        "message": "User registered",
        "token": token,
        "cert": json.dumps(signed_csr),
    }


@router.get("/get_auth")
async def get_auth(phone: str, db=Depends(get_db)):
    """
    Генерация транзакции для аутентификации
    :param phone:
    :return: {"message": "TRS generated, you have 5 seconds", "trs": {"rand": "random", "timestamp": "timestamp"}}
    """
    cursor, conn = db
    cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")
    cursor.execute("SELECT * FROM auth WHERE phone_number = %s", (phone,))
    authx = cursor.fetchone()
    if authx is not None:
        if authx["timestamp"].replace(tzinfo=timezone.utc) > datetime.now(
                timezone.utc
        ) - timedelta(minutes=5):
            raise HTTPException(
                status_code=400, detail="Too many requests, try again later"
            )
        else:
            cursor.execute("DELETE FROM auth WHERE phone_number = %s", (phone,))
            conn.commit()

    trs = generate_trs()
    cursor.execute(
        "INSERT INTO auth (phone_number, trs, timestamp, pubkey) VALUES (%s, %s, NOW(), %s)",
        (phone, str(trs), user["pubkey"]),
    )
    conn.commit()
    return {"message": "TRS generated, you have 5 seconds", "trs": trs}


@router.get("/auth")
async def auth(phone: str, signed_trs: str, db=Depends(get_db)):
    """
    Аутентификация пользователя
    :param phone:
    :param signed_trs:
    :return: {"message": "Auth success", "token": token}
    """
    cursor, conn = db

    cursor.execute("SELECT * FROM auth WHERE phone_number = %s", (phone,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")

    if user["timestamp"].replace(tzinfo=timezone.utc) < datetime.now(
            timezone.utc
    ) - timedelta(seconds=5):
        raise HTTPException(status_code=400, detail="TRS expired")

    crypto = GostDSA()
    if crypto.check(signed_trs, user["trs"].encode(), user["pubkey"]):
        cursor.execute("DELETE FROM auth WHERE phone_number = %s", (phone,))
        token = generate_bearer_token()
        cursor.execute(
            "UPDATE users SET token = %s WHERE phone_number = %s", (token, phone)
        )
        conn.commit()
        return {"message": "Auth success", "token": token}
    else:
        raise HTTPException(status_code=400, detail="Invalid signature")

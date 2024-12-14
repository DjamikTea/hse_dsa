#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-5.
#  All rights reserved.

import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from random import randint

from hseserver.app.database import get_db
from hseserver.app.greensms import Otp
from hseserver.app.telegram_gateway import TelegramGatewayAPI

router = APIRouter()
logger = logging.getLogger(__name__)
tg = TelegramGatewayAPI()
grsms = Otp()


@router.post("")
async def revoke(phone: str, request: Request, db=Depends(get_db)):
    """
    Отправляет код подтверждения на телефон для отзыва ключа и удаления пользователя
    :param phone:
    :param request:
    :return: {"message": "Verification code sent"}
    """
    cursor, conn = db

    cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")

    cursor.execute("SELECT * FROM revoke_requests WHERE phone_number = %s", (phone,))
    requestx = cursor.fetchone()
    if requestx is not None:
        if requestx["time"].replace(tzinfo=timezone.utc) > datetime.now(
            timezone.utc
        ) - timedelta(minutes=5):
            raise HTTPException(
                status_code=400, detail="Too many requests, try again later"
            )
        else:
            cursor.execute(
                "DELETE FROM revoke_requests WHERE phone_number = %s", (phone,)
            )
            conn.commit()
    ip = request.client.host

    if os.getenv("OTP", "GREEN_SMS") == "TG":
        verif_code = randint(100000, 999999)
        resp = await tg.send_verification_message(phone, code=str(verif_code))
        if not resp["ok"]:
            raise HTTPException(
                status_code=400, detail="Failed to send verification message"
            )
    else:
        verif_code = await grsms.send_otp(phone)
        resp = {"result": {"request_id": "green_sms"}}

    cursor.execute(
        "INSERT INTO revoke_requests (phone_number, pubkey, ip, time, tries, verif_code, request_id)"
        "VALUES (%s, %s, %s, NOW(), 0, %s, %s)",
        (phone, user["pubkey"], ip, verif_code, resp["result"]["request_id"]),
    )
    conn.commit()
    return {"message": "Verification code sent"}


@router.get("/verify")
async def revoke_verify(phone: str, code: str, request: Request, db=Depends(get_db)):
    """
    Подтверждает отзыв ключа и удаление пользователя
    :param phone:
    :param code:
    :param request:
    :return: {"message": "Key revoked and user deleted"}
    """
    cursor, conn = db

    cursor.execute("SELECT * FROM revoke_requests WHERE phone_number = %s", (phone,))
    requestx = cursor.fetchone()
    if requestx is None:
        raise HTTPException(status_code=400, detail="Request not found")
    if requestx["time"].replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    ) - timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="Verification code expired")
    if requestx["tries"] >= 3:
        raise HTTPException(status_code=400, detail="Too many tries, try again later")
    if requestx["ip"] != request.client.host:
        raise HTTPException(status_code=400, detail="IP address mismatch")
    if requestx["verif_code"] != code:
        cursor.execute(
            "UPDATE revoke_requests SET tries = %s WHERE phone_number = %s",
            (requestx["tries"] + 1, phone),
        )
        conn.commit()
        raise HTTPException(status_code=400, detail="Invalid verification code")

    cursor.execute(
        "INSERT INTO revoked_keys (phone_number, pubkey, time, ip) VALUES (%s, %s, NOW(), %s)",
        (phone, requestx["pubkey"], requestx["ip"]),
    )
    cursor.execute("DELETE FROM users WHERE phone_number = %s", (phone,))
    cursor.execute("DELETE FROM revoke_requests WHERE phone_number = %s", (phone,))
    conn.commit()

    return {"message": "Key revoked and user deleted"}


@router.get("/check", response_model=dict, )
async def check(public_key: str, db=Depends(get_db)):
    """
    Проверяет, отозван ли ключ
    :param public_key:
    :return: {"revoked": False, "message": "Key not revoked"} or {"revoked": True, "message": "Key revoked"}
    """
    cursor, conn = db

    cursor.execute("SELECT * FROM revoked_keys WHERE pubkey = %s", (public_key,))
    user = cursor.fetchone()
    if user is None:
        return {"revoked": False, "message": "Key not revoked"}
    else:
        return {"revoked": True, "message": "Key revoked"}

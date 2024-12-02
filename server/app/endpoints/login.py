import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from random import randint

from server.app.database import connection_pool, get_db
from server.app.telegram_gateway import TelegramGatewayAPI
router = APIRouter()

logger = logging.getLogger(__name__)
tg = TelegramGatewayAPI()

@router.get("/register")
async def register(phone_number: str, fio: str, public_key: str, request: Request, db=Depends(get_db)):
    cursor, conn = db
    verif_code = randint(100000, 999999)
    ip = request.client.host

    cursor.execute("SELECT * FROM user_register WHERE phone_number = %s", (phone_number,))
    user = cursor.fetchone()
    if user is not None:
        if user['time'].replace(tzinfo=timezone.utc) > datetime.now(timezone.utc) - timedelta(minutes=5):
            raise HTTPException(status_code=400, detail=f"Too many requests, try again later")
        else:
            cursor.execute("DELETE FROM user_register WHERE phone_number = %s", (phone_number,))
            conn.commit()

    cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone_number,))
    user = cursor.fetchone()
    if user is not None:
        raise HTTPException(status_code=400, detail="User already exists")

    resp = await tg.send_verification_message(phone_number, code=str(verif_code))
    if not resp['ok']:
        raise HTTPException(status_code=400, detail="Failed to send verification message")

    cursor.execute("INSERT INTO user_register (fio, phone_number, pubkey, ip, time, verif_code, request_id) "
        "VALUES (%s, %s, %s, %s, NOW(), %s, %s)", (fio, phone_number, public_key, ip, verif_code, resp['result']['request_id']))
    conn.commit()
    return {"message": "Verification code sent"}

@router.get("/verify")
async def verify(phone_number: str, code: str, request: Request, db=Depends(get_db)):
    cursor, conn = db
    cursor.execute("SELECT * FROM user_register WHERE phone_number = %s", (phone_number,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=400, detail="Register not found")

    if user['time'].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="Verification code expired")

    ip = request.client.host
    if user['ip'] != ip:
        raise HTTPException(status_code=400, detail="IP address mismatch")

    if user['tries'] >= 3:
        raise HTTPException(status_code=400, detail="Too many tries, try again later")

    if user['verif_code'] != code:
        cursor.execute("UPDATE user_register SET tries = %s WHERE phone_number = %s", (user['tries'] + 1, phone_number,))
        conn.commit()
        raise HTTPException(status_code=400, detail="Invalid verification code")

    cursor.execute("INSERT INTO users (fio, phone_number, pubkey, time_register) "
        "VALUES (%s, %s, %s, NOW())", (user['fio'], user['phone_number'], user['pubkey']))
    cursor.execute("DELETE FROM user_register WHERE phone_number = %s", (phone_number,))
    conn.commit()
    return {"message": "User registered"}
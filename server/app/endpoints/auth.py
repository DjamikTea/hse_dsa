import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from random import randint

# from crypto.dsa import GostDSA

from server.app.database import connection_pool, get_db
from server.app.telegram_gateway import TelegramGatewayAPI
import secrets

router = APIRouter()
logger = logging.getLogger(__name__)
tg = TelegramGatewayAPI()

def generate_bearer_token():
    return secrets.token_urlsafe(64)

def generate_trs():
    return {'rand': secrets.token_urlsafe(64), 'timestamp': datetime.now(timezone.utc).timestamp()}

@router.post("/register")
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

    token = generate_bearer_token()
    cursor.execute("INSERT INTO users (fio, phone_number, pubkey, time_register, token) "
        "VALUES (%s, %s, %s, NOW(), %s)", (user['fio'], user['phone_number'], user['pubkey'], token))
    cursor.execute("DELETE FROM user_register WHERE phone_number = %s", (phone_number,))
    conn.commit()
    return {"message": "User registered", "token": token}

@router.get("/get_auth")
async def get_auth(phone: str, db=Depends(get_db)):
    cursor, conn = db
    cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")
    cursor.execute("SELECT * FROM auth WHERE phone_number = %s", (phone,))
    auth = cursor.fetchone()
    if auth is not None:
        if auth['timestamp'].replace(tzinfo=timezone.utc) > datetime.now(timezone.utc) - timedelta(minutes=5):
            raise HTTPException(status_code=400, detail="Too many requests, try again later")
        else:
            cursor.execute("DELETE FROM auth WHERE phone_number = %s", (phone,))
            conn.commit()

    trs = generate_trs()
    cursor.execute("INSERT INTO auth (phone_number, trs, timestamp) VALUES (%s, %s, NOW())", (phone, str(trs)))
    conn.commit()
    return {"message": "TRS generated", "trs": trs}



@router.get("/auth")
async def auth(phone: str, signed_trs: str, db=Depends(get_db)):
    pass
    #TODO: Implement auth

    # cursor, conn = db
    # cursor.execute("SELECT * FROM auth WHERE phone_number = %s", (phone,))
    # auth = cursor.fetchone()
    # if auth is None:
    #     raise HTTPException(status_code=400, detail="Auth not found")
    # if auth['timestamp'].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(seconds=10):
    #     raise HTTPException(status_code=400, detail="Auth expired")
    #
    # cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
    # user = cursor.fetchone()
    # if user is None:
    #     raise HTTPException(status_code=400, detail="User not found")
    # pubkey = user['pubkey']
    # dsa = GostDSA
    #
    # if not dsa.check(signed_trs, auth['trs'], pubkey):
    #     raise HTTPException(status_code=400, detail="Invalid signature")
    #
    # cursor.execute("DELETE FROM auth WHERE phone_number = %s", (phone,))
    # conn.commit()
    # return {"message": "User authenticated"}
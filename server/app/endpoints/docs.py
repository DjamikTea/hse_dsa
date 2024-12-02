#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-2.
#  All rights reserved.
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from random import randint

from server.app.database import connection_pool, get_db
from server.app.telegram_gateway import TelegramGatewayAPI
router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/new_document")
async def new_document(name: str, db=Depends(get_db)):
    cursor, conn = db
    cursor.execute("INSERT INTO documents (name, created_at) VALUES (%s, NOW())", (name,))
    conn.commit()
    return {"message": "Document created"}
#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-2.
#  All rights reserved.
import hashlib
import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from mysql.connector import IntegrityError
from starlette.responses import FileResponse

from app.database import get_db, check_token
from utils.sign import check_document
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.put("/upload")
async def new_document(
    file: UploadFile = File(...),
    sha256: str = Header(None),
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    """
    Создает новый документ в базе данных
    :param sha256:
    :param file:
    :param authorization:
    :param db:
    :return: timeuuid файла
    """
    cursor, conn = db
    user = check_token(authorization, cursor)

    timeuuid = str(uuid.uuid1())
    file_name = file.filename
    file_format = file_name.split(".")[-1]
    file_location = os.path.join(UPLOAD_DIR, f"{timeuuid}.{file_format}")
    content = await file.read()
    sha256_file = hashlib.sha256(content).hexdigest()
    if sha256_file != sha256:
        raise HTTPException(
            status_code=400, detail=f"Hashes do not match: {sha256_file}"
        )

    with open(file_location, "wb") as f:
        f.write(content)

    try:
        cursor.execute(
            "INSERT INTO documents (timeuuid, path, filename, user_id, created, sha256) "
            "VALUES (%s, %s, %s, %s, NOW(), %s)",
            (timeuuid, file_location, file_name, user["id"], sha256),
        )
        conn.commit()
    except IntegrityError as e:
        logger.error(f"Error while uploading file: {e}")
        raise HTTPException(status_code=400, detail="File already exists")

    return {"timeuuid": timeuuid}


@router.post("/sign/{timeuuid}")
async def sign_document(
    timeuuid: str,
    signature: str = Header(None),
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    """
    Подписывает документ
    :param timeuuid:
    :param signature:
    :param authorization:
    :param db:
    :return: None
    """
    cursor, conn = db
    user = check_token(authorization, cursor)

    cursor.execute("SELECT * FROM documents WHERE timeuuid = %s", (timeuuid,))
    document = cursor.fetchone()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    cursor.execute("SELECT pubkey FROM root_key WHERE id = 1")
    root_pubkey = cursor.fetchone()

    user_pubkey = user["pubkey"]
    signaturex = json.loads(signature)

    if not check_document(
        signaturex, document["sha256"], user_pubkey, timeuuid, root_pubkey["pubkey"]
    ):
        raise HTTPException(status_code=400, detail="Invalid signature")

    cursor.execute(
        "UPDATE documents SET sign_verified = 1, sign = %s WHERE timeuuid = %s",
        (
            signature,
            timeuuid,
        ),
    )
    conn.commit()
    return {"status": "ok"}


@router.get("/download/{timeuuid}")
async def download_document(
    timeuuid: str, authorization: Optional[str] = Header(None), db=Depends(get_db)
):
    """
    Скачивает документ
    :param timeuuid:
    :param authorization:
    :param db:
    :return: файл
    """
    cursor, conn = db
    user = check_token(authorization, cursor)

    cursor.execute("SELECT * FROM documents WHERE timeuuid = %s", (timeuuid,))
    document = cursor.fetchone()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document["user_id"] != user["id"]:
        if document["can_access"]:
            if user["id"] in document["can_access"].split(" "):
                raise HTTPException(status_code=403, detail="Forbidden")
        else:
            raise HTTPException(status_code=403, detail="Forbidden")

    return FileResponse(document["path"])


@router.get("/list")
async def list_documents(
    authorization: Optional[str] = Header(None), db=Depends(get_db)
):
    """
    Возвращает список документов
    :param authorization:
    :param db:
    :return: список документов
    """
    cursor, conn = db
    user = check_token(authorization, cursor)

    cursor.execute("SELECT * FROM documents WHERE user_id = %s", (user["id"],))
    documents = cursor.fetchall()
    return {"documents": documents}


@router.post("/send/{timeuuid}")
async def send_document(
    timeuuid: str,
    phone: str = Header(None),
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    """
    Отправляет документ по номеру телефона
    :param timeuuid:
    :param phone:
    :param authorization:
    :param db:
    :return: None
    """
    cursor, conn = db
    user = check_token(authorization, cursor)

    cursor.execute("SELECT * FROM documents WHERE timeuuid = %s", (timeuuid,))
    document = cursor.fetchone()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    # send document to phone_number
    cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
    reciver = cursor.fetchone()
    if not reciver:
        raise HTTPException(status_code=404, detail="Reciver not registered")

    if document["can_access"]:
        recivers = document["can_access"].split(" ")
        recivers.append(reciver["id"])
        recivers = " ".join(recivers)
    else:
        recivers = reciver["id"]

    cursor.execute(
        "UPDATE documents SET can_access = %s WHERE timeuuid = %s",
        (
            recivers,
            timeuuid,
        ),
    )
    cursor.execute(
        "INSERT INTO new_docs_available (user_id, timeuuid, filename, created, sign, sha256) "
        "VALUES (%s, %s, %s, NOW(), %s, %s)",
        (
            reciver["id"],
            timeuuid,
            document["filename"],
            document["sign"],
            document["sha256"],
        ),
    )
    conn.commit()
    return {"message": f"Document sent to {phone}"}


@router.get("/available")
async def available_documents(
    authorization: Optional[str] = Header(None), db=Depends(get_db)
):
    """
    Возвращает список доступных документов
    :param authorization:
    :param db:
    :return: список документов
    """
    cursor, conn = db
    user = check_token(authorization, cursor)

    cursor.execute("SELECT * FROM new_docs_available WHERE user_id = %s", (user["id"],))
    documents = cursor.fetchall()
    return {"documents": documents}


@router.post("/accept/{timeuuid}")
async def accept_document(
    timeuuid: str, authorization: Optional[str] = Header(None), db=Depends(get_db)
):
    """
    Принимает документ и отмечает его полученным
    :param timeuuid:
    :param authorization:
    :param db:
    :return: None
    """
    cursor, conn = db
    user = check_token(authorization, cursor)

    cursor.execute(
        "SELECT * FROM new_docs_available WHERE timeuuid = %s AND user_id = %s",
        (timeuuid, user["id"]),
    )
    document = cursor.fetchone()
    if not document:
        raise HTTPException(status_code=404, detail="Not found")

    cursor.execute(
        "DELETE FROM new_docs_available WHERE timeuuid = %s AND user_id = %s",
        (timeuuid, user["id"]),
    )
    conn.commit()
    return {"message": "Document accepted"}

import asyncio
import hashlib
from http.client import responses
from importlib.metadata import files
from inspect import signature

from hsecrypto import GostDSA
from datetime import datetime, timezone
import os
import requests
import json
from alive_progress import alive_bar
from tabulate import tabulate

from hseclient.content import json_data, crypt, api, cglobal
from hseclient.content.cprint import p_error, p_success
from hseclient.content.database import Database
from hseclient.content.json_data import (
    write_token,
    write_phone_number,
    read_phone_number,
    write_root_pubkey,
)


def get_external_ip():
    try:
        response = requests.get("https://api.ipify.org")
        if response.status_code == 200:
            return response.text
        else:
            print(
                f"Error: Unable to fetch IP address. Status code: {response.status_code}"
            )
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def set_host():
    host = input("Введите адрес сервера: ")

    if host.startswith("http://"):
        host = host.replace("http://", "")

    if not host.startswith("https://"):
        host = "https://" + host

    if len(host.split(".")) == 1:
        p_error("Некорректный адрес сервера.")
        return set_host()

    if requests.get(host).status_code != 200:
        p_error("Сервер не доступен.")
        return set_host()

    with open(cglobal.host_file, "w") as file:
        json.dump({"host": host}, file, indent=4)

    return host


def generate_keys():
    dsa = GostDSA()
    privkey, pubkey = dsa.generate_key_pair()
    json_data.write_keys(privkey, pubkey)


def register():
    try:
        keys = json_data.read_keys()
        if keys["privkey"] is None or keys["pubkey"] is None:
            p_error("Ключи не найдены.")
            return False
        privkey = keys["privkey"]
        pubkey = keys["pubkey"]
    except FileNotFoundError:
        p_error("Ключи не найдены.")
        return False

    country = "RU"
    organization = input("Введите название организации: ")
    full_name = get_full_name()
    phone_number = get_phone_number()
    ip = get_external_ip()

    response, status = asyncio.run(api.register(phone_number, full_name, pubkey))
    if status != 200:
        if response.get("detail") == "User already exists":
            p_error("Пользователь с таким номером телефона уже зарегистрирован.")
            return False
        elif response.get("detail") == "Too many requests, try again later":
            print("Введите ранее отправленный.")
            return False
        else:
            p_error(f"{response.get('detail')}")
            return False

    sms_code = get_sms_code()

    try:
        csr = crypt.generate_csr(
            privkey, pubkey, country, organization, phone_number, ip, full_name
        )
    except Exception as e:
        p_error(f"Ошибка при генерации CSR: {e}")
        return False

    response, status = asyncio.run(api.verify(phone_number, sms_code, json.dumps(csr)))

    if status != 200:
        p_error(f"{response.get('detail')}")
        return False
    else:
        write_token(response.get("token"))
        write_phone_number(phone_number)
        cert = json.loads(response.get("cert"))
        json_data.write_cert(cert)
        url = json_data.read_host().split("//")[1]

        if crypt.check_csr_root(cert, url, None):
            write_root_pubkey(csr["client"]["public_key"])
            p_success("Регистрация прошла успешно.")
            return True
        else:
            p_error(
                "Внимание: Ошибка при проверке корневого сертификата. Используйте на свой страх и риск."
            )
            accept = input("Продолжить? (y/n): ")
            if accept.lower() == "y":
                p_success("Регистрация прошла успешно.")
                return True
            else:
                return False


def get_full_name() -> str:
    """Запрос ФИО."""
    full_name = input("Введите ФИО: ")
    if not full_name.strip():
        print("Ошибка: ФИО не может быть пустым.")
        return get_full_name()
    return full_name


def get_phone_number():
    """Запрос номера телефона."""
    phone_number = input("Введите номер телефона: ")
    if not phone_number.isdigit() or len(phone_number) != 11 or phone_number[0] != "7":
        print(
            "Ошибка: некорректный номер телефона. Формат: 11 цифр, без +, начинается с 7."
        )
        return get_phone_number()
    return phone_number


def get_sms_code():
    """Запрос кода из мессенджера."""
    sms_code = input("Введите последние 4 цифры из звонка: ")
    if not sms_code.isdigit() or len(sms_code) != 4:
        print("Ошибка: код должен состоять из 4 цифр.")
        return get_sms_code()
    return sms_code


def upload_file(file_path: str):
    """
    Загрузка файла на сервер.
    :param file_path: Путь к файлу.
    :return: ID файла or False
    """
    if not os.path.exists(file_path):
        p_error("Файл не найден.")
        return False

    sha256_file = hashlib.sha256(open(file_path, "rb").read()).hexdigest()

    response, status = asyncio.run(api.upload_file(file_path, sha256_file))
    if status != 200:
        p_error(f"При загрузке файла: {response.get('detail')}")
        return False
    else:
        timeuuid = response.get("timeuuid")
        p_success(f"Файл успешно загружен. ID файла: {timeuuid}")
        return timeuuid


def sign_document(timeuuid: str, file_path: str):
    """
    Подписывает документ и отправляет на сервер.
    :param timeuuid: ID документа.
    :param file_path: путь к файлу.
    """
    try:
        keys = json_data.read_keys()
        if keys["privkey"] is None or keys["pubkey"] is None:
            p_error("Ключи не найдены.")
            return False
        privkey = keys["privkey"]
        pubkey = keys["pubkey"]
    except FileNotFoundError:
        p_error("Ключи не найдены.")
        return False

    try:
        cert = json_data.read_cert()
    except FileNotFoundError:
        p_error("Сертификат не найден.")
        return False

    sha256_file = hashlib.sha256(open(file_path, "rb").read()).hexdigest()

    signature = json.dumps(crypt.sign_document(timeuuid, sha256_file, privkey, cert))
    response, status = asyncio.run(api.sign_document(timeuuid, signature))
    if status != 200:
        p_error(f"При подписи документа: {response.get('detail')}")
        return False
    else:
        p_success("Документ успешно подписан.")
        return True


def send_document(timeuuid: str, phone_number: str):
    """
    Загружает и подписывает документ.
    :param timeuuid: ID документа.
    :param phone_number: Номер телефона получателя.
    """
    response, status = asyncio.run(api.send_document(timeuuid, phone_number))
    if status != 200:
        p_error(f"При отправке документа: {response.get('detail')}")
        return False
    else:
        p_success("Документ успешно отправлен.")
        return True


def list_files():
    """
    Выводит список файлов пользователя.
    """
    response, status = asyncio.run(api.get_my_files())
    if status != 200:
        p_error(f"При получении списка файлов: {response.get('detail')}")
        return False
    else:
        documents = response["documents"]
        for i in range(len(documents)):
            documents[i] = {
                key: documents[i][key]
                for key in [
                    "timeuuid",
                    "filename",
                    "created",
                    "sha256",
                    "sign_verified",
                    "can_access",
                ]
            }
        headers = "keys"
        table = tabulate(documents, headers=headers, tablefmt="pretty")
        print(table)


def check_new_docs(db: Database):
    """
    Проверяет новые документы и добавляет в базу данных.
    :param db: База данных.
    """
    response, status = asyncio.run(api.get_available_docs())
    if status != 200:
        p_error(f"При получении новых документов: {response.get('detail')}")
        return False
    else:
        documents = response["documents"]
        docs_view = []
        for i in range(len(documents)):
            documents[i] = {
                key: documents[i][key]
                for key in [
                    "timeuuid",
                    "filename",
                    "created",
                    "sign",
                    "sha256",
                    "sender_phone",
                ]
            }
            docs_view.append(
                {
                    "timeuuid": documents[i]["timeuuid"],
                    "filename": documents[i]["filename"],
                    "created": documents[i]["created"],
                    "sender_phone": documents[i]["sender_phone"],
                }
            )
        headers = "keys"
        table = tabulate(docs_view, headers=headers, tablefmt="pretty")
        print(table)

        know_docs = db.query("SELECT timeuuid FROM docs_available;")

        ids = []
        for dcs in know_docs:
            ids.append(dcs[0])
        for document in documents:
            if document["timeuuid"] in ids:
                continue
            db.execute(
                "INSERT INTO docs_available (timeuuid, filename, created, sign, sha256, sender_phone) VALUES (?, ?, ?, ?, ?, ?);",
                document["timeuuid"],
                document["filename"],
                document["created"],
                document["sign"],
                document["sha256"],
                document["sender_phone"],
            )
        p_success("Документы успешно обновлены.")
        return True


def get_sender_docs(db: Database, timeuuid: str):
    """
    Скачивает файл по ID и проверяет подпись.
    :param db: База данных.
    :param timeuuid: ID файла.
    """
    file_path, status = asyncio.run(api.get_file(timeuuid))
    if status != 200:
        p_error(f"При скачивании файла: {file_path.get('detail')}")
        return False
    else:
        p_success(f"Файл успешно скачан: {file_path}")

    current_metadata = db.query(
        "SELECT * FROM docs_available WHERE timeuuid = ?;", timeuuid
    )
    if current_metadata is None:
        p_error("Ошибка: метаданные не найдены.")
        return False

    sha256_file = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
    if current_metadata[0][5] != sha256_file:
        p_error("Ошибка: хэш файла не совпадает.")
        return False

    signaturex = json.loads(current_metadata[0][4])
    pubkey = signaturex["cert"]["client"]["public_key"]

    revoke_ch, stat = asyncio.run(api.revoke_check(pubkey))

    if revoke_ch.get("revoked"):
        p_error("Отправитель отозван.")
        return False
    else:
        print("Ключ отправителя не отозван.")

    pubkey_know = db.query(
        "SELECT pubkey FROM known_users WHERE phone_number = ?;", current_metadata[0][6]
    )

    if not pubkey_know:
        print("Отправитель не найден в известных номерах.")
        engl_or_spanish = input("Хотите добавить его? (y/n): ")
        if engl_or_spanish.lower().strip() == "y":
            db.execute(
                "INSERT INTO known_users (phone_number, pubkey) VALUES (?, ?);",
                current_metadata[0][6],
                pubkey,
            )
            p_success("Отправитель добавлен.")
            pubkey_know = db.query(
                "SELECT pubkey FROM known_users WHERE phone_number = ?;",
                current_metadata[0][6],
            )
        else:
            p_error("Отправитель не добавлен.")
            return False

    result = crypt.check_document(
        signaturex,
        sha256_file,
        pubkey_know[0][0],
        json_data.read_host().split("//")[1],
        timeuuid,
        json_data.read_root_pubkey(),
        current_metadata[0][6],
    )
    if result:
        p_success("Подпись документа верна.")
        asyncio.run(api.accept_doc(timeuuid))
        return True
    else:
        p_error("Подпись документа неверна.")
        return False


def delete_file(timeuuid: str):
    """
    Удаляет документ из базы данных.
    :param db: База данных.
    :param timeuuid: ID документа.
    """
    respone, status = asyncio.run(api.delete_file(timeuuid))
    if status != 200:
        p_error(f"при удалении файла: {respone.get('detail')}")
        return False
    else:
        p_success("Файл успешно удален.")
        return True


def auth():
    response, status = asyncio.run(api.get_auth(read_phone_number()))
    if status != 200:
        p_error(f"При авторизации: {response.get('detail')}")
        return False

    try:
        keys = json_data.read_keys()
        if keys["privkey"] is None or keys["pubkey"] is None:
            p_error("Ключи не найдены.")
            return False
        privkey = keys["privkey"]
        pubkey = keys["pubkey"]
    except FileNotFoundError:
        p_error("Ключи не найдены.")
        return False

    crypto = GostDSA()

    trs = response.get("trs")
    signed_trs = crypto.sign(str(trs).encode(), private_key=privkey)

    response, status = asyncio.run(api.auth(read_phone_number(), signed_trs))
    if status != 200:
        p_error(f"При проверке подписи: {response.get('detail')}")
        return False
    else:
        token = response.get("token")
        write_token(token)
        p_success("Подпись верна.")
        return True


def revoke():
    response, status = asyncio.run(api.revoke(read_phone_number()))
    if status != 200:
        p_error(f"При отзыве ключа: {response.get('detail')}")
        return False

    sms = get_sms_code()

    response, status = asyncio.run(api.revoke_verify(read_phone_number(), sms))
    if status != 200:
        p_error(f"При проверке кода: {response.get('detail')}")
        return False
    else:
        p_success("Ключ успешно отозван и аккаунт удален.")
        return True

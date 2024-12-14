import hashlib

import aiohttp
from hseclient.content.json_data import read_host, read_token
from hseclient.content.cglobal import download_dir

async def register(number_phone: str, fio: str, pubkey: str):
    """
    Регистрация пользователя.
    :param number_phone: Номер телефона.
    :param fio: ФИО.
    :param pubkey: Публичный ключ.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{read_host()}/login/register",
            params={
                "phone_number": number_phone,
                "fio": fio,
                "public_key": pubkey,
            },
        ) as response:
            return await response.json(), response.status

async def verify(number_phone: str, sms_code: str, csr: str):
    """
    Проверка кода из СМС.
    :param number_phone: Номер телефона.
    :param sms_code: Код из СМС.
    :param csr: CSR в формате json.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{read_host()}/login/verify",
            params={
                "phone_number": number_phone,
                "code": sms_code,
                "csr": csr,
            },
        ) as response:
            return await response.json(), response.status

async def upload_file(file_path: str, sha256: str):
    """
    Загрузка файла.
    :param file_path: Путь к файлу.
    :param sha256: Хэш файла.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        token = read_token()
        form = aiohttp.FormData()
        form.add_field(
            "file", open(file_path, "rb"), filename=file_path.split("/")[-1]
        )

        async with session.put(
            f"{read_host()}/docs/upload",
            headers={"Authorization": f"{token}", "sha256": sha256},
            data=form,
        ) as response:
            return await response.json(), response.status

async def sign_document(timeuuid: str, signature: str):
    """
    Подписывает документ.
    :param timeuuid: timeuuid документа.
    :param signature: Подпись.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        token = read_token()
        async with session.post(
            f"{read_host()}/docs/sign/{timeuuid}",
            headers={"Authorization": f"{token}", "signature": signature},
        ) as response:
            return await response.json(), response.status

async def send_document(timeuuid: str, phone_number: str):
    """
    Отправка документа.
    :param timeuuid: timeuuid документа.
    :param phone_number: Номер телефона.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        token = read_token()
        async with session.post(
            f"{read_host()}/docs/send/{timeuuid}",
            headers={"Authorization": f"{token}", "phone": phone_number},
        ) as response:
            return await response.json(), response.status

async def get_my_files():
    """
    Получение списка файлов.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        token = read_token()
        async with session.get(
            f"{read_host()}/docs/list",
            headers={"Authorization": f"{token}"},
        ) as response:
            return await response.json(), response.status

async def delete_file(timeuuid: str):
    """
    Удаление файла.
    :param timeuuid: timeuuid файла.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        token = read_token()
        async with session.delete(
            f"{read_host()}/docs/delete/{timeuuid}",
            headers={"Authorization": f"{token}"},
        ) as response:
            return await response.json(), response.status

async def get_available_docs():
    """
    Получение доступных документов.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        token = read_token()
        async with session.get(
            f"{read_host()}/docs/available",
            headers={"Authorization": f"{token}"},
        ) as response:
            return await response.json(), response.status

async def accept_doc(timeuuid: str):
    """
    Принятие документа.
    :param timeuuid: timeuuid документа.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        token = read_token()
        async with session.post(
            f"{read_host()}/docs/accept/{timeuuid}",
            headers={"Authorization": f"{token}"},
        ) as response:
            return await response.json(), response.status

async def get_file(timeuuid: str):
    """
    Получение файла.
    :param timeuuid: timeuuid файла.
    :return: file_path, status
    """
    async with aiohttp.ClientSession() as session:
        token = read_token()
        async with session.get(
            f"{read_host()}/docs/download/{timeuuid}",
            headers={"Authorization": f"{token}"},
        ) as response:
            if response.status == 200:
                file_path = f"{download_dir}/{response.headers.get('filename')}"
                with open(file_path, "wb") as f:
                    f.write(await response.read())
                print("Download success")
                return file_path, response.status
            else:
                return await response.json(), response.status

async def revoke(phone_number: str):
    """
    Отзыв ключа и удаление аккаунта.
    :param phone_number: Номер телеф
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{read_host()}/revoke",
            params={"phone": phone_number},
        ) as response:
            return await response.json(), response.status

async def revoke_verify(phone_number: str, code: str):
    """
    Подтверждение отзыва ключа.
    :param code: Код из СМС.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{read_host()}/revoke/verify",
            params={"phone": phone_number, "code": code},
        ) as response:
            return await response.json(), response.status

async def revoke_check(pubkey: str):
    """
    Проверка отзыва ключа.
    :param pubkey: Публичный ключ.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{read_host()}/revoke/check",
            params={"public_key": pubkey},
        ) as response:
            return await response.json(), response.status

async def get_auth(phone_number: str):
    """
    Авторизация.
    :param phone_number: Номер телефона.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{read_host()}/login/get_auth",
            params={"phone": phone_number},
        ) as response:
            return await response.json(), response.status

async def auth(phone: str, signed_trs: str):
    """
    Проверка подписи.
    :param phone: Номер телефона.
    :param signed_trs: Подписаная транзакция.
    :return: JSON, status
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{read_host()}/login/auth",
            params={"phone": phone, "signed_trs": signed_trs},
        ) as response:
            return await response.json(), response.status
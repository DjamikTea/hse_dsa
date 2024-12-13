#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-1.
#  All rights reserved.

import os

import aiohttp


class TelegramGatewayAPI:
    def __init__(self, api_token: str = ""):
        """
        Инициализация класса с токеном API.

        :param api_token: Токен доступа к Telegram Gateway API.
        """
        if api_token:
            self.api_token = api_token
        else:
            self.api_token = os.getenv("TELEGRAM_GATEWAY_API_TOKEN", "")
        self.api_url = "https://gatewayapi.telegram.org/"

    async def send_verification_message(
        self,
        phone_number,
        code=None,
        code_length=6,
        sender_username=None,
        ttl=None,
        callback_url=None,
    ):
        """
        Отправка сообщения с кодом подтверждения.

        :param phone_number: Номер телефона получателя в формате E.164.
        :param code: Необязательно. Пользовательский код подтверждения (4-8 цифр).
        :param code_length: Длина кода, если генерируется Telegram (4-8).
        :param sender_username: Необязательно. Юзернейм канала, от имени которого отправляется сообщение.
        :param ttl: Необязательно. Время жизни сообщения в секундах (60-86400).
        :param callback_url: Необязательно. URL для получения отчетов о доставке.
        :return: Ответ API в формате JSON.
        """
        endpoint = "sendVerificationMessage"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "phone_number": phone_number,
            "code": code,
            "code_length": code_length,
            "sender_username": sender_username,
            "ttl": ttl,
            "callback_url": callback_url,
        }
        # Удаление ключей с None значениями
        payload = {k: v for k, v in payload.items() if v is not None}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}{endpoint}", json=payload, headers=headers
            ) as response:
                return await response.json()

    async def check_send_ability(self, phone_number):
        """
        Проверка возможности отправки сообщения на указанный номер.

        :param phone_number: Номер телефона в формате E.164.
        :return: Ответ API в формате JSON.
        """
        endpoint = "checkSendAbility"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {"phone_number": phone_number}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}{endpoint}", json=payload, headers=headers
            ) as response:
                return await response.json()

    async def check_verification_status(self, request_id, code=None):
        """
        Асинхронная проверка статуса отправленного сообщения и валидация кода.

        :param request_id: Уникальный идентификатор запроса.
        :param code: Необязательно. Код, введенный пользователем.
        :return: Ответ API в формате JSON.
        """
        endpoint = "checkVerificationStatus"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {"request_id": request_id, "code": code}
        # Удаление ключей с None значениями
        payload = {k: v for k, v in payload.items() if v is not None}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}{endpoint}", json=payload, headers=headers
            ) as response:
                return await response.json()

    async def revoke_verification_message(self, request_id):
        """
        Асинхронный отзыв ранее отправленного сообщения с кодом подтверждения.

        :param request_id: Уникальный идентификатор запроса.
        :return: Ответ API в формате JSON.
        """
        endpoint = "revokeVerificationMessage"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {"request_id": request_id}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}{endpoint}", json=payload, headers=headers
            ) as response:
                return await response.json()


def mock_http(mocked_aiohttp, test_phone_number):
    mocked_aiohttp.post(
        "https://gatewayapi.telegram.org/sendVerificationMessage",
        payload={
            "ok": True,
            "result": {
                "request_id": "345452344",
                "phone_number": test_phone_number,
                "request_cost": 0,
                "remaining_balance": 0,
                "delivery_status": {"status": "sent", "updated_at": 1733119413},
            },
        },  # Ответ, который вернет мок
    )

    mocked_aiohttp.post(
        "https://gatewayapi.telegram.org/checkSendAbility",
        payload={
            "ok": True,
            "result": {
                "request_id": "345452344",
                "phone_number": test_phone_number,
                "request_cost": 0,
                "remaining_balance": 0,
            },
        },  # Ответ, который вернет мок
    )

    mocked_aiohttp.post(
        "https://gatewayapi.telegram.org/checkVerificationStatus",
        payload={
            "ok": True,
            "result": {
                "request_id": "345452344",
                "phone_number": test_phone_number,
                "request_cost": 0,
                "delivery_status": {"status": "sent", "updated_at": 1733119413},
            },
        },
    )

    mocked_aiohttp.post(
        "https://gatewayapi.telegram.org/revokeVerificationMessage",
        payload={"ok": True, "result": True},
    )

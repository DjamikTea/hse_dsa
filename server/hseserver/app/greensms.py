import os
import aiohttp


class Otp:
    def __init__(self):
        self.cred = {
            "user": os.getenv("GREENSMS_USER", ""),
            "pass": os.getenv("GREENSMS_PASSWD", ""),
        }
        self.token = os.getenv("GREENSMS_TOKEN", "")

    async def authorize(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api3.greensms.ru/account/token", json=self.cred
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to authorize, {await response.text()}")
                self.token = (await response.json())["access_token"]

    async def send_otp(self, phone_number):
        url = "https://api3.greensms.ru/call/send"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "to": phone_number,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to send OTP, {await response.text()}")
                return (await response.json())["code"]

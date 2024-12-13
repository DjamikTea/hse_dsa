import aiohttp
from hseclient.content.json_data import read_host

async def register(number_phone, fio, pubkey):
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

async def verify(number_phone, sms_code, csr):
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
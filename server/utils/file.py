import hashlib
import json

from utils.sign import sign_document, check_document

import aiohttp
import asyncio


SERVER_URL = "http://127.0.0.1:8000"
TOKEN = "vE29ulftbYSopANCflTiVzpOXSA3miUjnwkj2_WgmAua-c5LnDj7t2tcoV-G_P3Eqo2Y0vrGdl6erbOb7JscZA"
priv_key = "7233096205a1014b9c14a334e0b608e6a1fd47abc126568ec862151c43fbd161"
pub_key = "022439d6800c32a3e1522248c933e517b5c7a88d09f30600473fabbf2438302bc2"
cert = {"client": {"public_key": "022439d6800c32a3e1522248c933e517b5c7a88d09f30600473fabbf2438302bc2", "country": "RU", "organization": "DjamikTea", "phone_number": "79637108400", "fio": "Dzhamal Dzhamalovich", "ip": "testclient", "date_generation": "2024-12-06T21:08:31.696347+00:00"}, "client_sign_time": "2024-12-06T21:08:31.696360+00:00", "client_sign": "6344ea3e20bfe32d973271133076c52cdd60e100843155dc861f495dc39c056b54058c04af8327def00d51ae366fc91805846877eadbf164a751b42bb283c0c2", "root": {"root_ca": {"country": "RU", "organization": "DjamikTea", "email": "abakarovda@edu.hse.ru", "public_key": "0352e5969fb40c331c0bb85482baa99506a53dff1d693b8587004f4f68bade8869", "domain": "secr.gopass.dev", "date_generation": "2024-12-06T21:08:29.896747+00:00"}, "root_sign": "7fd4750c8cdc2dc3b9c66b594820091e2b575ec86fbb9fab0b7714c5c4a8c847330f154f58348899a9c022fbf511fe07e88b2b17f645ac874b1670713fdaf66f"}, "root_sign_time": "2024-12-06T21:08:33.040696+00:00", "root_sign": "5a2ae83a58b6d8855a0ec31b3d6fa2c5efd8aa05371b59311d17f9a31a8b106e5141de280815a24cbe06f2bd96db1c2ff36287785360f42f5a284573883ad051"}
timeuuid_file = '45979f34-b418-11ef-a9bb-422d3b16eee0'
sha256_file = 'fe92e88c98c98488673caabe5bc3a89609437628a6d69e8494f027d56e5ae7b7'

async def upload_file(filepath):
    global timeuuid_file, sha256_file
    url = f"{SERVER_URL}/docs/upload"
    sha256_file = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
    headers = {
        "Authorization": TOKEN,
        "sha256": sha256_file
    }
    form = aiohttp.FormData()
    form.add_field('file',
                   open(filepath, 'rb'),
                   filename=filepath)

    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, data=form) as resp:
            if resp.status == 200:
                json_response = await resp.json()
                print("Upload success:", json_response)
                timeuuid_file = json_response["timeuuid"]
            else:
                text = await resp.text()
                print("Upload failed:", resp.status, text)

async def sign_file(timeuuid):
    url = f"{SERVER_URL}/docs/sign/{timeuuid}"

    sign = sign_document(timeuuid_file, sha256_file, priv_key, cert)

    headers = {
        "Authorization": TOKEN,
        "timeuuid": timeuuid,
        "signature": json.dumps(sign)
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            if resp.status == 200:
                print("Sign success")
            else:
                text = await resp.text()
                print("Sign failed:", resp.status, text)

async def download_file(timeuuid):
    url = f"{SERVER_URL}/docs/download/{timeuuid}"
    headers = {
        "Authorization": TOKEN
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                with open(f"{timeuuid}.txt", "wb") as f:
                    f.write(await resp.read())
                print("Download success")
            else:
                text = await resp.text()
                print("Download failed:", resp.status, text)

if __name__ == "__main__":
    # asyncio.run(upload_file("test.txt"))
    # asyncio.run(sign_file(timeuuid_file))
    asyncio.run(download_file(timeuuid_file))
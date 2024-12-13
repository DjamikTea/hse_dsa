from hsecrypto import GostDSA

from hseclient.content import cglobal
import json
from hseclient.content.cprint import p_error, p_success


def read_host() -> str:
    with open(cglobal.host_file) as f:
        return json.load(f).get("host")


def write_keys(private_key, public_key) -> None:
    with open(cglobal.keys_file, "w") as f:
        json.dump({"private_key": private_key,
                   "public_key": public_key,
                   "algorithm": "GostDSA"}, f, indent=4)
    p_success("Ключи сохранены")

def write_root_pubkey(pubkey: str) -> None:
    with open(cglobal.root_pubkey_file, "w") as f:
        json.dump({"pubkey": pubkey}, f, indent=4)
    p_success("Публичный ключ корневого центра сохранен")

def read_root_pubkey() -> str:
    with open(cglobal.root_pubkey_file) as f:
        return json.load(f).get("pubkey")

def read_keys() -> dict:
    with open(cglobal.keys_file) as f:
        data = json.load(f)
        return {"privkey": data.get("private_key"),
                "pubkey": data.get("public_key")}

def write_token(token: str) -> None:
    with open(cglobal.token_file, "w") as f:
        json.dump({"token": token}, f, indent=4)
    p_success("Токен сохранен")

def read_token() -> str:
    with open(cglobal.token_file) as f:
        return json.load(f).get("token")

def write_cert(cert: dict) -> None:
    with open(cglobal.cert_file, "w") as f:
        json.dump(cert, f, indent=4)
    p_success("Сертификат сохранен")

def read_cert() -> dict:
    with open(cglobal.cert_file) as f:
        return json.load(f)

def write_phone_number(phone_number: str) -> None:
    with open(cglobal.phone_number_file, "w") as f:
        json.dump({"phone_number": phone_number}, f, indent=4)
    p_success("Номер телефона сохранен")

def read_phone_number() -> str:
    with open(cglobal.phone_number_file) as f:
        return json.load(f).get("phone_number")
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


def read_keys() -> dict:
    with open(cglobal.keys_file) as f:
        data = json.load(f)
        return {"privkey": data.get("private_key"),
                "pubkey": data.get("public_key")}

from datetime import datetime, timezone
from hsecrypto import GostDSA
from .csr import check_csr_root


def sign_document(
    timeuuid: str, sha256: str, private_key: str, certificate: str
) -> dict:
    """
    Подписывает документ
    :param timeuuid: timeuuid документа
    :param private_key: приватный ключ
    :param certificate: сертификат
    :param sha256: sha256 файла
    :return: подписанный документ
    """
    signature = {
        "timeuuid": timeuuid,
        "sha256": sha256,
        "cert": certificate,
        "sign_time": datetime.now(timezone.utc).isoformat(),
    }
    crypto = GostDSA()
    signature["sign"] = crypto.sign(str(signature).encode(), private_key)
    return signature


def check_document(
    signature: dict,
    sha256: str,
    pubkey: str,
    timeuuid: str = None,
    server_pubkey: str = None,
) -> bool:
    """
    Проверяет подпись документа
    :param signature: подпись документа
    :param sha256: sha256 файла
    :param pubkey: публичный ключ
    :param timeuuid: timeuuid документа
    :param server_pubkey: публичный ключ сервера
    :return: результат проверки
    """
    crypto = GostDSA()
    sigx = {
        "timeuuid": signature["timeuuid"],
        "sha256": signature["sha256"],
        "cert": signature["cert"],
        "sign_time": signature["sign_time"],
    }
    if sha256 != signature["sha256"]:
        return False
    if pubkey != signature["cert"]["client"]["public_key"]:
        return False
    if timeuuid:
        if timeuuid != signature["timeuuid"]:
            return False
    if not check_csr_root(signature["cert"], "secr.gopass.dev", server_pubkey):
        return False
    return crypto.check(signature["sign"], str(sigx).encode(), pubkey)

from hsecrypto import GostDSA
from datetime import datetime, timezone


def generate_csr(
    private_key: str,
    public_key: str,
    country: str,
    organization: str,
    phone_number: str,
    ip: str,
    fio: str,
) -> dict:
    """
    Генерация запроса на подписание сертификата (CSR).
    :param private_key: Приватный ключ.
    :param public_key: Публичный ключ.
    :param country: Двухбуквенный код страны (ISO 3166-1 alpha-2).
    :param organization: Название организации.
    :param phone_number: Номер телефона.
    :param ip: IP-адрес.
    :param fio: ФИО.
    :return: CSR в формате json.
    """
    csr = {
        "client": {
            "public_key": public_key,
            "country": country,
            "organization": organization,
            "phone_number": phone_number,
            "fio": fio,
            "ip": ip,
            "date_generation": datetime.now(timezone.utc).isoformat(),
        },
        "client_sign_time": datetime.now(timezone.utc).isoformat(),
    }
    crypto = GostDSA()
    csr["client_sign"] = crypto.sign(str(csr).encode(), private_key)
    return csr

def check_csr_root(
    csr: dict, server_domain: str | None = None, server_pubkey: str | None = None
) -> bool:
    """
    Проверка подписи корневого центра CSR.

    :param csr: CSR в формате json.
    :param server_domain: Домен сервера.
    :param server_pubkey: Публичный ключ сервера.
    :return: Результат проверки.
    """
    crypto = GostDSA()
    root_ca = {
        "root_ca": csr["root"]["root_ca"],
    }
    if server_pubkey:
        if csr["root"]["root_ca"]["public_key"] != server_pubkey:
            return False
    if crypto.check(
        csr["root"]["root_sign"],
        str(root_ca).encode(),
        csr["root"]["root_ca"]["public_key"],
    ):
        if server_domain:
            if csr["root"]["root_ca"]["domain"] != server_domain:
                return False
    else:
        return False

    csrx = {
        "client": csr["client"],
        "client_sign_time": csr["client_sign_time"],
        "client_sign": csr["client_sign"],
        "root": csr["root"],
        "root_sign_time": csr["root_sign_time"],
    }
    return crypto.check(
        csr["root_sign"], str(csrx).encode(), csr["root"]["root_ca"]["public_key"]
    )



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
    server_domain: str,
    timeuuid: str = None,
    server_pubkey: str = None,
    client_phone_number: str = None,
) -> bool:
    """
    Проверяет подпись документа
    :param signature: подпись документа
    :param sha256: sha256 файла
    :param pubkey: публичный ключ
    :param server_domain: домен сервера
    :param timeuuid: timeuuid документа
    :param server_pubkey: публичный ключ сервера
    :param client_phone_number: номер телефона клиента
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
        return "sha256 not equal"
    if pubkey != signature["cert"]["client"]["public_key"]:
        return "pubkey not equal"
    if timeuuid:
        if timeuuid != signature["timeuuid"]:
            return "timeuuid not equal"
    if not check_csr_root(signature["cert"], server_domain, server_pubkey):
        return "check_csr_root failed"
    if not client_phone_number:
        if client_phone_number != signature["cert"]["client"]["phone_number"]:
            return "phone number not equal"
    return crypto.check(signature["sign"], str(sigx).encode(), pubkey)

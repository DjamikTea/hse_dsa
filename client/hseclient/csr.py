from datetime import datetime, timezone
from hsecrypto import GostDSA
import json


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
    Генерация запроса на сертификат (CSR).

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
<<<<<<< HEAD:client/hseclient/csr.py
    csr.get["client_sign"] = crypto.sign(str(csr).encode(), private_key)
=======
    csr.get("client_sign") = crypto.sign(str(csr).encode(), private_key)
>>>>>>> 4de22ca (cli for generate pair key , csr and registration):client/csr.py
    return csr


def check_csr_client(
<<<<<<< HEAD:client/hseclient/csr.py
    csr: dict, phone_number: str | None = None, ip: str | None = None
) -> bool:
=======
        csr: dict, 
        phone_number: str | None = None, 
        ip: str | None = None) -> bool:
>>>>>>> 4de22ca (cli for generate pair key , csr and registration):client/csr.py
    """
    Проверка подписи клиента CSR.
    :param csr: CSR в формате json.
    :param phone_number: Номер телефона.
    :param ip: IP-адрес.
    :return: Результат проверки.
    """
    crypto = GostDSA()
<<<<<<< HEAD:client/hseclient/csr.py
    csrx = {
        "client": csr.get("client"),
        "client_sign_time": csr.get("client_sign_time"),
    }
=======
    csrx = {"client": csr.get("client"), "client_sign_time": csr.get("client_sign_time")}
>>>>>>> 4de22ca (cli for generate pair key , csr and registration):client/csr.py

    if phone_number:
        if csr.get("client")("phone_number") != phone_number:
            return False
    if ip:
        if csr.get("client")("ip") != ip:
            return False
    return crypto.check(
        csr.get("client_sign"), str(csrx).encode(), csr.get("client")("public_key")
    )


def sign_csr(
    csr: dict,
    root_private_key: str,
    root_ca: dict,
    phone_number: str | None = None,
    ip: str | None = None,
) -> dict:
    """
    Проверка и подпись CSR.

    :param csr: CSR в формате json.
    :param root_private_key: Приватный ключ.
    :param root_ca: Сертификат корневого центра.
    :param phone_number: Номер телефона.
    :param ip: IP-адрес.
    :return: Подписанный CSR.
    """
    crypto = GostDSA()
    csrx = csr
    if check_csr_client(csr, phone_number, ip):
        csrx["root"] = root_ca
        csrx["root_sign_time"] = datetime.now(timezone.utc).isoformat()
        csrx["root_sign"] = crypto.sign(str(csrx).encode(), root_private_key)
        return csrx
    else:
        raise ValueError("CSR client signature is invalid")


def check_csr_root(
<<<<<<< HEAD:client/hseclient/csr.py
    csr: dict, server_domain: str | None = None, server_pubkey: str | None = None
=======
    csr: dict, 
    server_domain: str | None = None, 
    server_pubkey: str | None = None
>>>>>>> 4de22ca (cli for generate pair key , csr and registration):client/csr.py
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
        "root_ca": csr.get("root")("root_ca"),
    }
    if server_pubkey:
        if csr.get("root")("root_ca")("public_key") != server_pubkey:
            return False
    if crypto.check(
        csr.get("root")("root_sign"),
        str(root_ca).encode(),
        csr.get("root")("root_ca")("public_key"),
    ):
        if server_domain:
            if csr.get("root")("root_ca")("domain") != server_domain:
                return False
    else:
        return False

    csrx = {
        "client": csr.get("client"),
        "client_sign_time": csr.get("client_sign_time"),
        "client_sign": csr.get("client_sign"),
        "root": csr.get("root"),
        "root_sign_time": csr.get("root_sign_time"),
    }
    return crypto.check(
<<<<<<< HEAD:client/hseclient/csr.py
        csr.get("root_sign"),
        str(csrx).encode(),
        csr.get("root")("root_ca")("public_key"),
    )
=======
        csr.get("root_sign"), str(csrx).encode(), csr.get("root")("root_ca")("public_key")
    )
>>>>>>> 4de22ca (cli for generate pair key , csr and registration):client/csr.py

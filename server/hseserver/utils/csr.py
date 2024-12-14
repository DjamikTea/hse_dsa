#  Copyright (c) 2024 DjamikTea.
#  Created by Dzhamal on 2024-12-5.
#  All rights reserved.
from datetime import datetime, timezone
from hsecrypto import GostDSA


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
    csr["client_sign"] = crypto.sign(str(csr).encode(), private_key)
    return csr


def check_csr_client(
    csr: dict, phone_number: str | None = None, ip: str | None = None
) -> bool:
    """
    Проверка подписи клиента CSR.
    :param csr: CSR в формате json.
    :param phone_number: Номер телефона.
    :param ip: IP-адрес.
    :return: Результат проверки.
    """
    crypto = GostDSA()
    csrx = {"client": csr["client"], "client_sign_time": csr["client_sign_time"]}

    if phone_number:
        if csr["client"]["phone_number"] != phone_number:
            return False
    if ip:
        if csr["client"]["ip"] != ip:
            return False
    return crypto.check(
        csr["client_sign"], str(csrx).encode(), csr["client"]["public_key"]
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


# if __name__ == '__main__':
#     # ----- prepare root_ca -----
#     crypto2 = GostDSA()
#     privkeyroot, pubkeyroot = crypto2.generate_key_pair()
#     root_ca = {
#         "root_ca": {
#             "country": "RU",
#             "organization": "DjamikTea",
#             "email": "abakarovda@edu.hse.ru",
#             "public_key": pubkeyroot,
#             "domain": "secr.gopass.dev",
#             "date_generation": datetime.now(timezone.utc).isoformat()
#         }
#     }
#     cert_sign = crypto2.sign(str(root_ca).encode(), privkeyroot)
#     root_ca['root_sign'] = cert_sign
#     # ----- end prepare root_ca -----
#
#     # ----- prepare csr (client) -----
#     crypto = GostDSA()
#     privkey, pubkey = crypto.generate_key_pair()
#
#     csr = generate_csr(privkey, pubkey, "RU", "DjamikTea", "+79161234567", "0.0.0.0", "Dzhamal Dzhamalovich")
#     print(csr)
#     # ----- end prepare csr (client) -----
#
#     # ----- sign csr (server side) -----
#     signed_csr = sign_csr(csr, privkeyroot, root_ca)
#     print(signed_csr)
#     # ----- end sign csr (server side) -----
#
#     # ----- check csr (client side) -----
#     print(check_csr_root(signed_csr, "secr.gopass.dev", pubkeyroot))
#     # ----- end check csr (client side) -----
#     signed_csr_str = json.dumps(signed_csr)
#     signed_csr = json.loads(signed_csr_str)

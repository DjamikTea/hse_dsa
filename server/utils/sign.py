from datetime import datetime, timezone
from hsecrypto import GostDSA
from .csr import check_csr_root

def sign_document(timeuuid: str, sha256: str, private_key: str, certificate: str) -> dict:
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
        "sign_time": datetime.now(timezone.utc).isoformat()
    }
    crypto = GostDSA()
    signature['sign'] = crypto.sign(str(signature).encode(), private_key)
    return signature

def check_document(signature: dict, sha256: str, pubkey: str, timeuuid: str = None, server_pubkey: str = None) -> bool:
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
        "timeuuid": signature['timeuuid'],
        "sha256": signature['sha256'],
        "cert": signature['cert'],
        "sign_time": signature['sign_time']
    }
    if sha256 != signature['sha256']:
        return False
    if pubkey != signature['cert']['client']['public_key']:
        return False
    if timeuuid:
        if timeuuid != signature['timeuuid']:
            return False
    if not check_csr_root(signature['cert'], "secr.gopass.dev", server_pubkey):
        return False
    return crypto.check(signature['sign'], str(sigx).encode(), pubkey)

# if __name__ == '__main__':
#     from utils.csr import generate_csr, sign_csr
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
#
#     # ----- prepare document -----
#     sign = sign_document("timedfuuid", "shafdff256", privkey, signed_csr)
#     print(sign)
#     # ----- end prepare document -----
#     print(check_document(sign, "shafdff256", pubkey, "timedfuuid", pubkeyroot))
#     # ----- end check document -----

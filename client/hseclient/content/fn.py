import asyncio

from hsecrypto import GostDSA
from datetime import datetime, timezone
import os
import requests
import json
from alive_progress import alive_bar
from hseclient.content import json_data, crypt, api, cglobal
from hseclient.content.cprint import p_error, p_success

def get_external_ip():
    try:
        response = requests.get("https://api.ipify.org")
        if response.status_code == 200:
            return response.text
        else:
            print(
                f"Error: Unable to fetch IP address. Status code: {response.status_code}"
            )
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def set_host():
            host = input("Введите адрес сервера: ")

            if host.startswith("http://"):
                host = host.replace("http://", "")

            if not host.startswith("https://"):
                host = "https://" + host

            if len(host.split(".")) == 1:
                p_error("Некорректный адрес сервера.")
                return set_host()

            if requests.get(host).status_code != 200:
                p_error("Сервер не доступен.")
                return set_host()

            with open(cglobal.host_file, "w") as file:
                json.dump({"host": host}, file, indent=4)

            return host

def generate_keys():
    dsa = GostDSA()
    privkey, pubkey = dsa.generate_key_pair()
    json_data.write_keys(privkey, pubkey)

def register():

    country = "RU"
    # organization = input("Введите название организации: ")
    # full_name = get_full_name()
    # phone_number = get_phone_number()
    organization = "HSE"
    full_name = "Ivanov Ivan Ivanovich"
    phone_number = "79637108400"

    # items = range(100)
    # bar = alive_bar(len(items))

    try:
        keys = json_data.read_keys()
        if keys["privkey"] is None or keys["pubkey"] is None:
            p_error("Ключи не найдены.")
            return False
        privkey = keys["privkey"]
        pubkey = keys["pubkey"]
    except FileNotFoundError:
        p_error("Ключи не найдены.")
        return False

    ip = get_external_ip()


    response, status = asyncio.run(api.register(phone_number, full_name, pubkey))
    if status != 200:
        if response.get("detail") == "User already exists":
            p_error("Пользователь с таким номером телефона уже зарегистрирован.")
            return False
        elif response.get("detail") == "Too many requests, try again later":
            print("Введите ранее отправленный.")
            return False
        else:
            return False

    sms_code = get_sms_code()

    try:
        csr = crypt.generate_csr(
            privkey, pubkey, country, organization, phone_number, ip, full_name
        )
    except Exception as e:
        p_error(f"Ошибка при генерации CSR: {e}")
        return False
    response, status = asyncio.run(api.verify(phone_number, sms_code, json.dumps(csr)))

    if status != 200:
        p_error(f"{response.get('detail')}")
        return False
    else:
        breakpoint()
        p_success("Регистрация прошла успешно.")
        return True

# def read_private_key(file_path):
#     """
#     Считывает приватный ключ из файла и возвращает его в виде строки.
#     """
#     try:
#         with open(file_path, "r") as key_file:
#             private_key = key_file.read().strip()
#         return private_key
#     except FileNotFoundError:
#         print(f"Файл приватного ключа не найден: {file_path}")
#         return None
#     except Exception as e:
#         print(f"Ошибка при чтении приватного ключа: {e}")
#         return None
#
# def _load_keys(self):
#     """Автоматическая загрузка ключей из директории."""
#     if not os.path.exists(self.keys_directory):
#         print(f"Директория с ключами '{self.keys_directory}' не найдена.")
#         return False
#
#     files = [
#         f for f in os.listdir(self.keys_directory) if f.endswith("public_key.pem")
#     ]
#     if not files:
#         print(f"В директории '{self.keys_directory}' нет файлов ключей.")
#         return False
#
#     try:
#         file_path = os.path.join(self.keys_directory, files[0])
#         with open(file_path, "r") as f:
#             self.keys = f.read().strip()
#         self.data["file_path"] = file_path
#         return True
#     except Exception as e:
#         print(f"Ошибка при загрузке ключей: {e}")
#         return False
#
#
# def _get_file_path(self):
#     """Запрос пути к файлу ключей и загрузка ключей."""
#     file_path = input("Введите путь к файлу ключей: ")
#     try:
#         with open(file_path, "r") as f:
#             self.keys = f.read().strip()
#         self.data["file_path"] = file_path
#         print("Ключи успешно загружены.")
#         self._get_full_name()
#     except FileNotFoundError:
#         print("Ошибка: файл не найден. Попробуйте еще раз.")
#         self._get_file_path()
#     except Exception as e:
#         print(f"Ошибка при чтении файла: {e}")
#         self._get_file_path()


def get_full_name() -> str:
    """Запрос ФИО."""
    full_name = input("Введите ФИО: ")
    if not full_name.strip():
        print("Ошибка: ФИО не может быть пустым.")
        return get_full_name()
    return full_name


def get_phone_number():
    """Запрос номера телефона."""
    phone_number = input("Введите номер телефона: ")
    if (
            not phone_number.isdigit()
            or len(phone_number) != 11
            or phone_number[0] != "7"
    ):
        print(
            "Ошибка: некорректный номер телефона. Формат: 11 цифр, без +, начинается с 7."
        )
        return get_phone_number()
    return phone_number


# def _send_registration_data(self, phone_number, fio, public_key):
#     """Отправка регистрационных данных на сервер."""
#     url = f"{self.url}/login/register"
#     params = {"phone_number": phone_number, "fio": fio, "public_key": public_key}
#
#     try:
#         response = requests.post(url, params=params)
#         if response.status_code == 200:
#             print("Регистрация прошла успешно!")
#             print(response.json())
#             self._get_sms_code()
#         elif response.status_code == 400:
#             print(response.json())
#             self._get_sms_code()
#         else:
#             print(f"Ошибка при регистрации: {response.status_code}")
#             print(response.json())
#     except requests.exceptions.RequestException as e:
#         print(f"Ошибка при запросе: {e}")
#
#
def get_sms_code():
    """Запрос кода из мессенджера."""
    sms_code = input("Введите код из Telegram: ")
    if not sms_code.isdigit() or len(sms_code) != 6:
        print("Ошибка: код должен состоять из 6 цифр.")
        return get_sms_code()
    return sms_code
#
#
# def _send_verification_code(self, phone_number, code):
#     """Функция отправки кода для верификации на сервер."""
#     url = f"{self.url}/login/verify"
#     params = {"phone_number": phone_number, "code": code}
#     csr_file = os.path.join(self.keys_directory, "csr.json")
#     try:
#         with open(csr_file, "r") as file:
#             csr = json.load(file)
#         params["csr"] = json.dumps(csr)
#     except FileNotFoundError:
#         print(f"Ошибка: файл {csr_file} не найден.")
#         return
#     except json.JSONDecodeError:
#         print(f"Ошибка: не удалось декодировать JSON из {csr_file}.")
#         return
#
#     try:
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             print("Код верификации успешно отправлен!")
#             response_data = response.json()
#             token = response_data.get("token")
#             signed_csr = response_data.get("cert")
#
#             if token and signed_csr:
#                 self.token = token
#
#                 output_file = os.path.join(
#                     self.keys_directory, "registration_data.json"
#                 )
#                 with open(output_file, "w") as file:
#                     json.dump(
#                         {"token": token, "cert": signed_csr},
#                         file,
#                         indent=4,
#                     )
#
#                 print(f"Токен и сертификат успешно сохранены в файл: {output_file}")
#             else:
#                 print(
#                     "Ответ не содержит необходимых данных (токен или сертификат)."
#                 )
#
#             self._complete_registration()
#         else:
#             print(f"Ошибка при отправке кода: {response.status_code}")
#             print(response.json())
#     except requests.exceptions.RequestException as e:
#         print(f"Ошибка при запросе: {e}")
#
#
# def _complete_registration(self):
#     """Вывод результатов регистрации."""
#     print("\nРегистрация завершена!")
#     print(f"ФИО: {self.data['full_name']}")
#     print(f"Номер телефона: {self.data['phone_number']}")
#     print(f"Код из Telegram: {self.data['sms_code']}")
#     print(f"Файл ключей: {self.data['file_path']}")
#     print(f"Ключи: {self.keys}")
#
#
# def _load_token(self):
#     """Загрузка токена из файла."""
#     token_file = "keys/auth_token.json"
#     try:
#         with open(token_file, "r") as file:
#             data = json.load(file)
#             self.token = data.get("token")
#             if self.token:
#                 print("Токен успешно загружен.")
#             else:
#                 print("Токен отсутствует в файле.")
#     except FileNotFoundError:
#         print(f"Файл токена '{token_file}' не найден.")
#         self.token = None
#     except json.JSONDecodeError:
#         print(f"Ошибка: не удалось декодировать JSON из файла '{token_file}'.")
#         self.token = None
#     except Exception as e:
#         print(f"Ошибка при загрузке токена: {e}")
#         self.token = None
#
#     def _send_revoke_request(self, phone_number):
#         """
#         Отправляет запрос на удаление пользователя.
#         """
#         url = f"{self.url}/revoke"
#         params = {"phone": phone_number}
#
#         try:
#             response = requests.post(url, params=params)
#             if response.status_code == 200:
#                 print("Код для подтверждения удаления отправлен на указанный номер.")
#                 self._confirm_revoke(phone_number)
#             else:
#                 print(
#                     f"Ошибка при запросе на удаление пользователя: {response.status_code}"
#                 )
#                 print(response.json())
#         except requests.exceptions.RequestException as e:
#             print(f"Ошибка при запросе: {e}")
#
#     def _confirm_revoke(self, phone_number):
#         """
#         Подтверждает удаление пользователя.
#         """
#         code = input("Введите код подтверждения удаления: ").strip()
#
#         url = f"{self.url}/revoke/verify"
#         params = {"phone": phone_number, "code": code}
#
#         try:
#             response = requests.get(url, params=params)
#             if response.status_code == 200:
#                 print("Пользователь успешно удалён.")
#             else:
#                 print(f"Ошибка при подтверждении удаления: {response.status_code}")
#                 print(response.json())
#         except requests.exceptions.RequestException as e:
#             print(f"Ошибка при запросе: {e}")
#
# def _get_phone_number_for_login(self):
#         """Запрос номера телефона для авторизации."""
#         phone_number = input("Введите номер телефона: ")
#         if (
#             not phone_number.isdigit()
#             or len(phone_number) != 11
#             or phone_number[0] != "7"
#         ):
#             print(
#                 "Ошибка: некорректный номер телефона. Формат: 11 цифр, без +, начинается с 7."
#             )
#             return self._get_phone_number_for_login()
#         self.data["phone_number"] = phone_number
#         self._get_transaction_data(phone_number)
#
# def _get_transaction_data(self, phone_number):
#     """Получение данных для подписи транзакции."""
#     url = f"{self.url}/login/get_auth"
#     params = {"phone": phone_number}
#
#     try:
#         print("Отправка запроса для получения данных для авторизации...")
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             response_data = response.json()
#             trs = response_data.get("trs")
#             if trs:
#                 print("Данные для авторизации получены.")
#                 self._sign_transaction(trs)
#             else:
#                 print("Ошибка: данные для авторизации отсутствуют в ответе.")
#                 print(response)
#         else:
#             print(f"Ошибка при получении данных: {response.status_code}")
#             print(response.json())
#     except requests.exceptions.RequestException as e:
#         print(f"Ошибка при запросе: {e}")
#
# def _sign_transaction(self, trs):
#     """Подписание транзакции приватным ключом."""
#     print("Подписание транзакции...")
#     try:
#         private_key_path = "./keys/private_key.pem"
#
#         private_key = read_private_key(private_key_path)
#         if not private_key:
#             print("Приватный ключ не загружен.")
#             return
#
#         crypto = GostDSA()
#         signed_trs = crypto.sign(str(trs).encode(), private_key=private_key)
#
#         self._send_signed_transaction(self.data["phone_number"], signed_trs)
#     except Exception as e:
#         print(f"Ошибка при подписании транзакции: {e}")
#
# def _send_signed_transaction(self, phone_number, signed_trs):
#     """Отправка подписанной транзакции на сервер."""
#     url = f"{self.url}/login/auth"
#     params = {"phone": phone_number, "signed_trs": signed_trs}
#
#     try:
#         print("Отправка подписанной транзакции на сервер...")
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             print("Авторизация прошла успешно!")
#             response_data = response.json()
#             token = response_data.get("token")
#             if token:
#                 self.token = token
#
#                 token_file = "keys/auth_token.json"
#                 with open(token_file, "w") as file:
#                     json.dump({"token": token}, file, indent=4)
#                 print(f"Токен успешно сохранён в файл: {token_file}")
#             else:
#                 print("Ответ не содержит токена.")
#         else:
#             print(f"Ошибка при авторизации: {response.status_code}")
#             print(response.json())
#     except requests.exceptions.RequestException as e:
#         print(f"Ошибка при запросе: {e}")
import asyncio

import aiohttp
from hsecrypto import GostDSA
from datetime import datetime, timezone
import cmd
import os
import requests
import json
import hashlib
from tabulate import tabulate


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


def read_private_key(file_path):
    """
    Считывает приватный ключ из файла и возвращает его в виде строки.
    """
    try:
        with open(file_path, "r") as key_file:
            private_key = key_file.read().strip()
        return private_key
    except FileNotFoundError:
        print(f"Файл приватного ключа не найден: {file_path}")
        return None
    except Exception as e:
        print(f"Ошибка при чтении приватного ключа: {e}")
        return None


class MyCLI(cmd.Cmd):
    prompt = ">> "

    def __init__(self):
        super().__init__()
        self.data = {}
        self.keys = None
        self.keys_directory = "keys"
        self.host_file = os.path.join(self.keys_directory, "host.json")
        os.makedirs(self.keys_directory, exist_ok=True)

        def set_host():
            host = input("Введите адрес сервера: ")

            if host.startswith("http://"):
                host = host.replace("http://", "")

            if not host.startswith("https://"):
                host = "https://" + host

            if len(host.split(".")) == 1:
                print("Ошибка: некорректный адрес сервера.")
                return False

            if requests.get(host).status_code != 200:
                print("Ошибка: сервер не доступен.")
                return False

            with open(self.host_file, "w") as file:
                json.dump({"host": host}, file, indent=4)

            self.url = host
            print(f"Адрес сервера успешно сохранен")
            return True

        if os.path.exists(self.host_file):
            with open(self.host_file, "r") as file:
                self.url = json.load(file).get("host")
        else:
            if not set_host():
                set_host()

        self.timeuuid = ""

    def do_generate(self, arg):
        """
        Команда для генерации пары ключей и создания CSR.
        """
        dsa = GostDSA()
        private_key, public_key = dsa.generate_key_pair()

        public_key_file = os.path.join(self.keys_directory, "public_key.pem")
        try:
            with open(public_key_file, "w") as file:
                file.write(public_key)
            print(f"Публичный ключ успешно сохранен в файл: {public_key_file}")
        except Exception as e:
            print(f"Ошибка записи ключа в файл: {e}")
            return

        private_key_file = os.path.join(self.keys_directory, "private_key.pem")
        try:
            with open(private_key_file, "w") as file:
                file.write(private_key)
            print(f"Публичный ключ успешно сохранен в файл: {private_key_file}")
        except Exception as e:
            print(f"Ошибка записи ключа в файл: {e}")
            return

        country = "RU"
        organization = input("Введите название организации: ")
        phone_number = input("Введите номер телефона: ")

        ip = get_external_ip()
        if not ip:
            ip = input(f"Введите IP-адрес: ")

        fio = input("Введите ФИО: ")

        try:
            csr = generate_csr(
                private_key, public_key, country, organization, phone_number, ip, fio
            )
            print("CSR успешно сгенерирован")
        except Exception as e:
            print(f"Не получилось сгенерировать CSR: {e}")

        csr_file = os.path.join(self.keys_directory, "csr.json")
        try:
            with open(csr_file, "w") as file:
                json.dump(csr, file, indent=4)
            print(f"CSR успешно сохранен в файл: {csr_file}")
        except Exception as e:
            print(f"Ошибка записи CSR в файл: {e}")

        print("\nСгенерированный CSR:")
        print(json.dumps(csr, indent=4))

    def do_register(self, arg):
        """
        Регистрация пользователя.
        Запускает пошаговый процесс ввода данных.
        """
        print("Инициализация ключей...")
        if self._load_keys():
            print("Ключи успешно загружены.")
            self._get_full_name()
        else:
            print("Ключи не найдены. Регистрация:")
            self._get_file_path()

    def _load_keys(self):
        """Автоматическая загрузка ключей из директории."""
        if not os.path.exists(self.keys_directory):
            print(f"Директория с ключами '{self.keys_directory}' не найдена.")
            return False

        files = [
            f for f in os.listdir(self.keys_directory) if f.endswith("public_key.pem")
        ]
        if not files:
            print(f"В директории '{self.keys_directory}' нет файлов ключей.")
            return False

        try:
            file_path = os.path.join(self.keys_directory, files[0])
            with open(file_path, "r") as f:
                self.keys = f.read().strip()
            self.data["file_path"] = file_path
            return True
        except Exception as e:
            print(f"Ошибка при загрузке ключей: {e}")
            return False

    def _get_file_path(self):
        """Запрос пути к файлу ключей и загрузка ключей."""
        file_path = input("Введите путь к файлу ключей: ")
        try:
            with open(file_path, "r") as f:
                self.keys = f.read().strip()
            self.data["file_path"] = file_path
            print("Ключи успешно загружены.")
            self._get_full_name()
        except FileNotFoundError:
            print("Ошибка: файл не найден. Попробуйте еще раз.")
            self._get_file_path()
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            self._get_file_path()

    def _get_full_name(self):
        """Запрос ФИО."""
        full_name = input("Введите ФИО: ")
        if not full_name.strip():
            print("Ошибка: ФИО не может быть пустым.")
            return self._get_full_name()
        self.data["full_name"] = full_name
        self._get_phone_number()

    def _get_phone_number(self):
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
            return self._get_phone_number()
        self.data["phone_number"] = phone_number
        self._send_registration_data(
            self.data["phone_number"], self.data["full_name"], self.keys
        )

    def _send_registration_data(self, phone_number, fio, public_key):
        """Отправка регистрационных данных на сервер."""
        url = f"{self.url}/login/register"
        params = {"phone_number": phone_number, "fio": fio, "public_key": public_key}

        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                print("Регистрация прошла успешно!")
                print(response.json())
                self._get_sms_code()
            elif response.status_code == 400:
                print(response.json())
                self._get_sms_code()
            else:
                print(f"Ошибка при регистрации: {response.status_code}")
                print(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")

    def _get_sms_code(self):
        """Запрос кода из мессенджера."""
        sms_code = input("Введите код из Telegram: ")
        if not sms_code.isdigit() or len(sms_code) != 6:
            print("Ошибка: код должен состоять из 6 цифр.")
            return self._get_sms_code()
        self.data["sms_code"] = sms_code
        self._send_verification_code(self.data["phone_number"], self.data["sms_code"])

    def _send_verification_code(self, phone_number, code):
        """Функция отправки кода для верификации на сервер."""
        url = f"{self.url}/login/verify"
        params = {"phone_number": phone_number, "code": code}
        csr_file = os.path.join(self.keys_directory, "csr.json")
        try:
            with open(csr_file, "r") as file:
                csr = json.load(file)
            params["csr"] = json.dumps(csr)
        except FileNotFoundError:
            print(f"Ошибка: файл {csr_file} не найден.")
            return
        except json.JSONDecodeError:
            print(f"Ошибка: не удалось декодировать JSON из {csr_file}.")
            return

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                print("Код верификации успешно отправлен!")
                response_data = response.json()
                token = response_data.get("token")
                signed_csr = response_data.get("cert")

                if token and signed_csr:
                    self.token = token

                    output_file = os.path.join(
                        self.keys_directory, "registration_data.json"
                    )
                    with open(output_file, "w") as file:
                        json.dump(
                            {"token": token, "cert": signed_csr},
                            file,
                            indent=4,
                        )

                    print(f"Токен и сертификат успешно сохранены в файл: {output_file}")
                else:
                    print(
                        "Ответ не содержит необходимых данных (токен или сертификат)."
                    )

                self._complete_registration()
            else:
                print(f"Ошибка при отправке кода: {response.status_code}")
                print(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")

    def _complete_registration(self):
        """Вывод результатов регистрации."""
        print("\nРегистрация завершена!")
        print(f"ФИО: {self.data['full_name']}")
        print(f"Номер телефона: {self.data['phone_number']}")
        print(f"Код из Telegram: {self.data['sms_code']}")
        print(f"Файл ключей: {self.data['file_path']}")
        print(f"Ключи: {self.keys}")

    def _load_token(self):
        """Загрузка токена из файла."""
        token_file = "keys/auth_token.json"
        try:
            with open(token_file, "r") as file:
                data = json.load(file)
                self.token = data.get("token")
                if self.token:
                    print("Токен успешно загружен.")
                else:
                    print("Токен отсутствует в файле.")
        except FileNotFoundError:
            print(f"Файл токена '{token_file}' не найден.")
            self.token = None
        except json.JSONDecodeError:
            print(f"Ошибка: не удалось декодировать JSON из файла '{token_file}'.")
            self.token = None
        except Exception as e:
            print(f"Ошибка при загрузке токена: {e}")
            self.token = None

    def do_upload(self, arg):
        """
        Загружает файл на сервер с использованием токена.
        """
        self._load_token()

        if not self.token:
            print("Ошибка: Токен отсутствует. Авторизуйтесь, чтобы получить токен.")
            return

        try:
            file_path = input("Введите путь к файлу для загрузки: ")
            url = f"{self.url}/docs/upload"

            sha256_file = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
            headers = {"Authorization": self.token, "sha256": sha256_file}
            form = aiohttp.FormData()
            form.add_field(
                "file", open(file_path, "rb"), filename=file_path.split("/")[-1]
            )

            async def upload_file():
                async with aiohttp.ClientSession() as session:
                    async with session.put(url, headers=headers, data=form) as resp:
                        if resp.status == 200:
                            json_response = await resp.json()
                            self.timeuuid = json_response.get("timeuuid")
                        else:
                            text = await resp.text()
                            raise Exception("Upload failed:", resp.status, text)

            asyncio.run(upload_file())
        except FileNotFoundError:
            print("Ошибка: Файл не найден. Проверьте путь и попробуйте снова.")
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")
        finally:
            print(f"Файл успешно загружен. timeuuid: {self.timeuuid}")

    def do_list(self, arg):
        """
        Показывает список файлов на сервере.
        """
        self._load_token()

        if not self.token:
            print("Ошибка: Токен отсутствует. Авторизуйтесь, чтобы получить токен.")
            return

        try:
            url = f"{self.url}/docs/list"
            headers = {"Authorization": f"{self.token}"}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                print("Список файлов:")
                data = response.json()
                documents = data["documents"]
                for i in range(len(documents)):
                    documents[i] = {
                        key: value
                        for key, value in documents[i].items()
                        if not key in ["sign_verifed", "user_id", "sha256", "path"]
                    }
                headers = "keys"
                table = tabulate(documents, headers=headers, tablefmt="pretty")
                print(table)
            else:
                print(f"Ошибка при выдаче списка файлов: {response.status_code}")
                print(response.json())

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")

    def do_revoke(self, arg):
        """
        Удаляет пользователя.
        Использование: revoke
        """
        phone_number = input("Введите номер телефона для удаления: ").strip()

        if (
            not phone_number.isdigit()
            or len(phone_number) != 11
            or phone_number[0] != "7"
        ):
            print(
                "Ошибка: некорректный номер телефона. Формат: 11 цифр, начинается с 7."
            )
            return

        confirmation = (
            input(
                f"Вы уверены, что хотите удалить пользователя {phone_number}? (yes/no): "
            )
            .strip()
            .lower()
        )
        if confirmation != "yes":
            print("Отмена удаления.")
            return

        self._send_revoke_request(phone_number)

    def _send_revoke_request(self, phone_number):
        """
        Отправляет запрос на удаление пользователя.
        """
        url = f"{self.url}/revoke"
        params = {"phone": phone_number}

        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                print("Код для подтверждения удаления отправлен на указанный номер.")
                self._confirm_revoke(phone_number)
            else:
                print(
                    f"Ошибка при запросе на удаление пользователя: {response.status_code}"
                )
                print(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")

    def _confirm_revoke(self, phone_number):
        """
        Подтверждает удаление пользователя.
        """
        code = input("Введите код подтверждения удаления: ").strip()

        url = f"{self.url}/revoke/verify"
        params = {"phone": phone_number, "code": code}

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                print("Пользователь успешно удалён.")
            else:
                print(f"Ошибка при подтверждении удаления: {response.status_code}")
                print(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")

    def do_sign(self, arg):
        """
        Подписывает документ.
        Эта команда запросит аргументы последовательно:
        - timeuuid
        - путь к приватному ключу
        - путь к сертификату
        """

        timeuuid = input("Введите timeuuid документа: ").strip()
        if not timeuuid:
            print("Ошибка: timeuuid не может быть пустым.")
            return

        private_key_path = input("Введите путь к приватному ключу: ").strip()
        if not private_key_path or not os.path.exists(private_key_path):
            print(f"Ошибка: файл приватного ключа '{private_key_path}' не найден.")
            return

        certificate_path = input("Введите путь к сертификату: ").strip()
        if not certificate_path or not os.path.exists(certificate_path):
            print(f"Ошибка: файл сертификата '{certificate_path}' не найден.")
            return

        try:
            sha256 = input("Введите SHA256 хеш файла: ").strip()
            if not sha256:
                print("Ошибка: SHA256 хеш не может быть пустым.")
                return
        except Exception as e:
            print(f"Ошибка при вводе SHA256: {e}")
            return

        self._send_sign_request(timeuuid, sha256, private_key_path, certificate_path)

        def _send_sign_request(
            self, timeuuid, sha256, private_key_path, certificate_path
        ):
            """
            Отправляет запрос на подпись документа.
            """
            try:
                with open(private_key_path, "r") as key_file:
                    private_key = key_file.read()
                with open(certificate_path, "r") as cert_file:
                    certificate = cert_file.read()
            except Exception as e:
                print(f"Ошибка при чтении ключа или сертификата: {e}")
                return

            try:
                signature_data = sign_document(
                    timeuuid, sha256, private_key, certificate
                )
            except Exception as e:
                print(f"Ошибка при создании подписи: {e}")
                return

            url = f"{self.url}/docs/sign/{timeuuid}"
            headers = {"Authorization": self.token}
            try:
                response = requests.post(url, json=signature_data, headers=headers)
                if response.status_code == 200:
                    print("Документ успешно подписан.")
                    print(response.json())
                else:
                    print(f"Ошибка при подписании документа: {response.status_code}")
                    print(response.json())
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при запросе: {e}")

    def do_login(self, arg):
        """
        Авторизация пользователя.
        Запускает пошаговый процесс ввода данных.
        """
        print("Проверка наличия ключей...")
        if self._load_keys():
            print("Ключи успешно загружены.")
            self._get_phone_number_for_login()
        else:
            print(
                "Ключи не найдены. Проверьте корректность настроек или зарегистрируйтесь."
            )
            return

    def _get_phone_number_for_login(self):
        """Запрос номера телефона для авторизации."""
        phone_number = input("Введите номер телефона: ")
        if (
            not phone_number.isdigit()
            or len(phone_number) != 11
            or phone_number[0] != "7"
        ):
            print(
                "Ошибка: некорректный номер телефона. Формат: 11 цифр, без +, начинается с 7."
            )
            return self._get_phone_number_for_login()
        self.data["phone_number"] = phone_number
        self._get_transaction_data(phone_number)

    def _get_transaction_data(self, phone_number):
        """Получение данных для подписи транзакции."""
        url = f"{self.url}/login/get_auth"
        params = {"phone": phone_number}

        try:
            print("Отправка запроса для получения данных для авторизации...")
            response = requests.get(url, params=params)
            if response.status_code == 200:
                response_data = response.json()
                trs = response_data.get("trs")
                if trs:
                    print("Данные для авторизации получены.")
                    self._sign_transaction(trs)
                else:
                    print("Ошибка: данные для авторизации отсутствуют в ответе.")
                    print(response)
            else:
                print(f"Ошибка при получении данных: {response.status_code}")
                print(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")

    def _sign_transaction(self, trs):
        """Подписание транзакции приватным ключом."""
        print("Подписание транзакции...")
        try:
            private_key_path = "./keys/private_key.pem"

            private_key = read_private_key(private_key_path)
            if not private_key:
                print("Приватный ключ не загружен.")
                return

            crypto = GostDSA()
            signed_trs = crypto.sign(str(trs).encode(), private_key=private_key)

            self._send_signed_transaction(self.data["phone_number"], signed_trs)
        except Exception as e:
            print(f"Ошибка при подписании транзакции: {e}")

    def _send_signed_transaction(self, phone_number, signed_trs):
        """Отправка подписанной транзакции на сервер."""
        url = f"{self.url}/login/auth"
        params = {"phone": phone_number, "signed_trs": signed_trs}

        try:
            print("Отправка подписанной транзакции на сервер...")
            response = requests.get(url, params=params)
            if response.status_code == 200:
                print("Авторизация прошла успешно!")
                response_data = response.json()
                token = response_data.get("token")
                if token:
                    self.token = token

                    token_file = "keys/auth_token.json"
                    with open(token_file, "w") as file:
                        json.dump({"token": token}, file, indent=4)
                    print(f"Токен успешно сохранён в файл: {token_file}")
                else:
                    print("Ответ не содержит токена.")
            else:
                print(f"Ошибка при авторизации: {response.status_code}")
                print(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")

    def do_download(self, arg):
        """Загружает документ с сервера по timeuuid."""
        if not self.timeuuid:
            print(
                "Ошибка: timeuuid не установлен. Укажите timeuuid перед вызовом do_download."
            )
            return

        self._load_token()

        if not self.token:
            print("Ошибка: Токен отсутствует. Авторизуйтесь, чтобы получить токен.")
            return

        url = f"{self.url}/docs/download/{self.timeuuid}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            print(f"Загрузка документа с ID {self.timeuuid}...")
            response = requests.get(url, headers=headers, stream=True)

            if response.status_code == 200:
                content_disposition = response.headers.get("Content-Disposition", "")
                filename = (
                    content_disposition.split("filename=")[-1].strip('"')
                    if "filename=" in content_disposition
                    else None
                )
                if not filename:
                    filename = f"{self.timeuuid}.bin"

                with open(filename, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)

                print(f"Документ успешно загружен и сохранен как '{filename}'.")
            else:
                print(f"Ошибка при загрузке документа: {response.status_code}")
                print(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")


def run():
    MyCLI().cmdloop()


if __name__ == "__main__":
    MyCLI().cmdloop()

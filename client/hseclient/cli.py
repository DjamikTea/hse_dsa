import cmd
import os

from hseclient.content import fn, cglobal, json_data, cprint


class MyCLI(cmd.Cmd):
    prompt = ">> "
    privkey = None
    pubkey = None
    url = None


    def __init__(self):
        super().__init__()

        if os.path.exists(cglobal.host_file):
            self.url = json_data.read_host()
        else:
            self.url = fn.set_host()

        if not os.path.exists(cglobal.keys_file):
            print("Ключи не найдены. Генерация ключей...")
            fn.generate_keys()
            cprint.p_success("Ключи успешно сгенерированы")

        if not os.path.exists(cglobal.cert_file):
            print("Регистрация пользователя...")
            fn.register()





    def do_generate(self, arg):
        """
        Команда для генерации пары ключей и создания CSR.
        """
        print("Генерация ключей:")
        fn.generate_keys()
        #
        # country = "RU"
        # organization = input("Введите название организации: ")
        # phone_number = input("Введите номер телефона: ")
        #
        # ip = fn.get_external_ip()
        # if not ip:
        #     ip = input(f"Введите IP-адрес: ")
        #
        # fio = input("Введите ФИО: ")
        #
        # try:
        #     csr = generate_csr(
        #         private_key, public_key, country, organization, phone_number, ip, fio
        #     )
        #     print("CSR успешно сгенерирован")
        # except Exception as e:
        #     print(f"Не получилось сгенерировать CSR: {e}")
        #
        # csr_file = os.path.join(self.keys_directory, "csr.json")
        # try:
        #     with open(csr_file, "w") as file:
        #         json.dump(csr, file, indent=4)
        #     print(f"CSR успешно сохранен в файл: {csr_file}")
        # except Exception as e:
        #     print(f"Ошибка записи CSR в файл: {e}")
        #
        # print("\nСгенерированный CSR:")
        # print(json.dumps(csr, indent=4))

    def do_register(self, arg):
        """
        Регистрация пользователя.
        Запускает пошаговый процесс ввода данных.
        """
        print("Регистрация пользователя:")
        fn.register()

    # def do_upload(self, arg):
    #     """
    #     Загружает файл на сервер с использованием токена.
    #     """
    #     self._load_token()
    #
    #     if not self.token:
    #         print("Ошибка: Токен отсутствует. Авторизуйтесь, чтобы получить токен.")
    #         return
    #
    #     try:
    #         file_path = input("Введите путь к файлу для загрузки: ")
    #         url = f"{self.url}/docs/upload"
    #
    #         sha256_file = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
    #         headers = {"Authorization": self.token, "sha256": sha256_file}
    #         form = aiohttp.FormData()
    #         form.add_field(
    #             "file", open(file_path, "rb"), filename=file_path.split("/")[-1]
    #         )
    #
    #         async def upload_file():
    #             async with aiohttp.ClientSession() as session:
    #                 async with session.put(url, headers=headers, data=form) as resp:
    #                     if resp.status == 200:
    #                         json_response = await resp.json()
    #                         self.timeuuid = json_response.get("timeuuid")
    #                     else:
    #                         text = await resp.text()
    #                         raise Exception("Upload failed:", resp.status, text)
    #
    #         asyncio.run(upload_file())
    #     except FileNotFoundError:
    #         print("Ошибка: Файл не найден. Проверьте путь и попробуйте снова.")
    #     except requests.exceptions.RequestException as e:
    #         print(f"Ошибка при запросе: {e}")
    #     finally:
    #         print(f"Файл успешно загружен. timeuuid: {self.timeuuid}")
    #
    # def do_list(self, arg):
    #     """
    #     Показывает список файлов на сервере.
    #     """
    #     self._load_token()
    #
    #     if not self.token:
    #         print("Ошибка: Токен отсутствует. Авторизуйтесь, чтобы получить токен.")
    #         return
    #
    #     try:
    #         url = f"{self.url}/docs/list"
    #         headers = {"Authorization": f"{self.token}"}
    #         response = requests.get(url, headers=headers)
    #
    #         if response.status_code == 200:
    #             print("Список файлов:")
    #             data = response.json()
    #             documents = data["documents"]
    #             for i in range(len(documents)):
    #                 documents[i] = {
    #                     key: value
    #                     for key, value in documents[i].items()
    #                     if not key in ["sign_verifed", "user_id", "sha256", "path"]
    #                 }
    #             headers = "keys"
    #             table = tabulate(documents, headers=headers, tablefmt="pretty")
    #             print(table)
    #         else:
    #             print(f"Ошибка при выдаче списка файлов: {response.status_code}")
    #             print(response.json())
    #
    #     except requests.exceptions.RequestException as e:
    #         print(f"Ошибка при запросе: {e}")
    #
    # def do_revoke(self, arg):
    #     """
    #     Удаляет пользователя.
    #     Использование: revoke
    #     """
    #     phone_number = input("Введите номер телефона для удаления: ").strip()
    #
    #     if (
    #         not phone_number.isdigit()
    #         or len(phone_number) != 11
    #         or phone_number[0] != "7"
    #     ):
    #         print(
    #             "Ошибка: некорректный номер телефона. Формат: 11 цифр, начинается с 7."
    #         )
    #         return
    #
    #     confirmation = (
    #         input(
    #             f"Вы уверены, что хотите удалить пользователя {phone_number}? (yes/no): "
    #         )
    #         .strip()
    #         .lower()
    #     )
    #     if confirmation != "yes":
    #         print("Отмена удаления.")
    #         return
    #
    #     self._send_revoke_request(phone_number)
    #
    # def do_sign(self, arg):
    #     """
    #     Подписывает документ.
    #     Эта команда запросит аргументы последовательно:
    #     - timeuuid
    #     - путь к приватному ключу
    #     - путь к сертификату
    #     """
    #
    #     timeuuid = input("Введите timeuuid документа: ").strip()
    #     if not timeuuid:
    #         print("Ошибка: timeuuid не может быть пустым.")
    #         return
    #
    #     private_key_path = input("Введите путь к приватному ключу: ").strip()
    #     if not private_key_path or not os.path.exists(private_key_path):
    #         print(f"Ошибка: файл приватного ключа '{private_key_path}' не найден.")
    #         return
    #
    #     certificate_path = input("Введите путь к сертификату: ").strip()
    #     if not certificate_path or not os.path.exists(certificate_path):
    #         print(f"Ошибка: файл сертификата '{certificate_path}' не найден.")
    #         return
    #
    #     try:
    #         sha256 = input("Введите SHA256 хеш файла: ").strip()
    #         if not sha256:
    #             print("Ошибка: SHA256 хеш не может быть пустым.")
    #             return
    #     except Exception as e:
    #         print(f"Ошибка при вводе SHA256: {e}")
    #         return
    #
    #     self._send_sign_request(timeuuid, sha256, private_key_path, certificate_path)
    #
    #     def _send_sign_request(
    #         self, timeuuid, sha256, private_key_path, certificate_path
    #     ):
    #         """
    #         Отправляет запрос на подпись документа.
    #         """
    #         try:
    #             with open(private_key_path, "r") as key_file:
    #                 private_key = key_file.read()
    #             with open(certificate_path, "r") as cert_file:
    #                 certificate = cert_file.read()
    #         except Exception as e:
    #             print(f"Ошибка при чтении ключа или сертификата: {e}")
    #             return
    #
    #         try:
    #             signature_data = sign_document(
    #                 timeuuid, sha256, private_key, certificate
    #             )
    #         except Exception as e:
    #             print(f"Ошибка при создании подписи: {e}")
    #             return
    #
    #         url = f"{self.url}/docs/sign/{timeuuid}"
    #         headers = {"Authorization": self.token}
    #         try:
    #             response = requests.post(url, json=signature_data, headers=headers)
    #             if response.status_code == 200:
    #                 print("Документ успешно подписан.")
    #                 print(response.json())
    #             else:
    #                 print(f"Ошибка при подписании документа: {response.status_code}")
    #                 print(response.json())
    #         except requests.exceptions.RequestException as e:
    #             print(f"Ошибка при запросе: {e}")
    #
    # def do_login(self, arg):
    #     """
    #     Авторизация пользователя.
    #     Запускает пошаговый процесс ввода данных.
    #     """
    #     print("Проверка наличия ключей...")
    #     if self._load_keys():
    #         print("Ключи успешно загружены.")
    #         self._get_phone_number_for_login()
    #     else:
    #         print(
    #             "Ключи не найдены. Проверьте корректность настроек или зарегистрируйтесь."
    #         )
    #         return
    #
    # def do_download(self, arg):
    #     """Загружает документ с сервера по timeuuid."""
    #     if not self.timeuuid:
    #         print(
    #             "Ошибка: timeuuid не установлен. Укажите timeuuid перед вызовом do_download."
    #         )
    #         return
    #
    #     self._load_token()
    #
    #     if not self.token:
    #         print("Ошибка: Токен отсутствует. Авторизуйтесь, чтобы получить токен.")
    #         return
    #
    #     url = f"{self.url}/docs/download/{self.timeuuid}"
    #     headers = {"Authorization": f"Bearer {self.token}"}
    #
    #     try:
    #         print(f"Загрузка документа с ID {self.timeuuid}...")
    #         response = requests.get(url, headers=headers, stream=True)
    #
    #         if response.status_code == 200:
    #             content_disposition = response.headers.get("Content-Disposition", "")
    #             filename = (
    #                 content_disposition.split("filename=")[-1].strip('"')
    #                 if "filename=" in content_disposition
    #                 else None
    #             )
    #             if not filename:
    #                 filename = f"{self.timeuuid}.bin"
    #
    #             with open(filename, "wb") as file:
    #                 for chunk in response.iter_content(chunk_size=8192):
    #                     file.write(chunk)
    #
    #             print(f"Документ успешно загружен и сохранен как '{filename}'.")
    #         else:
    #             print(f"Ошибка при загрузке документа: {response.status_code}")
    #             print(response.json())
    #     except requests.exceptions.RequestException as e:
    #         print(f"Ошибка при запросе: {e}")
    #

def run():
    MyCLI().cmdloop()


if __name__ == "__main__":
    os.makedirs(cglobal.data_dir, exist_ok=True)
    MyCLI().cmdloop()

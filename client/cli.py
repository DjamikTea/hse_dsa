import cmd
import os
import requests
import json
import time
from hsecrypto import GostDSA
from datetime import datetime, timezone

def generate_csr(private_key: str, public_key: str, country: str, organization: str, phone_number: str, ip: str, fio: str) -> dict:
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

class MyCLI(cmd.Cmd):
    prompt = ">> "
    
    def __init__(self):
        super().__init__()
        self.data = {}  
        self.keys = None  
        self.keys_directory = "keys"  
        os.makedirs(self.keys_directory, exist_ok=True) 
    
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

        country = input("Введите код страны (ISO 3166-1 alpha-2): ")
        organization = input("Введите название организации: ")
        phone_number = input("Введите номер телефона: ")
        ip = input("Введите IP-адрес: ")
        fio = input("Введите ФИО: ")

        csr = generate_csr(private_key, public_key, country, organization, phone_number, ip, fio)
        
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

        files = [f for f in os.listdir(self.keys_directory) if f.endswith(".pem")]
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
        if not phone_number.isdigit() or len(phone_number) != 11 or phone_number[0] != "8":
            print("Ошибка: некорректный номер телефона. Формат: 11 цифр, без +, начинается с 8.")
            return self._get_phone_number()
        self.data["phone_number"] = phone_number
        self._send_registration_data(
            self.data["phone_number"],
            self.data["full_name"],
            self.keys
        )
    
    
    def _send_registration_data(self, phone_number, fio, public_key):
        url = "https://hse.gopass.dev/login/register"
        params = {
            "phone_number": phone_number,
            "fio": fio,
            "public_key": public_key
        }

        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                print("Регистрация прошла успешно!")
                print(response.json())
                self._get_sms_code()
            elif response.status_code == 400:
                print("У вас уже есть код")
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
        self._send_verification_code(
            self.data["phone_number"],
            self.data["sms_code"]
        )

    def _send_verification_code(self, phone_number, code):
            """
            Функция отправки кода для верификации на второй URL.
            """
            url = "https://hse.gopass.dev/login/verify"
            params = {
                "phone_number": phone_number,
                "code": code
            }
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
                    print(response.json())
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

        # Отправка данных на API
        self._send_registration_data(self.data['phone_number'], self.data['full_name'], self.keys)

    def do_exit(self, arg):
        """Выход из программы."""
        print("До свидания!")
        return True

if __name__ == "__main__":
    MyCLI().cmdloop()

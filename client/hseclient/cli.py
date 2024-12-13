import cmd
import os

from hseclient.content import fn, cglobal, json_data, cprint
from hseclient.content.database import Database


class MyCLI(cmd.Cmd):
    prompt = ">> "
    privkey = None
    pubkey = None
    url = None


    def __init__(self):
        super().__init__()

        self.db = Database()

        if os.path.exists(cglobal.host_file):
            self.url = json_data.read_host()
        else:
            self.url = fn.set_host()

        if not os.path.exists(cglobal.keys_file):
            print("Ключи не найдены. Генерация ключей...")
            fn.generate_keys()

        if not os.path.exists(cglobal.cert_file):
            print("Регистрация пользователя...")
            fn.register()

    def do_generate(self, arg):
        """
        Команда для генерации пары ключей.
        """
        print("Генерация ключей:")
        fn.generate_keys()

    def do_register(self, arg):
        """
        Регистрация пользователя.
        Запускает пошаговый процесс ввода данных.
        """
        print("Регистрация пользователя:")
        fn.register()

    def do_login(self, arg):
        """
        Авторизация пользователя.
        Запускает пошаговый процесс ввода данных.
        """
        print("Авторизация пользователя:")
        fn.auth()

    def do_upload(self, arg):
        """
        Загрузка файла на сервер.
        """
        file_path = input("Введите путь к файлу для загрузки: ")
        timeuuid = fn.upload_file(file_path)
        if timeuuid:
            fn.sign_document(timeuuid, file_path)

    def do_sign(self, arg):
        """
        Подпись документа.
        """
        timeuuid = input("Введите timeuuid документа: ")
        file_path = input("Введите путь к файлу: ")
        fn.sign_document(timeuuid, file_path)

    def do_send(self, arg):
        """
        Отправка документа.
        """
        timeuuid = input("Введите timeuuid документа: ")
        phone_number = input("Введите номер телефона получателя: ")
        fn.send_document(timeuuid, phone_number)

    def do_my_files(self, arg):
        """
        Получение списка своих файлов.
        """
        fn.list_files()

    def do_revoke(self, arg):
        """
        Удаление пользователя.
        """
        fn.revoke()

    def do_check_available(self, arg):
        """
        Проверка доступности сервера.
        """
        fn.check_new_docs(db=self.db)

    def do_download(self, arg):
        """
        Скачивание документа.
        """
        timeuuid = input("Введите timeuuid документа: ")
        fn.get_sender_docs(self.db, timeuuid)

    def do_delete(self, arg):
        """
        Удаление документа.
        """
        timeuuid = input("Введите timeuuid документа: ")
        fn.delete_file(timeuuid)



def run():
    MyCLI().cmdloop()


if __name__ == "__main__":
    os.makedirs(cglobal.data_dir, exist_ok=True)
    os.makedirs(cglobal.download_dir, exist_ok=True)
    MyCLI().cmdloop()

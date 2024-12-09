# Привет мой дорогой девопсер) Здесь ты найдешь инструкцию запуску бэкенда.

# Контейнеры

	1.	db: MySQL база данных.
	2.	server: Python-сервис с FastAPI. Перед запуском приложения внутри контейнера выполняются тесты. Если все тесты проходят успешно, стартует Uvicorn.
	3.	nginx: Реверс-прокси, который принимает запросы на порты 80 и 443 и перенаправляет их на приложение.
	4.	certbot: Сервис для получения SSL-сертификатов от Let’s Encrypt с помощью webroot-челленджа.

# Предварительные требования

	•	Доступный домен
	•	Возможность открыть порты 80 и 443 на вашем хосте
	•	Действущий токен на Telegram Gateway и донат Павлу Дурову. 

# Переменные окружения

В .env инициализированы переменные окружения, которые нужно измененить:

	•	MYSQL_ROOT_PASSWORD: Пароль для root-пользователя базы данных.
	•	MYSQL_PASSWORD: Пароль пользователя базы данных.
	•	TELEGRAM_GATEWAY_TOKEN: Токен для Telegram Gateway.
	•	TELEGRAM_TEST_PHONE: Номер телефона для тестовых уведомлений. (Телефон на котором зарегестрирован Gateway)
	•	DB_PASSWORD: Пароль пользователя базы данных.
	•	DOMAIN: Ваш домен.
	•	EMAIL: Ваш email для рекламы от Let’s Encrypt.

В файле nginx.conf необходимо указать ваш реальный домен вместо example.com

# Шаги для запуска
```
# Установка Docker
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 
sudo docker run hello-world


cd server

mkdir -p certbot/www certbot/certs
mkdir -p certbot/certs/live/example.com    # Вместо example.com укажите ваш домен !!!!!!

# Создаем самоподписанный сертификат чтоб запустился nginx, его потом заменит на сертификат от Let’s Encrypt
openssl req -x509 -nodes -days 1 -newkey rsa:2048 \ 
-keyout certbot/certs/live/example.com/privkey.pem \ # Вместо example.com укажите ваш домен !!!!!!
-out certbot/certs/live/example.com/fullchain.pem \  # Вместо example.com укажите ваш домен !!!!!!
-subj "/CN=example.com"         # Вместо example.com укажите ваш домен !!!!!!

sudo docker compose up -d
```
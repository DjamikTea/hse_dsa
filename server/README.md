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
    •	ORGANIZATION: Название вашей организации.
	•	DOMAIN: Ваш домен.
	•	EMAIL: Ваш email для рекламы от Let’s Encrypt.

В файле nginx.conf необходимо указать ваш реальный домен вместо example.com

# Шаги для запуска
```bash
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
sudo docker compose up -d --build
```

# Проверьте чтоб certbot получил сертификаты!

```bash
sudo docker logs hse-certbot
```

Если все хорошо, то раскомментируйте последние строки в nginx.conf и перезапустите nginx контейнер.

```bash
sudo docker restart hse-nginx
```
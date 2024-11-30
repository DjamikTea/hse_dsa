docker run -d \
  --name mysql_hse \
  -e MYSQL_ROOT_PASSWORD=XXXXXXXXX \
  -e MYSQL_DATABASE=hse \
  -e MYSQL_USER=fastapi \
  -e MYSQL_PASSWORD=XXXXXXXXX \
  -v /var/lib/mysql:/var/lib/mysql \
  -p 3306:3306 \
  --restart always \
  mysql:latest
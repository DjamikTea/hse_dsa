import os
from mysql.connector import pooling

dbconfig = {
    "host": os.getenv("DB_HOST", "your_host"),
    "user": os.getenv("DB_USER", "your_user"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "database": os.getenv("DB_NAME", "your_database"),
    "port": int(os.getenv("DB_PORT", 3306)),
}


# Создаем пул подключений
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    **dbconfig
)

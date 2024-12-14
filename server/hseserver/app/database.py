import os
from mysql.connector import pooling
from fastapi import HTTPException

dbconfig = {
    "host": os.getenv("DB_HOST", "your_host"),
    "user": os.getenv("DB_USER", "your_user"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "database": os.getenv("DB_NAME", "your_database"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

if __name__ != "__main__":
    # f#cking docs
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mypool", pool_size=5, **dbconfig
    )


def get_db():
    conn = connection_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        yield cursor, conn
    finally:
        cursor.close()
        conn.close()


def check_token(token: str | None, cursor) -> dict:
    cursor.execute("SELECT * FROM users WHERE token = %s", (token,))
    user = cursor.fetchone()
    if user:
        return user
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

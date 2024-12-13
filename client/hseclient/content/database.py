import sqlite3

class Database:
    def __init__(self, db_file: str = "content/client.sqlite"):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def query(self, query, *args):
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def execute(self, query, *args):
        self.cursor.execute(query, args)
        self.conn.commit()

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchmany(self, size):
        return self.cursor.fetchmany(size)

    def lastrowid(self):
        return self.cursor.lastrowid

    def close(self):
        self.conn.close()
import sqlite3

class Database:
    def __init__(self, db_file: str = "content/client.sqlite"):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

        # check if table exists
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='known_users';")
        if not self.cursor.fetchone():
            query = """
                    create table known_users
            (
                id           integer
                    constraint table_name_pk
                        primary key autoincrement,
                phone_number text(16)  not null
                    constraint table_name_pk_2
                        unique,
                pubkey       text(255) not null
                    constraint table_name_pk_3
                        unique
            );
            """
            self.cursor.execute(query)

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='docs_available';")
        if not self.cursor.fetchone():
            query1 = """
            create table docs_available
            (
                id           integer    not null
                    constraint documents_available_pk
                        primary key,
                timeuuid     text(36)   not null
                    constraint documents_available_pk_2
                        unique,
                filename     text(255)  not null,
                created      text(24)   not null,
                sign         text(4096) not null,
                sha256       text(64)   not null,
                sender_phone text(16)   not null
            );
            """
            query2 = """
            create index docs_available_sender_phone_index
                on docs_available (sender_phone);
            """
            self.cursor.execute(query1)
            self.cursor.execute(query2)



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

    def close(self):
        self.conn.close()
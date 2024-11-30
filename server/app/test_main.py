from fastapi.testclient import TestClient
from mysql.connector import ProgrammingError

from server.app.database import connection_pool
from server.app.main import app
client = TestClient(app)

def test_first_launch():
    db = connection_pool.get_connection()
    cursor = db.cursor()
    first_launch_flag: bool = False
    try:
        cursor.execute("SELECT * FROM first_launch")
        first_launch_flag = True
    except ProgrammingError as e:
        print(e)

    if not first_launch_flag:
        print("First launch flag not found")
        print("Creating tables...")

        cursor.execute("CREATE TABLE first_launch (yes INT)")
        print("Table first_launch created")
        first_launch_flag = True

    assert first_launch_flag == True

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {'message': 'hello world'}

def test_mysql_select():
    response = client.get("/test/items", params={"item_id": "bruh"})
    assert response.status_code == 200
    assert response.json() == {'find_val': 'bruh', 'id': 1}

# if __name__ == "__main__":
#     first_launch()
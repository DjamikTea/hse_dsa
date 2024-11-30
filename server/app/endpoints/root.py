from fastapi import APIRouter
from server.app.database import connection_pool
router = APIRouter()

def get_db():
    conn = connection_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
    finally:
        cursor.close()
        conn.close()

@router.get("/")
async def read_root():
    return {"message": "hello world"}
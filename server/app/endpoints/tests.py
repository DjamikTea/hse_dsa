from fastapi import APIRouter, Depends, HTTPException
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


@router.get("/items")
async def read_item(item_id: str, db=Depends(get_db)):
    db.execute("SELECT * FROM items WHERE find_val = %s", (item_id,))
    item = db.fetchone()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

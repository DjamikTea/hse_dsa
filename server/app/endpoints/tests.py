from fastapi import APIRouter, Depends, HTTPException
from app.database import connection_pool, get_db

router = APIRouter()

@router.get("/items")
async def read_item(item_id: str, db=Depends(get_db)):
    cursor, conn = db
    cursor.execute("SELECT * FROM items WHERE find_val = %s", (item_id,))
    item = cursor.fetchone()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

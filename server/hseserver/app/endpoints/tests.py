from fastapi import APIRouter, Depends, HTTPException
from hseserver.app.database import get_db

router = APIRouter()


@router.get("/items")
async def read_item(item_id: str, db=Depends(get_db)):
    """
    Тестовый метод
    :param item_id:
    :return:
    """
    cursor, conn = db
    cursor.execute("SELECT * FROM items WHERE find_val = %s", (item_id,))
    item = cursor.fetchone()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

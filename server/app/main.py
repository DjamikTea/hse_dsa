from sys import prefix

from fastapi import FastAPI
from app.endpoints import tests, root, auth, revoke, docs
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Starting server")
app = FastAPI()

app.include_router(root.router, prefix="")
app.include_router(tests.router, prefix="/test")
app.include_router(auth.router, prefix="/login")
app.include_router(revoke.router, prefix="/revoke")

app.include_router(docs.router, prefix="/docs")

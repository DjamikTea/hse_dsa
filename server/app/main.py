from sys import prefix

from fastapi import FastAPI
from server.app.endpoints import tests, root
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Starting server")
app = FastAPI()

app.include_router(root.router, prefix="")
app.include_router(tests.router, prefix="/test")




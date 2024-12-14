FROM python:3.13-slim
WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install poetry

RUN poetry install

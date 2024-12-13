FROM python:3.13-slim
WORKDIR /app

COPY pyproject.toml pyproject.toml

COPY . .

RUN pip install --upgrade pip && pip install poetry
RUN pip install pytest

RUN poetry install

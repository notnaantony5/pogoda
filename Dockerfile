FROM python:3.12-slim-bullseye

WORKDIR /opt/app

RUN pip install poetry==1.8.1

COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock

RUN poetry config virtualenvs.create false
RUN poetry install --only=main --no-ansi --no-interaction

COPY . .

CMD python main.py
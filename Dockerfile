ARG PYTHON_VERSION=3.10-slim-bullseye

FROM python:${PYTHON_VERSION}

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock /app
RUN poetry config virtualenvs.create false

RUN poetry install --only main --no-root --no-interaction
COPY yorubatts_bot/ /app/yorubatts_bot/

EXPOSE 5000

CMD ["python", "-m", "yorubatts_bot"]


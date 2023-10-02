FROM python:3.10

WORKDIR /app

ENV PYTHONPATH .

COPY poetry.lock pyproject.toml ./

RUN pip install poetry

RUN poetry config virtualenvs.create false && poetry install --no-dev

COPY . .

EXPOSE 8000

ENTRYPOINT ["python", "main.py"]
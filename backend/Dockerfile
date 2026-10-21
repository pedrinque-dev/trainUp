FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt psycopg2-binary
COPY app ./app
COPY alembic ./alembic
COPY tests ./tests
RUN useradd --system --no-create-home trainup && chown -R trainup /code
USER trainup
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

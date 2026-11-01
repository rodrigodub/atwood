FROM python:3.14-slim AS dependencies

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN groupadd --gid 10001 atwood && useradd --uid 10001 --gid atwood --create-home atwood

COPY --from=dependencies /install /usr/local
COPY src ./src
COPY --chown=atwood:atwood datasets ./datasets
COPY --chown=atwood:atwood db.sqlite3 .

USER atwood

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health').read()" || exit 1

CMD ["uvicorn", "atwood.api:app", "--host", "0.0.0.0", "--port", "8000"]

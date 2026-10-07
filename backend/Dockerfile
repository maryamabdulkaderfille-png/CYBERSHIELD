FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc g++ unixodbc-dev libzbar0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 5000

CMD ["flask", "--app", "wsgi.py", "run", "--host=0.0.0.0", "--port=5000", "--debug"]

# Message Broker Service

Media komunikasi asynchronous antar service (SAS-07), backed by Apache Kafka.

## Konsep

Pemetaan konsep SAS-07 ke Kafka:

| SAS-07 | Implementasi |
|--------|--------------|
| Exchange | Prefix nama topik (`exchange__routing_key`) |
| Routing key | Bagian kedua nama topik |
| Queue | Topik Kafka yang dikonsumsi consumer |

Satu binding `(stream_exchange, stream_data)` menghasilkan topik
`stream_exchange__stream_data`. Queue default `stream_queue` dibuat terpisah
sesuai dokumen.

## REST API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check + status Kafka |
| `GET /status` | Operational status |
| `POST /config/reload` | Reload konfigurasi dari Configuration Service |
| `POST /api/v1/publish` | Publish `{exchange, routing_key, message}` (kontrak `BrokerClient` SDK) |
| `POST /api/v1/consume` | Baca pesan dari queue (non-destructive peek) |
| `GET /api/v1/queue` | Daftar queue + backlog |
| `GET /api/v1/queue/{name}` | Info satu queue |
| `GET /api/v1/exchange/{name}` | Binding di bawah exchange |
| `GET /api/v1/connections` | Status koneksi Kafka |
| `GET /statistics` | Total publish/consume/fail, queue size, rate |

## Menjalankan

```bash
# 1. Kafka via docker compose (dari root repo)
docker compose -f docker/docker-compose.yml up -d kafka

# 2. Install dependencies
pip install -r services/message-broker/requirements.txt

# 3. Jalankan service
python services/message-broker/main.py
```

Service berjalan di port 8003 sesuai `DefaultPorts.MESSAGE_BROKER`.

## Konfigurasi

Diambil dari Configuration Service (key `message-broker`), dengan bootstrap
defaults: host, port, exchange, queue, routing_key, prefetch_count,
retry_count.

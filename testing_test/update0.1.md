# Update 0.1 — Status Layanan Platform (SAS-04 s.d. SAS-07)

Tanggal: 2026-08-26
Branch: `proses1`

---

## 1. Ringkasan

Sampai SAS-07, tiga service sudah berjalan dan saling terhubung, didukung Apache Kafka
sebagai infrastruktur streaming:

| # | Service | SAS | Port | Status |
|---|---------|-----|------|--------|
| 1 | Configuration Service | SAS-05 | 8001 | Berjalan (fungsional penuh) |
| 2 | Streaming Preprocessing Service | SAS-06 | 8002 | Berjalan (pipeline preprocessing aktif) |
| 3 | Message Broker Service | SAS-07 | 8003 | Berjalan (publish/consume + ack + DLQ) |

Service yang **belum dibangun**: Online ML Engine (SAS-08), State Store (SAS-09),
Storage Layer (SAS-10), Monitoring Dashboard (SAS-11).

Prasyarat infrastruktur: **Apache Kafka** via Docker (`aslp-kafka`, port 9092).
Database konfigurasi: SQLite otomatis (`services/configuration-service/configuration.db`).

```
sample_data/sample.csv
        │
        ▼
┌──────────────────────────────┐   bootstrap/reload    ┌─────────────────────────┐
│ Streaming Preprocessing      │ ────────────────────► │ Configuration Service   │
│ Service (:8002)              │                       │ (:8001, SQLite)         │
│ CSV → validasi → transform → │                       └─────────────────────────┘
│ payload StreamMessage →      │
│ publish HTTP                 │
└──────────────┬───────────────┘
               │ POST /api/v1/publish
               ▼
┌──────────────────────────────┐
│ Message Broker (:8003)       │  Kafka topic: stream_exchange__<routing_key>
│ subscribe → fetch → ack/nack │  DLQ topic:    <queue>__dlq
└──────────────────────────────┘
```

---

## 2. Fungsi Tiap Service

### 2.1 Configuration Service (SAS-05) — port 8001

Single source of truth konfigurasi seluruh platform.

| Endpoint | Fungsi |
|---|---|
| `GET /api/v1/config` | Daftar semua konfigurasi service |
| `GET /api/v1/config?service_name=X` | Konfigurasi satu service |
| `GET /api/v1/config/{service_name}` | Konfigurasi satu service (format SDK, dipakai ConfigLoader) |
| `PUT /api/v1/config` | Buat/update konfigurasi (upsert, versi bertambah) |
| `POST /api/v1/config/reload` | Muat ulang cache dari database |
| `POST /api/v1/config/delete?service_name=X` | Hapus konfigurasi |
| `GET /api/v1/health` | Health check (status database) |
| `GET /api/v1/status` | Statistik operasional |

Detail:
- Database SQLite async (SQLAlchemy + aiosqlite), tabel `configurations`
  (`service_name` unik, `config_data` JSON, `version`).
- Saat startup, service melakukan *seed* konfigurasi default untuk semua platform
  (preprocessing, broker, oml-engine, state-store, storage-layer) — hanya jika belum ada.
- Konfigurasi dapat diubah runtime lewat `PUT /api/v1/config`; service lain akan
  mengambilnya saat reload tanpa perlu restart.

### 2.2 Streaming Preprocessing Service (SAS-06) — port 8002

Membaca data CSV, menjalankan pipeline preprocessing, dan menerbitkan pesan ke broker.

Pipeline aktif per baris data (semua dikendalikan dari Configuration Service):
1. **Validasi** — schema validation (opsional), penanganan missing value
   (fill constant/mean/median/mode), deteksi duplikat (reject/keep_first/mark)
2. **Transformasi** — type conversion, cleaning rules, encoding kategorikal,
   normalisasi numerik (semua tahap dapat diaktifkan/dimatikan via config)
3. **Feature engineering** — derived features, window features, agregasi
4. **Payload builder** — setiap baris menjadi `StreamMessage`
   (`{stream_id, timestamp, source, event_type, data, metadata}`)
5. **Publisher** — mengirim ke broker via `BrokerClient` (HTTP)

| Endpoint | Fungsi |
|---|---|
| `POST /stream/start` | Mulai sesi streaming di background task |
| `POST /stream/stop` | Hentikan sesi dengan rapi |
| `GET /stream/status` | Progres sesi berjalan |
| `GET /statistics` | Statistik detail sesi (batch, sukses/gagal, error) |
| `GET /bootstrap` | Muat konfigurasi awal dari Configuration Service |
| `POST /config/reload` | Muat ulang konfigurasi tanpa restart |
| `GET /health` · `GET /status` | Health & status |
| `GET /pipeline/validation` · `/transformation` · `/features` · `/stats` | Statistik tiap tahap pipeline |
| `GET /pipeline/session/errors` | Error preprocessing sesi berjalan |
| `POST /pipeline/reset` | Reset state pipeline |

Parameter sesi (`batch_size`, `polling_interval`, `publish_topic`) diambil dari
Configuration Service; nilai eksplisit pada body request tetap menang.
Fallback: bila Configuration Service tidak tersedia, service memakai default lokal
sehingga tetap bisa berjalan.

### 2.3 Message Broker Service (SAS-07) — port 8003

Distribusi pesan asynchronous antar service, di atas Apache Kafka.
Pemetaan konsep SAS-07 → Kafka:

| Konsep desain | Implementasi Kafka |
|---|---|
| Exchange + routing key | Topik `<exchange>__<routing_key>` (mis. `stream_exchange__stream_data`) |
| Queue | Topik Kafka yang di-subscribe consumer |
| Consumer workflow (subscribe → receive → ack) | Consumer group persisten, offset di-commit manual |
| Dead Letter Queue | Topik `<queue>__dlq` berisi pesan gagal + metadata alasan |
| Requeue (nack + requeue) | Rewind posisi group sehingga pesan dikirim ulang |

| Endpoint | Fungsi |
|---|---|
| `POST /api/v1/publish` | Terbitkan pesan `{exchange, routing_key, message}` (retry eksponensial) |
| `POST /api/v1/subscribe` | Daftarkan consumer group pada sebuah queue |
| `POST /api/v1/fetch` | Terima pesan + `delivery_tag`, offset belum di-commit |
| `POST /api/v1/ack` | Acknowledgement — commit offset pesan |
| `POST /api/v1/nack` | Tolak pesan: `requeue=true` kirim ulang; `requeue=false` ke DLQ |
| `DELETE /api/v1/subscription` | Lepaskan subscription consumer |
| `POST /api/v1/consume` | Peek non-destruktif (monitoring, tidak commit) |
| `GET /api/v1/queue` · `/api/v1/queue/{name}` | Info backlog queue |
| `GET /api/v1/exchange/{name}` | Daftar binding exchange |
| `GET /connections` | Koneksi publisher/consumer aktif |
| `GET /statistics` | Total publish/consume/fail, laju proses |
| `GET /health` · `/status` · `POST /config/reload` | Health, status operasional, reload config |

Konfigurasi (host, port, exchange, queue, prefetch_count, retry_count) juga dimuat
dari Configuration Service.

---

## 3. Cara Menjalankan

### Langkah 0 — Prasyarat (sekali)

```powershell
# dari root repo streaming-platform/
# 1) Virtual environment sudah ada di .env\ (Python 3.12)
#    Jika belum, buat dan install dependensi:
python -m venv .env
.\.env\Scripts\pip install -r requirements\development.txt
.\.env\Scripts\pip install -e shared-sdk

# 2) Jalankan Kafka (sudah sehat sejak awal):
docker compose -f docker/docker-compose.yml up -d kafka
docker ps          # pastikan aslp-kafka status "healthy"
```

> Catatan penamaan: folder virtual environment bernama `.env\` (bukan `.venv`),
> jangan tertukar dengan file konfigurasi `.env`.

### Langkah 1 — Configuration Service (port 8001)

```powershell
cd services\configuration-service
..\..\.env\Scripts\python.exe main.py
```

Cek: <http://localhost:8001/api/v1/health>
Database SQLite beserta seed konfigurasi default dibuat otomatis saat pertama kali jalan.

### Langkah 2 — Streaming Preprocessing Service (port 8002)

```powershell
cd services\streaming-preprocessing-service
..\..\.env\Scripts\python.exe main.py
```

Cek: <http://localhost:8002/health>

### Langkah 3 — Message Broker Service (port 8003)

```powershell
cd services\message-broker
..\..\.env\Scripts\python.exe main.py
```

Cek: <http://localhost:8003/health> — field `kafka` harus `"connected"`.

Urutan penting: **Configuration Service dulu**, baru dua lainnya (keduanya memuat
konfigurasi saat startup; bila configuration-service mati mereka tetap jalan dengan
default lokal).

### Langkah 4 — Uji alur end-to-end (CSV → preprocessing → broker)

```powershell
# mulai stream dari sample_data/sample.csv
curl -X POST http://localhost:8002/stream/start `
  -H "Content-Type: application/json" `
  -d "{\"source_path\": \"sample_data/sample.csv\", \"batch_size\": 5}"

# pantau progres
curl http://localhost:8002/stream/status
curl http://localhost:8002/statistics

# verifikasi pesan tiba di broker (peek non-destruktif)
curl -X POST http://localhost:8003/api/v1/consume `
  -H "Content-Type: application/json" `
  -d "{\"queue\": \"stream_exchange__stream_data\", \"max_messages\": 5, \"timeout_ms\": 3000}"

# hentikan stream
curl -X POST http://localhost:8002/stream/stop
```

### Langkah 5 — Contoh consumer dengan ack + DLQ (broker)

```powershell
# daftarkan consumer group
curl -X POST http://localhost:8003/api/v1/subscribe `
  -H "Content-Type: application/json" `
  -d "{\"queue\": \"stream_exchange__stream_data\", \"group_id\": \"oml-engine\"}"

# ambil pesan (offset BELUM di-commit sampai ack)
curl -X POST http://localhost:8003/api/v1/fetch `
  -H "Content-Type: application/json" `
  -d "{\"queue\": \"stream_exchange__stream_data\", \"group_id\": \"oml-engine\", \"max_messages\": 10}"

# acknowledgement (tempel delivery_tag dari hasil fetch)
curl -X POST http://localhost:8003/api/v1/ack `
  -H "Content-Type: application/json" `
  -d "{\"queue\": \"stream_exchange__stream_data\", \"group_id\": \"oml-engine\", \"delivery_tag\": \"<topic>:<partition>:<offset>\"}"

# tolak pesan: requeue=true kirim ulang; requeue=false masuk DLQ (<queue>__dlq)
curl -X POST http://localhost:8003/api/v1/nack `
  -H "Content-Type: application/json" `
  -d "{\"queue\": \"stream_exchange__stream_data\", \"group_id\": \"oml-engine\", \"delivery_tag\": \"...\", \"requeue\": false, \"reason\": \"bad payload\"}"
```

### Menghentikan semua

Tekan `Ctrl+C` di tiap terminal service, lalu:

```powershell
docker compose -f docker/docker-compose.yml stop kafka
```

---

## 4. Testing

Semua smoke test ada di folder `testing_test/` dan dijalankan dengan venv proyek
(`.env\Scripts\python.exe`). Bagian statis berjalan mandiri; bagian HTTP butuh
service live (jalankan dulu sesuai Bagian 3).

| Perintah | Cakupan | Hasil terakhir |
|---|---|---|
| `.env\Scripts\python.exe testing_test\milestone2_smoke_test.py` | Configuration Service (endpoint, DB, CRUD) | 23/23 PASS |
| `.env\Scripts\python.exe testing_test\milestone3_smoke_test.py` | Preprocessing Service (import, route, CSV reader, StreamMessage, alur start→stop) | 23/23 PASS |
| `.env\Scripts\python.exe testing_test\milestone4_smoke_test.py` | Message Broker (import, route, health, publish REST contract, consume, queue/exchange info, statistics) | 12/12 PASS (butuh broker live + Kafka) |

Hasil tiap eksekusi tersimpan di `testing_test/milestone*_smoke_result.json`.

Verifikasi tambahan yang sudah dilakukan (tidak termasuk smoke test resmi):

- Pipeline preprocessing terkendali config: validasi (fill missing value),
  duplikat keep_first, parameter sesi dari Configuration Service, override
  eksplisit request menang.
- Broker end-to-end langsung ke Kafka: publish → fetch → ack → nack-DLQ →
  redelivery requeue; isi DLQ memuat `_dead_letter.reason`.
- REST broker live: subscribe/fetch/ack/nack/unsubscribe 200,
  unsubscribe ganda 404.

---

## 5. Deviasi Desain yang Perlu Diketahui

| Desain dokumen | Implementasi | Alasan/status |
|---|---|---|
| SAS-07 memakai RabbitMQ | Apache Kafka | Transport final; konsep exchange/queue/DLQ tetap dipetakan |
| Reader multi-sumber (CSV/JSON/MongoDB/REST) | Baru CSV (docs/05 §14) | Sumber lain menyusul |
| Response standar `{success, message, data, timestamp}` (docs/12) | Belum seragam di semua endpoint | Endpoint baru `GET /config/{service_name}` sudah pakai format SDK |
| `scripts/run_all.py` | Masih placeholder | Start service masih manual per terminal |

## 6. Langkah Berikutnya

- SAS-08 Online ML Engine: consumer pertama nyata dari broker (memakai
  subscribe/fetch/ack yang baru selesai dibangun).
- Menyeragamkan response format docs/12 via `shared_sdk.responses`.

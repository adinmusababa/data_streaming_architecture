# 05. Streaming Preprocessing Service

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Streaming Preprocessing Service |
| Document Code | SAS-06 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan arsitektur, workflow, struktur project, modul, serta target implementasi Streaming Preprocessing Service sebagai pintu masuk utama data streaming. |

---

# 1. Purpose

Streaming Preprocessing Service merupakan service pertama pada arsitektur integrasi data streaming.

Service ini bertanggung jawab membaca data dari berbagai sumber, melakukan preprocessing, membentuk format data yang seragam, kemudian mengirimkan data tersebut ke Message Broker.

Online ML Engine tidak diperbolehkan melakukan preprocessing data.

Seluruh proses preprocessing harus diselesaikan pada service ini.

---

# 2. Goals

Streaming Preprocessing Service memiliki beberapa tujuan utama.

## Goal 1

Menghubungkan berbagai sumber data.

Target

- Mendukung berbagai jenis data source.
- Mudah menambahkan source baru.

---

## Goal 2

Melakukan preprocessing secara terpusat.

Target

- Validasi data.
- Data cleaning.
- Feature engineering.
- Data transformation.

---

## Goal 3

Menghasilkan format data yang konsisten.

Target

Seluruh data yang dikirim ke Message Broker memiliki format yang sama.

---

## Goal 4

Mengirimkan data ke Message Broker.

Target

Publisher berjalan secara stabil.

---

# 3. Responsibilities

Streaming Preprocessing Service bertanggung jawab terhadap:

- Membaca data source.
- Mengambil konfigurasi dari Configuration Service.
- Melakukan validasi data.
- Membersihkan data.
- Melakukan transformasi data.
- Melakukan feature engineering.
- Menyusun payload standar.
- Mengirim data ke Message Broker.
- Menyimpan log proses preprocessing.

Service ini tidak bertanggung jawab terhadap proses machine learning.

---

# 4. High Level Workflow

```
Datasource

↓

Read Data

↓

Validation

↓

Cleaning

↓

Transformation

↓

Feature Engineering

↓

Build Payload

↓

Publish

↓

Message Broker
```

---

# 5. Supported Data Sources

Pada tahap pertama service harus mendukung beberapa sumber data berikut.

- CSV File
- JSON File
- MongoDB
- PostgreSQL
- REST API

Pengembangan selanjutnya dapat ditambahkan:

- Kafka
- MQTT
- Sensor IoT
- Apache Flink
- Apache Spark
- Cloud Storage

---

# 6. Internal Architecture

```
Streaming Preprocessing Service

│

├── Configuration Client

├── Source Reader

├── Data Validator

├── Data Cleaner

├── Feature Processor

├── Payload Builder

├── Publisher

├── Logger

└── REST API
```

---

# 7. Folder Structure

```
streaming-preprocessing-service/

app/

api/

core/

reader/

validators/

cleaners/

transformers/

features/

publisher/

clients/

models/

schemas/

services/

routes/

utils/

logs/

tests/

main.py

requirements.txt
```

---

# 8. Module Responsibilities

## Configuration Client

Mengambil konfigurasi dari Configuration Service.

---

## Source Reader

Membaca data dari berbagai sumber.

---

## Validator

Memastikan struktur data valid.

---

## Cleaner

Membersihkan data.

Contoh

- Missing Value
- Invalid Value
- Duplicate

---

## Transformer

Melakukan transformasi data.

Contoh

- Encoding
- Normalisasi
- Standardisasi
- Type Conversion

---

## Feature Processor

Melakukan feature engineering.

Contoh

- Window Feature
- Aggregation
- Derived Feature

---

## Payload Builder

Menyusun payload standar.

---

## Publisher

Mengirim data menuju Message Broker.

---

# 9. Standard Payload

Seluruh data yang dikirim ke broker harus memiliki struktur yang sama.

Contoh

```json
{
    "stream_id": "",
    "timestamp": "",
    "source": "",
    "event_type": "",
    "data": {},
    "metadata": {}
}
```

Keterangan

- stream_id : identitas stream
- timestamp : waktu data diproses
- source : asal data
- event_type : jenis event
- data : hasil preprocessing
- metadata : informasi tambahan

---

# 10. Configuration Parameters

Service mengambil konfigurasi dari Configuration Service.

Contoh parameter

| Parameter | Description |
|------------|-------------|
| source_type | Jenis sumber data |
| batch_size | Ukuran batch |
| polling_interval | Interval pembacaan data |
| preprocessing_pipeline | Pipeline preprocessing |
| publish_topic | Nama topic atau queue |
| retry_count | Jumlah retry |

---

# 11. REST API

## Health

```
GET /health
```

---

## Status

```
GET /status
```

---

## Start Streaming

```
POST /stream/start
```

---

## Stop Streaming

```
POST /stream/stop
```

---

## Get Configuration

```
GET /config
```

---

## Reload Configuration

```
POST /config/reload
```

---

## Statistics

```
GET /statistics
```

Informasi yang ditampilkan

- Total Data
- Total Publish
- Error Count
- Processing Time

---

# 12. Logging

Seluruh aktivitas berikut dicatat.

- Start Service
- Stop Service
- Configuration Request
- Data Read
- Validation Error
- Transformation Error
- Publish Success
- Publish Failed

---

# 13. Monitoring Information

Dashboard dapat membaca informasi berikut.

- Service Status
- Current Source
- Total Data Processed
- Processing Rate
- Publish Rate
- Error Rate
- Last Publish Time

---

# 14. Development Checklist

## Initialization

- [ ] Repository dibuat
- [ ] Virtual Environment
- [ ] FastAPI

---

## Source Reader

- [ ] CSV Reader
- [ ] JSON Reader
- [ ] MongoDB Reader
- [ ] PostgreSQL Reader
- [ ] REST API Reader

---

## Validation

- [ ] Schema Validation
- [ ] Missing Value
- [ ] Duplicate Detection

---

## Transformation

- [ ] Data Cleaning
- [ ] Encoding
- [ ] Normalization
- [ ] Type Conversion

---

## Feature Engineering

- [ ] Feature Builder
- [ ] Window Feature
- [ ] Aggregation

---

## Publisher

- [ ] Publish Message
- [ ] Retry Mechanism
- [ ] Error Handling

---

## API

- [ ] Health
- [ ] Status
- [ ] Start Streaming
- [ ] Stop Streaming
- [ ] Statistics

---

## Testing

- [ ] Unit Test
- [ ] Integration Test
- [ ] Streaming Test

---

# 15. Acceptance Criteria

Streaming Preprocessing Service dianggap selesai apabila:

- Service dapat dijalankan secara independen.
- Konfigurasi berhasil diambil dari Configuration Service.
- Data berhasil dibaca dari data source.
- Seluruh preprocessing berjalan dengan benar.
- Payload sesuai standar.
- Data berhasil dipublikasikan ke Message Broker.
- Monitoring Dashboard dapat membaca status service.

---

# 16. Future Development

Fitur berikut direncanakan untuk pengembangan selanjutnya.

- Multiple Source Reader
- Parallel Processing
- Dynamic Pipeline
- Plugin Preprocessing
- Stream Buffer
- Window Processing
- Event Filtering
- Rule Engine
- Data Quality Monitoring

---

# 17. Next Document

Dokumen berikutnya:

06-Message-Broker.md

Dokumen ini menjelaskan konfigurasi Message Broker, struktur komunikasi publish-subscribe, manajemen queue, serta integrasi dengan Streaming Preprocessing Service dan Online ML Engine.
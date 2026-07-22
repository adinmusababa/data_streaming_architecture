# 06. Message Broker

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Message Broker |
| Document Code | SAS-07 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan arsitektur Message Broker sebagai media komunikasi asynchronous antar service pada arsitektur integrasi data streaming. |

---

# 1. Purpose

Message Broker berfungsi sebagai media komunikasi asynchronous antar service pada sistem.

Message Broker hanya bertugas mengirimkan data dari Publisher menuju Consumer tanpa mengetahui isi data maupun logika bisnis yang diproses.

Dengan menggunakan Message Broker, setiap service dapat berjalan secara independen sehingga kegagalan pada satu service tidak secara langsung mempengaruhi service lainnya.

---

# 2. Goals

## Goal 1

Memisahkan komunikasi antar service.

Target

- Publisher tidak mengetahui Consumer.
- Consumer tidak mengetahui Publisher.

---

## Goal 2

Menyediakan komunikasi asynchronous.

Target

Data dapat diproses secara independen.

---

## Goal 3

Meningkatkan skalabilitas sistem.

Target

Penambahan Publisher maupun Consumer tidak memerlukan perubahan service lain.

---

## Goal 4

Menjadi media distribusi data streaming.

Target

Seluruh data streaming melewati Message Broker.

---

# 3. Responsibilities

Message Broker bertanggung jawab terhadap:

- Menerima data dari Publisher.
- Menyimpan message sementara.
- Mengirim message ke Consumer.
- Menjamin urutan pengiriman message.
- Menyediakan mekanisme retry apabila terjadi kegagalan.
- Menyediakan monitoring queue.

Message Broker tidak bertanggung jawab terhadap:

- Data preprocessing.
- Online Machine Learning.
- Penyimpanan state.
- Penyimpanan database.
- Monitoring model.

---

# 4. High Level Workflow

```
Streaming Preprocessing Service

        │

Publish Message

        │

        ▼

Message Broker

        │

Queue

        │

        ▼

Online ML Engine
```

---

# 5. Architecture

```
Publisher

        │

        ▼

Exchange

        │

        ▼

Queue

        │

        ▼

Consumer
```

Message Broker hanya menyediakan jalur komunikasi.

Seluruh data tetap diproses pada service masing-masing.

---

# 6. Internal Components

Message Broker terdiri dari beberapa komponen utama.

## Exchange

Bertugas menerima message dari Publisher.

---

## Queue

Tempat penyimpanan sementara sebelum message dikirim menuju Consumer.

---

## Routing

Menentukan tujuan pengiriman message.

---

## Consumer Connection

Menghubungkan Queue dengan Online ML Engine.

---

## Publisher Connection

Menghubungkan Streaming Preprocessing Service dengan Exchange.

---

# 7. Communication Flow

```
Datasource

↓

Streaming Preprocessing Service

↓

Publish

↓

Exchange

↓

Queue

↓

Consumer

↓

Online ML Engine
```

---

# 8. Queue Structure

Pada tahap pertama sistem hanya menggunakan satu queue utama.

```
stream_queue
```

Pengembangan selanjutnya memungkinkan beberapa queue.

Contoh

```
stream_queue

prediction_queue

training_queue

monitoring_queue

state_queue
```

---

# 9. Standard Message Format

Seluruh Publisher harus menggunakan payload yang sama.

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

Message Broker tidak melakukan validasi terhadap isi payload.

---

# 10. Configuration Parameters

Seluruh konfigurasi diperoleh dari Configuration Service.

Parameter

| Parameter | Description |
|------------|-------------|
| host | Host Message Broker |
| port | Port |
| username | Username |
| password | Password |
| exchange | Exchange Name |
| queue | Queue Name |
| routing_key | Routing Key |
| prefetch_count | Prefetch Message |
| retry_count | Retry Count |

---

# 11. Publisher Workflow

```
Read Configuration

↓

Connect Broker

↓

Connect Exchange

↓

Build Message

↓

Publish

↓

Success
```

---

# 12. Consumer Workflow

```
Connect Broker

↓

Subscribe Queue

↓

Receive Message

↓

Send To OML Engine

↓

Acknowledgement
```

---

# 13. REST API

Walaupun Message Broker berjalan sebagai middleware komunikasi, service ini tetap memiliki REST API untuk kebutuhan monitoring.

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

## Queue Information

```
GET /queue
```

---

## Statistics

```
GET /statistics
```

Menampilkan

- Total Message
- Total Publish
- Total Consume
- Queue Size
- Processing Rate

---

## Reload Configuration

```
POST /config/reload
```

---

# 14. Monitoring Information

Monitoring Dashboard dapat mengambil informasi berikut.

- Broker Status
- Queue Status
- Active Connection
- Queue Size
- Publish Rate
- Consume Rate
- Error Count
- Retry Count
- Last Message Timestamp

---

# 15. Logging

Seluruh aktivitas berikut dicatat.

- Broker Connected
- Broker Disconnected
- Publish Success
- Publish Failed
- Consumer Connected
- Consumer Disconnected
- Queue Error
- Retry Message

---

# 16. Folder Structure

```
message-broker/

app/

api/

broker/

clients/

config/

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

# 17. Development Checklist

## Initialization

- [ ] Repository
- [ ] FastAPI
- [ ] RabbitMQ

---

## Publisher

- [ ] Connection
- [ ] Publish
- [ ] Retry

---

## Consumer

- [ ] Subscribe
- [ ] Ack
- [ ] Retry

---

## Queue

- [ ] Queue Creation
- [ ] Exchange
- [ ] Routing Key

---

## API

- [ ] Health
- [ ] Status
- [ ] Queue
- [ ] Statistics

---

## Monitoring

- [ ] Queue Monitoring
- [ ] Connection Monitoring
- [ ] Publish Monitoring
- [ ] Consume Monitoring

---

## Testing

- [ ] Unit Test
- [ ] Queue Test
- [ ] Integration Test

---

# 18. Acceptance Criteria

Message Broker dianggap selesai apabila memenuhi kondisi berikut.

- Publisher berhasil mengirim data.
- Queue berhasil menerima data.
- Consumer berhasil menerima data.
- Message berhasil diteruskan menuju Online ML Engine.
- Monitoring Dashboard dapat membaca status broker.
- Seluruh endpoint REST API berjalan dengan baik.

---

# 19. Future Development

Pengembangan berikutnya dapat mencakup.

- Multiple Queue
- Multiple Exchange
- Dead Letter Queue
- Priority Queue
- Delayed Queue
- Broadcast Queue
- Topic Exchange
- Message Compression
- Message Encryption
- Automatic Retry
- Queue Auto Recovery

---

# 20. Next Document

Dokumen berikutnya adalah:

**08-OnlineML-Engine.md**

Dokumen ini menjelaskan rancangan Online Machine Learning Engine sebagai inti dari sistem, termasuk struktur modul, alur pemrosesan data streaming, pengelolaan model, integrasi dengan State Store dan Storage Layer, serta target implementasi engine yang akan dikembangkan secara mandiri menggunakan Python.
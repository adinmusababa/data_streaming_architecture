# 9. Storage Layer

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Storage Layer |
| Document Code | SAS-10 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan rancangan Storage Layer sebagai service yang bertanggung jawab mengelola seluruh proses penyimpanan data sistem melalui abstraction layer yang independen dari teknologi database. |

---

# 1. Purpose

Storage Layer merupakan service yang bertanggung jawab terhadap seluruh proses penyimpanan data pada sistem.

Service ini menyediakan abstraction layer sehingga service lain tidak perlu mengetahui jenis database yang digunakan.

Seluruh komunikasi terhadap media penyimpanan dilakukan melalui REST API Storage Layer.

Dengan pendekatan ini, perubahan database tidak akan mempengaruhi service lain.

---

# 2. Goals

## Goal 1

Menyediakan abstraction terhadap berbagai media penyimpanan.

Target

- Service tidak mengetahui jenis database.
- Mudah menambahkan backend baru.

---

## Goal 2

Menyediakan REST API penyimpanan data.

Target

Semua proses penyimpanan dilakukan melalui REST API.

---

## Goal 3

Memisahkan data berdasarkan kategori.

Target

Setiap jenis data memiliki repository masing-masing.

---

## Goal 4

Mendukung penelitian.

Target

Data eksperimen mudah disimpan, dicari, dan dianalisis.

---

# 3. Responsibilities

Storage Layer bertanggung jawab terhadap:

- Menyimpan data eksperimen.
- Menyimpan metrics.
- Menyimpan prediction.
- Menyimpan evaluation.
- Menyimpan metadata.
- Menyediakan REST API.
- Menyediakan monitoring storage.

Storage Layer tidak menjalankan machine learning.

Storage Layer tidak menyimpan state model.

---

# 4. High Level Workflow

```
Online ML Engine

↓

REST API

↓

Storage Layer

↓

Storage Manager

↓

Storage Adapter

↓

Database Backend
```

---

# 5. Internal Architecture

```
Storage Layer

│

├── REST API

├── Storage Manager

├── Adapter Manager

├── Repository

├── Validation

├── Logger

└── Database Backend
```

---

# 6. Folder Structure

```
storage-layer/

app/

api/

manager/

repository/

adapter/

schemas/

models/

routes/

utils/

clients/

logs/

tests/

main.py

requirements.txt
```

---

# 7. Module Responsibilities

## REST API

Menerima seluruh request penyimpanan.

---

## Storage Manager

Mengelola proses penyimpanan data.

---

## Adapter Manager

Menentukan adapter yang digunakan.

---

## Repository

Berinteraksi dengan backend storage.

---

## Validation

Memastikan data valid.

---

## Logger

Mencatat aktivitas storage.

---

# 8. Supported Data

Tahap pertama Storage Layer mendukung penyimpanan:

- Experiment
- Metrics
- Prediction
- Evaluation
- Metadata
- Service Log

Tahap berikutnya dapat dikembangkan menjadi:

- Artifact
- Feature Store
- Dataset
- Model Registry
- Audit Trail

---

# 9. Supported Storage Backend

Storage Layer tidak bergantung pada satu database.

Backend yang direncanakan:

- MongoDB
- PostgreSQL
- Redis
- SQLite
- Elasticsearch
- MinIO

Penambahan backend baru hanya memerlukan Adapter baru.

---

# 10. REST API

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

## Save Data

```
POST /storage
```

---

## Get Data

```
GET /storage/{collection}/{id}
```

---

## Update Data

```
PUT /storage/{collection}/{id}
```

---

## Delete Data

```
DELETE /storage/{collection}/{id}
```

---

## List Collection

```
GET /storage/{collection}
```

---

## Statistics

```
GET /statistics
```

---

## Reload Configuration

```
POST /config/reload
```

---

# 11. Data Categories

Storage Layer mengelola beberapa kategori data.

| Category | Description |
|----------|-------------|
| experiment | Hasil eksperimen |
| prediction | Hasil prediksi |
| metrics | Metrics Online ML |
| evaluation | Evaluasi model |
| logs | Log service |
| metadata | Metadata sistem |

---

# 12. Monitoring Information

Dashboard dapat mengambil informasi berikut.

- Storage Status
- Storage Provider
- Total Collections
- Total Documents
- Request Count
- Write Rate
- Read Rate
- Last Write
- Last Error

---

# 13. Logging

Storage Layer mencatat aktivitas berikut.

- Insert
- Update
- Delete
- Read
- Validation Error
- Storage Error
- Adapter Error

---

# 14. Configuration Parameters

Diambil dari Configuration Service.

| Parameter | Description |
|-----------|-------------|
| provider | Backend aktif |
| timeout | Request timeout |
| retry | Retry request |
| max_connection | Maksimum koneksi |
| database | Nama database |

---

# 15. Development Checklist

## Initialization

- [ ] Repository
- [ ] FastAPI

---

## API

- [ ] Save
- [ ] Read
- [ ] Update
- [ ] Delete

---

## Adapter

- [ ] MongoDB
- [ ] PostgreSQL
- [ ] Redis

---

## Monitoring

- [ ] Statistics
- [ ] Status
- [ ] Health

---

## Testing

- [ ] Unit Test
- [ ] Integration Test
- [ ] Adapter Test

---

# 16. Acceptance Criteria

Storage Layer dianggap selesai apabila:

- Data berhasil disimpan.
- Data berhasil dibaca.
- Data berhasil diperbarui.
- Data berhasil dihapus.
- Adapter dapat diganti tanpa mengubah service lain.
- Monitoring Dashboard dapat membaca informasi Storage Layer.

---

# 17. Future Development

Pengembangan berikutnya meliputi:

- Multi Database
- Database Replication
- Data Partitioning
- Storage Compression
- Storage Encryption
- Automatic Backup
- Distributed Storage
- Time-Series Database Adapter
- Object Storage Adapter
- Feature Store Adapter

---

# 18. Next Document

Dokumen berikutnya adalah:

**11-Monitoring-Dashboard.md**

Dokumen ini menjelaskan arsitektur Monitoring Dashboard berbasis Streamlit yang berfungsi sebagai pusat observabilitas sistem, menampilkan status seluruh service, konfigurasi, metrics, state model, dan informasi penyimpanan melalui REST API.
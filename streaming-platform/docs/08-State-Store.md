# 08. State Store

## Document Information

| Item | Description |
|------|-------------|
| Document Name | State Store |
| Document Code | SAS-09 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan rancangan State Store sebagai service yang bertanggung jawab mengelola seluruh state model Online Machine Learning. |

---

# 1. Purpose

State Store merupakan service yang bertanggung jawab mengelola seluruh state model Online Machine Learning.

Service ini berfungsi sebagai media penyimpanan state sehingga Online ML Engine tidak perlu mengetahui bagaimana maupun di mana state disimpan.

State Store hanya menyediakan REST API.

Seluruh proses penyimpanan, pembacaan, pembaruan maupun penghapusan state dilakukan melalui REST API tersebut.

---

# 2. Goals

State Store dikembangkan dengan tujuan berikut.

## Goal 1

Menyediakan penyimpanan state yang independen.

Target

- Online ML Engine tidak mengetahui media penyimpanan.
- State dapat dipindahkan ke backend lain tanpa mengubah Engine.

---

## Goal 2

Menyediakan REST API pengelolaan state.

Target

- Save State
- Load State
- Update State
- Delete State

---

## Goal 3

Mendukung pengembangan berbagai jenis state.

Target

Tahap pertama hanya mendukung model state.

Tahap berikutnya dapat mendukung checkpoint, operational state, cache, dan jenis state lainnya.

---

## Goal 4

Mempermudah recovery model.

Target

Model dapat dilanjutkan tanpa kehilangan proses pembelajaran.

---

# 3. Responsibilities

State Store bertanggung jawab terhadap:

- Menyimpan state model.
- Memuat state model.
- Memperbarui state model.
- Menghapus state model.
- Menyediakan metadata state.
- Menyediakan endpoint monitoring.

State Store tidak menjalankan algoritma Online Machine Learning.

State Store tidak melakukan evaluasi model.

---

# 4. High Level Workflow

```
Online ML Engine

↓

Generate State

↓

State Store

↓

Validation

↓

Storage Adapter

↓

Database
```

---

# 5. Internal Architecture

```
State Store

│

├── REST API

├── State Manager

├── Validation

├── Metadata Manager

├── Storage Adapter

├── Repository

├── Logger

└── Database
```

---

# 6. Folder Structure

```
state-store/

app/

api/

clients/

manager/

repository/

storage/

metadata/

schemas/

models/

routes/

utils/

logs/

tests/

main.py

requirements.txt
```

---

# 7. Module Responsibilities

## REST API

Menerima request dari service lain.

---

## State Manager

Mengatur seluruh lifecycle state.

---

## Validation

Memastikan state valid sebelum disimpan.

---

## Metadata Manager

Mengelola informasi tambahan mengenai state.

---

## Storage Adapter

Menghubungkan State Store dengan media penyimpanan.

---

## Repository

Berkomunikasi dengan backend penyimpanan.

---

## Logger

Mencatat seluruh aktivitas.

---

# 8. State Lifecycle

```
Create State

↓

Validate

↓

Save

↓

Update

↓

Load

↓

Delete
```

---

# 9. Supported State

Tahap pertama hanya mendukung:

```
Model State
```

Pengembangan berikutnya.

```
Checkpoint State

Operational State

Consumer Offset

Feature Cache

Window State

Evaluation State
```

---

# 10. Metadata Structure

Setiap state memiliki metadata.

| Field | Description |
|---------|-------------|
| state_id | ID state |
| model_name | Nama model |
| version | Versi state |
| created_at | Waktu dibuat |
| updated_at | Waktu diperbarui |
| description | Keterangan |

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

## Save State

```
POST /state
```

---

## Load State

```
GET /state/{state_id}
```

---

## Update State

```
PUT /state/{state_id}
```

---

## Delete State

```
DELETE /state/{state_id}
```

---

## List State

```
GET /state
```

---

## Metadata

```
GET /metadata
```

---

## Reload Configuration

```
POST /config/reload
```

---

# 12. Monitoring Information

Dashboard dapat membaca.

- Total State
- Active State
- Last Update
- State Version
- Storage Backend
- Total Request
- Service Status

---

# 13. Logging

Aktivitas yang dicatat.

- Save State
- Update State
- Delete State
- Load State
- Validation Error
- Database Error

---

# 14. Configuration Parameters

Diambil dari Configuration Service.

| Parameter | Description |
|------------|-------------|
| storage_provider | Backend penyimpanan |
| auto_save | Penyimpanan otomatis |
| save_interval | Interval penyimpanan |
| retry_count | Retry API |
| timeout | Timeout request |

---

# 15. Development Checklist

## Initialization

- [ ] Repository
- [ ] FastAPI

---

## API

- [ ] Save State
- [ ] Load State
- [ ] Update State
- [ ] Delete State
- [ ] Metadata

---

## Storage

- [ ] Storage Adapter
- [ ] Repository
- [ ] Validation

---

## Monitoring

- [ ] Health
- [ ] Status
- [ ] Metadata

---

## Testing

- [ ] Unit Test
- [ ] Integration Test
- [ ] Recovery Test

---

# 16. Acceptance Criteria

State Store dianggap selesai apabila.

- Online ML Engine berhasil menyimpan state.
- State dapat dimuat kembali.
- State berhasil diperbarui.
- Metadata berhasil ditampilkan.
- Dashboard berhasil melakukan monitoring.
- Service berjalan secara independen.

---

# 17. Future Development

Pengembangan berikutnya.

- State Versioning
- Checkpoint Manager
- Incremental State
- Snapshot State
- Distributed State
- State Compression
- State Encryption
- State Replication
- State Backup
- Automatic Recovery

---

# 18. Next Document

Dokumen berikutnya adalah:

**10-Storage-Layer.md**

Dokumen ini menjelaskan Storage Layer sebagai abstraction service yang menghubungkan seluruh komponen sistem dengan berbagai media penyimpanan tanpa membuat service lain bergantung pada jenis database tertentu.
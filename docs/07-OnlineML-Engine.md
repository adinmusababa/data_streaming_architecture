# 07. Online ML Engine

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Online ML Engine |
| Document Code | SAS-08 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan rancangan Online ML Engine sebagai inti sistem yang bertugas menerima data streaming, menjalankan proses pembelajaran online, melakukan prediksi, evaluasi, serta mengelola state model. |

---

# 1. Purpose

Online ML Engine merupakan komponen utama dalam arsitektur integrasi data streaming.

Service ini bertanggung jawab menerima data dari Message Broker, memproses data menggunakan algoritma Online Machine Learning, memperbarui model secara terus-menerus, menyimpan state model, serta mengirimkan hasil evaluasi dan metadata ke Storage Layer.

Berbeda dengan service lain, Online ML Engine dirancang sebagai lingkungan penelitian sehingga implementasi algoritma akan terus berkembang.

Engine tidak bergantung pada algoritma tertentu.

---

# 2. Goals

## Goal 1

Menerima data streaming secara real-time.

Target

- Data diterima tanpa kehilangan message.
- Data diproses sesuai urutan.

---

## Goal 2

Menyediakan framework pengembangan algoritma Online Machine Learning.

Target

- Algoritma dapat ditambahkan tanpa mengubah Engine.
- Engine dapat menjalankan satu atau beberapa model.

---

## Goal 3

Mengelola lifecycle model.

Target

- Model Initialization
- Learning
- Prediction
- Evaluation
- Save State

---

## Goal 4

Terintegrasi dengan State Store.

Target

- Model dapat menyimpan state.
- Model dapat dipulihkan.

---

## Goal 5

Terintegrasi dengan Storage Layer.

Target

- Metrics tersimpan.
- Prediction tersimpan.
- Experiment tersimpan.

---

# 3. Responsibilities

Online ML Engine bertanggung jawab terhadap:

- Mengambil konfigurasi dari Configuration Service.
- Menerima data streaming.
- Melakukan preprocessing ringan apabila diperlukan.
- Menjalankan algoritma Online Machine Learning.
- Melakukan update model.
- Melakukan prediksi.
- Menghitung metrik evaluasi.
- Menyimpan state model.
- Menyimpan hasil eksperimen.
- Menyediakan REST API monitoring.

Engine tidak bertanggung jawab terhadap preprocessing utama maupun penyimpanan database secara langsung.

---

# 4. High Level Workflow

```
Message Broker

↓

Receive Stream

↓

Validate Payload

↓

Feature Extraction (Optional)

↓

Online Learning

↓

Prediction

↓

Evaluation

↓

Save State

↓

Storage Layer

↓

Monitoring Dashboard
```

---

# 5. Internal Architecture

```
Online ML Engine

│

├── Configuration Client

├── Broker Consumer

├── Stream Manager

├── Model Manager

├── Learning Engine

├── Prediction Engine

├── Evaluation Engine

├── State Manager

├── Storage Client

├── Monitoring API

└── Logger
```

---

# 6. Folder Structure

```
online-ml-engine/

app/

api/

clients/

consumer/

engine/

models/

evaluation/

metrics/

state/

storage/

configuration/

schemas/

routes/

utils/

logs/

tests/

main.py

requirements.txt
```

---

# 7. Module Responsibilities

## Configuration Client

Mengambil konfigurasi dari Configuration Service.

---

## Broker Consumer

Mengambil data dari Message Broker.

---

## Stream Manager

Mengelola aliran data yang masuk.

---

## Model Manager

Mengatur lifecycle model.

Tugas

- Load Model
- Initialize Model
- Switch Model
- Reset Model

---

## Learning Engine

Menjalankan proses pembelajaran online.

---

## Prediction Engine

Menghasilkan prediksi.

---

## Evaluation Engine

Menghitung metrik evaluasi.

---

## State Manager

Mengelola komunikasi dengan State Store.

---

## Storage Client

Mengirim data menuju Storage Layer.

---

## Monitoring API

Menyediakan endpoint monitoring.

---

# 8. Model Lifecycle

```
Initialize Model

↓

Receive Data

↓

Learn

↓

Predict

↓

Evaluate

↓

Save State

↓

Wait Next Data
```

Proses di atas berlangsung secara terus-menerus selama service berjalan.

---

# 9. Data Flow

```
Message Broker

↓

Online ML Engine

↓

Model

↓

Prediction

↓

Evaluation

↓

State Store

↓

Storage Layer
```

---

# 10. Configuration Parameters

Konfigurasi diperoleh dari Configuration Service.

| Parameter | Description |
|-----------|-------------|
| model_name | Nama model aktif |
| learning_rate | Parameter model |
| batch_size | Ukuran batch jika diperlukan |
| state_interval | Interval penyimpanan state |
| evaluation_interval | Interval evaluasi |
| prediction_interval | Interval prediksi |

Parameter tambahan akan bergantung pada algoritma yang digunakan.

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

## Model Information

```
GET /model
```

---

## Model Metrics

```
GET /metrics
```

---

## Prediction Statistics

```
GET /prediction
```

---

## Learning Statistics

```
GET /learning
```

---

## Reload Configuration

```
POST /config/reload
```

---

## Save State

```
POST /state/save
```

---

## Load State

```
POST /state/load
```

---

# 12. Monitoring Information

Monitoring Dashboard dapat mengambil informasi berikut.

- Active Model
- Running Status
- Learning Status
- Prediction Rate
- Learning Rate
- Processed Records
- Active State
- Last Update
- Processing Latency

---

# 13. Logging

Aktivitas yang dicatat.

- Engine Started
- Engine Stopped
- Configuration Loaded
- Data Received
- Learning Completed
- Prediction Generated
- State Saved
- State Loaded
- Evaluation Updated
- Error

---

# 14. Development Checklist

## Initialization

- [ ] Repository
- [ ] Virtual Environment
- [ ] REST API

---

## Consumer

- [ ] Broker Connection
- [ ] Message Receiver

---

## Model

- [ ] Model Manager
- [ ] Learning Engine
- [ ] Prediction Engine

---

## Evaluation

- [ ] Online Metrics
- [ ] Statistics

---

## State

- [ ] Save State
- [ ] Load State

---

## Storage

- [ ] Storage Client
- [ ] Metrics Upload

---

## Monitoring

- [ ] Health
- [ ] Status
- [ ] Metrics
- [ ] Learning
- [ ] Prediction

---

## Testing

- [ ] Unit Test
- [ ] Streaming Test
- [ ] Integration Test

---

# 15. Acceptance Criteria

Online ML Engine dianggap selesai apabila memenuhi kondisi berikut.

- Berhasil menerima data dari Message Broker.
- Model berhasil melakukan pembelajaran online.
- Prediksi berhasil dihasilkan.
- State model berhasil disimpan.
- Metrics berhasil dikirim ke Storage Layer.
- Dashboard dapat menampilkan status Engine.

---

# 16. Future Development

Fitur berikut direncanakan untuk tahap selanjutnya.

- Multi Model Execution
- Model Switching
- Drift Detection
- Ensemble Learning
- Hyperparameter Adaptation
- Incremental Feature Selection
- Online Feature Engineering
- Automatic Checkpoint
- Plugin Algorithm
- Experiment Manager
- Distributed Online Learning

---

# 17. Next Document

Dokumen berikutnya adalah:

**09-State-Store.md**

Dokumen ini menjelaskan rancangan State Store sebagai service independen yang bertugas menyimpan, memuat, memperbarui, dan mengelola state model Online Machine Learning sehingga model dapat dipulihkan tanpa kehilangan informasi pembelajaran.
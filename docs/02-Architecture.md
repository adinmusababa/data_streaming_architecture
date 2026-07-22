# 02. Architecture

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Architecture |
| Document Code | SAS-02 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan arsitektur integrasi data streaming, hubungan antar service, aturan komunikasi, serta roadmap implementasi arsitektur. |

---

# 1. Purpose

Dokumen ini menjelaskan rancangan arsitektur utama sistem yang akan digunakan sebagai pedoman selama proses pengembangan.

Fokus utama dokumen ini bukan menjelaskan implementasi source code, melainkan menjelaskan bagaimana setiap service saling berinteraksi, batas tanggung jawab masing-masing service, serta aturan komunikasi antar service.

Seluruh implementasi source code nantinya harus mengikuti rancangan arsitektur yang dijelaskan pada dokumen ini.

---

# 2. Architecture Goals

Arsitektur ini dirancang dengan beberapa tujuan utama.

## Goal 1

Membagi sistem menjadi beberapa service independen.

Target

- Service dapat dijalankan secara terpisah.
- Service dapat dikembangkan secara mandiri.
- Service dapat diganti tanpa mempengaruhi service lain.

---

## Goal 2

Menyediakan komunikasi yang sederhana.

Target

- REST API digunakan untuk komunikasi service.
- Message Broker digunakan untuk distribusi data streaming.

---

## Goal 3

Menyediakan konfigurasi terpusat.

Target

- Seluruh konfigurasi berasal dari Configuration Service.
- Tidak ada konfigurasi yang ditulis secara hardcode.

---

## Goal 4

Menyediakan platform yang mudah dikembangkan.

Target

- Penambahan algoritma baru tidak mengubah arsitektur.
- Penambahan database baru tidak mengubah Online ML Engine.

---

# 3. High Level Architecture

Sistem terdiri atas tujuh service utama.

```
                   Configuration Service
                            │
            REST API Configuration
                            │
────────────────────────────────────────────────────

Datasource
      │
      ▼
Streaming Preprocessing Service
      │
      ▼
Message Broker
      │
      ▼
Online ML Engine
      │
      ├──────────────► State Store
      │
      └──────────────► Storage Layer

────────────────────────────────────────────────────

Monitoring Dashboard
        │
        ├────────► Configuration Service
        ├────────► Online ML Engine
        ├────────► State Store
        └────────► Storage Layer
```

---

# 4. Architecture Layer

Walaupun seluruh sistem menggunakan microservices, setiap service memiliki peran yang berbeda.

| Layer | Service |
|--------|----------|
| Management Layer | Configuration Service |
| Processing Layer | Streaming Preprocessing Service |
| Streaming Layer | Message Broker |
| Intelligence Layer | Online ML Engine |
| Persistence Layer | State Store |
| Persistence Layer | Storage Layer |
| Presentation Layer | Monitoring Dashboard |

---

# 5. Service Responsibility

## Configuration Service

Tanggung jawab

- Menyimpan konfigurasi seluruh service.
- Menyediakan REST API konfigurasi.
- Menyediakan endpoint update konfigurasi.
- Menjadi pusat konfigurasi sistem.

Output

Konfigurasi seluruh service.

---

## Streaming Preprocessing Service

Tanggung jawab

- Membaca data source.
- Membersihkan data.
- Melakukan preprocessing.
- Mengirim data ke Message Broker.

Output

Streaming data yang telah diproses.

---

## Message Broker

Tanggung jawab

- Mengirim data streaming.
- Menjadi media komunikasi asynchronous.

Output

Streaming message.

---

## Online ML Engine

Tanggung jawab

- Menerima data streaming.
- Menjalankan Online Machine Learning.
- Menghasilkan prediksi.
- Menyimpan state model.
- Menyimpan hasil eksperimen.

Output

Model state.

Prediction.

Metrics.

---

## State Store

Tanggung jawab

- Menyimpan state model.
- Mengambil state model.
- Menghapus state model.
- Menyediakan API state.

Output

State model.

---

## Storage Layer

Tanggung jawab

- Menyimpan hasil eksperimen.
- Menyimpan metrics.
- Menyimpan log.
- Menjadi abstraction database.

Output

Persistent data.

---

## Monitoring Dashboard

Tanggung jawab

- Menampilkan status service.
- Menampilkan konfigurasi.
- Menampilkan state model.
- Menampilkan metrics.

Output

Dashboard monitoring.

---

# 6. Communication Rules

Seluruh komunikasi mengikuti aturan berikut.

| Source | Destination | Communication |
|----------|-------------|----------------|
| Dashboard | Configuration Service | REST API |
| Dashboard | State Store | REST API |
| Dashboard | Storage Layer | REST API |
| Dashboard | Online ML Engine | REST API |
| Preprocessing | Broker | Publish |
| Broker | OML Engine | Subscribe |
| OML Engine | State Store | REST API |
| OML Engine | Storage Layer | REST API |
| Semua Service | Configuration Service | REST API |

---

# 7. Development Rules

Selama proses implementasi, seluruh service harus mengikuti aturan berikut.

- Setiap service memiliki folder sendiri.
- Setiap service memiliki REST API.
- Setiap service memiliki endpoint `/health`.
- Setiap service memiliki endpoint `/status`.
- Setiap service memiliki endpoint `/config`.
- Seluruh log dipisahkan dari source code.
- Tidak ada komunikasi langsung antar database.

---

# 8. Development Sequence

Pengembangan dilakukan secara bertahap.

## Tahap 1

Configuration Service

Target

Seluruh service dapat mengambil konfigurasi.

Deliverable

- REST API
- Database konfigurasi
- Endpoint konfigurasi

Status

Belum dikerjakan.

---

## Tahap 2

Streaming Preprocessing Service

Target

Data berhasil dikirim ke broker.

Deliverable

- Data Reader
- Preprocessing
- Publisher

Status

Belum dikerjakan.

---

## Tahap 3

Message Broker

Target

Streaming data berjalan.

Deliverable

- Queue
- Publish
- Subscribe

Status

Belum dikerjakan.

---

## Tahap 4

Online ML Engine

Target

Model menerima data streaming.

Deliverable

- Consumer
- Model
- Evaluation
- Metrics

Status

Belum dikerjakan.

---

## Tahap 5

State Store

Target

State model berhasil disimpan.

Deliverable

- Save
- Load
- Delete

Status

Belum dikerjakan.

---

## Tahap 6

Storage Layer

Target

Data hasil eksperimen berhasil disimpan.

Deliverable

- Storage API
- Adapter Database

Status

Belum dikerjakan.

---

## Tahap 7

Monitoring Dashboard

Target

Seluruh service dapat dipantau.

Deliverable

- Dashboard
- Monitoring
- Service Status
- Configuration Viewer

Status

Belum dikerjakan.

---

# 9. Folder Structure

```
streaming-platform/

docs/

services/

configuration-service/

preprocessing-service/

online-ml-engine/

state-store/

storage-layer/

monitoring-dashboard/

shared/

scripts/

tests/
```

---

# 10. Expected Result

Setelah seluruh tahapan selesai, sistem diharapkan memiliki karakteristik berikut.

- Setiap service dapat berjalan secara independen.
- Seluruh konfigurasi dapat diubah melalui REST API.
- Online ML Engine dapat dikembangkan tanpa mempengaruhi service lain.
- State model dapat disimpan secara terpisah.
- Storage dapat menggunakan berbagai jenis database.
- Monitoring dapat dilakukan melalui satu dashboard.
- Arsitektur mudah dikembangkan untuk penelitian selanjutnya.

---

# Next Document

Dokumen berikutnya adalah:

**03-Development-Roadmap.md**

Dokumen tersebut menjelaskan roadmap implementasi secara rinci, mulai dari struktur repository, milestone pengembangan, target setiap tahap, checklist implementasi, hingga urutan pengerjaan setiap service.
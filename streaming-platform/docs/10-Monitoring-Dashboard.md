# 10. Monitoring Dashboard

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Monitoring Dashboard |
| Document Code | SAS-11 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan rancangan Monitoring Dashboard sebagai pusat monitoring dan operasional seluruh arsitektur integrasi data streaming. |

---

# 1. Purpose

Monitoring Dashboard merupakan antarmuka utama sistem.

Dashboard bertugas menampilkan kondisi seluruh service secara real-time melalui REST API yang disediakan oleh masing-masing service.

Dashboard tidak melakukan pemrosesan data maupun machine learning.

Dashboard hanya mengambil informasi kemudian menampilkannya kepada pengguna.

---

# 2. Goals

## Goal 1

Menyediakan monitoring terpusat.

Target

Seluruh service dapat dipantau pada satu dashboard.

---

## Goal 2

Menyediakan visualisasi kondisi sistem.

Target

Pengguna dapat mengetahui kondisi sistem secara real-time.

---

## Goal 3

Menyediakan akses konfigurasi.

Target

Konfigurasi dapat dilihat dan diperbarui melalui Configuration Service.

---

## Goal 4

Menyediakan observability.

Target

Status seluruh komponen dapat diketahui tanpa membuka log masing-masing service.

---

# 3. Responsibilities

Monitoring Dashboard bertanggung jawab terhadap:

- Menampilkan status service.
- Menampilkan konfigurasi sistem.
- Menampilkan kondisi Message Broker.
- Menampilkan status Online ML Engine.
- Menampilkan informasi State Store.
- Menampilkan informasi Storage Layer.
- Menampilkan metrics.
- Menampilkan log sederhana.

Dashboard tidak menyimpan data.

Dashboard tidak menjalankan machine learning.

Dashboard tidak mengakses database secara langsung.

---

# 4. High Level Workflow

```
Configuration Service

        │

State Store

        │

Storage Layer

        │

Online ML Engine

        │

Message Broker

        │

Streaming Service

        │

        ▼

REST API Client

        │

        ▼

Monitoring Dashboard

        │

        ▼

User
```

---

# 5. Internal Architecture

```
Monitoring Dashboard

│

├── REST Client Layer

├── Dashboard Pages

├── Widget Manager

├── Visualization

├── Session Manager

├── Logger
```

---

# 6. Folder Structure

```
monitoring-dashboard/

app/

pages/

clients/

components/

widgets/

charts/

models/

schemas/

utils/

logs/

tests/

main.py

requirements.txt
```

---

# 7. Module Responsibilities

## REST Client Layer

Berkomunikasi dengan seluruh service melalui REST API.

---

## Dashboard Pages

Berisi halaman dashboard.

---

## Components

Komponen yang digunakan bersama.

---

## Widget Manager

Mengelola widget monitoring.

---

## Charts

Visualisasi data.

---

## Logger

Mencatat aktivitas dashboard.

---

# 8. Dashboard Pages

Tahap pertama dashboard terdiri dari beberapa halaman.

## Home

Menampilkan ringkasan sistem.

---

## Configuration

Menampilkan seluruh konfigurasi sistem.

Data berasal dari Configuration Service.

---

## Streaming

Menampilkan kondisi Streaming Preprocessing Service.

---

## Message Broker

Menampilkan kondisi Queue.

---

## Online ML Engine

Menampilkan informasi model.

---

## State Store

Menampilkan seluruh state model.

---

## Storage Layer

Menampilkan kondisi storage.

---

## Metrics

Menampilkan metrik model.

---

## Logs

Menampilkan ringkasan log seluruh service.

---

# 9. REST Client

Dashboard menggunakan client terpisah untuk setiap service.

```
clients/

configuration_client.py

streaming_client.py

broker_client.py

oml_client.py

state_client.py

storage_client.py
```

Seluruh komunikasi dilakukan melalui client tersebut.

Halaman dashboard tidak diperbolehkan melakukan request HTTP secara langsung.

---

# 10. Monitoring Information

## Configuration Service

- Service Status
- Total Configuration
- Last Update

---

## Streaming Service

- Current Source
- Processed Data
- Processing Rate

---

## Message Broker

- Queue Size
- Publish Rate
- Consume Rate

---

## Online ML Engine

- Active Model
- Processed Records
- Prediction Rate
- Learning Rate
- Active Metrics

---

## State Store

- Active State
- State Version
- Save Count

---

## Storage Layer

- Storage Provider
- Total Collections
- Write Rate
- Read Rate

---

# 11. Charts

Dashboard minimal menyediakan visualisasi berikut.

- Service Status
- Queue Activity
- Processing Rate
- Prediction Rate
- Metrics History
- State History
- Storage Usage

---

# 12. Refresh Strategy

Dashboard tidak menggunakan WebSocket pada tahap pertama.

Seluruh data diperbarui menggunakan polling REST API.

Interval refresh diperoleh dari Configuration Service.

---

# 13. Logging

Dashboard mencatat aktivitas berikut.

- Login Dashboard
- API Error
- Service Unavailable
- Refresh Dashboard

---

# 14. Development Checklist

## Initialization

- [ ] Streamlit
- [ ] Folder Structure

---

## REST Client

- [ ] Configuration Client
- [ ] Streaming Client
- [ ] Broker Client
- [ ] OML Client
- [ ] State Client
- [ ] Storage Client

---

## Dashboard

- [ ] Home
- [ ] Configuration
- [ ] Streaming
- [ ] Broker
- [ ] Online ML
- [ ] State Store
- [ ] Storage Layer

---

## Visualization

- [ ] Tables
- [ ] Charts
- [ ] Status Cards

---

## Testing

- [ ] API Test
- [ ] Dashboard Test

---

# 15. Acceptance Criteria

Monitoring Dashboard dianggap selesai apabila:

- Seluruh service dapat dipantau.
- Dashboard dapat mengambil data dari seluruh REST API.
- Konfigurasi dapat ditampilkan.
- Metrics dapat ditampilkan.
- State dapat ditampilkan.
- Storage dapat dipantau.
- Dashboard berjalan secara stabil.

---

# 16. Future Development

Tahap berikutnya dashboard akan dikembangkan menjadi pusat operasional sistem.

Fitur yang direncanakan:

- Start Service
- Stop Service
- Restart Service
- Edit Configuration
- Model Selection
- State Recovery
- Storage Management
- Alert Notification
- Authentication
- Authorization
- User Management
- Theme Management
- Plugin Dashboard

---

# 17. Next Document

Dokumen berikutnya adalah:

**12-Shared-SDK.md**

Dokumen ini menjelaskan library bersama yang digunakan oleh seluruh service agar komunikasi REST API, logging, schema, konfigurasi, serta utility memiliki implementasi yang konsisten dan tidak terjadi duplikasi kode.
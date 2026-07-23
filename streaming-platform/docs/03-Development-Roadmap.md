# 03. Development Roadmap

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Development Roadmap |
| Document Code | SAS-03 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan urutan implementasi sistem, target setiap tahapan, deliverables, dan acceptance criteria selama proses pengembangan. |

---

# 1. Purpose

Dokumen ini digunakan sebagai panduan implementasi seluruh sistem.

Setiap tahapan pengembangan memiliki target yang jelas sehingga proses implementasi dapat dilakukan secara bertahap, terukur, dan mudah dievaluasi.

Seluruh service dikembangkan secara incremental.

Tahapan berikutnya hanya dapat dimulai apabila target pada tahap sebelumnya telah terpenuhi.

---

# 2. Development Strategy

Pengembangan sistem dilakukan menggunakan pendekatan Incremental Development.

Setiap service dibangun secara mandiri dan diuji sebelum melanjutkan ke service berikutnya.

Keuntungan pendekatan ini antara lain:

- Mempermudah debugging.
- Mempermudah integrasi.
- Mengurangi ketergantungan antar service.
- Mempermudah pengembangan fitur baru.
- Mengurangi risiko kegagalan sistem.

---

# 3. Development Flow

```

Planning

↓

Repository Preparation

↓

Configuration Service

↓

Streaming Preprocessing Service

↓

Message Broker

↓

Online ML Engine

↓

State Store

↓

Storage Layer

↓

Monitoring Dashboard

↓

Integration Testing

↓

System Validation

```

---

# 4. Development Milestones

## Milestone 1

### Repository Initialization

Goal

Membangun struktur project utama.

Deliverables

- Root Repository
- Folder Services
- Folder Documentation
- Folder Shared
- Folder Scripts
- Folder Testing

Checklist

- [ ] Repository dibuat
- [ ] Struktur folder selesai
- [ ] README tersedia
- [ ] Dokumentasi SAS tersedia

Acceptance Criteria

Repository dapat digunakan sebagai dasar pengembangan.

---

## Milestone 2

### Configuration Service

Goal

Membangun pusat konfigurasi seluruh service.

Deliverables

- REST API
- Configuration Database
- CRUD Configuration
- Service Registration

Checklist

- [ ] FastAPI berjalan
- [ ] Database konfigurasi tersedia
- [ ] Endpoint GET Config
- [ ] Endpoint UPDATE Config
- [ ] Endpoint DELETE Config
- [ ] Endpoint Service Registration
- [ ] Endpoint Health

Acceptance Criteria

Seluruh service dapat mengambil konfigurasi melalui REST API.

---

## Milestone 3

### Streaming Preprocessing Service

Goal

Menyiapkan seluruh data streaming sebelum dikirim menuju Message Broker.

Deliverables

- Data Reader
- Data Validation
- Data Cleaning
- Feature Engineering
- Publisher

Checklist

- [ ] Source Reader
- [ ] Validation
- [ ] Transformation
- [ ] Feature Extraction
- [ ] Publisher
- [ ] Logging

Acceptance Criteria

Data berhasil dipublikasikan ke Message Broker.

---

## Milestone 4

### Message Broker

Goal

Menghubungkan seluruh pipeline streaming.

Deliverables

- Queue
- Exchange
- Publisher
- Consumer

Checklist

- [ ] Queue tersedia
- [ ] Publish berhasil
- [ ] Subscribe berhasil
- [ ] Retry berjalan
- [ ] Dead Letter Queue tersedia

Acceptance Criteria

Data berhasil diterima oleh Online ML Engine.

---

## Milestone 5

### Online ML Engine

Goal

Mengembangkan engine utama Online Machine Learning.

Deliverables

- Consumer
- Learning Engine
- Prediction Engine
- Evaluation Engine
- Metrics Engine

Checklist

- [ ] Consumer
- [ ] Online Learning
- [ ] Prediction
- [ ] Evaluation
- [ ] Metrics
- [ ] Logging

Acceptance Criteria

Model dapat menerima data streaming dan melakukan pembelajaran secara online.

---

## Milestone 6

### State Store

Goal

Menyimpan state model secara independen.

Deliverables

- Save State
- Load State
- Delete State
- State Metadata

Checklist

- [ ] REST API
- [ ] Save
- [ ] Load
- [ ] Delete
- [ ] Version
- [ ] Logging

Acceptance Criteria

State model berhasil dipulihkan setelah service dijalankan kembali.

---

## Milestone 7

### Storage Layer

Goal

Membangun abstraction layer terhadap berbagai media penyimpanan.

Deliverables

- Storage Manager
- Database Adapter
- Metadata

Checklist

- [ ] Storage API
- [ ] Mongo Adapter
- [ ] PostgreSQL Adapter
- [ ] Redis Adapter
- [ ] Logging

Acceptance Criteria

Data berhasil disimpan tanpa diketahui oleh service lain.

---

## Milestone 8

### Monitoring Dashboard

Goal

Menyediakan dashboard monitoring seluruh sistem.

Deliverables

- Dashboard
- Configuration Viewer
- Service Monitoring
- State Monitoring
- Metrics Monitoring

Checklist

- [ ] Dashboard
- [ ] Health Monitoring
- [ ] Metrics Monitoring
- [ ] Configuration Monitoring
- [ ] State Monitoring

Acceptance Criteria

Seluruh service dapat dipantau melalui satu dashboard.

---

## Milestone 9

### Integration Testing

Goal

Memastikan seluruh service dapat berjalan bersama.

Deliverables

- End-to-End Testing
- API Testing
- Stream Testing

Checklist

- [ ] Semua service berjalan
- [ ] REST API terhubung
- [ ] Streaming berjalan
- [ ] State Store berjalan
- [ ] Storage berjalan

Acceptance Criteria

Pipeline berjalan dari awal hingga akhir tanpa error.

---

## Milestone 10

### System Validation

Goal

Memastikan sistem siap digunakan sebagai platform penelitian.

Deliverables

- Functional Validation
- Performance Validation
- Documentation

Checklist

- [ ] Semua fungsi berjalan
- [ ] Semua dokumentasi selesai
- [ ] Tidak ada error kritis
- [ ] Monitoring berjalan

Acceptance Criteria

Platform siap digunakan untuk penelitian Online Machine Learning.

---

# 5. Development Priority

| Priority | Component | Status |
|----------|-----------|--------|
| High | Repository | Pending |
| High | Configuration Service | Pending |
| High | Streaming Preprocessing Service | Pending |
| High | Message Broker | Pending |
| High | Online ML Engine | Pending |
| Medium | State Store | Pending |
| Medium | Storage Layer | Pending |
| Medium | Monitoring Dashboard | Pending |
| Low | Performance Optimization | Pending |

---

# 6. Dependencies

| Component | Depends On |
|------------|------------|
| Configuration Service | Repository |
| Preprocessing Service | Configuration Service |
| Message Broker | Preprocessing Service |
| Online ML Engine | Message Broker |
| State Store | Online ML Engine |
| Storage Layer | Online ML Engine |
| Monitoring Dashboard | Semua Service |

---

# 7. Completion Criteria

Tahapan pengembangan dianggap selesai apabila:

- Seluruh milestone telah memenuhi acceptance criteria.
- Seluruh service memiliki dokumentasi.
- Seluruh REST API dapat diakses.
- Seluruh service dapat dijalankan secara independen.
- Seluruh pipeline berjalan tanpa error.
- Monitoring berhasil menampilkan seluruh status service.

---

# 8. Next Document

Dokumen berikutnya:

**04-Configuration-Service.md**

Dokumen ini akan menjadi panduan implementasi Configuration Service secara lengkap, meliputi:

- Tujuan service.
- Struktur folder.
- Arsitektur internal.
- Desain database.
- Desain REST API.
- Workflow konfigurasi.
- Checklist implementasi.
- Milestone pengembangan.
- Acceptance criteria.
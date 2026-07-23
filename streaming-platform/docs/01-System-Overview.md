# 01 System Overview

## Document Information

| Item | Description |
|------|-------------|
| Document Name | System Overview |
| Document Code | SAS-01 |
| Version | 1.0 |
| Status | Draft |
| Project | Adaptive Stream Learning Platform (ASLP) |
| Purpose | Menjelaskan gambaran umum platform, tujuan pembangunan sistem, ruang lingkup, filosofi desain, serta target pengembangan jangka panjang. |

---

# 1. Introduction

Adaptive Stream Learning Platform (ASLP) merupakan sebuah platform penelitian yang dirancang untuk mendukung pengembangan algoritma Online Machine Learning (OML) pada lingkungan data streaming.

Berbeda dengan platform machine learning konvensional yang berorientasi pada pemrosesan data statis (batch processing), ASLP dikembangkan untuk menangani data yang terus mengalir secara real-time sehingga model pembelajaran dapat diperbarui secara berkelanjutan tanpa harus melakukan proses pelatihan ulang terhadap keseluruhan dataset.

Platform ini bukan sekadar pipeline streaming maupun framework machine learning. ASLP dirancang sebagai sebuah research platform yang menyediakan fondasi arsitektur modular sehingga peneliti dapat mengembangkan berbagai algoritma Online Machine Learning secara independen tanpa harus mengubah keseluruhan sistem.

Seluruh komponen pada platform dikembangkan menggunakan pendekatan service-oriented architecture dengan komunikasi berbasis REST API dan Message Broker sehingga masing-masing service memiliki tanggung jawab yang jelas serta dapat dikembangkan secara terpisah.

---

# 2. Background

Pertumbuhan volume data yang sangat cepat menyebabkan pendekatan batch learning semakin sulit diterapkan pada banyak sistem modern.

Pada lingkungan data streaming, data memiliki karakteristik sebagai berikut:

- Data terus mengalir tanpa batas.
- Distribusi data dapat berubah sewaktu-waktu.
- Kecepatan kedatangan data tidak konstan.
- Penyimpanan seluruh data sering kali tidak memungkinkan.
- Model harus mampu beradaptasi terhadap perubahan pola data.

Sebagian besar framework machine learning masih berorientasi pada pelatihan model menggunakan dataset statis.

Pendekatan tersebut memiliki beberapa keterbatasan, antara lain:

- Membutuhkan proses retraining secara berkala.
- Membutuhkan sumber daya komputasi yang besar.
- Tidak mampu merespons perubahan data secara cepat.
- Tidak dirancang untuk menangani data yang terus berkembang.

Di sisi lain, framework data streaming umumnya hanya berfokus pada pemrosesan aliran data dan belum menyediakan lingkungan penelitian yang fleksibel untuk pengembangan algoritma Online Machine Learning.

Oleh karena itu diperlukan sebuah platform yang mampu mengintegrasikan pengelolaan data streaming, konfigurasi sistem, state management, penyimpanan data, monitoring, dan pengembangan algoritma Online Machine Learning ke dalam satu arsitektur yang modular.

---

# 3. Problem Statement

Pengembangan algoritma Online Machine Learning masih menghadapi berbagai tantangan, antara lain:

- Belum tersedia platform penelitian yang benar-benar modular.
- Integrasi antar komponen sering kali bersifat tightly coupled.
- Sulit mengganti algoritma tanpa memodifikasi sistem lain.
- State model sering disimpan secara lokal sehingga sulit dipantau.
- Konfigurasi sistem tersebar pada berbagai file.
- Monitoring belum terintegrasi.
- Penambahan database baru membutuhkan perubahan pada banyak komponen.
- Eksperimen algoritma sulit direproduksi.

Masalah tersebut menyebabkan proses penelitian menjadi kurang fleksibel dan sulit dikembangkan dalam jangka panjang.

---

# 4. Vision

Membangun platform penelitian Online Machine Learning yang modular, scalable, configurable, extensible, dan mudah dikembangkan untuk mendukung penelitian data streaming jangka panjang.

---

# 5. Mission

Platform dikembangkan dengan tujuan berikut:

- Memisahkan seluruh komponen menjadi service independen.
- Menyediakan konfigurasi sistem secara terpusat.
- Menyediakan mekanisme state management.
- Menyediakan abstraction layer terhadap berbagai media penyimpanan.
- Menyediakan monitoring seluruh service.
- Menyediakan lingkungan penelitian untuk pengembangan berbagai algoritma Online Machine Learning.

---

# 6. Core Objectives

Platform memiliki enam tujuan utama.

## Objective 1

Membangun pipeline data streaming yang modular.

Success Criteria

- Setiap service berdiri sendiri.
- Tidak ada ketergantungan langsung antar service.
- Service dapat diganti tanpa mempengaruhi service lain.

---

## Objective 2

Menyediakan konfigurasi sistem yang terpusat.

Success Criteria

- Seluruh konfigurasi tersedia melalui REST API.
- Konfigurasi dapat diperbarui tanpa mengubah source code.
- Konfigurasi dapat dipantau melalui dashboard.

---

## Objective 3

Menyediakan Online Machine Learning Engine yang fleksibel.

Success Criteria

- Algoritma dapat ditambahkan tanpa mengubah engine utama.
- Mendukung eksperimen berbagai metode OML.
- Mendukung evaluasi model secara online.

---

## Objective 4

Menyediakan State Store yang independen.

Success Criteria

- Model state dapat disimpan.
- Model state dapat dipulihkan.
- Mendukung pengembangan checkpoint di masa depan.

---

## Objective 5

Menyediakan Storage Layer yang independen terhadap database.

Success Criteria

- Mendukung berbagai database.
- Tidak ada service yang mengakses database secara langsung.
- Seluruh akses dilakukan melalui Storage Layer.

---

## Objective 6

Menyediakan monitoring sistem secara menyeluruh.

Success Criteria

- Monitoring service.
- Monitoring konfigurasi.
- Monitoring state.
- Monitoring performa pipeline.

---

# 7. Scope

Platform pada fase pertama mencakup komponen berikut.

- Configuration Service
- Streaming Preprocessing Service
- Message Broker
- Online Machine Learning Engine
- State Store
- Storage Layer
- Monitoring Dashboard

---

# 8. Out of Scope

Fitur berikut belum menjadi bagian dari fase pertama.

- Distributed Cluster
- Kubernetes Deployment
- Multi-node Processing
- Authentication
- Authorization
- High Availability
- Automatic Scaling
- Cloud Deployment
- CI/CD Pipeline
- Model Marketplace

---

# 9. Design Principles

Seluruh pengembangan mengikuti prinsip berikut.

## Service Isolation

Setiap service bertanggung jawab terhadap satu fungsi utama.

---

## Loose Coupling

Tidak ada service yang mengetahui implementasi internal service lain.

---

## High Cohesion

Seluruh fungsi yang saling berkaitan ditempatkan dalam service yang sama.

---

## API First

Seluruh komunikasi dilakukan melalui REST API.

---

## Configuration First

Seluruh konfigurasi harus berasal dari Configuration Service.

---

## Storage Independence

Tidak ada service yang mengetahui jenis database yang digunakan.

---

## State Persistence

Seluruh state model harus dapat disimpan secara independen.

---

## Research Friendly

Platform harus mempermudah eksperimen berbagai algoritma OML.

---

# 10. High Level Architecture

Platform terdiri atas tujuh komponen utama.

1. Configuration Service

Mengelola konfigurasi seluruh service.

2. Streaming Preprocessing Service

Menyiapkan data streaming sebelum dipublikasikan.

3. Message Broker

Menghubungkan seluruh pipeline streaming.

4. Online Machine Learning Engine

Melakukan pembelajaran, prediksi, dan evaluasi model.

5. State Store

Mengelola state model.

6. Storage Layer

Mengelola seluruh penyimpanan data.

7. Monitoring Dashboard

Melakukan monitoring seluruh service.

---

# 11. Service Communication Principles

Platform menggunakan dua mekanisme komunikasi.

## REST API

Digunakan untuk:

- konfigurasi
- monitoring
- state management
- storage management

REST API digunakan untuk komunikasi request-response antar service.

---

## Message Broker

Digunakan untuk:

- streaming data
- publish
- subscribe

Message Broker digunakan hanya untuk distribusi data streaming.

---

# 12. System Characteristics

Platform memiliki karakteristik berikut.

| Characteristic | Description |
|---------------|-------------|
| Modular | Setiap service berdiri sendiri |
| Configurable | Konfigurasi melalui REST API |
| Extensible | Mudah menambahkan service baru |
| Scalable | Dapat dikembangkan menjadi distributed system |
| Maintainable | Mudah dipelihara |
| Research-Oriented | Berorientasi pada eksperimen OML |

---

# 13. Development Philosophy

Pengembangan platform dilakukan secara bertahap.

Tahap pertama berfokus pada pembangunan fondasi arsitektur.

Tahap kedua berfokus pada integrasi antar service.

Tahap ketiga berfokus pada pengembangan Online Machine Learning Engine.

Tahap keempat berfokus pada state management.

Tahap kelima berfokus pada storage abstraction.

Tahap keenam berfokus pada monitoring.

Seluruh pengembangan dilakukan secara incremental sehingga setiap service dapat diuji sebelum memasuki tahap berikutnya.

---

# 14. Expected Outcomes

Pada akhir fase pertama, platform diharapkan mampu:

- Mengelola konfigurasi seluruh service.
- Menjalankan pipeline data streaming.
- Menjalankan algoritma Online Machine Learning.
- Menyimpan state model.
- Menyimpan hasil eksperimen.
- Menampilkan monitoring seluruh service.

Platform pada fase ini sudah dapat digunakan sebagai fondasi penelitian Online Machine Learning berbasis data streaming.

---

# 15. Next Document

Dokumen berikutnya adalah:

02 Architecture

Dokumen tersebut menjelaskan struktur arsitektur platform secara rinci, hubungan antar service, aliran data, dependency, sequence komunikasi, serta boundary setiap komponen.
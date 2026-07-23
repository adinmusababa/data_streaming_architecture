# 04. Repository Structure

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Repository Structure |
| Document Code | SAS-04 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan struktur repository, standar penamaan folder, tanggung jawab setiap direktori, serta aturan pengelolaan source code selama pengembangan sistem. |

---

# 1. Purpose

Dokumen ini menjadi pedoman dalam menyusun struktur repository sehingga seluruh proses pengembangan mengikuti standar yang sama.

Struktur repository yang baik akan memberikan beberapa keuntungan:

- Mempermudah pengembangan service baru.
- Mempermudah navigasi project.
- Mempermudah maintenance.
- Mempermudah dokumentasi.
- Mempermudah testing.
- Mempermudah deployment.

Seluruh service yang dikembangkan harus mengikuti struktur repository yang dijelaskan pada dokumen ini.

---

# 2. Repository Goals

Repository dirancang dengan beberapa tujuan utama.

## Goal 1

Memisahkan setiap service menjadi module yang independen.

Target

- Setiap service memiliki folder sendiri.
- Tidak ada source code service lain yang tercampur.

---

## Goal 2

Mempermudah pengembangan.

Target

- Struktur project mudah dipahami.
- Lokasi file konsisten.
- Mudah mencari source code.

---

## Goal 3

Mempermudah scaling.

Target

- Penambahan service baru tidak mengubah struktur project.
- Penambahan module baru tetap mengikuti standar repository.

---

# 3. Repository Overview

Root repository hanya berisi komponen utama sistem.

```
streaming-integration-architecture/

│

├── docs/

├── services/

├── shared/

├── scripts/

├── tests/

├── docker/

├── configs/

├── requirements/

├── .env.example

├── .gitignore

├── README.md

└── LICENSE
```

---

# 4. Directory Responsibilities

## docs/

Berisi seluruh dokumentasi Software Architecture Specification (SAS).

Isi folder:

```
docs/

00-README.md

01-System-Overview.md

02-Architecture.md

03-Development-Roadmap.md

04-Repository-Structure.md

05-Configuration-Service.md

06-Streaming-Preprocessing-Service.md

07-Message-Broker.md

08-OnlineML-Engine.md

09-State-Store.md

10-Storage-Layer.md

11-Monitoring-Dashboard.md

12-REST-API-Specification.md
```

Tujuan

- Menjadi acuan utama selama pengembangan.
- Menyimpan seluruh dokumentasi sistem.

---

## services/

Berisi seluruh microservice yang membangun sistem.

Setiap service berdiri sendiri.

```
services/

configuration-service/

streaming-preprocessing-service/

online-ml-engine/

state-store/

storage-layer/

monitoring-dashboard/
```

Setiap folder service harus dapat dijalankan secara independen.

---

## shared/

Berisi module yang digunakan bersama oleh seluruh service.

Contoh

```
shared/

models/

schemas/

clients/

utils/

exceptions/

constants/
```

Folder ini tidak boleh berisi business logic.

Folder ini hanya berisi library yang dapat digunakan oleh seluruh service.

---

## scripts/

Berisi seluruh script pendukung.

Contoh

```
scripts/

install.py

run_all.py

stop_all.py

clean.py

reset.py
```

---

## tests/

Berisi seluruh testing.

```
tests/

unit/

integration/

performance/
```

Testing service tidak boleh ditempatkan di dalam folder service.

---

## docker/

Berisi konfigurasi Docker.

```
docker/

configuration/

preprocessing/

broker/

storage/

dashboard/
```

Online ML Engine tidak ditempatkan pada Docker karena akan dikembangkan secara langsung menggunakan Python.

---

## configs/

Berisi konfigurasi global project.

Contoh

```
configs/

logging/

database/

broker/
```

Konfigurasi service tetap berada pada Configuration Service.

Folder ini hanya menyimpan konfigurasi project secara umum.

---

## requirements/

Berisi dependency project.

```
requirements/

base.txt

development.txt

production.txt
```

---

# 5. Service Structure

Seluruh service menggunakan struktur folder yang sama.

```
service-name/

app/

api/

core/

models/

schemas/

services/

repositories/

routes/

middleware/

utils/

logs/

tests/

main.py

requirements.txt

README.md
```

---

# 6. Directory Responsibilities Inside Service

## app/

Berisi source code utama.

---

## api/

Berisi implementasi REST API.

---

## core/

Berisi konfigurasi internal service.

---

## models/

Berisi representasi object.

---

## schemas/

Berisi schema request dan response.

---

## services/

Berisi business logic.

---

## repositories/

Berisi komunikasi terhadap database atau storage.

---

## routes/

Berisi routing endpoint.

---

## middleware/

Berisi middleware.

---

## utils/

Berisi helper.

---

## logs/

Berisi file log.

---

## tests/

Berisi testing khusus service.

---

# 7. Naming Convention

Seluruh penamaan mengikuti aturan berikut.

Folder

```
configuration-service

state-store

storage-layer
```

Menggunakan lowercase dan hyphen.

---

Python Package

```
configuration_service

storage_layer
```

Menggunakan snake_case.

---

Python File

```
config_service.py

state_manager.py

storage_adapter.py
```

Menggunakan snake_case.

---

Class

```
ConfigurationManager

StorageManager

StateController
```

Menggunakan PascalCase.

---

Function

```
load_configuration()

save_state()

publish_message()
```

Menggunakan snake_case.

---

REST Endpoint

```
/config

/config/update

/state

/state/save

/storage

/storage/save
```

Menggunakan lowercase.

---

# 8. Development Rules

Seluruh service wajib memiliki komponen berikut.

- main.py
- requirements.txt
- README.md
- app/
- logs/
- tests/

Tidak diperbolehkan membuat struktur folder yang berbeda tanpa alasan yang jelas.

---

# 9. Repository Workflow

Urutan pengembangan repository adalah sebagai berikut.

Repository

↓

Service

↓

Module

↓

REST API

↓

Testing

↓

Integration

↓

Documentation

---

# 10. Development Checklist

## Repository

- [ ] Root repository dibuat.
- [ ] Struktur folder dibuat.
- [ ] README tersedia.
- [ ] Dokumentasi SAS tersedia.

---

## Shared Module

- [ ] Folder shared dibuat.
- [ ] Utility tersedia.
- [ ] Schema tersedia.
- [ ] HTTP Client tersedia.

---

## Services

- [ ] Configuration Service.
- [ ] Streaming Preprocessing Service.
- [ ] Online ML Engine.
- [ ] State Store.
- [ ] Storage Layer.
- [ ] Monitoring Dashboard.

---

## Testing

- [ ] Unit Test.
- [ ] Integration Test.
- [ ] Performance Test.

---

# 11. Acceptance Criteria

Repository dianggap selesai apabila memenuhi kondisi berikut.

- Seluruh folder utama telah tersedia.
- Seluruh service memiliki struktur yang konsisten.
- Tidak terdapat source code yang berada di luar struktur repository.
- Dokumentasi tersedia.
- Repository siap digunakan untuk implementasi seluruh service.

---

# 12. Next Document

Dokumen berikutnya adalah:

05-Configuration-Service.md

Dokumen ini akan menjelaskan secara rinci implementasi Configuration Service, mulai dari arsitektur internal, struktur folder, desain database, workflow konfigurasi, REST API, hingga target implementasi.
# 12. REST API Convention

## Document Information

| Item | Description |
|------|-------------|
| Document Name | REST API Convention |
| Document Code | SAS-13 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menetapkan standar REST API yang digunakan oleh seluruh service pada arsitektur integrasi data streaming. |

---

# 1. Purpose

Dokumen ini menjadi standar pengembangan REST API bagi seluruh service.

Seluruh service wajib mengikuti aturan yang dijelaskan pada dokumen ini agar komunikasi antar service tetap konsisten dan mudah dipelihara.

Dokumen ini tidak mendefinisikan endpoint dari setiap service, tetapi mendefinisikan aturan umum yang digunakan oleh seluruh endpoint.

---

# 2. Goals

## Goal 1

Menyediakan standar komunikasi.

Target

Seluruh service memiliki format API yang sama.

---

## Goal 2

Menyediakan format request dan response yang konsisten.

Target

Dashboard maupun service lain tidak perlu memiliki parser berbeda.

---

## Goal 3

Mempermudah pengembangan.

Target

Penambahan service baru mengikuti standar yang telah ditentukan.

---

# 3. API Versioning

Seluruh endpoint menggunakan prefix version.

Contoh

```
/api/v1/
```

Contoh endpoint

```
GET /api/v1/config

GET /api/v1/state

POST /api/v1/storage
```

Apabila terjadi perubahan besar yang tidak kompatibel, maka digunakan versi baru.

Contoh

```
/api/v2/
```

---

# 4. Resource Naming

Seluruh resource menggunakan huruf kecil.

Gunakan tanda hubung (-) apabila terdiri dari beberapa kata.

Contoh

```
configuration

state

storage

metrics

prediction

service-status
```

---

# 5. HTTP Method

## GET

Digunakan untuk membaca data.

---

## POST

Digunakan untuk membuat data baru atau menjalankan suatu proses.

---

## PUT

Digunakan untuk memperbarui seluruh data.

---

## PATCH

Digunakan untuk memperbarui sebagian data.

---

## DELETE

Digunakan untuk menghapus data.

---

# 6. URL Convention

Gunakan format berikut.

```
/api/v1/{resource}

/api/v1/{resource}/{id}

/api/v1/{resource}/{id}/action
```

Contoh

```
GET /api/v1/config

GET /api/v1/config/oml-engine

PUT /api/v1/config/oml-engine

DELETE /api/v1/state/model-01
```

---

# 7. Request Format

Request menggunakan JSON.

Contoh

```json
{
    "parameter": "learning_rate",
    "value": 0.001
}
```

---

# 8. Response Format

Seluruh response menggunakan struktur yang sama.

```json
{
    "success": true,
    "message": "Configuration updated successfully.",
    "data": {},
    "timestamp": "2026-07-22T10:30:00Z"
}
```

---

# 9. Error Response

```json
{
    "success": false,
    "message": "Validation failed.",
    "errors": [],
    "timestamp": "2026-07-22T10:30:00Z"
}
```

---

# 10. HTTP Status Code

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Resource Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

# 11. Health Endpoint

Seluruh service wajib memiliki endpoint berikut.

```
GET /api/v1/health
```

Response

```json
{
    "service": "",
    "status": "running",
    "version": "",
    "uptime": ""
}
```

---

# 12. Status Endpoint

```
GET /api/v1/status
```

Berisi informasi operasional service.

---

# 13. Statistics Endpoint

```
GET /api/v1/statistics
```

Digunakan oleh Monitoring Dashboard.

---

# 14. Configuration Endpoint

Seluruh service wajib menyediakan endpoint berikut.

```
GET /api/v1/config

POST /api/v1/config/reload
```

Service tidak diperbolehkan melakukan pembacaan konfigurasi secara langsung ke database.

---

# 15. Pagination

Endpoint yang mengembalikan daftar data wajib mendukung pagination.

Parameter

```
page

size

sort

order
```

Contoh

```
GET /api/v1/state?page=1&size=20
```

---

# 16. Filtering

Filtering menggunakan query parameter.

Contoh

```
GET /api/v1/storage?category=metrics

GET /api/v1/storage?model=dbstream
```

---

# 17. Logging

Seluruh request minimal mencatat informasi berikut.

- Timestamp
- HTTP Method
- Endpoint
- Status Code
- Processing Time

---

# 18. Timeout

REST Client menggunakan timeout yang diperoleh dari Configuration Service.

Apabila request gagal maka dilakukan retry sesuai konfigurasi.

---

# 19. Authentication

Tahap pertama belum menggunakan Authentication.

Seluruh service diasumsikan berada pada jaringan internal.

Fitur Authentication akan ditambahkan pada tahap pengembangan berikutnya.

---

# 20. Development Checklist

- [ ] Seluruh endpoint menggunakan prefix `/api/v1`.
- [ ] Seluruh response mengikuti format standar.
- [ ] Seluruh error mengikuti format standar.
- [ ] Seluruh service memiliki endpoint `health`.
- [ ] Seluruh service memiliki endpoint `status`.
- [ ] Seluruh service memiliki endpoint `statistics`.
- [ ] Seluruh endpoint mendukung JSON.
- [ ] Seluruh endpoint memiliki dokumentasi Swagger.

---

# 21. Acceptance Criteria

REST API dianggap memenuhi standar apabila:

- Struktur endpoint konsisten.
- Response konsisten.
- Error response konsisten.
- Status code sesuai.
- Seluruh service mengikuti konvensi yang sama.

---

# 22. Next Document

Dokumen berikutnya adalah:

**14-REST-API-Specification.md**

Dokumen ini akan mendefinisikan seluruh endpoint REST API dari setiap service secara rinci, termasuk request, response, parameter, validasi, serta contoh implementasi sehingga dapat langsung dijadikan acuan pada proses pengembangan.
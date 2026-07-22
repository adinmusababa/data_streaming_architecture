# 11. Shared SDK

## Document Information

| Item | Description |
|------|-------------|
| Document Name | Shared SDK |
| Document Code | SAS-12 |
| Version | 1.0 |
| Status | Draft |
| Purpose | Menjelaskan library bersama yang digunakan oleh seluruh service agar implementasi memiliki standar yang konsisten dan menghindari duplikasi kode. |

---

# 1. Purpose

Shared SDK merupakan library internal yang digunakan oleh seluruh service.

SDK ini menyediakan komponen umum yang dapat digunakan bersama sehingga setiap service hanya berfokus pada business logic.

Seluruh service diperbolehkan menggunakan Shared SDK.

Seluruh business logic tetap berada pada masing-masing service.

---

# 2. Goals

## Goal 1

Mengurangi duplikasi kode.

Target

Utility hanya ditulis satu kali.

---

## Goal 2

Menyediakan implementasi yang konsisten.

Target

Seluruh service menggunakan logger, response, exception dan client yang sama.

---

## Goal 3

Mempermudah maintenance.

Target

Perubahan utility hanya dilakukan pada Shared SDK.

---

# 3. Responsibilities

Shared SDK menyediakan komponen umum.

SDK tidak memiliki business logic.

SDK tidak berkomunikasi dengan database.

SDK tidak menjalankan machine learning.

---

# 4. Folder Structure

```
shared-sdk/

shared_sdk/

clients/

responses/

exceptions/

logger/

validators/

schemas/

models/

utils/

constants/

configuration/

__init__.py

README.md

pyproject.toml
```

---

# 5. SDK Modules

## Clients

Berisi REST API Client.

```
clients/

configuration_client.py

broker_client.py

state_client.py

storage_client.py
```

Seluruh komunikasi antar service dilakukan melalui client ini.

---

## Logger

Berisi implementasi logging.

Contoh

```
SystemLogger

RequestLogger

ErrorLogger
```

Seluruh service menggunakan logger yang sama.

---

## Responses

Berisi response standar.

Contoh

```
SuccessResponse

ErrorResponse

ValidationResponse
```

---

## Exceptions

Berisi exception standar.

Contoh

```
ValidationException

ConfigurationException

StorageException

StateException

APIException
```

---

## Validators

Berisi validator umum.

Contoh

```
RequiredValidator

NumberValidator

StringValidator

DateValidator
```

---

## Schemas

Berisi schema yang digunakan bersama.

Contoh

```
BaseResponse

BaseRequest

Pagination

Metadata
```

---

## Utils

Utility umum.

Contoh

```
Datetime

Json

UUID

Retry

Converter
```

---

## Constants

Konstanta sistem.

Contoh

```
HTTP Status

Service Name

Default Timeout

Version
```

---

## Configuration

Utility pembacaan konfigurasi.

---

# 6. REST Clients

SDK menyediakan client untuk setiap service.

```
ConfigurationClient

StreamingClient

BrokerClient

OnlineMLClient

StateStoreClient

StorageClient
```

Tujuan

Service lain tidak perlu membuat request HTTP secara manual.

---

# 7. Standard Response

Seluruh service menggunakan response yang sama.

Contoh

```json
{
    "success": true,
    "message": "",
    "data": {},
    "timestamp": ""
}
```

---

# 8. Standard Error

Contoh

```json
{
    "success": false,
    "error": "",
    "detail": "",
    "timestamp": ""
}
```

---

# 9. Logging Standard

Seluruh logger memiliki format.

```
Timestamp

Service

Level

Message

Module
```

---

# 10. Exception Standard

Exception minimal.

- ValidationException
- StorageException
- StateException
- APIException
- ConfigurationException

---

# 11. Development Checklist

## SDK

- [ ] Package
- [ ] README
- [ ] pyproject.toml

---

## Logger

- [ ] Base Logger

---

## Response

- [ ] Success Response
- [ ] Error Response

---

## Clients

- [ ] Configuration Client
- [ ] Broker Client
- [ ] State Client
- [ ] Storage Client

---

## Validators

- [ ] Base Validator

---

## Testing

- [ ] Unit Test

---

# 12. Acceptance Criteria

Shared SDK dianggap selesai apabila.

- Seluruh service dapat menggunakannya.
- Tidak terdapat utility yang ditulis berulang.
- REST Client dapat digunakan.
- Logger dapat digunakan.
- Response memiliki format yang sama.

---

# 13. Future Development

Pengembangan berikutnya.

- Authentication Client
- Cache Manager
- Retry Manager
- Circuit Breaker
- Plugin Loader
- Event System

---

# 14. Next Document

Dokumen berikutnya adalah:

13-REST-API-Convention.md

Dokumen ini menjelaskan standar penulisan REST API yang harus diikuti oleh seluruh service, termasuk format endpoint, struktur request dan response, status code, penamaan resource, serta aturan versioning API.
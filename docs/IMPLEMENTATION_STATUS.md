# Status Implementasi

## Tersedia pada fondasi versi 0.1.0

- Schema inti PostgreSQL dan Alembic.
- Login JWT dasar dan bootstrap administrator.
- RBAC permission server-side.
- Pembuatan, pembaruan, versioning, dan hash dokumen.
- Workflow definition, publish, instance, task, action, return, dan concurrency checking.
- Approval terikat versi dokumen.
- Tabel disposisi, agenda, notifikasi, perangkat, chat, template, dan integrasi SIPS.
- Android Compose: login, dashboard, Tugas Saya, navigation shell, DataStore, Hilt, Retrofit.
- Panel Adminator-inspired responsive dashboard.
- CI backend, admin web, dan debug APK.

## Tahap lanjutan

- Form lengkap perjalanan dinas, rapat, surat masuk, agenda, dan disposisi.
- Editor workflow visual lengkap dan user/role administration.
- Renderer DOCX/PDF server-side menggunakan placeholder template resmi.
- Upload ke Object Storage, antivirus, preview PDF, FCM, WebSocket chat, dan Room cache.
- Endpoint service account SIPS, webhook, retry outbox, dan idempotency.
- Signing release APK/AAB, staging, observability, serta security testing.

## Tersedia pada tahap 0.2.0

- Master 15 jenis rapat dari template resmi, aktif/nonaktif dan diurutkan dari backend.
- API pembuatan, pembacaan, dan perubahan Permintaan Rapat dengan versioning dokumen.
- Validasi zona waktu, maksimal 20 undangan, pencegahan undangan duplikat, dan ownership edit.
- Permission khusus `meeting_request.create` dan `meeting_request.edit`.
- Profil API mengirim permission efektif agar menu Android mengikuti hak akses Administrator.
- Form Android Permintaan Rapat dengan daftar undangan dinamis dan penyimpanan draft.

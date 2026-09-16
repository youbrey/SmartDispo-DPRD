# Status Implementasi SmartDispo 0.4.0

## Fungsi yang tersedia

- Backend FastAPI dengan access/refresh token rotation, logout, RBAC granular, perangkat aktif, audit append-only, rate limiting Redis, concurrency check, versioning dokumen, dan hash SHA-256.
- Workflow yang dibuat Administrator, memiliki versi DRAFT/PUBLISHED/RETIRED, assignment user/role/unit, aturan ALL/ANY/SELECTED, return, reject, dan approval yang terikat versi dokumen.
- Form Android Permintaan Rapat, Perjalanan Dinas, Surat Masuk DPRD/Setwan, Disposisi Ketua, dan Disposisi Sekwan.
- Daftar undangan rapat, pelaksana/pendamping perjalanan, serta tujuan disposisi unit/AKD/role/pengguna bersifat dinamis.
- Generator DOCX dan PDF untuk empat template resmi dengan nama pejabat aktif dari role assignment.
- Preview PDF multipage, timeline, lampiran tervalidasi, arsip/search, Notification Center, profil, dan pencabutan perangkat.
- Live chat umum/per dokumen melalui REST dan WebSocket terautentikasi.
- Push notification FCM menggunakan outbox database agar konsisten dengan transaksi workflow.
- Cache Room untuk tugas, dokumen, notifikasi, ruang, dan pesan terakhir. SIGN, VERIFY, COORDINATE, APPROVE, DISPOSITION, RETURN, dan tindakan task lain dinonaktifkan saat offline.
- Panel Admin untuk pengguna, multi-role, permission, Unit/AKD, pejabat aktif, workflow, template berversi, dashboard, dan audit log.
- Endpoint SIPS dengan service key terpisah serta event idempotent.

## Verifikasi terakhir

- Ruff backend bersih.
- 18 unit test backend lulus; mencakup versioning/hash, validasi form, disposisi, renderer target dinamis, realtime hub, security header, dan rate limit.
- Build produksi Admin Web lulus (`tsc` dan `vite build`).
- Template Disposisi DPRD dan Setwan dirender menjadi DOCX/PDF dan diperiksa visual satu halaman tanpa clipping atau overlap.
- `git diff --check` dijalankan sebelum commit.

## Gerbang lingkungan dan produksi

- Tiga integration test PostgreSQL dijalankan GitHub Actions karena container PostgreSQL tidak tersedia di workspace lokal.
- APK debug dibangun GitHub Actions karena repository plugin Android Google tidak dapat dijangkau dari workspace lokal.
- Push FCM memerlukan Firebase project milik instansi, service-account pada server, dan `android/app/google-services.json` saat build. Rahasia tersebut tidak disimpan di repository.
- Release produksi tetap memerlukan domain HTTPS, signing key Android, backup, monitoring, antivirus lampiran, serta penetration test milik instansi.

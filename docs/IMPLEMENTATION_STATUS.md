# Status Implementasi Lokal

Perubahan berikut masih berada di working tree. Belum ada commit atau push karena APK dan integration suite PostgreSQL belum dapat dijalankan penuh pada lingkungan lokal ini.

## Sudah diimplementasikan dan lolos pemeriksaan lokal

- Backend FastAPI: access/refresh token dengan rotation dan logout, RBAC, dokumen berversi dan SHA-256, workflow versioned, concurrency checking, audit append-only, notifikasi, perangkat, attachment tervalidasi, chat REST, dan endpoint SIPS.
- Form Android Permintaan Rapat, Perjalanan Dinas, Surat Masuk, dan dua jenis lembar disposisi.
- Draft dapat dipreview sebagai PDF multipage, dikirim ke workflow, dibuka dari tugas, ditampilkan timeline-nya, serta diberi lampiran upload/download.
- Dokumen rapat/perjalanan berstatus `DRAFT` atau `RETURNED` dapat diperbaiki menjadi versi baru dan dikirim ulang.
- Disposisi hanya dapat diisi pejabat aktif yang mempunyai task `DISPOSITION`; Ketua dan Sekwan memiliki pilihan berbeda.
- Tindakan sensitif memerlukan perangkat aktif terdaftar dan identitas perangkat dicatat pada approval.
- Template DOCX bawaan dan upload Admin memakai versioning; setiap versi dokumen dikunci ke versi template yang digunakan.
- Panel Admin: pengguna, multi-role, reset password, role/permission, Unit/AKD, pejabat aktif, workflow multi-step, template upload/activation, dashboard, dan audit log.
- Empat renderer template resmi: Permintaan Rapat, Perjalanan Dinas, Disposisi DPRD, dan Disposisi Setwan.
- Pemeriksaan terakhir: Ruff bersih, 15 unit test lulus, build produksi Admin Web lulus, dan `git diff --check` bersih.

## Gerbang yang belum terbukti

- Tiga integration test PostgreSQL dilewati lokal karena PostgreSQL/Docker tidak tersedia. CI sudah disiapkan untuk menjalankannya.
- Kompilasi Android lokal berhenti sebelum membaca source karena plugin Android Gradle 8.7.3 tidak dapat diunduh dari repository jaringan lingkungan ini. CI sudah disiapkan untuk `testDebugUnitTest assembleDebug` dan upload APK debug.
- Karena dua gerbang tersebut belum hijau, proyek belum dianggap final dan belum boleh di-commit/push sesuai instruksi pengguna.

## Pekerjaan berikutnya

- WebSocket chat dan push FCM end-to-end.
- Tujuan disposisi Unit/AKD dinamis pada Android dan renderer Setwan.
- Room offline cache serta pemastian tindakan approval tidak tersedia ketika offline.
- Menjalankan PostgreSQL integration suite dan build APK pada runner yang memiliki dependency Android, memperbaiki seluruh kegagalan, lalu baru menilai kelayakan commit/push.

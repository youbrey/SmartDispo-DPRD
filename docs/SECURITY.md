# Keamanan SmartDispo DPRD

## Kontrol utama

- HTTPS wajib pada staging dan produksi.
- Access token berumur singkat; refresh token disimpan dalam bentuk hash dan dirotasi.
- Password menggunakan Argon2 melalui konfigurasi `pwdlib` yang direkomendasikan.
- Permission selalu diverifikasi backend.
- Device dapat diregistrasi dan dicabut; token aplikasi dienkripsi AES-GCM dengan kunci non-exportable di Android Keystore sebelum disimpan melalui DataStore.
- Mutation workflow memakai transaction, row lock, dan optimistic lock version.
- Lampiran wajib divalidasi berdasarkan MIME, signature, ukuran, serta hasil antivirus sebelum disimpan.
- Audit log dilindungi trigger PostgreSQL dari UPDATE dan DELETE.
- Signing key Android hanya disimpan sebagai GitHub Actions secret, tidak di repository.
- Rate limiting memakai Redis untuk login dan API umum; fallback memori menjaga proteksi dasar bila Redis terputus.
- Kredensial Firebase dibaca dari file service-account yang dipasang sebagai secret server dan tidak pernah disimpan di repository.

## Sebelum produksi

- Ganti seluruh placeholder domain dan secret.
- Aktifkan TLS, rate limiting, backup terenkripsi, pemulihan bencana, serta monitoring.
- Konfigurasikan Firebase service account dan Object Storage melalui secret manager.
- Lakukan penetration test dan uji pemulihan backup.
- Terapkan retention policy serta klasifikasi data sesuai kebijakan Pemerintah Kota Bitung.

# SmartDispo DPRD Kota Bitung

Pusat workflow persuratan digital Sekretariat DPRD Kota Bitung. Repository ini berisi API FastAPI, aplikasi Android Kotlin/Jetpack Compose, panel administrator, migrasi PostgreSQL, dan pipeline CI pembentukan APK.

## Modul awal

- Permintaan perjalanan dinas dan permintaan rapat
- Surat masuk Ketua DPRD dan Sekretaris DPRD
- Workflow dinamis, tugas, paraf, persetujuan, dan disposisi
- RBAC dan permission granular yang dikelola administrator
- Versioning dokumen, SHA-256, dan audit log append-only
- Notifikasi, perangkat, chat, serta integrasi SIPS Terpadu

## Implementasi saat ini

Versi Android `0.4.1` menyediakan konfigurasi alamat server saat runtime tanpa build ulang. Backend dan Admin Web
versi `0.4.0` menyediakan alur operasional Permintaan Rapat, Permintaan Perjalanan Dinas, Surat Masuk
DPRD/Setwan, lembar disposisi dinamis, workflow administratif, generator DOCX/PDF, panel administrator,
live chat WebSocket, push notification FCM, cache baca offline Room, RBAC, audit trail, dan integrasi SIPS.
Lihat `docs/IMPLEMENTATION_STATUS.md` untuk hasil verifikasi dan konfigurasi produksi yang masih diperlukan.

## Menjalankan backend

```bash
cp .env.example .env
docker compose up --build
```

API tersedia di `http://localhost:8000`, dokumentasi OpenAPI di `/docs`, dan health check di `/health`.
Panel Administrator tersedia di `http://localhost:8080` dan otomatis meneruskan permintaan API ke backend.
Saat container API dimulai, migration dan bootstrap akun administrator dijalankan otomatis. Ganti seluruh
nilai rahasia dan kata sandi pada `.env` sebelum dipakai di jaringan kantor.

Panel admin dijalankan dengan `npm run dev` dari folder `admin-web`. Secara default panel mengakses
`http://localhost:8000/api/v1`; gunakan `VITE_API_BASE_URL` untuk alamat server lain.

Pada APK Android `0.4.1` atau lebih baru, pilih **Atur alamat server** pada layar login. Masukkan alamat
komputer yang dapat dijangkau HP, misalnya `192.168.1.10:8000`, lalu pilih **Uji & Simpan**. Aplikasi
menambahkan `/api/v1/` secara otomatis sehingga APK tidak perlu dibangun ulang ketika IP server berubah.
HTTP lokal hanya diizinkan pada debug APK; build release tetap mewajibkan HTTPS.

Panduan lengkap untuk menjadikan komputer Windows sebagai server lokal, membuat konfigurasi aman,
membuka firewall LAN, menjalankan container otomatis, dan menghubungkan APK tersedia di
[`docs/LOCAL_SERVER_WINDOWS.md`](docs/LOCAL_SERVER_WINDOWS.md). Skrip `scripts/setup-local-server.ps1`
menyiapkan konfigurasi dan menjalankan seluruh layanan tanpa memerlukan XAMPP.

## Pengembangan

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

Android dibuka dari folder `android/`. Panel administrator dibuka dari folder `admin-web/`. Build dan pengujian otomatis dijalankan oleh GitHub Actions pada setiap push dan pull request.

## Firebase

Push notification aktif bila server memperoleh `SMARTDISPO_FIREBASE_PROJECT_ID` dan lokasi service-account
melalui `SMARTDISPO_FIREBASE_SERVICE_ACCOUNT_FILE`. File `android/app/google-services.json` harus dipasang
oleh administrator pada saat build dan sengaja diabaikan Git. Tanpa konfigurasi Firebase, aplikasi tetap
berfungsi dengan Notification Center dan live chat WebSocket, tetapi push di luar aplikasi tidak dikirim.

## Keamanan

Jangan menyimpan rahasia, signing key, token, atau kredensial produksi di repository. Nilai pada `.env.example` hanya untuk pengembangan lokal dan wajib diganti di produksi.

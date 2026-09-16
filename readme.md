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

Versi `0.4.0` menyediakan alur operasional Permintaan Rapat, Permintaan Perjalanan Dinas, Surat Masuk
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

Untuk debug APK pada HP fisik, build dengan alamat komputer/server yang dapat dijangkau HP:

```bash
cd android
gradle assembleDebug -PSMARTDISPO_DEBUG_API_BASE_URL=http://192.168.1.10:8000/api/v1/
```

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

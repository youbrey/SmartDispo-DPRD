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

Versi `0.3.0` menyediakan fondasi workflow dan vertical slice Permintaan Rapat: master jenis rapat,
API draft/versioning, permission server-side, serta formulir Android dengan undangan dinamis maksimal 20 tujuan.
Lihat `docs/IMPLEMENTATION_STATUS.md` untuk batas fitur dan tahap berikutnya.

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

## Keamanan

Jangan menyimpan rahasia, signing key, token, atau kredensial produksi di repository. Nilai pada `.env.example` hanya untuk pengembangan lokal dan wajib diganti di produksi.

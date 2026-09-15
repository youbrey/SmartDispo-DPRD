# SmartDispo DPRD Kota Bitung

Pusat workflow persuratan digital Sekretariat DPRD Kota Bitung. Repository ini berisi API FastAPI, aplikasi Android Kotlin/Jetpack Compose, panel administrator, migrasi PostgreSQL, dan pipeline CI pembentukan APK.

## Modul awal

- Permintaan perjalanan dinas dan permintaan rapat
- Surat masuk Ketua DPRD dan Sekretaris DPRD
- Workflow dinamis, tugas, paraf, persetujuan, dan disposisi
- RBAC dan permission granular yang dikelola administrator
- Versioning dokumen, SHA-256, dan audit log append-only
- Notifikasi, perangkat, chat, serta integrasi SIPS Terpadu

## Menjalankan backend

```bash
cp .env.example .env
docker compose up --build
```

API tersedia di `http://localhost:8000`, dokumentasi OpenAPI di `/docs`, dan health check di `/health`.

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

# Server Lokal SmartDispo di Windows

Panduan ini menjalankan API FastAPI, PostgreSQL, Redis, generator DOCX/PDF, dan Panel Administrator pada
satu komputer lokal menggunakan Docker Desktop. XAMPP tidak digunakan karena SmartDispo bukan aplikasi
PHP/MySQL.

## 1. Persyaratan

- Windows 10/11 64-bit dengan virtualisasi aktif.
- RAM minimum 8 GB; 16 GB lebih nyaman untuk banyak pengguna atau pembuatan PDF bersamaan.
- Ruang kosong minimal 30 GB pada SSD.
- Komputer server dan ponsel berada pada Wi-Fi/LAN yang sama.
- Docker Desktop menggunakan backend WSL 2.
- Git for Windows untuk mengambil dan memperbarui source code.
- APK debug SmartDispo 0.4.1 atau lebih baru untuk koneksi HTTP pada jaringan lokal.

Build release hanya menerima HTTPS. Untuk pengujian LAN gunakan APK debug yang sudah disediakan proyek.

## 2. Siapkan Windows

1. Masuk BIOS/UEFI dan aktifkan **AMD-V/SVM** atau **Intel VT-x** bila belum aktif.
2. Buka PowerShell sebagai Administrator, lalu jalankan:

   ```powershell
   wsl --install
   ```

3. Restart Windows bila diminta.
4. Instal Docker Desktop dari situs resminya.
5. Di Docker Desktop, aktifkan **Use the WSL 2 based engine** dan **Start Docker Desktop when you sign in**.
6. Ubah jaringan Wi-Fi/Ethernet Windows menjadi **Private network**.
7. Agar server tidak tidur, buka **Settings > System > Power & battery** lalu atur Sleep menjadi **Never**
   saat tersambung listrik.

## 3. Ambil proyek

Buka PowerShell biasa:

```powershell
cd C:\
git clone https://github.com/youbrey/SmartDispo-DPRD.git
cd C:\SmartDispo-DPRD
git checkout main
```

Jika folder proyek sudah ada:

```powershell
cd C:\SmartDispo-DPRD
git pull origin main
```

Jangan menyimpan proyek di folder yang otomatis disinkronkan OneDrive.

## 4. Bangun server pertama kali

Pastikan Docker Desktop sudah berstatus **Engine running**. Buka PowerShell sebagai Administrator:

```powershell
cd C:\SmartDispo-DPRD
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-local-server.ps1
```

Skrip akan:

1. meminta username administrator, default `admin`;
2. meminta kata sandi administrator 12–128 karakter dengan huruf, angka, atau karakter `! @ # % _ + = . , : -`;
3. membuat rahasia JWT, kunci SIPS, dan password PostgreSQL acak;
4. membuka port TCP `8000` dan `8080` hanya untuk jaringan lokal Private;
5. membangun image Docker dan menjalankan semua layanan;
6. menjalankan migrasi database dan membuat akun administrator;
7. menampilkan alamat IPv4 yang harus dimasukkan ke APK.

Jangan membagikan atau mengunggah file konfigurasi rahasia server ke GitHub.

## 5. Pastikan server berjalan

Pada komputer server, buka:

- API health: `http://127.0.0.1:8000/health`
- Dokumentasi API: `http://127.0.0.1:8000/docs`
- Panel Administrator: `http://127.0.0.1:8080`

Masuk ke Panel Administrator dengan akun yang dibuat pada langkah setup. Status container juga dapat
diperiksa dengan:

```powershell
docker compose ps
docker compose logs api --tail 200
```

Container memakai kebijakan `restart: unless-stopped`, sehingga hidup kembali ketika Docker Engine hidup.

## 6. Temukan IP komputer server

Jalankan:

```powershell
ipconfig
```

Cari **IPv4 Address** pada adapter Wi-Fi atau Ethernet aktif, misalnya `192.168.1.10`. Jangan memakai:

- `127.0.0.1`;
- alamat adapter Docker/WSL;
- default gateway/router, misalnya `192.168.1.1`.

Uji dari browser ponsel yang memakai Wi-Fi sama:

```text
http://192.168.1.10:8000/health
```

Jika berhasil, browser menampilkan respons health server. Panel admin dari perangkat lain tersedia pada:

```text
http://192.168.1.10:8080
```

## 7. Hubungkan APK

1. Instal APK debug SmartDispo versi 0.4.1 atau lebih baru.
2. Sambungkan ponsel ke Wi-Fi/LAN yang sama dengan komputer server.
3. Pada layar Login pilih **Atur alamat server**.
4. Masukkan `192.168.1.10:8000`, sesuaikan dengan IPv4 komputer.
5. Pilih **Uji & Simpan**.
6. Login memakai akun administrator yang dibuat saat setup.

APK otomatis mengubah alamat menjadi `http://192.168.1.10:8000/api/v1/`. Jika IP komputer berubah, cukup
ubah alamat dari layar Login atau menu Profil; APK tidak perlu dibangun ulang.

## 8. Pertahankan IP agar tidak sering berubah

Pilihan yang paling aman adalah **DHCP Reservation** pada router:

1. lihat MAC Address komputer dengan `ipconfig /all`;
2. masuk ke halaman administrasi router;
3. cari DHCP Reservation/Static Lease;
4. pasangkan MAC Address komputer dengan IP, misalnya `192.168.1.10`;
5. restart koneksi komputer dan pastikan IP tetap sama.

Jika router tidak menyediakan fitur tersebut, APK tetap dapat diarahkan ke IP baru tanpa build ulang.

## 9. Menjalankan dan menghentikan server

Menjalankan kembali:

```powershell
cd C:\SmartDispo-DPRD
.\scripts\start-local-server.ps1
```

Menghentikan sementara:

```powershell
docker compose stop
```

Menjalankan setelah dihentikan:

```powershell
docker compose start
```

Jangan menjalankan `docker compose down -v`; opsi `-v` menghapus volume database dan dokumen.

## 10. Backup

Jalankan PowerShell:

```powershell
cd C:\SmartDispo-DPRD
.\scripts\backup-local-server.ps1
```

ZIP backup berisi database, dokumen hasil, lampiran, dan template. Salin ZIP ke disk atau komputer lain.
File rahasia server tidak dimasukkan ke ZIP dan harus dicadangkan terpisah dengan akses terbatas.

## 11. Memperbarui aplikasi server

Sebelum pembaruan, buat backup. Kemudian:

```powershell
cd C:\SmartDispo-DPRD
git pull origin main
docker compose up -d --build
```

Migrasi database dijalankan otomatis saat container API dimulai.

## 12. Pemecahan masalah

### `health` bisa dibuka di komputer tetapi tidak di ponsel

- Pastikan kedua perangkat berada pada jaringan yang sama.
- Pastikan profil jaringan Windows adalah Private.
- Jalankan ulang setup sebagai Administrator agar aturan firewall dibuat.
- Matikan fitur AP/client isolation pada router Wi-Fi.
- Pastikan VPN ponsel dan komputer dimatikan selama pengujian LAN.

### APK menolak HTTP

Pastikan APK yang dipasang adalah build **debug**. Build release sengaja mewajibkan HTTPS. Untuk akses dari
internet atau penggunaan produksi, pasang domain, sertifikat HTTPS, dan reverse proxy; jangan membuka port
8000 langsung ke internet.

### API gagal hidup setelah password database diubah

Nilai `SMARTDISPO_POSTGRES_PASSWORD` dan password pada `SMARTDISPO_DATABASE_URL` harus sama. Untuk server
yang sudah memiliki volume database, jangan mengganti password hanya pada file konfigurasi.

### Lupa kata sandi administrator

Mengubah nilai bootstrap setelah akun dibuat tidak mengganti password akun lama. Gunakan fungsi reset
password dari akun administrator lain atau prosedur administrasi database yang terkontrol.

## 13. Batas penggunaan server lokal

- Selama hanya digunakan pada Wi-Fi/LAN kantor, APK tidak dapat mengakses server dari luar kantor.
- Untuk akses internet, gunakan HTTPS melalui domain/VPN yang dikelola; port PostgreSQL dan Redis tidak
  boleh dibuka ke router.
- Komputer harus tetap menyala, Docker Desktop aktif, dan Windows tidak dalam mode sleep.
- Gunakan UPS agar transaksi dan file tidak rusak ketika listrik padam.

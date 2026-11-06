# Broadcast Information

Sistem distribusi dokumen dan broadcast email untuk TV Engineering, PT SHARP Electronics Indonesia. Aplikasi ini menyimpan dokumen PDF, mengelola daftar penerima per divisi, lalu mengirim email pengingat berisi tautan unduhan dokumen ke penerima yang relevan.

Dibangun dengan FastAPI, SQLAlchemy, SQLite, dan template Jinja2 + Bootstrap 5.

## Fitur

- Autentikasi ganda: session cookie untuk halaman web dan JWT Bearer untuk API.
- Peran pengguna admin dan user biasa; halaman manajemen user hanya untuk admin.
- Registrasi mandiri untuk akun pertama (bootstrap admin), selanjutnya hanya oleh admin.
- Unggah dokumen PDF dengan validasi tipe file, ukuran, nomor dokumen unik, dan divisi tujuan.
- Pencarian dan paginasi daftar dokumen serta penerima.
- Registri penerima per divisi dengan kategori Direct atau CC.
- Broadcast email melalui relay internal SHARP atau Office 365, dengan pengaturan pengirim per user.
- Kompatibilitas database lama: nama tabel/kolom historis dipertahankan dan migrasi dijalankan otomatis saat startup.
- Halaman error dan pesan flash yang konsisten, plus logging request.

## Tumpukan Teknologi

| Komponen | Teknologi |
| --- | --- |
| Web framework | FastAPI 0.115+ |
| Server | Uvicorn |
| ORM / database | SQLAlchemy 2 + SQLite |
| Validasi / konfigurasi | Pydantic 2 + pydantic-settings |
| Template | Jinja2 + Bootstrap 5 |
| Autentikasi | itsdangerous SessionMiddleware, python-jose (JWT), bcrypt |
| Email | smtplib (EmailMessage) |
| Pengujian | pytest + httpx TestClient |

## Struktur Proyek

```
broadcast_information/
├── app/
│   ├── main.py              # application factory, middleware, error handler
│   ├── config.py            # settings dari environment / app/.env
│   ├── core/                # security, dependency, error, flash, templating
│   ├── db/                  # engine, session, model, migrasi
│   ├── routers/             # halaman HTML dan endpoint JSON
│   ├── schemas/             # skema Pydantic
│   ├── services/            # logika dokumen, penerima, user, broadcast, SMTP
│   ├── templates/           # template Jinja2
│   ├── static/              # CSS, JS, gambar, font
│   ├── database/            # file SQLite
│   ├── storage/documents/   # file PDF yang diunggah
│   └── .env.example         # contoh konfigurasi
├── tests/                   # pengujian pytest
├── run.py                   # entry point pengembangan
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

## Menjalankan Secara Lokal

Prasyarat: Python 3.11 atau lebih baru (dikembangkan dengan Python 3.13).

```bash
python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate      # Linux/macOS
pip install -r requirements.txt
copy app\.env.example app\.env  # Windows
# cp app/.env.example app/.env  # Linux/macOS
python run.py
```

Buka `http://localhost:8000`. Saat database masih kosong, buka `/register` untuk membuat akun pertama; akun tersebut otomatis menjadi admin. Setelah itu pendaftaran user hanya bisa dilakukan admin melalui menu Users atau `/app/users`.

Dokumentasi OpenAPI otomatis tersedia di `/docs`.

## Konfigurasi

Semua pengaturan dibaca dari environment variable atau `app/.env`. Nama variabel tidak peka huruf besar/kecil. Path relatif untuk `DATABASE_URL` dan `STORAGE_DIR` dihitung terhadap direktori `app/`.

| Variabel | Default | Keterangan |
| --- | --- | --- |
| `APP_NAME` | Broadcast Information | Nama aplikasi |
| `APP_HOST` / `APP_PORT` | localhost / 8000 | Alamat bind `run.py` |
| `PUBLIC_BASE_URL` | http://localhost:8000 | Basis URL tautan dokumen di email; wajib disesuaikan di produksi |
| `DEBUG` | false | Mengaktifkan reload dan log debug |
| `DATABASE_URL` | sqlite:///database/broadcast_db.sqlite | Koneksi database |
| `SECRET_KEY` | - | Kunci penandatangan JWT; ganti dengan nilai acak |
| `JWT_ALGORITHM` | HS256 | Algoritma JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Masa berlaku access token |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | 10080 | Masa berlaku refresh token (7 hari) |
| `SESSION_SECRET_KEY` | - | Kunci cookie session; ganti dengan nilai acak |
| `SESSION_MAX_AGE_SECONDS` | 28800 | Umur cookie session (8 jam) |
| `SESSION_COOKIE_NAME` | broadcast_session | Nama cookie session |
| `COOKIE_HTTPS_ONLY` | false | Set `true` jika aplikasi diakses via HTTPS |
| `STORAGE_DIR` | storage/documents | Direktori penyimpanan PDF |
| `MAX_UPLOAD_MB` | 20 | Batas ukuran unggahan |
| `SMTP_SENDER_EMAIL` / `SMTP_SENDER_PASSWORD` | kosong | Akun pengirim cadangan |
| `SMTP_TIMEOUT_SECONDS` | 20 | Timeout koneksi SMTP |
| `SHARP_SMTP_HOST` / `SHARP_SMTP_PORT` | relay.sharp.co.jp / 25 | Relay internal SHARP |
| `SHARP_SMTP_STARTTLS` | true | STARTTLS relay SHARP |
| `OFFICE_SMTP_HOST` / `OFFICE_SMTP_PORT` | smtp.office365.com / 587 | Server Office 365 |
| `OFFICE_SMTP_STARTTLS` | true | STARTTLS Office 365 |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | 10 / 100 | Batas paginasi |

Membuat kunci acak:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

File `app/.env` tidak dilacak Git dan tidak boleh di-commit karena memuat kredensial SMTP.

## Alur Penggunaan

1. Admin mendaftarkan penerima di menu Recipients: email, nama, divisi, dan kategori Direct/CC.
2. User mengunggah PDF di menu Upload Document, memilih tipe dokumen dan divisi tujuan.
3. Dari dashboard, pilih nomor dokumen dan server SMTP, lalu kirim broadcast.
4. Penerima Direct menerima email dengan tautan unduhan; penerima CC masuk di kolom Cc.

## Aturan Dokumen

- Hanya berkas PDF yang diterima, diverifikasi dari magic byte `%PDF-`, bukan hanya ekstensi.
- Ukuran maksimum mengikuti `MAX_UPLOAD_MB`.
- Nomor dokumen harus unik dan hanya boleh berisi huruf, angka, titik, garis bawah, atau tanda hubung (`^[A-Za-z0-9][A-Za-z0-9._-]*$`).
- Tipe dokumen dan divisi tujuan harus berasal dari katalog di `app/services/catalog.py`.
- File disimpan di disk dengan nama UUID; dokumen lama yang masih berupa BLOB di database tetap bisa dibuka.
- Menghapus dokumen juga menghapus file fisiknya.

## Perilaku Broadcast

- Penerima diambil dari divisi tujuan dokumen: kategori Direct menjadi To, kategori CC menjadi Cc.
- Minimal harus ada satu penerima Direct; jika tidak, permintaan ditolak dengan status 422.
- Subjek email: `[Reminder] <subject dokumen>`.
- Isi email: deskripsi dokumen (jika ada) dan tautan `{PUBLIC_BASE_URL}/app/documents/{document_no}/file`.
- Pengirim dipilih dari email dan mail password user yang sedang login; jika kosong, dipakai `SMTP_SENDER_EMAIL` dan `SMTP_SENDER_PASSWORD`.
- Kegagalan autentikasi atau koneksi SMTP dilaporkan sebagai 502 tanpa mengubah data dokumen.
- Waktu broadcast terakhir disimpan di `last_broadcast_at`.

## Autentikasi

- Halaman web memakai cookie session bertanda tangan (itsdangerous). Request tanpa sesi ke halaman terlindungi diarahkan ke `/login?next=...`.
- API memakai OAuth2 password flow dengan JWT HS256. Endpoint menerima header `Authorization: Bearer <token>`; jika tidak ada, sesi cookie masih diterima sebagai fallback.
- Password di-hash dengan bcrypt; hash lama `$2b$` tetap kompatibel.
- Akun pertama otomatis menjadi admin; migrasi juga mempromosikan user pertama pada database lama jika belum ada admin.

Contoh memperoleh token:

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=rahasia"
```

## Referensi Endpoint

Halaman HTML:

| Metode | Path | Keterangan |
| --- | --- | --- |
| GET | `/` | Redirect ke `/app` |
| GET/POST | `/login` | Form login |
| POST | `/logout` | Keluar dan hapus sesi |
| GET/POST | `/register` | Registrasi akun (bootstrap atau admin) |
| GET | `/app` | Dashboard, statistik, form broadcast |
| GET | `/app/documents` | Daftar dokumen (`page`, `perpage`, `q`) |
| GET | `/app/documents/{document_no}/file` | Unduh/tampilkan PDF |
| GET | `/app/upload` | Form unggah dokumen |
| GET/POST | `/app/recipients` | Daftar dan tambah penerima |
| GET/POST | `/app/users` | Manajemen user (admin) |

API JSON (butuh autentikasi):

| Metode | Path | Keterangan |
| --- | --- | --- |
| POST | `/api/auth/token` | Ambil access dan refresh token |
| POST | `/api/auth/refresh` | Perbarui token |
| GET | `/api/auth/me` | Profil user aktif |
| GET | `/api/documents` | Daftar dokumen (`page`, `page_size`, `q`) |
| GET | `/api/documents/numbers` | Daftar nomor dokumen |
| GET | `/api/documents/{document_no}` | Detail dokumen |
| POST | `/api/documents` | Unggah dokumen (multipart) |
| DELETE | `/api/documents/{document_no}` | Hapus dokumen |
| GET | `/api/recipients` | Daftar penerima (`page`, `page_size`, `q`, `division`) |
| POST | `/api/recipients` | Tambah penerima |
| DELETE | `/api/recipients/{recipient_id}` | Hapus penerima |
| POST | `/api/broadcast` | Kirim broadcast `{ "document_no": "...", "server": "sharp" }` |

Posting unggahan memakai field form `document_no`, `document_type`, `subject`, `description`, `model_tv`, `distributed_to` (boleh berulang), dan `file`.

## Database dan Migrasi

Database SQLite berada di `app/database/broadcast_db.sqlite` dan dibuat otomatis saat startup. Tabel mempertahankan nama historis `tb_users`, `tb_documents`, dan `tb_recipients`.

Saat aplikasi mulai, `app/db/migrations.py` menjalankan migrasi idempoten:

- Menambah kolom baru yang belum ada (mis. `is_admin`, `stored_filename`, `uploader_id`).
- Mempromosikan user pertama menjadi admin bila belum ada admin.
- Menormalkan format tanggal lama seperti `20 October 2023, 09:47` menjadi `YYYY-MM-DD HH:MM:SS`.

Selalu buat cadangan file SQLite sebelum melakukan upgrade:

```bash
copy app\database\broadcast_db.sqlite app\database\broadcast_db.sqlite.bak
```

## Pengujian

```bash
pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest
```

Test menggunakan database dan direktori penyimpanan sementara, serta memalsukan pengiriman SMTP sehingga tidak ada email sungguhan yang terkirim. Cakupan meliputi autentikasi, unggah/daftar/hapus dokumen, penerima, dan broadcast.

## Catatan Deployment

- Jalankan dengan satu worker karena SQLite: `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Gunakan reverse proxy (IIS, nginx) untuk HTTPS.
- Set `PUBLIC_BASE_URL` ke alamat yang dapat diakses penerima; tautan di email memakai nilai ini.
- Set `COOKIE_HTTPS_ONLY=true` bila sudah memakai HTTPS.
- Pastikan `SECRET_KEY`, `SESSION_SECRET_KEY`, dan kredensial SMTP diisi dari environment atau `.env` yang aman.
- Direktori `app/storage/documents` dan `app/database` harus dapat ditulis oleh proses aplikasi dan disertakan dalam strategi backup.

## Keamanan

Versi ini belum mencakup hardening lanjutan (rate limiting, CSP, audit log, dan sejenisnya). Yang sudah diterapkan: hash bcrypt, cookie HttpOnly dengan SameSite Lax, validasi unggahan berbasis isi file, sanitasi pesan error, dan pemisahan peran admin.

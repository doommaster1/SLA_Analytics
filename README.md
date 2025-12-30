# SLA Predictor - Skripsi Project

Aplikasi prediksi SLA tiket menggunakan algoritma Random Forest dan K-Prototypes.
Project ini dibangun menggunakan **Django** (Backend), **React.js** (Frontend), dan **PostgreSQL** (Database).

---

## Prasyarat (Prerequisites)
Pastikan software berikut sudah terinstall di komputer Anda:
1.  **Python** (v3.8 ke atas)
2.  **Node.js & npm** (untuk menjalankan React)
3.  **PostgreSQL** (dan pgAdmin untuk manajemen database)
4.  **Git**

---

## Langkah 1: Konfigurasi Database

Aplikasi ini membutuhkan database PostgreSQL. Ikuti langkah berikut:

1.  Buka **pgAdmin** atau terminal PostgreSQL.
2.  Buat database baru dengan nama: `sla_predictor`
3.  **PENTING: Sesuaikan Kredensial Database**
    Secara default, aplikasi ini dikonfigurasi untuk user `sla_user` dan password `admin`. Kemungkinan besar konfigurasi PostgreSQL di laptop Anda berbeda (biasanya user: `postgres`).
    
    Silakan buka file: `backend/sla_backend/settings.py`
    Cari bagian `DATABASES` (sekitar baris 130), lalu sesuaikan dengan milik Anda. Contoh penyesuaian:

    ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'sla_predictor',  # Nama DB yang baru dibuat
            'USER': 'postgres',       # <--- Ganti dengan user PostgreSQL Anda
            'PASSWORD': 'password_anda', # <--- Ganti dengan password Anda
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    ```

---

## Langkah 2: Instalasi Backend (Django)

Buka terminal/command prompt, arahkan ke folder project, lalu ikuti langkah ini:

**1. Masuk ke direktori backend**
```bash
cd backend

```

**2. Buat dan Aktifkan Virtual Environment**

```bash
# Untuk Windows
python -m venv venv
venv\Scripts\activate


```

**3. Install Library Python**

```bash
pip install -r requirements.txt

```

**4. DOWNLOAD MODEL MACHINE LEARNING (WAJIB)**
Karena ukuran file model melebihi batas GitHub, file `.pkl` tidak disertakan dalam repository ini.
Silakan download file model melalui link berikut:

https://drive.google.com/drive/folders/1KTOO5I_vyJJGg6evXwhBhRhRByEayFBr?usp=sharing

Setelah didownload, pindahkan file-file `.pkl` tersebut ke dalam folder:
`backend/tickets/utils/`

**5. Migrasi Database**

```bash
python manage.py makemigrations
python manage.py migrate

```

**6. Buat Superuser (Admin)**

```bash
python manage.py createsuperuser

```

**7. Jalankan Server Django**

```bash
python manage.py runserver

```

*Backend akan berjalan di https://www.google.com/search?q=http://127.0.0.1:8000/*

---

## 💻 Langkah 3: Instalasi Frontend (React)

Biarkan terminal Backend tetap berjalan. Buka **Terminal Baru**, lalu:

**1. Masuk ke direktori frontend**

```bash
cd frontend

```

**2. Install Dependencies (Wajib)**
Langkah ini akan mendownload semua library React (node_modules). Harap tunggu hingga selesai.

```bash
npm install

```

**3. Jalankan React**

```bash
npm start

```

*Browser akan otomatis terbuka di http://localhost:3000/*

---

## Catatan Penting Penggunaan

### 1. Verifikasi Email & OTP

Aplikasi ini menggunakan sistem verifikasi email untuk registrasi. Karena masih dalam mode development (`DEBUG = True`), email **TIDAK AKAN DIKIRIM KE GMAIL/INBOX**.

**Cara melihat link verifikasi / OTP:**

1. Lakukan registrasi di website.
2. Buka **Terminal Backend** (tempat `python manage.py runserver` berjalan).
3. Link verifikasi atau kode OTP akan muncul di text log terminal tersebut.

### 2. Login Admin

Untuk mengakses panel admin dan melihat data tiket:

* URL: https://www.google.com/search?q=http://127.0.0.1:8000/admin/
* Gunakan akun superuser yang dibuat pada Langkah 2 poin 6.

---

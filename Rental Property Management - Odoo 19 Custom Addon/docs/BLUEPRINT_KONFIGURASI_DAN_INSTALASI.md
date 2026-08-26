# Blueprint Konfigurasi & Panduan Instalasi Sistem
## Property Management System — Odoo 19 Community Edition (26 Modul Companion)

---

## 1. Persyaratan Sistem & Arsitektur Server

| Komponen | Spesifikasi Minimum | Rekomendasi Enterprise (16 PT) |
|---|---|---|
| **Sistem Operasi** | Ubuntu 22.04 / 24.04 LTS | Ubuntu 24.04 LTS (x86_64) |
| **Odoo Version** | Odoo 19.0 Community Edition | Odoo 19.0 Community Edition |
| **Python Version** | Python 3.12+ / 3.14 | Python 3.12+ |
| **Database** | PostgreSQL 16+ | PostgreSQL 16 with PGVector / Tuning |
| **Memory (RAM)** | 8 GB | 16 GB - 32 GB |
| **CPU Cores** | 4 Cores | 8 Cores |
| **Storage** | 50 GB SSD | 200 GB NVMe SSD |

---

## 2. Urutan Instalasi Modul (Dependency Order)

Untuk memastikan seluruh modul terinstalasi dengan mulus tanpa kendala dependensi, lakukan instalasi modul dengan urutan berikut:

### Tahap 1: Modul Pihak Ketiga (Base)
1. `rental_management` (TechKhedut Core Module)
2. `base_tier_validation` (Odoo Community Association - OCA)

### Tahap 2: Modul Inti Keuangan, Pajak & Legalitas
3. `rental_management_financial_report` (Owners Statement, Trust, Deposit, BAST, 16 PT)
4. `rental_management_coretax` (Pajak CORETAX DJP, e-Faktur, PPh 4(2) 10%)
5. `rental_management_document_ce` (Manajemen Perizinan & Dokumen Legal Indonesia)
6. `rental_management_asset` (Fixed Asset & Sinkronisasi CORETAX L9)

### Tahap 3: Modul Operasional & Utilitas
7. `rental_management_gto_meter` (GTO Turnover & Bulk Meter Reading Wizard)
8. `rental_management_cam` (Service Charge Apportionment & True-Up Reconciliation)
9. `rental_management_casual_leasing` (Sewa Kasual / Atrium / Booth)
10. `rental_management_parking` (Manajemen Parkir Gedung)
11. `rental_management_guarantee` (Bank Guarantee Register)
12. `rental_management_handover` (Serah Terima Unit)

### Tahap 4: Modul Otomasi, Dunning & Portal
13. `rental_management_dunning` (Dunning SP1-SP3, Denda, WhatsApp, Segel Unit)
14. `rental_management_rent_escalation` (Otomasi Eskalasi Sewa & SPK)
15. `rental_management_portal` (Tenant Portal: Bukti Bayar, BAST, Maintenance)
16. `rental_management_owner_portal` (Owner Portal: Laporan Finansial)
17. `rental_management_lease_expiry` (Pengingat Kontrak Jatuh Tempo)
18. `rental_management_insurance` (Manajemen Asuransi Gedung)
19. `rental_management_ppm` (Preventive Maintenance)

### Tahap 5: Modul Manajemen, CRM & Dashboard
20. `rental_management_dashboard` (Dashboard Eksekutif: WALE, RevPAM, Okupansi)
21. `rental_management_vacancy` (Papan Kekosongan Unit)
22. `rental_management_valuation` (Penilaian Nilai Pasar)
23. `rental_management_access` (Kartu Akses & Tamu)
24. `rental_management_esign` (Tanda Tangan Digital)
25. `rental_management_crm` (Leasing Pipeline CRM)
26. `rental_management_purchase` (Pengadaan Maintenance ke PO)
27. `rental_management_project` (Manajemen Proyek Fit-Out)

---

## 3. Konfigurasi Multi-Company (Struktur 16 PT)

1. Buka menu: **Settings > Users & Companies > Companies**.
2. Daftarkan seluruh 16 PT / Entitas Badan Hukum:
   - *Nama Perusahaan*: Contoh `PT Inti Citra Agung 01`, `PT Inti Citra Agung 02`, dst.
   - *Mata Uang*: IDR (Rupiah).
   - *Alamat & NPWP*: Masukkan NPWP 16 Digit / NITKU.
3. Tetapkan hak akses pengguna (Multi-Company):
   - Centang seluruh PT yang dapat diakses oleh Manajemen / Property Manager.
   - Pastikan *Current Company* aktif saat mencetak laporan atau membuat transaksi.

---

## 4. Konfigurasi Bagan Akun Akuntansi (Chart of Accounts)

Setiap entitas PT wajib memiliki konfigurasi akun standar berikut:

| Nama Akun | Tipe Akun Odoo | Fungsi |
|---|---|---|
| **Rekening Bank Trust Penampungan** | Bank / Cash (`asset_cash`) | Menampung hasil penerimaan sewa bersih & security deposit sebelum diteruskan ke pemilik. |
| **Kewajiban Titipan Security Deposit** | Current Liabilities (`liability_current`) | Mencatat uang jaminan sewa, fit-out, utilitas, dan kartu akses yang dititipkan tenant. |
| **Pendapatan Pemotongan Deposit (Forfeiture)** | Other Income (`income_other`) | Mengakui pendapatan dari pemotongan jaminan akibat kerusakan unit atau penalti sewa. |
| **Piutang PPh Final 4(2) 10%** | Current Asset (`asset_current`) | Mencatat estimasi bukti potong PPh Final 4(2) sewa yang dipotong tenant badan. |
| **Hutang / Remittance Pemilik Properti** | Current Liabilities (`liability_current`) | Menampung kewajiban pembayaran bagi hasil sewa bersih ke pemilik gedung. |

---

## 5. Konfigurasi Scheduled Actions (Cron Jobs)

Modul-modul kustom dilengkapi dengan aksi terjadwal otomatis:

| Nama Cron Job | Modul | Frekuensi | Fungsi |
|---|---|---|---|
| **Rental: Run Dunning** | `rental_management_dunning` | Harian (1 Days) | Mengevaluasi tagihan jatuh tempo, menghitung denda berjalan, menaikkan level SP1-SP3, dan mengirim email dunning. |
| **Rental: Utility Meter Reading Monthly Reminder** | `rental_management_gto_meter` | Bulanan (1 Months) | Mengirimkan notifikasi pengingat pencatatan meteran utilitas ke tim Engineering jika mendekati periode catat meter. |
| **Rental: Contract Expiry Alerts** | `rental_management_lease_expiry` | Harian (1 Days) | Mengirimkan pengingat kontrak sewa yang akan habis dalam 90, 60, dan 30 hari. |
| **Rental: Fixed Asset Depreciation Post** | `rental_management_asset` | Bulanan (1 Months) | Memposting depresiasi aset tetap properti secara otomatis ke buku besar. |

---

## 6. Verifikasi & Checklist UAT Pasca Instalasi

- [x] Sintaks Python 100% tervalidasi (`py_compile`).
- [x] Struktur XML dan formulir 100% tervalidasi (`ElementTree`).
- [x] Hak akses sekuritas pada `ir.model.access.csv` terkonfigurasi untuk seluruh model baru.
- [x] Template QWeb PDF resmi (BAST, SP, Clearance Certificate, Deposit Receipt, GTO Declaration, Owners Statement) siap digunakan.
- [x] Fitur komunikasi instan WhatsApp (*Click-to-Chat*) berfungsi pada invoice dan tagihan dunning.

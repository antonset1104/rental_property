# Panduan Lengkap Pengguna & Buku Petunjuk Operasional (SOP)
## Property Management System — Odoo 19 Community Edition Suite (26 Modul)

Buku petunjuk operasional lengkap ini disusun untuk tim **Property Management**, **Building Management (MEP)**, **Finance & Accounting**, **Tenant Relations (TR)**, dan **Manajemen Eksekutif (Direksi)**.

---

## 📑 DAFTAR ISI

1. [Struktur Master Data: Unit Properti, Master Unit ID & MEP](#1-struktur-master-data-unit-properti-master-unit-id--mep)
2. [Multi-Company (16 PT) & Multi-Owner (%)](#2-multi-company-16-pt--multi-owner-)
3. [Alur Kontrak Sewa (Tenancy Details) & Smart Button](#3-alur-kontrak-sewa-tenancy-details--smart-button)
4. [Digital BAST Serah Terima (Move-In / Move-Out) & Cetak PDF](#4-digital-bast-serah-terima-move-in--move-out--cetak-pdf)
5. [Pengelolaan Multi-Type Deposit & Fit-Out (SLA 30 Hari & Auto-Jurnal)](#5-pengelolaan-multi-type-deposit--fit-out-sla-30-hari--auto-jurnal)
6. [Billing Bulanan, Bulk Meter Reading & Deklarasi GTO Omzet](#6-billing-bulanan-bulk-meter-reading--deklarasi-gto-omzet)
7. [Integrasi Pajak Indonesia: CORETAX e-Faktur & PPh Final 4(2) 10%](#7-integrasi-pajak-indonesia-coretax-e-faktur--pph-final-42-10)
8. [Penagihan & Dunning SP1–SP3, WhatsApp, Cetak SP & Segel Unit](#8-penagihan--dunning-sp1sp3-whatsapp-cetak-sp--segel-unit)
9. [Tenant Self-Service Portal (Bukti Bayar, BAST, Maintenance)](#9-tenant-self-service-portal-bukti-bayar-bast-maintenance)
10. [Dashboard Eksekutif: Metrik WALE, RevPAM & Okupansi](#10-dashboard-eksekutif-metrik-wale-revpam--okupansi)
11. [Alur Tutup Kontrak & Surat Bebas Kewajiban (Clearance Certificate)](#11-alur-tutup-kontrak--surat-bebas-kewajiban-clearance-certificate)
12. [Laporan Keuangan Pemilik (Owners Statement) Konsolidasi 16 PT & Ekspor Excel](#12-laporan-keuangan-pemilik-owners-statement-konsolidasi-16-pt--ekspor-excel)
13. [Manajemen Perizinan & Dokumen Legal Gedung](#13-manajemen-perizinan--dokumen-legal-gedung)
14. [Surat Izin Kerja (SIK) Renovasi / Fit-Out Work Permit](#14-surat-izin-kerja-sik-renovasi--fit-out-work-permit)
15. [Tarif Listrik Beban Puncak PLN (WBP / LWBP) & Utilitas Ganda](#15-tarif-listrik-beban-puncak-pln-wbp--lwbp--utilitas-ganda)
16. [Rating Kepuasan Tenant (CSAT) pada Portal Maintenance](#16-rating-kepuasan-tenant-csat-pada-portal-maintenance)

---

## 1. Struktur Master Data: Unit Properti, Master Unit ID & MEP

### A. Format Master Unit ID
Setiap unit properti memiliki kode unik terstruktur berformat:
`[Kode Gedung]-[Lantai]-[Nomor Unit]` (Contoh: `PMKBN001-GF-01` atau `TWR-A-05-12`).
- Buka menu: **Rental Management > Properties > Properties**.
- Buka unit properti, masuk ke tab **Owners & Financial**.
- Masukkan Nomor Unit dan klik tombol **"Format ID"** untuk menghasilkan format standar otomatis.

### B. Atribut Spesifikasi Teknis MEP
Pengelola gedung dan tim Engineering dapat mencatat kapasitas teknis unit pada tab yang sama:
- **Daya Listrik (VA)**: Contoh 6.600 VA, 13.200 VA, 33.000 VA, dsb.
- **Suplai Air Bersih**: PDAM / Deep Well / WTP Mandiri.
- **Line Telepon & Internet**: Jumlah sambungan kabel optik/tembaga.
- **Unit AC**: Jumlah unit indoor/outdoor dan tipe split/VRV/chiller.
- **Proteksi Kebakaran**: Checklist Fire Sprinkler, Smoke Detector, dan Speaker Evakuasi.
- **Sistem Pembuangan Air**: Saluran Sewage Treatment Plant (STP) / Grease Trap (khusus tenant F&B).

---

## 2. Multi-Company (16 PT) & Multi-Owner (%)

Sistem dirancang untuk mendukung kepemilikan gedung oleh lebih dari satu badan hukum (PT) atau individu dengan pembagian persentase kepemilikan (*prorated daily ownership*):
1. Pada form properti, buka tabel **Owners**.
2. Tambahkan baris pemilik, pilih partner pemilik, dan tentukan **Ownership %** (total seluruh pemilik wajib 100%).
3. Masukkan rentang tanggal berlaku kepemilikan (*Berlaku Dari* dan *Berlaku Sampai*) bila terdapat perpindahan kepemilikan di tengah tahun buku.
4. Sistem akan otomatis membagi hasil sewa bersih (*Net Rental Income*) dan laporan keuangan secara proporsional sesuai persentase kepemilikan.

---

## 3. Alur Kontrak Sewa (Tenancy Details) & Smart Button

### A. Membuat & Mengaktifkan Kontrak
1. Buka menu: **Rental Management > Tenancies > Tenancy Contracts**.
2. Masukkan Penyewa (Tenant), Unit Properti, Tanggal Mulai (*Start Date*), dan Tanggal Berakhir (*End Date*).
3. Tentukan nilai sewa pokok (*Base Rent*), periode penagihan (Bulanan / Triwulan / Tahunan), dan akun analitik.
4. Klik **Confirm** untuk mengesahkan kontrak.

### B. Tombol Cepat (Smart Buttons) di Header Kontrak
- **📋 BAST & Inspeksi**: Membuka daftar dokumen serah terima awal (Move-In) dan pengosongan (Move-Out) terkait kontrak tersebut.
- **🖨️ Cetak Clearance Certificate**: Mencetak Surat Keterangan Bebas Kewajiban resmi saat masa sewa berakhir.
- **🚨 Segel Unit / Buka Segel**: Mengubah status penyegelan unit akibat sanksi penagihan dunning SP3.

---

## 4. Digital BAST Serah Terima (Move-In / Move-Out) & Cetak PDF

### A. Pelaksanaan Pemeriksaan Lapangan
1. Buka menu: **Rental Management > BAST & Inspeksi Unit** (atau via Smart Button kontrak).
2. Klik **New**, pilih jenis BAST:
   - *Serah Terima Awal (Move-In)*
   - *Pengosongan / Pengembalian (Move-Out)*
   - *Inspeksi Berkala (Maintenance Audit)*
3. Pilih nomor kontrak sewa.
4. Klik tombol **"📋 Muat Standar Checklist (10 Item)"** untuk memunculkan otomatis daftar pemeriksaan fisik standar:
   - *Pintu Utama & Kunci Handle*
   - *Dinding Ruangan & Cat Finishing*
   - *Lantai (Keramik / Homogeneous / Vinyl)*
   - *Plafon & Lampu Penerangan*
   - *Unit AC & Remote*
   - *Fire Sprinkler & Smoke Detector*
   - *Sanitair & Saluran Pembuangan Air (STP)*
   - *Panel MCB & Instalasi Listrik*
   - *Kaca Jendela & Kusen Aluminium*
   - *Fisik Segel Meteran Utilitas*
5. Isi kondisi fisik (*Baik, Rusak, Hilang, N/A*), catatan detail, dan unggah foto kondisi fisik lapangan.
6. Catat **Stand Angka Meter Listrik (kWh)** dan **Stand Angka Meter Air (m³)** serah terima.

### B. Pengesahan & Pencetakan BAST PDF
1. Klik **"✅ Sahkan BAST & Hasil Pemeriksaan"**.
2. Klik tombol **"🖨️ Cetak BAST (PDF)"** untuk mencetak dokumen Berita Acara Serah Terima formal yang siap ditandatangani oleh Tenant dan Building Manager.
3. Untuk BAST Move-Out, tanggal BAST otomatis mengunci dan memulai **perhitungan mundur SLA 30 hari** pada modul Security Deposit.

---

## 5. Pengelolaan Multi-Type Deposit & Fit-Out (SLA 30 Hari & Auto-Jurnal)

### A. Kategori Deposit
Buka menu: **Rental Management > Property Deposits**. Kategori deposit yang didukung:
- **Security Deposit (Sewa Unit)**: Jaminan sewa umum.
- **Fit-Out / Renovation Deposit**: Jaminan pekerjaan renovasi tenant.
- **Utility Deposit**: Jaminan tagihan listrik dan air.
- **Access Card Deposit**: Jaminan kartu akses gedung.

### B. Verifikasi Khusus Deposit Fit-Out / Renovasi
Khusus untuk deposit Fit-Out, formulir menyediakan seksi verifikasi:
- Tanggal Selesai Renovasi.
- Checklist **"Inspeksi Akhir Fit-Out Lolos"** (*boolean toggle*).
- Catatan Kerusakan Struktur / MEP (jika ada kerusakan yang harus diperbaiki tenant).

### C. SLA 30 Hari Pengembalian & Cetak Tanda Terima PDF
- Saat dana deposit diterima, klik tombol **"🖨️ Cetak Tanda Terima (Receipt)"** untuk memberikan bukti setor resmi berklausul legal kepada tenant.
- Setelah BAST Move-Out ditandatangani, sistem menampilkan indikator SLA:
  - 🟢 **On Track**: Masih dalam rentang waktu SLA (< 23 hari).
  - 🟡 **Warning**: Mendekati batas waktu (sisa ≤ 7 hari).
  - 🔴 **Overdue**: Melewati batas 30 hari kalender.

### D. Otomatisasi Jurnal Akuntansi (*Settlement Posting*)
Klik tombol **"Post Deductions/Refunds"**:
- **Pemotongan Deposit**: Otomatis menjurnal *Dr Deposit Liability Account / Cr Deposit Income/Biaya Perbaikan*.
- **Pengembalian Sisa (Refund)**: Otomatis menjurnal *Dr Deposit Liability Account / Cr Trust Bank Account*.

---

## 6. Billing Bulanan, Bulk Meter Reading & Deklarasi GTO Omzet

### A. Bulk Meter Reading (Pencatatan Meteran Cepat)
1. Buka menu: **Rental Management > Utilitas & Meteran > Catat Meter Massal (Wizard)**.
2. Pilih Gedung / Properti, Tipe Utilitas (Listrik / Air), dan Tanggal Pencatatan.
3. Tabel akan otomatis menampilkan seluruh unit beserta stand meteran sebelumnya.
4. Petugas cukup memasukkan angka **Stand Meter Saat Ini**; sistem langsung menghitung pemakaian konsumsi dan nilai estimasi tagihan.
5. Klik **"Proses & Buat Draft Invoice"** untuk membuat seluruh invoice tagihan utilitas sekaligus.

### B. GTO (Gross Turnover) / Sewa Bagi Hasil
1. Pada kontrak sewa tenant F&B/retail, aktifkan opsi **GTO / Revenue Sharing** dan pilih tipe:
   - *Higher of Base Rent or % Turnover* (Pilih mana yang lebih tinggi antara sewa pokok vs % omzet)
   - *Base Rent + Overage* (Sewa pokok + kelebihan omzet di atas batas *breakpoint*)
   - *Pure % of Turnover* (Murni persentase omzet)
2. Setiap akhir bulan, tenant menyerahkan laporan penjualan; input pada **Turnover Declarations**.
3. Klik tombol **"🖨️ Cetak Pernyataan Omzet (GTO)"** untuk mencetak formulir surat pernyataan omzet formal.
4. Klik **Create Invoice** untuk menerbitkan tagihan bagi hasil sewa.

---

## 7. Integrasi Pajak Indonesia: CORETAX e-Faktur & PPh Final 4(2) 10%

### A. Pelacakan Bukti Potong PPh Final Pasal 4 Ayat (2) Sewa (10%)
Berdasarkan peraturan perpajakan Indonesia, sewa tanah dan bangunan dipotong PPh Final 10% oleh tenant berstatus Wajib Pajak Badan:
1. Pada setiap invoice tagihan sewa/ruangan, sistem secara otomatis:
   - Menandai opsi **"Objek PPh Final 4(2) 10%"**.
   - Menghitung **Estimasi PPh 4(2) Dipotong (10% dari DPP)**.
   - Mengatur status Bukti Potong ke **Menunggu Bukti Potong (Pending)**.
2. Ketika tenant menyerahkan Bukti Potong e-Bupot Unifikasi:
   - Ubah status menjadi **Bukti Potong Diterima**.
   - Masukkan Nomor Bukti Potong e-Bupot dan Tanggal Terbit.
   - Unggah berkas PDF Bukti Potong pada field **File Bukti Potong**.

### B. Batch Update Nomor Seri e-Faktur CORETAX DJP
1. Buka menu: **Invoicing > Pajak CORETAX > Update Batch Nomor Faktur**.
2. Masukkan Nomor Awal Faktur (contoh: `010.001-26.00000100`) dan Tanggal Faktur.
3. Klik **"Terapkan Nomor Faktur Berurutan"** untuk mengalokasikan nomor seri faktur pajak keluaran (PK) ke puluhan invoice sekaligus.
4. Ekspor file XML skema CORETAX DJP untuk diunggah langsung ke portal CORETAX DJP.

---

## 8. Penagihan & Dunning SP1–SP3, WhatsApp, Cetak SP & Segel Unit

### A. Tangga Dunning (SP1, SP2, SP3) & Perhitungan Denda
Sistem menjalankan evaluasi terjadwal (*Automated Cron Job*) setiap hari:
- **Level 1 (SP1 - Lewat 7 Hari)**: Denda berjalan mingguan (2%/minggu) atau harian (1‰/hari) + Email Peringatan I.
- **Level 2 (SP2 - Lewat 14 Hari)**: Teguran keras tunggakan sewa + Email Peringatan II.
- **Level 3 (SP3 - Lewat 21 Hari)**: Peringatan Terakhir + Rekomendasi Penyegelan Fisik Unit.

### B. Notifikasi WhatsApp Instan (*Click-to-Chat*)
1. Buka invoice tagihan yang belum lunas (`not_paid` / `partial`).
2. Klik tombol **"📲 Kirim WhatsApp"** di header form invoice.
3. Sistem membuka chat WhatsApp resmi (`wa.me`) dengan pesan otomatis yang rapi dan terformat lengkap dengan rincian invoice, nominal, due date, dan rekening bank.

### C. Cetak Surat Peringatan (SP) Formal PDF
1. Klik tombol **"🖨️ Cetak Surat Peringatan (SP)"** pada form invoice.
2. Sistem menerbitkan surat somasi/teguran fisik berkop surat resmi sesuai level dunning berjalan (SP1, SP2, atau SP3) lengkap dengan klausul hukum batas waktu pelunasan.

### D. Tindakan Penyegelan Fisik Unit / Pemutusan Layanan
1. Pada form kontrak sewa (`tenancy.details`), klik tombol **"🚨 Segel Unit / Putus Layanan"**.
2. Masukkan alasan penyegelan dan konfirmasi.
3. Layar kontrak menampilkan **Banner Merah Peringatan**: *"UNIT INI SEDANG DALAM STATUS DISEGEL / LAYANAN DIBLOKIR"*.
4. Setelah tenant melunasi tunggakan, klik tombol **"✅ Buka Segel Unit"**.

---

## 9. Tenant Self-Service Portal (Bukti Bayar, BAST, Maintenance)

Tenant dapat mengakses portal mandiri via browser di URL `/my`:
- **/my/invoices**: Melihat tagihan dan mengunggah bukti transfer bank (PDF/foto slip) melalui form *"Upload Bukti Transfer Bank (Slip/Foto Struk)"*. Sistem otomatis mengirim notifikasi ke tim Finance.
- **/my/contracts**: Melihat rincian kontrak sewa aktif dan riwayat dokumen **Berita Acara Serah Terima (BAST)** beserta angka stand meter listrik & air.
- **/my/maintenance**: Mengajukan tiket keluhan atau permintaan perbaikan teknis ruangan (*Maintenance Request*) mandiri lengkap dengan foto kendala.

---

## 10. Dashboard Eksekutif: Metrik WALE, RevPAM & Okupansi

Buka menu: **Rental Management > KPI Dashboard**:
- **WALE (Weighted Average Lease Expiry)**: Menghitung rata-rata sisa masa sewa seluruh portofolio gedung berbobot nilai kontrak (dalam satuan Tahun dan Bulan) untuk mengukur risiko kekosongan massal (*lease expiry risk*).
- **RevPAM (Revenue per Available Square Meter)**: Rasio pendapatan kotor per meter persegi total luas area sewa yang tersedia.
- **Occupancy Rate (%)**: Tingkat keterisian unit aktif dibandingkan total kapasitas unit gedung.
- **Collection Rate (%) & Arrears Total**: Tingkat efektivitas penagihan kas dan total piutang sewa tertunggak.
- **Net Operating Income (NOI)**: Pendapatan operasional bersih (Pendapatan Sewa & Utilitas dikurangi Beban Pemeliharaan & Operasional).

---

## 11. Alur Tutup Kontrak & Surat Bebas Kewajiban (Clearance Certificate)

Ketika masa sewa tenant berakhir:
1. Buat dan sahkan **BAST Move-Out** (pemeriksaan fisik 10 komponen dan angka meter akhir).
2. Verifikasi pelunasan seluruh tagihan invoice sewa pokok, service charge, dan utilitas terakhir.
3. Buka form kontrak sewa (`tenancy.details`) dan klik tombol **"🖨️ Cetak Clearance Certificate"**.
4. Terbitkan dokumen resmi **Surat Keterangan Bebas Kewajiban (Tenant Move-Out Clearance Certificate)** yang ditandatangani oleh *Chief Engineering*, *Finance Manager*, dan *Building Manager*.
5. Lakukan penyelesaian sisa saldo Security Deposit pada menu *Property Deposits*.

---

## 12. Laporan Keuangan Pemilik (Owners Statement) Konsolidasi 16 PT & Ekspor Excel

1. Buka menu: **Rental Management > Financial Reports > Laporan Pemilik (Wizard)**.
2. Pilih Mode Laporan:
   - **Per Properti**: Laporan performa finansial 1 gedung/unit tertentu.
   - **Gabungan per Entitas / Pemilik**: Laporan seluruh properti milik 1 pemilik.
   - **Konsolidasi Seluruh Entitas (16 PT)**: Laporan gabungan seluruh portofolio 16 PT dalam grup holding.
3. Pilih rentang periode fiskal dan masukkan **Catatan Manajemen / Ringkasan Eksekutif** (narasi kinerja dari Manajer Properti).
4. Klik **"Cetak Laporan Pemilik (PDF)"** untuk menghasilkan dokumen PDF komprehensif (9 bagian laporan: *Performance Summary, Income & Expenditure Accrual, Receipts & Payments Cash Basis, Tenant Balances, Aged Arrears, Payment Details, Trial Balance, Balance Sheet, GST/PPN Reconciliation*).
5. Klik **"📊 Ekspor Excel (.xlsx)"** untuk mengunduh spreadsheet Excel multi-tab (*Summary, Income & Expenditure, Receipts & Payments, Tenant Balances, Trial Balance*) dengan formula dan format sel rapi.
6. Klik tombol **"📧 Kirim Email ke Pemilik"** untuk mengirimkan PDF statement secara otomatis ke seluruh alamat email pemilik yang terdaftar.

---

## 13. Manajemen Perizinan & Dokumen Legal Gedung

Buka menu: **Rental Management > Dokumen Legal & Perizinan** (Modul `rental_management_document_ce`):
- Registrasi dokumen legalitas properti Indonesia:
  - **Sertifikat Tanah**: SHM (Sertifikat Hak Milik), HGB (Hak Guna Bangunan).
  - **Perizinan Bangunan**: IMB / PBG (Persetujuan Bangunan Gedung), SLF (Sertifikat Laik Fungsi).
  - **Pajak & Legalitas**: PBB (Pajak Bumi & Bangunan), NPWP, SPPKP, NITKU.
  - **Perjanjian**: PKS (Perjanjian Kerja Sama Sewa / Induk).
  - **Lingkungan & Keselamatan**: AMDAL / UKL-UPL, Sertifikat Keselamatan Kebakaran (Damkar).
- Setiap dokumen dilengkapi tanggal kedaluwarsa (*expiry date*) dan notifikasi pengingat perpanjangan sebelum izin habis masa berlaku.

---

## 14. Surat Izin Kerja (SIK) Renovasi / Fit-Out Work Permit

Sebelum kontraktor tenant memulai pekerjaan fisik/dekorasi:
1. Buka menu: **Rental Management > Surat Izin Kerja (SIK)**.
2. Klik **New**, pilih Kontrak Sewa (`tenancy.details`).
3. Masukkan identitas kontraktor pelaksana, nama PIC, nomor WhatsApp, dan jumlah pekerja.
4. Tentukan **Kategori Pekerjaan** (*Minor Fit-Out, Renovasi Mayor, MEP, Pembongkaran*) dan **Jam Kerja** (*Siang Hari, Malam Hari 21:00-05:00, Weekend*).
5. Aktifkan opsi **"Izin Pengelasan / Hot Work Permit"** jika ada pekerjaan panas serta verifikasi ketersediaan APAR dan Safety Briefing K3.
6. Klik **"✅ Setujui SIK"**, lalu klik **"🖨️ Cetak SIK (PDF)"** untuk mencetak Surat Izin Kerja resmi bertandatangan 3 pihak (*Kontraktor, Tenant, Building Management*).

---

## 15. Tarif Listrik Beban Puncak PLN (WBP / LWBP) & Utilitas Ganda

Khusus tenant komersial golongan tarif PLN B3/I3:
1. Pada form meteran listrik (`property.meter`), centang opsi **"Tarif Beban Puncak PLN (WBP / LWBP)"**.
2. Masukkan **Tarif WBP (Beban Puncak)** dan **Tarif LWBP (Luar Beban Puncak)**.
3. Saat mencatat meteran (`property.meter.reading`), masukkan angka stand meter WBP dan LWBP secara terpisah.
4. Sistem secara otomatis menghitung pemakaian kwh dan subtotal biaya masing-masing beban puncak, lalu menggabungkannya ke dalam 1 invoice tagihan utilitas bulanan.

---

## 16. Rating Kepuasan Tenant (CSAT) pada Portal Maintenance

1. Saat tiket pemeliharaan (*Maintenance Request*) telah selesai dikerjakan oleh tim Engineering/Teknisi.
2. Tenant membuka halaman tiket di portal `/my/maintenance/<id>`.
3. Tenant dapat memberikan **Rating Bintang (1 s.d. 5 Bintang)** dan ulasan masukan (*feedback*) kepuasan pelayanan.
4. Nilai kepuasan CSAT otomatis tercatat pada backend Odoo dan muncul sebagai indikator penilaian SLA kinerja tim operasional gedung.

---


---

## 21. Manajemen Langganan Parkir Tenant & Kendaraan RFID

Untuk mengelola alokasi parkir kendaraan penyewa (mobil, motor, slot VIP):
1. Buka menu: **Rental Management > Langganan Parkir Tenant**.
2. Klik **New**, pilih Kontrak Sewa (`tenancy.details`).
3. Masukkan data: Nomor Polisi (Plat Nomor), Merk/Model Kendaraan, Nama Pengemudi/Karyawan Tenant, dan Nomor Kartu RFID Parkir.
4. Tentukan **Kategori Kuota**:
   - **Jatah Kuota Gratis (Allotted)**: Kuota parkir cuma-cuma sesuai perjanjian luas sewa unit.
   - **Langganan Berbayar Bulanan**: Dikenakan tarif sewa slot parkir bulanan.
5. Klik **"✅ Aktifkan Pass Parkir"** dan klik **"🖨️ Cetak Formulir Parkir (PDF)"** untuk mencetak bukti tanda daftar dan stiker parkir resmi.

---

## 22. Proyeksi Arus Kas Bergulir 12 Bulan (Rolling Cash Flow Forecast)

Untuk perencanaan likuiditas dan anggaran belanja modal (*Capex*):
1. Buka menu: **Rental Management > Reports > Proyeksi Arus Kas (12 Bulan)**.
2. Tentukan Bulan Awal Proyeksi (misal: Januari 2026) dan pilih Perusahaan / PT.
3. Klik **"🖨️ Cetak Proyeksi (PDF)"** untuk menerbitkan laporan eksekutif arus kas 12 bulan.
4. Klik **"📊 Ekspor Excel (.xlsx)"** untuk mengunduh spreadsheet proyeksi multi-kolom (*Inflows, Outflows, Monthly Net Cash Flow, dan Cumulative Cash Flow*).

---

## 23. Pemesanan Fasilitas Bersama & Ruang Rapat (Meeting Room & Ballroom)

Untuk mengoptimalkan pendapatan sewa non-ruangan (*ancillary revenue*):
1. Buka menu: **Rental Management > Fasilitas & Meeting Room > Pemesanan Fasilitas**.
2. Pilih Fasilitas (Ruang Rapat, Ballroom, Atrium Mall, Rooftop Lounge) dan tanggal pemakaian.
3. Pilih Sesi Waktu (*Pagi, Siang, Malam, atau Seharian Penuh*). Sistem secara otomatis memeriksa ketersediaan jadwal untuk mencegah *double booking*.
4. Klik **"✅ Konfirmasi Jadwal"**, lalu klik **"🧾 Terbitkan Invoice"** untuk membuat tagihan sewa fasilitas dan deposit kebersihan secara otomatis.

---

## 24. Kontrak Sewa Valas (USD/SGD) & Kurs Pajak KMK / BI

Khusus tenant multinasional dengan tarif sewa dalam valuta asing:
1. Pada form invoice tagihan sewa (`account.move`), centang opsi **"Kontrak Sewa Valas (USD/SGD)"**.
2. Masukkan mata uang valas (USD/SGD) dan nominal asli tagihan sewa.
3. Masukkan **Kurs Pajak KMK** resmi dan **Kurs Transaksi Bank Indonesia** pada tanggal penerbitan tagihan.
4. Nilai DPP dan PPN dikonversi otomatis ke Rupiah (IDR) untuk pelaporan e-Faktur CORETAX DJP.

---

## 25. Adendum Kontrak & Audit Trail Perubahan Sewa

Jika terjadi perubahan klausul kontrak di tengah masa sewa berjalan:
1. Buka menu: **Rental Management > Contracts > Adendum & Perubahan Kontrak**.
2. Klik **New**, pilih Kontrak Sewa Induk (`tenancy.details`).
3. Pilih Jenis Adendum (*Penyesuaian Tarif Sewa, Perubahan Luas Unit m², Perpanjangan Masa Sewa, atau Grace Period*).
4. Masukkan nilai komparasi (Tarif/Tanggal Lama vs Nilai Baru yang Ditetapkan).
5. Klik **"✅ Setujui Adendum"**, lalu klik **"⚡ Terapkan ke Kontrak"** untuk mengupdate data kontrak induk secara otomatis.
6. Klik **"🖨️ Cetak Surat Adendum (PDF)"** untuk mencetak dokumen Surat Perjanjian Perubahan Sewa resmi bertandatangan 2 pihak.

---
*Dokumentasi disusun dan diverifikasi pada versi Odoo 19 Community Edition.*

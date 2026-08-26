# Arsitektur Sistem & Alur Proses Bisnis
### Property Management System Odoo 19 — addon `rental_management` + 26 Modul Companion

> Diagram ditulis dalam **Mermaid** dan dirender otomatis oleh GitHub/IDE Markdown viewer.
> Dokumen ini menyajikan arsitektur lengkap, alur data, integrasi cross-cutting, dan proses bisnis end-to-end terkini (Tahap 1 s.d. Tahap 4).

---

## 1. Arsitektur Sistem (Layered Companion Architecture)

Pendekatan **companion-module non-invasif**: seluruh modul kustom berdiri di atas addon pihak ketiga `rental_management` (OPL-1) dan modul standar Odoo 19 Community Edition, tanpa memodifikasi kode sumber berlisensi secara langsung.

```mermaid
graph TD
    subgraph CLIENT["Lapisan Akses & Antarmuka"]
        WEB["Backend Web UI Odoo 19"]
        TPORTAL["Tenant Portal /my/contracts • /my/invoices • /my/maintenance"]
        OPORTAL["Owner Portal /my/properties • /my/statements"]
        WA["WhatsApp Click-to-Chat (62xxx)"]
        PDF["QWeb PDF Dokumen Resmi (BAST, SP, Clearance, Receipt, Statement)"]
        CORETAX_XML["Ekspor XML CORETAX DJP"]
    end

    subgraph CUSTOM["26 Modul Companion Kustom (100% Odoo 19 Community)"]
        direction TB
        FIN["financial_report<br/>Owners Statement (16 PT Konsolidasi) • Trust • Remittance<br/>Budget • Multi-Type Deposit • BAST Digital • Clearance"]
        OPS["Operasional: gto_meter • casual_leasing<br/>guarantee • handover • cam • parking"]
        TAX["coretax<br/>(Batch e-Faktur, PPh Final 4(2) 10%, SPT 11 Ekspor XML)"]
        ASSET["asset<br/>Depresiasi • Revaluasi • Sinkronisasi CORETAX L9"]
        AUTO["Otomasi & Penagihan: dunning (SP1-SP3, Segel)<br/>rent_escalation • insurance • lease_expiry • ppm"]
        MGMT["Manajemen & Eksekutif: dashboard (WALE, RevPAM)<br/>vacancy • valuation • access • esign"]
        INTG["Integrasi & Legal: purchase • crm • project<br/>document_ce (Legal ID) • portal • owner_portal"]
    end

    subgraph BASE["Addon Pihak Ketiga"]
        RM["rental_management (TechKhedut)<br/>property.details • tenancy.details<br/>maintenance.request"]
    end

    subgraph STD["Modul Standar Odoo 19 Community Edition"]
        ACC["account (Accounting + Analytic Plans)"]
        PUR["purchase"]
        CRM["crm"]
        PRJ["project"]
        PORT["portal"]
        MAIL["mail (Chatter, Activities, Mail Templates)"]
        PROD["product"]
        MAINT["maintenance"]
    end

    WEB --> CUSTOM
    TPORTAL --> PORT
    OPORTAL --> PORT
    WA --> CUSTOM
    CUSTOM --> PDF
    CUSTOM --> CORETAX_XML

    CUSTOM --> RM
    RM --> ACC
    RM --> MAINT

    FIN --> ACC
    OPS --> ACC
    OPS --> PROD
    TAX --> ACC
    ASSET --> ACC
    AUTO --> MAIL
    AUTO --> ACC
    INTG --> PUR
    INTG --> CRM
    INTG --> PRJ
    INTG --> PORT

    classDef custom fill:#1F3964,color:#fff,stroke:#11203a;
    classDef base fill:#006A4E,color:#fff,stroke:#024;
    classDef std fill:#E7ECF5,color:#11203a,stroke:#9bb;
    class FIN,OPS,TAX,ASSET,AUTO,MGMT,INTG custom;
    class RM base;
    class ACC,PUR,CRM,PRJ,PORT,MAIL,PROD,MAINT std;
```

---

## 2. Arsitektur Data — Rantai Atribusi Properti & Analitik Otomatis

Setiap dokumen keuangan ditelusuri ke **satu unit/properti** melalui `account.move.property_financial_id` (computed stored). Saat `account.move._post`, baris pendapatan/beban otomatis dicap **analytic account** properti → mengalir ke Owners Statement, laporan analitik, dan anggaran (budget).

```mermaid
graph LR
    PROP["property.details<br/>(+ Master Unit ID, MEP,<br/>analytic account, 16 PT Owner %)"]

    TEN["tenancy.details<br/>(Kontrak Sewa)"]
    INSP["property.unit.inspection<br/>(BAST Digital)"]
    DEP["property.security.deposit<br/>(Multi-Type & Fit-Out)"]
    GTO["property.gto.turnover<br/>(Bagi Hasil)"]
    MTR["property.meter.reading<br/>(Listrik/Air)"]
    CAM["property.cam.budget<br/>(True-Up CAM)"]
    PO["purchase.order / Vendor Bill"]

    INV["account.move<br/>(Invoice / Bill / Journal Entry)"]
    AML["account.move.line<br/>(Income / Expense / Liability)"]
    AAL["account.analytic.line"]

    PROP --> TEN --> INV
    PROP --> INSP --> DEP --> INV
    PROP --> GTO --> INV
    PROP --> MTR --> INV
    PROP --> CAM --> INV
    PROP --> PO --> INV

    INV -->|"property_financial_id (computed)"| AML
    AML -->|"_post → analytic_distribution = {property.analytic : 100%}"| AAL

    AML --> RPT["Owners Statement Suite<br/>(16 PT Konsolidasi • 9 Bagian)"]
    AAL --> ANA["Analytic Reporting & Budget"]

    classDef p fill:#006A4E,color:#fff;
    classDef m fill:#1F3964,color:#fff;
    classDef r fill:#E7ECF5,color:#11203a;
    class PROP,INSP,DEP,GTO,MTR,CAM,PO p;
    class TEN,INV,AML,AAL m;
    class RPT,ANA r;
```

---

## 3. Alur Bisnis E2E — Siklus Hidup Tenant Komersial

```mermaid
flowchart TD
    A["Prospek / Lead (CRM Leasing Pipeline)"] --> B{Deal / Negosiasi?}
    B -- "Tidak" --> A
    B -- "Ya" --> C["Buat Kontrak Sewa (tenancy.details)<br/>+ Master Unit ID & Spesifikasi MEP"]
    C --> D["Konfigurasi Skema:<br/>• Sewa Pokok & Jadwal Invoice<br/>• GTO Bagi Hasil & Breakdown<br/>• Eskalasi Berkala (Proposal SPK)<br/>• Service Charge / CAM Bulanan"]
    D --> E["BAST Move-In (property.unit.inspection)<br/>• Catat Stand Meter Listrik & Air Awal<br/>• Checklist 10 Komponen Fisik Ruangan<br/>• Cetak Dokumen BAST Move-In PDF"]
    E --> F["Penerimaan Security & Fit-Out Deposit<br/>• Terbitkan Tanda Terima Deposit PDF<br/>• Jurnal Dr Trust Bank / Cr Deposit Liability"]
    F --> G["Aktivitas Fit-Out Tenant (Bila Ada)<br/>• Verifikasi Selesai Renovasi<br/>• Lolos Inspeksi Fit-Out"]
    G --> H["MASA SEWA BERJALAN (Billing & Operasional)<br/>• Invoice Sewa & CAM Bulanan<br/>• Input Meter Reading Listrik/Air (Bulk Wizard)<br/>• Deklarasi Omzet GTO & Cetak Form PDF<br/>• Pelacakan PPh Final 4(2) 10% & e-Bupot<br/>• Tenant Portal (Upload Bukti Bayar, Komplain)"]
    H --> I{Keterlambatan Pembayaran?}
    I -- "Ya" --> J["Dunning Ladder (Cron Harian):<br/>• SP1 (Hari ke-7) + Denda 2%/minggu atau 1‰/hari<br/>• SP2 (Hari ke-14)<br/>• SP3 (Hari ke-21) + Notifikasi Segel<br/>• 📲 Kirim Pengingat WhatsApp Instan<br/>• 🖨️ Cetak Surat Peringatan (SP) Formal PDF<br/>• 🚨 Tindakan Segel Fisik Unit / Putus Layanan"]
    J --> H
    I -- "Tidak / Lunas" --> K{Akhir Masa Sewa?}
    K -- "Perpanjang (Renewal)" --> L["Alur Eskalasi Sewa:<br/>Kirim Proposal Kenaikan → Disetujui → Kontrak Diperbarui"]
    L --> H
    K -- "Pengosongan (Move-Out)" --> M["BAST Move-Out (Inspeksi Fisik & Stand Meter Akhir)<br/>• Hitung SLA Refund 30 Hari<br/>• Terbitkan Tenant Clearance Certificate PDF"]
    M --> N["Settlement Security Deposit:<br/>• Potong Biaya Kerusakan/Tunggakan (Auto Jurnal)<br/>• Refund Sisa Saldo ke Tenant (Auto Jurnal)"]
    N --> O["Kontrak Selesai / Ditutup (Closed)"]

    classDef start fill:#006A4E,color:#fff;
    classDef warn fill:#b91c1c,color:#fff;
    classDef done fill:#1F3964,color:#fff;
    class A,C,D,E,F start;
    class J warn;
    class O done;
```

---

## 4. Alur Billing Bulanan, Pajak CORETAX & Dunning

```mermaid
flowchart TD
    subgraph GEN["Generasi Tagihan Bulanan"]
        R1["Invoice Sewa Pokok<br/>(rental_management)"]
        R2["Input Meteran Bulk Wizard<br/>→ Tagihan Listrik/Air"]
        R3["Deklarasi Omzet GTO<br/>→ Percentage/Overage Rent"]
        R4["Alokasi CAM / Service Charge<br/>(+ Year-End True-Up Reconciliation)"]
        R5["Tagihan Sewa Parkir & Casual Leasing"]
    end

    R1 & R2 & R3 & R4 & R5 --> POST["Posting Invoice (account.move)"]
    POST --> TAX["CORETAX & Perpajakan Indonesia:<br/>• Batch Faktur Generator (Nomor Seri Berurutan)<br/>• Hitung Estimasi PPh Final 4(2) 10%<br/>• Lacak e-Bupot Unifikasi & File Lampiran<br/>• Ekspor XML Faktur Keluaran & SPT 11"]
    
    POST --> DUE{Jatuh Tempo & Sisa Saldo > 0?}
    DUE -- "Ya" --> DUN["Dunning Ladder (Cron Harian):<br/>• SP1 (Hari ke-7) + Denda Keterlambatan<br/>• SP2 (Hari ke-14)<br/>• SP3 (Hari ke-21) + Rekomendasi Segel Unit"]
    DUN --> COMM["Kanal Komunikasi Penagihan:<br/>• 📲 Kirim WhatsApp Otomatis (+62)<br/>• 🖨️ Cetak Surat Peringatan Formal (PDF)<br/>• ✉️ Email Notifikasi Otomatis"]
    COMM --> DUE
    DUE -- "Dibayar" --> PAY["Tenant Upload Bukti Bayar di Portal<br/>→ Verifikasi Mutasi & Rekonsiliasi Bank"]
    PAY --> TRUST["Masuk Saldo Trust Account Pemilik (Cash Basis)"]

    classDef a fill:#1F3964,color:#fff;
    class POST,TAX,TRUST a;
```

---

## 5. Alur Tutup Periode — Owners Statement Konsolidasi 16 PT & Remittance

```mermaid
sequenceDiagram
    autonumber
    participant PM as Property Manager / Direksi
    participant SYS as Financial Report Suite
    participant GL as Buku Besar (GL 16 PT)
    participant OWN as Pemilik Properti / Holding

    PM->>SYS: Buka Wizard Laporan Pemilik (property.owner.statement.wizard)
    PM->>SYS: Pilih Mode: "Konsolidasi Seluruh Entitas (16 PT)" / Per Pemilik
    PM->>SYS: Masukkan Periode Fiskal & Catatan Manajemen / Narasi Eksekutif
    SYS->>GL: Ambil Transaksi Pendapatan & Beban (Accrual Basis)
    SYS->>GL: Ambil Realisasi Penerimaan Kas & Pengeluaran (Cash Basis)
    SYS->>GL: Hitung Saldo Awal Trust, Mutasi Kas Bersih, dan Saldo Akhir
    GL-->>SYS: Data Konsolidasi Multi-Entitas
    SYS-->>PM: Terbitkan PDF Owners Statement Lengkap (9 Bagian + Catatan Manajemen)
    PM->>SYS: Klik "📧 Kirim Email ke Pemilik" (Distribusi Massal PDF)
    SYS-->>OWN: Email Laporan Finansial Resmi terkirim ke Pemilik
    PM->>SYS: Jalankan Owner Remittance (Split Hak Pemilik sesuai % Kepemilikan)
    SYS->>GL: Jurnal Otomatis Dr Owners Remittance / Cr Trust Bank
    GL-->>OWN: Transfer Dana Hasil Sewa Bersih ke Rekening Pemilik
```

---

## 6. Daftar Modul Companion & Status Integrasi (26 Modul)

| # | Nama Modul | Fungsi Utama | Status |
|---|------------|--------------|--------|
| 1 | `rental_management_financial_report` | Owners Statement Suite (9 Section), Konsolidasi 16 PT, Trust Accounting, Remittance, Budget, Multi-Type Deposit, BAST Digital, Tenant Clearance Certificate, Master Unit ID & MEP. | ✅ Aktif & Terverifikasi |
| 2 | `rental_management_dunning` | Dunning Ladder SP1-SP3, Denda Keterlambatan (2%/minggu, 1‰/hari), Penyegelan Unit, Notifikasi WhatsApp, Cetak SP Formal PDF, Cron Harian. | ✅ Aktif & Terverifikasi |
| 3 | `rental_management_coretax` | Integrasi Pajak Indonesia CORETAX DJP, Batch Update Faktur Pajak Berurutan, Pelacakan PPh Final 4(2) 10% & e-Bupot, Ekspor XML SPT 11. | ✅ Aktif & Terverifikasi |
| 4 | `rental_management_gto_meter` | GTO Revenue Sharing (Higher-of, Base+Overage, Pure), Formulir Pernyataan Omzet PDF, Bulk Meter Reading Wizard, Cron Bulanan Engineering. | ✅ Aktif & Terverifikasi |
| 5 | `rental_management_portal` | Tenant Self-Service: Upload Bukti Transfer Bank, Riwayat BAST & Stand Meter, Pengajuan Komplain & Maintenance Tiket, Lihat Invoice. | ✅ Aktif & Terverifikasi |
| 6 | `rental_management_dashboard` | Dashboard Eksekutif: Metrik WALE (Tahun/Bulan), RevPAM (Pendapatan/m²), Occupancy Rate %, Arrears Aging, NOI, Collection Rate. | ✅ Aktif & Terverifikasi |
| 7 | `rental_management_cam` | CAM / Service Charge Apportionment, Budgeting, dan Year-End True-Up Reconciliation (Balancing Invoices & Credit Notes). | ✅ Aktif & Terverifikasi |
| 8 | `rental_management_rent_escalation` | Otomasi Kenaikan Sewa Berkala (Fixed %, Index), Alur Pengajuan Proposal Kenaikan Sewa & Persetujuan Manajemen. | ✅ Aktif & Terverifikasi |
| 9 | `rental_management_document_ce` | Manajemen Perizinan & Dokumen Legal Properti Indonesia (SHM/HGB, IMB/PBG, SLF, PBB, PKS, NPWP, AMDAL, Damkar) — 100% Community. | ✅ Aktif & Terverifikasi |
| 10 | `rental_management_owner_portal` | Portal Mandiri Pemilik Unit: Akses Owners Statement, Laporan Remittance, dan Portofolio Properti. | ✅ Aktif & Terverifikasi |
| 11 | `rental_management_casual_leasing` | Penyewaan Area Kasual / Booth / Pop-up Store / Atrium / Spanduk dengan alokasi otomatis. | ✅ Aktif & Terverifikasi |
| 12 | `rental_management_guarantee` | Register Bank Guarantee & Security Deposit Insurance untuk jaminan sewa tenant komersial. | ✅ Aktif & Terverifikasi |
| 13 | `rental_management_handover` | Modul Serah Terima Unit dengan integrasi Project/Task Odoo. | ✅ Aktif & Terverifikasi |
| 14 | `rental_management_parking` | Manajemen Slot Parkir Gedung, Alokasi Tenant, dan Tagihan Parkir Berkala. | ✅ Aktif & Terverifikasi |
| 15 | `rental_management_insurance` | Manajemen Polis Asuransi Gedung (Property All Risks, Public Liability) & Notifikasi Perpanjangan. | ✅ Aktif & Terverifikasi |
| 16 | `rental_management_lease_expiry` | Pelacakan Kontrak Mendekati Jatuh Tempo & Pengingat Perpanjangan Otomatis. | ✅ Aktif & Terverifikasi |
| 17 | `rental_management_ppm` | Preventive Maintenance Scheduling & Checklist Pemeliharaan Gedung Berkala. | ✅ Aktif & Terverifikasi |
| 18 | `rental_management_vacancy` | Papan Ketersediaan Unit (Vacancy Board) & Analisis Tingkat Kekosongan Ruangan. | ✅ Aktif & Terverifikasi |
| 19 | `rental_management_valuation` | Buku Penilaian Nilai Pasar Properti (Market Valuation) Berkala. | ✅ Aktif & Terverifikasi |
| 20 | `rental_management_access` | Manajemen Kartu Akses Tenant & Registrasi Pengunjung Gedung. | ✅ Aktif & Terverifikasi |
| 21 | `rental_management_esign` | Integrasi Tanda Tangan Digital untuk Surat Perjanjian & Dokumen BAST. | ✅ Aktif & Terverifikasi |
| 22 | `rental_management_purchase` | Integrasi Pengadaan Barang/Jasa Maintenance ke Purchase Order & Vendor Bill ter-tag properti. | ✅ Aktif & Terverifikasi |
| 23 | `rental_management_crm` | Pipeline Leasing CRM untuk pengelolaan prospek tenant dari Lead hingga Kontrak Sah. | ✅ Aktif & Terverifikasi |
| 24 | `rental_management_project` | Integrasi Manajemen Proyek Fit-Out & Renovasi Gedung. | ✅ Aktif & Terverifikasi |
| 25 | `rental_management_asset` | Manajemen Fixed Asset Properti, Depresiasi, Revaluasi Aset, dan Sinkronisasi CORETAX L9. | ✅ Aktif & Terverifikasi |
| 26 | `rental_management_documents` | Integrasi Dokumen Properti (dengan fallback penuh ke `rental_management_document_ce` di Community). | ✅ Aktif & Terverifikasi |

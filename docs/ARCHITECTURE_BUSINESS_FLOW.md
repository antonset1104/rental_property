# Arsitektur Sistem & Alur Proses Bisnis
### Property Management System Odoo 19 — addon `rental_management` + 26 modul companion

> Diagram ditulis dalam **Mermaid** dan dirender otomatis oleh GitHub.
> Dokumen ini melengkapi `Blueprint_Installation_Configuration.docx` dan `INTEGRATIONS.md`.

---

## 1. Arsitektur Sistem (Layered)

Pendekatan **companion-module non-invasif**: modul kustom berdiri di atas addon
pihak ketiga `rental_management` (OPL-1) dan modul standar Odoo, tanpa menambal
kode berlisensi.

```mermaid
graph TD
    subgraph CLIENT["Lapisan Akses"]
        WEB["Backend Web UI"]
        TPORTAL["Tenant Portal /my/contracts"]
        OPORTAL["Owner Portal /my/properties"]
        PDF["Laporan PDF / Ekspor XML"]
    end

    subgraph CUSTOM["26 Modul Companion (kustom)"]
        direction TB
        FIN["financial_report<br/>Owners Statement • Trust • Remittance<br/>Budget • Security Deposit • Analytic"]
        OPS["Operasi: gto_meter • casual_leasing<br/>guarantee • handover • cam • parking"]
        TAX["coretax<br/>(e-Faktur & SPT 11 ekspor XML)"]
        ASSET["asset<br/>Depresiasi • Revaluation • Sync L9"]
        AUTO["Otomasi: rent_escalation • dunning<br/>insurance • lease_expiry • ppm"]
        MGMT["Manajemen: dashboard • vacancy<br/>valuation • access • esign"]
        INTG["Integrasi: purchase • crm • project<br/>documents • document_ce<br/>portal • owner_portal"]
    end

    subgraph BASE["Addon Pihak Ketiga"]
        RM["rental_management (TechKhedut)<br/>property.details • tenancy.details<br/>maintenance.request"]
    end

    subgraph STD["Modul Standar Odoo 19"]
        ACC["account<br/>(Accounting + Analytic)"]
        PUR["purchase"]
        CRM["crm"]
        PRJ["project"]
        PORT["portal"]
        MAIL["mail (Activities/Chatter)"]
        PROD["product"]
        MAINT["maintenance"]
        DOCS["documents (Enterprise)"]
    end

    WEB --> CUSTOM
    TPORTAL --> PORT
    OPORTAL --> PORT
    CUSTOM --> PDF

    CUSTOM --> RM
    RM --> ACC
    RM --> MAINT

    FIN --> ACC
    OPS --> ACC
    OPS --> PROD
    TAX --> ACC
    ASSET --> ACC
    AUTO --> MAIL
    INTG --> PUR
    INTG --> CRM
    INTG --> PRJ
    INTG --> PORT
    INTG --> DOCS

    classDef custom fill:#1F3964,color:#fff,stroke:#11203a;
    classDef base fill:#006A4E,color:#fff,stroke:#024;
    classDef std fill:#E7ECF5,color:#11203a,stroke:#9bb;
    class FIN,OPS,TAX,ASSET,AUTO,MGMT,INTG custom;
    class RM base;
    class ACC,PUR,CRM,PRJ,PORT,MAIL,PROD,MAINT,DOCS std;
```

---

## 2. Arsitektur Data — Rantai Atribusi Properti

Setiap dokumen keuangan ditelusuri ke **satu properti** melalui
`account.move.property_financial_id` (computed). Saat `account.move._post`,
item income/expense otomatis dicap **analytic account** properti → mengalir ke
Owners Statement, reporting analitik, dan budget standar Odoo.

```mermaid
graph LR
    PROP["property.details<br/>(+ analytic account,<br/>owners %, trust account)"]

    TEN["tenancy.details<br/>(kontrak)"]
    SALE["property.sold"]
    MAINT["maintenance.request"]
    MANUAL["property_manual_id<br/>(remittance, deposit, CAM, parkir)"]

    INV["account.move<br/>(invoice / bill / entry)"]
    AML["account.move.line<br/>(income / expense)"]
    AAL["account.analytic.line"]

    PROP --> TEN --> INV
    PROP --> SALE --> INV
    PROP --> MAINT --> INV
    PROP --> MANUAL --> INV

    INV -->|"property_financial_id<br/>(computed)"| AML
    AML -->|"_post → analytic_distribution<br/>= {property.analytic : 100%}"| AAL

    AML --> RPT["Owners Statement<br/>(9 section)"]
    AAL --> ANA["Analytic Reporting<br/>& Budget standar Odoo"]

    classDef p fill:#006A4E,color:#fff;
    classDef m fill:#1F3964,color:#fff;
    classDef r fill:#E7ECF5,color:#11203a;
    class PROP p;
    class INV,AML,AAL m;
    class RPT,ANA r;
```

---

## 3. Alur Bisnis E2E — Siklus Hidup Tenant

```mermaid
flowchart TD
    A["Lead masuk (CRM)<br/>leasing pipeline"] --> B{Deal?}
    B -- "Tidak" --> A
    B -- "Ya" --> C["Create Lease Contract<br/>(tenancy.details pre-filled)"]
    C --> D["Aktifkan kontrak<br/>+ konfigurasi GTO / eskalasi"]
    D --> E["Handover Move-in<br/>(checklist + dokumen)"]
    E --> F["Catat Guarantee<br/>(bank/insurance) + Security Deposit"]
    F --> G["Terbitkan Access Card<br/>+ alokasi Parking bay"]
    G --> H["MASA SEWA AKTIF<br/>(billing berjalan)"]
    H --> I{Akhir masa /<br/>Lease expiry?}
    I -- "Perpanjang" --> J["Renewal<br/>(rent escalation diterapkan)"]
    J --> H
    I -- "Selesai" --> K["Handover Move-out<br/>+ make-good"]
    K --> L["Security Deposit<br/>refund / deduction"]
    L --> M["Kontrak Closed"]

    classDef start fill:#006A4E,color:#fff;
    classDef done fill:#1F3964,color:#fff;
    class A start;
    class M done;
```

---

## 4. Alur Billing Bulanan & Penagihan

```mermaid
flowchart TD
    subgraph GEN["Generasi Tagihan"]
        R1["Invoice sewa<br/>(rental_management)"]
        R2["Meter reading<br/>→ recharge invoice"]
        R3["GTO turnover<br/>→ percentage/overage rent"]
        R4["CAM apportion<br/>→ service charge invoice"]
        R5["Parking<br/>→ invoice parkir"]
    end

    R1 & R2 & R3 & R4 & R5 --> POST["Post invoice<br/>(account.move)"]
    POST --> TAG["Auto-tag property<br/>+ analytic (_post)"]
    TAG --> CORETAX["Ekspor CORETAX<br/>Faktur Keluaran (PK)"]

    POST --> DUE{Jatuh tempo<br/>& belum bayar?}
    DUE -- "Ya" --> DUN["Dunning ladder (cron)<br/>reminder email + late fee"]
    DUN --> DUE
    DUE -- "Dibayar" --> PAY["Pembayaran<br/>+ rekonsiliasi"]
    PAY --> TRUST["Masuk Trust Balance<br/>(cash basis)"]

    classDef a fill:#1F3964,color:#fff;
    class POST,TAG,TRUST a;
```

---

## 5. Alur Pengeluaran — Procurement & Maintenance

```mermaid
flowchart LR
    MR["Maintenance Request<br/>(rental_management)"] -->|"Create PO"| PO["purchase.order<br/>+ property link"]
    PRC["Procurement langsung<br/>(RFQ/PO)"] --> PO
    PO --> RCV["Terima barang/jasa"]
    RCV --> BILL["Create Bill<br/>(vendor bill)"]
    BILL -->|"_prepare_invoice<br/>mewariskan property link"| POSTB["Post bill"]
    POSTB --> ATTR["Property + analytic<br/>ter-tag otomatis"]
    ATTR --> PD["Owners Statement →<br/>Payment Details + Expense"]

    classDef a fill:#1F3964,color:#fff;
    class PO,BILL,POSTB a;
```

---

## 6. Alur Tutup Periode — Owners Statement, Trust & Remittance

```mermaid
sequenceDiagram
    autonumber
    participant PM as Property Manager
    participant SYS as Financial Report
    participant GL as Accounting (GL)
    participant OWN as Owner

    PM->>SYS: Jalankan Owners Statement Wizard<br/>(properti, periode, awal tahun fiskal)
    SYS->>GL: Baca account.move.line (accrual)
    SYS->>GL: Baca alokasi pembayaran (cash basis)
    SYS->>GL: Hitung saldo akun trust
    GL-->>SYS: Data Income/Expense/Receipts/Payments
    SYS-->>PM: PDF Owners Statement (9 section)
    Note over SYS: Opening Trust + Net Cash − Remittances = Closing
    PM->>SYS: Owner Remittance → Compute from Owners (split %)
    PM->>SYS: Post Remittance
    SYS->>GL: Jurnal Dr Owners Remittance / Cr Trust Bank<br/>(konversi multi-currency bila perlu)
    GL-->>OWN: Dana diteruskan ke pemilik
    PM->>SYS: Ekspor CORETAX (PK / lampiran SPT)
```

---

## 7. Alur Fixed Asset — Depresiasi & Revaluation

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Running: Compute Depreciation<br/>+ Confirm (board dibuat)
    Running --> Running: Post Due Depreciation (cron)<br/>Dr Beban / Cr Akumulasi (tag properti)
    Running --> Running: Post Revaluation (+/-)<br/>vs Revaluation Reserve<br/>→ recompute prospektif board
    Running --> Closed: Nilai buku habis / disposal
    Running --> L9: Sync CORETAX L9<br/>(register penyusutan tahunan)
    Closed --> [*]
```

---

## 8. Integrasi Cross-Cutting — Analytic Accounting

Satu override global (`account.move._post`) membuat **seluruh** dokumen
ber-link properti dari modul manapun otomatis ter-tag analitik — tanpa langkah
tambahan per modul.

```mermaid
graph TD
    SRC["Sumber dokumen ber-link properti:<br/>GTO • Meter • Casual Lease • CAM<br/>Parking • Maintenance • Owner Remittance<br/>Security Deposit • Vendor Bill (PO) • Asset"]
    SRC --> HOOK["account.move._post()<br/>stamp analytic_distribution<br/>(hanya bila kosong)"]
    HOOK --> AAL["account.analytic.line<br/>(per property analytic account)"]
    AAL --> REP["Owners Statement<br/>+ Analytic Reporting<br/>+ Budget standar Odoo"]

    classDef a fill:#006A4E,color:#fff;
    class HOOK a;
```

---

### Catatan
- Semua diagram bersifat **logis/fungsional**; nama field & hook mengikuti kode pada branch `claude/gallant-curie-dpaatp`.
- Integrasi bersifat **decoupled** — modul memeriksa keberadaan field (mis. `property_manual_id`) sebelum memakainya, sehingga tiap modul dapat diinstal independen.
- Validasi: sintaks Python/XML/CSV ✅; **smoke test pada Odoo 19 staging tetap wajib** sebelum produksi.

---

## Versi Gambar (PNG)

Versi PNG resolusi tinggi (scale 2×) tersedia di `docs/diagrams/` untuk dipakai
pada slide presentasi / dokumen cetak:

| # | Diagram | File |
|---|---------|------|
| 1 | Arsitektur Sistem (Layered) | `diagrams/01-arsitektur-sistem.png` |
| 2 | Arsitektur Data — Atribusi Properti | `diagrams/02-arsitektur-data.png` |
| 3 | Siklus Hidup Tenant (E2E) | `diagrams/03-siklus-hidup-tenant.png` |
| 4 | Billing Bulanan & Penagihan | `diagrams/04-billing-penagihan.png` |
| 5 | Pengeluaran (Procurement & Maintenance) | `diagrams/05-pengeluaran.png` |
| 6 | Tutup Periode (Owners Statement, Trust, Remittance) | `diagrams/06-tutup-periode.png` |
| 7 | Fixed Asset — Depresiasi & Revaluation | `diagrams/07-fixed-asset.png` |
| 8 | Integrasi Cross-Cutting Analytic | `diagrams/08-analytic-crosscutting.png` |

![Arsitektur Sistem](diagrams/01-arsitektur-sistem.png)
![Arsitektur Data](diagrams/02-arsitektur-data.png)
![Siklus Hidup Tenant](diagrams/03-siklus-hidup-tenant.png)
![Billing & Penagihan](diagrams/04-billing-penagihan.png)
![Pengeluaran](diagrams/05-pengeluaran.png)
![Tutup Periode](diagrams/06-tutup-periode.png)
![Fixed Asset](diagrams/07-fixed-asset.png)
![Analytic Cross-Cutting](diagrams/08-analytic-crosscutting.png)

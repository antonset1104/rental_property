# Review: Kompatibilitas, Integritas Integrasi & Gap Analysis
**Property Management System — Odoo 19 Community Edition**
Companion modules untuk addon `rental_management` (TechKhedut). Tanggal: 20 Juni 2026.

---

## 1. Kompatibilitas dengan Odoo 19 Community

### 1.1 Ringkasan dependensi
| Modul custom | Depends | Community? |
|---|---|---|
| rental_management_financial_report | account | ✅ |
| rental_management_gto_meter | account, product | ✅ |
| rental_management_guarantee | mail | ✅ |
| rental_management_casual_leasing | account, product | ✅ |
| rental_management_handover | mail | ✅ |
| rental_management_portal | portal | ✅ |
| rental_management_coretax | account | ✅ |
| rental_management_purchase | purchase | ✅ |
| rental_management_crm | crm | ✅ |
| rental_management_project | project (+handover) | ✅ |
| rental_management_asset | account | ✅ |
| rental_management_documents | **documents** | ⚠️ **Enterprise-only** |

**Verdict: 11 dari 12 modul 100% kompatibel Community.** Modul standar yang dipakai
(`account`, `analytic`, `crm`, `portal`, `purchase`, `project`, `mail`, `maintenance`,
`product`, `website`) semuanya tersedia di Community. Analytic Accounting (account.analytic.*,
`analytic_distribution`) juga tersedia di Community.

> Catatan: addon dasar `rental_management` berlisensi OPL-1 (berbayar) namun dependensinya
> (`hr, crm, account, maintenance, website, contacts, mail`) semua ada di Community — tidak
> memerlukan Enterprise.

### 1.2 Satu-satunya isu Enterprise: `rental_management_documents`
`documents` adalah aplikasi **Enterprise**. Pada Community modul ini **tidak bisa diinstal**.
**Rekomendasi:** sediakan varian fallback berbasis `ir.attachment` (tab "Documents" yang
mengumpulkan lampiran properti) — Community-compatible — atau tandai modul ini `auto_install`
hanya jika `documents` hadir, dan jangan masukkan ke daftar instalasi wajib.

### 1.3 Titik API yang perlu diverifikasi saat smoke test (semua ada di Community, tapi sensitif versi)
| Item | Dipakai di | Catatan verifikasi |
|---|---|---|
| `account.move._post(self, soft=True)` | financial_report | Signature Odoo 17–19 ✓; override memanggil super(). |
| `analytic_distribution = {str(id): 100.0}` | financial_report | Format JSON Odoo 16+ ✓; validasi applicability plan → dibungkus try/except. |
| `account.analytic.line.account_id` | property action "Analytic Items" | Field analytic account di Community ✓ (verifikasi label kolom). |
| `matched_credit_ids/matched_debit_ids`, `partial.max_date` | Owners Statement cash | Tersedia Community ✓. |
| `<chatter/>` tag | beberapa form | Odoo 17+ ✓. |
| Hook `portal.portal_docs_entry`, `o_portal_docs` | portal | Tersedia Community; konfirmasi struktur `portal_my_home`. |
| `<list>` view, `widget="statinfo"`, `boolean_toggle` | semua | Odoo 17+ ✓. |
| `type=service` pada product.product (data) | gto_meter, casual | Valid Odoo 18/19 ✓. |
| ref `maintenance.hr_equipment_request_view_form` | purchase | Sama dengan yang dipakai addon dasar ✓. |

---

## 2. Integritas Data & Integrasi Antar-Modul

### 2.1 Rantai atribusi properti (KONSISTEN)
Setiap dokumen keuangan ditautkan ke properti melalui satu jalur terpadu:

```
tenancy_id / sold_id / maintenance_request_id / property_manual_id
        └──> account.move.property_financial_id (stored, computed)
                 └──> Owners Statement (filter) + Analytic stamping (_post)
```

- **Pendapatan**: sewa (addon), GTO turnover, meter recharge, casual lease → `out_invoice`
  ber-`tenancy_id`/`property_manual_id`.
- **Beban**: maintenance bill, vendor bill dari PO (via `_prepare_invoice`), penyusutan aset
  (`property_manual_id`).
- **Trust/owner**: owner remittance & security deposit posting `account.move` ber-properti.

➡️ Semua mengalir ke **Owners Statement** dan, saat posting, **otomatis ter-tag analytic
account properti** → masuk laporan Analytic/Budget standar Odoo. **Integrasi data konsisten.**

### 2.2 Decoupling (AMAN)
Modul saling lepas via pengecekan keberadaan field/model:
- `'property_manual_id' in account.move._fields` (casual, purchase, asset).
- `'coretax.asset.depreciation' not in self.env` (asset → coretax).
Sehingga tiap modul dapat diinstal independen tanpa error.

### 2.3 Temuan / risiko integritas (perlu diperhatikan)
1. **`_post` override global** mengevaluasi setiap `account.move` (skip cepat bila bukan
   properti). Overhead kecil; aman.
2. **Cash-basis Owners Statement** memakai alokasi pembayaran (pendekatan) — bukan GL kas
   murni; sudah didokumentasikan. Untuk audit ketat, pertimbangkan rekonsiliasi bank nyata.
3. **Trust balance** = Opening + NetCash − Remittances (mengikuti aritmetika CBRE); pastikan
   akun bank trust dikonfigurasi agar Opening/Closing dari GL akurat.
4. **Multi-company / multi-currency**: trust & remittance berasumsi satu mata uang company.
5. **CORETAX `_num`** memakai `repr(float)` — untuk nilai sangat besar bisa muncul notasi
   ilmiah; gunakan format desimal eksplisit bila ditemukan saat uji.

**Kesimpulan integritas: solid & konsisten.** Tidak ditemukan referensi field yang salah
atau pemutus rantai data; semua xmlid inherit menunjuk modul Community yang valid.

---

## 3. Gap Analysis — Fitur yang Kurang untuk PMS Lengkap & Komprehensif

Sudah tersedia: properti/unit, kontrak & invoicing sewa (addon), CRM pipeline, Owners
Statement/Trust/Remittance, Budget, Security Deposit, GTO, Meter, Guarantee, Casual Leasing,
Handover, Tenant Portal, CORETAX, Procurement, Maintenance (addon), Fixed Asset + Revaluation,
Analytic, Documents (ent).

### 3.1 Prioritas TINGGI (disarankan dibangun)
| # | Fitur | Mengapa penting | Integrasi standar |
|---|---|---|---|
| G1 | **Owner Portal** | Pemilik melihat Owners Statement, remittance, daftar properti secara mandiri (mirror Tenant Portal). | `portal` |
| G2 | **CAM / Service Charge apportionment & year-end reconciliation** | Inti mall/office: alokasi biaya area bersama ke tenant per share (m²), budget vs actual, true-up akhir tahun. | `account`, analytic |
| G3 | **Rent escalation / indexation otomatis** | Kenaikan sewa berkala (fixed % / CPI) terjadwal pada kontrak. | base addon + cron |
| G4 | **Management KPI Dashboard** | Occupancy, arrears aging, NOI, yield, **WALE** (weighted average lease expiry), collection rate. | `board`/spreadsheet/QWeb |
| G5 | **Arrears & Dunning otomatis** | Tangga reminder + denda keterlambatan otomatis (Community tidak punya account_followup). | `account`, mail, cron |

### 3.2 Prioritas MENENGAH
| # | Fitur | Catatan |
|---|---|---|
| G6 | **Lease Expiry / WALE report + renewal reminders** | Daftar kontrak akan berakhir + aktivitas perpanjangan. |
| G7 | **Property Insurance Policy register** | Polis asuransi bangunan (pemilik) + alert renewal (pola mirip Guarantee). |
| G8 | **Vacancy & Availability board** | Status unit (occupied/available/under-offer), tingkat hunian, papan leasing. |
| G9 | **Preventive Maintenance (PPM) scheduling + SLA** | Jadwal perawatan berkala & SLA kontraktor (perluas Maintenance). |
| G10 | **Parking / Car Park management** | Bay parkir, sewa parkir (CBRE punya Car Park Rental), casual parking. |

### 3.3 Prioritas RENDAH / Opsional
| # | Fitur | Catatan |
|---|---|---|
| G11 | **Property market valuation register** | Nilai pasar berkala (berbeda dari nilai buku aset). |
| G12 | **Visitor / access card management** | Kartu akses tenant (CBRE punya akses kartu). |
| G13 | **Budget approval workflow** | State & otorisasi pada Property Budget. |
| G14 | **Multi-currency owner remittance** | Untuk pemilik lintas negara. |
| G15 | **E-signature kontrak** | `sign` Enterprise; alternatif integrasi pihak ketiga. |
| G16 | **Documents Community fallback** | Varian `ir.attachment` agar manajemen dokumen jalan tanpa Enterprise. |

---

## 4. Rekomendasi Tindak Lanjut
1. **Perbaiki isu Enterprise**: buat fallback `documents` berbasis `ir.attachment` (G16) agar
   manajemen dokumen tersedia di Community.
2. **Bangun G1–G5** untuk menjadikannya PMS komersial yang lengkap (Owner Portal, CAM,
   eskalasi sewa, KPI dashboard, dunning).
3. **Smoke test di staging Odoo 19 Community** mengikuti UAT tracker (49 kasus) untuk
   memvalidasi titik API pada §1.3 dan validasi XML CORETAX terhadap XSD DJP.

> Status kode: seluruh modul lolos validasi sintaks Python/XML/CSV; belum dijalankan di
> instance Odoo 19 nyata pada lingkungan ini.

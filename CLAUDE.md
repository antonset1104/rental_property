# CLAUDE.md — Property Management System (Odoo 19 CE)

Baca berkas ini sampai habis sebelum mengubah apa pun. Isinya adalah keputusan
yang SUDAH diambil pada proyek ini; jangan diperdebatkan ulang, dan jangan
menebak pada hal yang tidak diatur di sini — tanyakan ke user (dalam bahasa
Indonesia).

## 1. Tentang proyek ini

Property Management System komprehensif untuk perusahaan properti Indonesia
(sedang mengevaluasi IFCA vs Odoo kustom), dibangun sebagai **26 modul
companion** di atas addon pihak ketiga berbayar `rental_management` v3.3.9
(TechKhedut, lisensi OPL-1) untuk **Odoo 19 Community Edition**. Deliverable
utamanya adalah paket laporan **Owners Statement** gaya CBRE/MRI (9 section),
ditambah pajak Indonesia (ekspor XML CORETAX e-Faktur/SPT), trust accounting,
owner remittance, GTO, CAM, fixed asset, portal, dan modul operasional.

**Tidak ada runtime Odoo di environment ini.** Kode hanya divalidasi secara
statis. Jangan pernah mengklaim sesuatu "sudah dites di Odoo" — katakan bahwa
kode lolos validasi sintaks/XML/CSV dan tetap memerlukan smoke test pada
instance staging Odoo 19.

## 2. Aturan keras (jangan pernah dilanggar)

1. **Jangan pernah mengubah `rental_management/`** — kode pihak ketiga
   berlisensi OPL-1. Semua ekstensi hidup di modul companion
   `rental_management_*` terpisah yang `depends` padanya.
2. **Community Edition dulu.** Jangan menambah dependensi ke aplikasi
   Enterprise. Satu-satunya pengecualian adalah `rental_management_documents`
   (depends `documents`) yang punya fallback Community
   `rental_management_document_ce`. `depends` modul lain harus resolve ke
   modul CE saja.
3. **Balas user dalam bahasa Indonesia.** Kode, identifier, dan subject commit
   dalam bahasa Inggris; body commit, dokumen untuk end user, dan balasan chat
   dalam bahasa Indonesia.
4. **Integrasi decoupled.** Sebuah modul boleh memakai field milik modul kustom
   lain (mis. `property_manual_id`) hanya di balik pengecekan keberadaan saat
   runtime (`if 'property_manual_id' in self.env['account.move']._fields:`),
   sehingga tiap modul bisa diinstal mandiri.
5. **Jangan membangun ledger paralel.** Semua transaksi keuangan lewat
   `account.move` standar. Atribusi properti + stamping analytic (bagian 4)
   adalah mekanisme tunggal — pakai ulang, jangan diduplikasi.
6. **Jujur di laporan dan teks PR**: validasi statis ≠ teruji. Tandai titik API
   yang sensitif versi (xpath inherit view, field analytic line, XSD CORETAX)
   setiap kali menyentuhnya.
7. Jangan mencantumkan identitas model AI di commit, teks PR, atau komentar
   kode. Pertahankan trailer `Co-Authored-By` dan `Claude-Session` persis
   seperti yang diberikan harness.

## 3. Tata letak repository

```
rental_management/               # addon dasar pihak ketiga — HANYA-BACA
rental_management_<fitur>/       # 26 modul companion (lihat INTEGRATIONS.md)
docs/                            # deliverable: .docx/.xlsx + .md + diagrams/
tools/docgen/                    # generator dokumen (python-docx/openpyxl)
INTEGRATIONS.md                  # peta integrasi modul ↔ Odoo standar
```

Setiap modul mengikuti kerangka yang sama:
`__manifest__.py`, `__init__.py`, `models/`, `views/`,
`security/ir.model.access.csv`, opsional `data/` (sequence, cron, produk),
`wizard/`, `report/`, `README.md`.

## 4. Arsitektur yang wajib dipertahankan

**Rantai atribusi properti** (tulang punggung — semua pelaporan lewat sini):
`tenancy_id / sold_id / maintenance_request_id / property_manual_id` pada
`account.move` → computed stored `property_financial_id` → memfilter Owners
Statement, dan saat `_post()` analytic account properti dicap ke baris
income/expense (`analytic_distribution = {str(analytic.id): 100.0}`, hanya
bila masih kosong). Didefinisikan di
`rental_management_financial_report/models/account_inherit.py`.

Konsekuensinya:
- Dokumen baru apa pun yang menagih/membebankan ke properti cukup mengisi
  `tenancy_id` **atau** `property_manual_id` pada `account.move` yang
  dibuatnya. Itu saja — pelaporan dan analytic mengikuti otomatis.
- Mesin Owners Statement ada di
  `rental_management_financial_report/wizard/owner_statement_wizard.py`
  (akrual dari posted move line; basis kas via
  `matched_credit_ids/matched_debit_ids` + `partial.max_date`). Perluas,
  jangan di-fork.
- Aritmetika trust bersifat tetap: Opening Trust + Net Cash − Remittances
  = Closing.

## 5. Konvensi koding Odoo 19 (gaya yang berlaku di repo ini)

- Manifest: `'version': "19.0.1.0.0"`, `'category': 'Realestate'`,
  `'license': 'LGPL-3'`, `'application': False`, daftarkan semua berkas data,
  dan urutkan CSV security sebelum views.
- Views: sintaks Odoo 19 — `<list>` bukan `<tree>`, `<chatter/>` bukan div
  message_follower lama, ekspresi atribut seperti
  `invisible="state != 'draft'"` (tanpa `attrs=`), `column_invisible` untuk
  kolom list.
- Models: selalu isi `_description`; `mail.thread` (+ `mail.activity.mixin`
  bila butuh activity/reminder); `@api.model_create_multi` untuk create;
  sequence via `self.env['ir.sequence'].next_by_code(...)` yang dibibit dari
  `data/sequence.xml`; terjemahan via `self.env._(...)` (gaya Odoo 19), bukan
  `_` level modul.
- Security: `ir.model.access.csv` 8 kolom; grup default `base.group_user`;
  aksi khusus manajer (approve budget, CORETAX) pakai
  `account.group_account_manager`; aturan portal pakai `base.group_portal`
  dengan record rule yang membatasi ke record miliknya sendiri.
- **Cron: jadwalkan pada jam 22.00–05.00 WIB** (di luar jam kerja). Set
  `nextcall` pada data XML ke jam 22:00 atau lebih malam; interval default
  harian. Beri nama deskriptif — cron tercantum di tabel cron Blueprint,
  perbarui tabel itu saat menambah cron baru.
- XML CORETAX: nama tag harus sama persis dengan template DJP, **termasuk
  salah ejanya yang resmi** (`CommercialMethode`, `FiscalDepretiationThisYear`,
  `AmountOfWitholding`). Jangan pernah "dibetulkan".

## 6. Definisi selesai — jalankan ini sebelum menyatakan beres

Sebuah perubahan baru boleh disebut selesai bila semua ini lolos (tidak ada
Odoo, jadi inilah keseluruhan gerbangnya):

```bash
# 1. Sintaks Python — setiap modul yang disentuh
find rental_management_<mod> -name "*.py" -exec python3 -m py_compile {} \;
# 2. XML well-formed — setiap XML yang disentuh
python3 -c "import xml.dom.minidom,glob; [xml.dom.minidom.parse(f) for f in glob.glob('rental_management_<mod>/**/*.xml', recursive=True)]"
# 3. Manifest ↔ berkas: semua path di 'data' ada; semua berkas baru terdaftar
# 4. CSV: 8 kolom per baris, id model cocok dengan _name (model_<nama pakai _>)
```

Lalu, bila perubahan menambah/mengganti nama modul atau fitur, sinkronkan
dokumen (bagian 7) — set dokumen yang belum sinkron berarti belum selesai.
Terakhir commit dan push (bagian 8) dan nyatakan gamblang di balasan bahwa
smoke test live masih diperlukan.

## 7. Set dokumentasi — jaga tetap sinkron

`docs/` adalah deliverable kelas satu yang diserahkan user ke stakeholder.
Saat modul/fitur berubah, perbarui yang tersentuh dari daftar ini:

| Berkas | Isinya |
|---|---|
| `INTEGRATIONS.md` | peta integrasi satu-baris-per-modul (root) |
| `docs/ARCHITECTURE_BUSINESS_FLOW.md` | 8 diagram Mermaid (pakai `<br/>` untuk ganti baris — GitHub tidak merender `\n`) + galeri PNG |
| `docs/diagrams/*.png` | dirender via `@mermaid-js/mermaid-cli` (`-s 2 -b white`, puppeteer `--no-sandbox`) |
| `docs/Blueprint_Installation_Configuration.docx` | blueprint: arsitektur, katalog modul, manual instalasi, konfigurasi tingkat-field (12 subseksi), PNG tersemat |
| `docs/Custom_Modules_Feature_List_UserGuide_TestScenarios.docx` | user guide teknis + tabel skenario test per modul |
| `docs/Panduan_Pengguna_Fitur_Sesuai_Alur_Bisnis.docx` | panduan non-teknis 13 BAB urut alur bisnis |
| `docs/UAT_Tracker_Custom_Modules.xlsx` | kasus UAT (79+) dengan dropdown Status, COUNTIF Summary, sheet Sign-off |
| `docs/Daftar_Pertanyaan_SME_Komprehensif_Semua_Modul.docx` | kuesioner SME (117 pertanyaan, area A–AF, kolom jawaban) |
| `docs/Project_Plan_Timeline_Implementasi.docx` | project plan 6 fase (1 Jul 2026 – go-live 1 Jan 2027), Gantt, migrasi/cut-over, risiko, kriteria go/no-go |

**Berkas .docx/.xlsx adalah hasil generate, jangan pernah diedit langsung.**
Generatornya ada di **`tools/docgen/`** (python-docx/openpyxl) — ubah
skripnya, jalankan dari folder itu (path output relatif), lalu commit skrip +
hasilnya bersama-sama. Baca `tools/docgen/README.md`. Konstanta gaya: NAVY
`#1F3964` (judul/modul kustom), GREEN `#006A4E` (subjudul/addon dasar),
abu-abu miring untuk caveat; konten Bahasa Indonesia.

Jawaban SME yang sudah terkonfirmasi (jangan ditanya ulang; desain mengikuti
ini): mata uang pelaporan hanya IDR; laporan bulanan, per properti DAN
konsolidasi per pemilik (wajib); tidak ada rekening bank trust fisik terpisah
(saldo trust adalah konsep GL); pembagian remittance proporsional %
kepemilikan; budget seasonal per bulan dengan approval 3 level dan riwayat
revisi; deposit adalah liabilitas ("titipan"), dikembalikan hanya setelah
settlement + BAST; PPN 11% + PPh final 10%; tahun fiskal Jan–Des; periode
dikunci setelah statement terbit; migrasi data dari MRI diharapkan; nomor
faktur CORETAX: arah integrasi (ekspor XML vs input nomor manual) masih
pertanyaan terbuka — cek
`docs/Daftar_Pertanyaan_SME_Komprehensif_Semua_Modul.docx` sebelum membangun.

## 8. Alur Git & PR

- Bekerja di branch `claude/*` yang ditetapkan (saat ini
  `claude/gallant-curie-dpaatp`); jangan pernah push ke tempat lain.
- Gaya commit: prefiks `feat:` / `docs:` / `fix:`, subject Inggris ringkas,
  body Indonesia berisi apa & mengapa, lalu trailer dari harness. Satu
  perubahan logis per commit; regenerasi dokumen boleh menumpang commit fitur
  penyebabnya.
- `git push -u origin <branch>`; retry dengan backoff hanya saat gagal
  jaringan.
- PR #1 adalah PR panjang untuk branch ini — **perbarui deskripsinya** (judul,
  jumlah modul, tautan dokumen) saat lingkup bertambah; jangan buka PR kedua
  untuk branch yang sama. Jaga blok tautan "Dokumentasi Utama" dan bagian
  jujur "Status verifikasi" tetap mutakhir.
- Akses GitHub via tool MCP (`mcp__github__*`), bukan `gh`.

## 9. Saat ragu

Lebih baik bertanya (dalam bahasa Indonesia) daripada mengarang aturan bisnis
— proyek ini punya proses kuesioner SME yang hidup; aturan yang belum jelas
masuk ke sana. Untuk ketidakpastian teknis Odoo 19 (id inherit view, rename
field antar versi minor), implementasikan secara defensif, catat sebagai item
smoke test, dan sebutkan di balasan.

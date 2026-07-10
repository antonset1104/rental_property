# Generator Dokumen (`tools/docgen/`)

Seluruh berkas `.docx`/`.xlsx` di `docs/` **dihasilkan oleh skrip di folder ini**
— jangan pernah mengedit berkas binernya langsung. Ubah skripnya, jalankan
ulang, lalu commit skrip + hasil generate bersama-sama.

| Skrip | Menghasilkan |
|---|---|
| `gen_blueprint.py` | `docs/Blueprint_Installation_Configuration.docx` (menyematkan PNG dari `docs/diagrams/`) |
| `gen_userguide.py` | `docs/Custom_Modules_Feature_List_UserGuide_TestScenarios.docx` |
| `gen_user_guide_flow.py` | `docs/Panduan_Pengguna_Fitur_Sesuai_Alur_Bisnis.docx` |
| `gen_uat.py` | `docs/UAT_Tracker_Custom_Modules.xlsx` |
| `gen_sme_questions.py` | `docs/Daftar_Pertanyaan_SME_Komprehensif_Semua_Modul.docx` |

## Cara menjalankan

```bash
pip install python-docx openpyxl   # dependensi
cd tools/docgen                    # WAJIB dari folder ini (path output relatif ../../docs/)
python3 gen_blueprint.py           # dst.
```

## Konstanta gaya (samakan di semua skrip)

- NAVY `#1F3964` — judul utama / modul kustom
- GREEN `#006A4E` — subjudul / addon dasar
- Abu-abu miring — catatan/caveat
- Konten dalam Bahasa Indonesia; heading tabel dwibahasa seperlunya

## Diagram PNG

PNG di `docs/diagrams/` dirender dari blok Mermaid pada
`docs/ARCHITECTURE_BUSINESS_FLOW.md` dengan:

```bash
npx -y @mermaid-js/mermaid-cli -i <file>.mmd -o <file>.png -b white -s 2 \
    -p <(echo '{"args":["--no-sandbox"]}')
```

Bila diagram Mermaid berubah, render ulang PNG lalu jalankan ulang
`gen_blueprint.py` agar sematan di Blueprint ikut terbarui.

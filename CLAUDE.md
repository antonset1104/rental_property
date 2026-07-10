# CLAUDE.md — Property Management System (Odoo 19 CE)

Read this file fully before making any change. It encodes decisions already made
in this project; do not re-litigate them, and do not guess where it is silent —
ask the user (in Indonesian).

## 1. What this project is

A comprehensive Property Management System for an Indonesian property company
(evaluating IFCA vs custom Odoo), built as **26 companion modules** on top of the
paid third-party addon `rental_management` v3.3.9 (TechKhedut, license OPL-1)
for **Odoo 19 Community Edition**. The flagship deliverable is a CBRE/MRI-style
**Owners Statement** report suite (9 sections) plus Indonesian tax (CORETAX
e-Faktur/SPT XML export), trust accounting, owner remittance, GTO, CAM, fixed
assets, portals, and operational modules.

There is **no Odoo runtime in this environment**. Code is validated statically
only. Never claim anything was "tested on Odoo" — say it passed syntax/XML/CSV
validation and still requires a smoke test on an Odoo 19 staging instance.

## 2. Hard rules (never break these)

1. **Never modify `rental_management/`** — it is OPL-1 licensed third-party
   code. All extensions live in separate `rental_management_*` companion
   modules that `depends` on it.
2. **Community Edition first.** Do not add a dependency on an Enterprise app.
   The only allowed exception is `rental_management_documents` (depends on
   `documents`), which has a Community fallback `rental_management_document_ce`.
   Every other module's `depends` must resolve to CE modules only.
3. **Reply to the user in Indonesian.** Code, identifiers, and commit subjects
   are in English; commit bodies, docs for end users, and chat replies are in
   Indonesian.
4. **Decoupled integrations.** A module may use another custom module's field
   (e.g. `property_manual_id`) only behind a runtime existence check
   (`if 'property_manual_id' in self.env['account.move']._fields:`), so every
   module installs independently.
5. **Do not build a parallel ledger.** All financials go through standard
   `account.move`. Property attribution and analytic stamping (section 4) are
   the single mechanism — reuse them, never duplicate them.
6. **Be honest in reports and PR text**: static validation ≠ tested. Flag
   version-sensitive API points (view inherit xpaths, analytic line fields,
   CORETAX XSD) whenever you touch them.
7. Do not include the model identifier in commits, PR text, or code comments.
   Keep the `Co-Authored-By` and `Claude-Session` trailers exactly as the
   harness provides them.

## 3. Repository layout

```
rental_management/               # third-party base addon — READ ONLY
rental_management_<feature>/     # 26 companion modules (see INTEGRATIONS.md)
docs/                            # deliverables: .docx/.xlsx + .md + diagrams/
INTEGRATIONS.md                  # module ↔ standard-Odoo integration map
```

Each module follows the same skeleton:
`__manifest__.py`, `__init__.py`, `models/`, `views/`, `security/ir.model.access.csv`,
optional `data/` (sequences, cron, products), `wizard/`, `report/`, `README.md`.

## 4. Architecture you must preserve

**Property attribution chain** (the backbone — everything reports through it):
`tenancy_id / sold_id / maintenance_request_id / property_manual_id` on
`account.move` → computed stored `property_financial_id` → filters the Owners
Statement, and on `_post()` the property's analytic account is stamped onto
income/expense lines (`analytic_distribution = {str(analytic.id): 100.0}`,
only when empty). Defined in
`rental_management_financial_report/models/account_inherit.py`.

Consequences:
- Any new document that bills or spends against a property must set
  `tenancy_id` **or** `property_manual_id` on the `account.move` it creates.
  That is all that's needed — reporting and analytic follow automatically.
- The Owners Statement engine lives in
  `rental_management_financial_report/wizard/owner_statement_wizard.py`
  (accrual from posted move lines; cash basis via
  `matched_credit_ids/matched_debit_ids` + `partial.max_date`). Extend it,
  don't fork it.
- Trust arithmetic is fixed: Opening Trust + Net Cash − Remittances = Closing.

## 5. Odoo 19 coding conventions (this repo's observed style)

- Manifest: `'version': "19.0.1.0.0"`, `'category': 'Realestate'`,
  `'license': 'LGPL-3'`, `'application': False`, list every data file, and
  order security CSV before views.
- Views: Odoo 19 syntax — `<list>` not `<tree>`, `<chatter/>` not the old
  message_follower divs, attribute expressions like `invisible="state != 'draft'"`
  (no `attrs=`), `column_invisible` for list columns.
- Models: `_description` always; `mail.thread` (+ `mail.activity.mixin` when
  activities/reminders are needed); `@api.model_create_multi` for create;
  sequences via `self.env['ir.sequence'].next_by_code(...)` seeded from
  `data/sequence.xml`; translations via `self.env._(...)` (Odoo 19 style),
  not the module-level `_`.
- Security: 8-column `ir.model.access.csv`; default group `base.group_user`;
  manager-gated actions (budget approve, CORETAX) use
  `account.group_account_manager`; portal rules use `base.group_portal` with
  record rules limiting to own records.
- Cron jobs live in `data/` and default to daily; name them descriptively
  (they are listed in the Blueprint's cron table — update it when adding one).
- CORETAX XML: tag names must match DJP templates **exactly, including their
  official misspellings** (`CommercialMethode`, `FiscalDepretiationThisYear`,
  `AmountOfWitholding`). Never "fix" them.

## 6. Definition of done — run these before saying finished

A change is finishable only when all of the following pass (no Odoo available,
so this is the whole gate):

```bash
# 1. Python syntax — every touched module
find rental_management_<mod> -name "*.py" -exec python3 -m py_compile {} \;
# 2. XML well-formedness — every touched XML
python3 -c "import xml.dom.minidom,glob; [xml.dom.minidom.parse(f) for f in glob.glob('rental_management_<mod>/**/*.xml', recursive=True)]"
# 3. Manifest ↔ files: every path in 'data' exists; every new file is listed
# 4. CSV: 8 columns per row, model ids match model _name (model_<name with _>)
```

Then, if the change adds/renames a module or feature, sync the docs (section 7)
— an unsynced doc set is not done. Finally commit and push (section 8) and
state plainly in the reply that live smoke testing is still required.

## 7. Documentation set — keep it in sync

`docs/` is a first-class deliverable the user hands to stakeholders. When
modules or features change, update whichever of these it touches:

| File | What it is |
|---|---|
| `INTEGRATIONS.md` | one-row-per-module integration map (root) |
| `docs/ARCHITECTURE_BUSINESS_FLOW.md` | 8 Mermaid diagrams (use `<br/>` for line breaks — GitHub does not render `\n`) + PNG gallery |
| `docs/diagrams/*.png` | rendered via `@mermaid-js/mermaid-cli` (`-s 2 -b white`, puppeteer `--no-sandbox`) |
| `docs/Blueprint_Installation_Configuration.docx` | blueprint: architecture, module catalog, install manual, field-level configuration (12 subsections), embedded PNGs |
| `docs/Custom_Modules_Feature_List_UserGuide_TestScenarios.docx` | technical user guide + per-module test scenario tables |
| `docs/Panduan_Pengguna_Fitur_Sesuai_Alur_Bisnis.docx` | non-technical guide in 13 BAB ordered by business flow |
| `docs/UAT_Tracker_Custom_Modules.xlsx` | UAT cases (79+) with Status dropdown, Summary COUNTIFs, Sign-off sheet |
| `docs/Daftar_Pertanyaan_SME_Komprehensif_Semua_Modul.docx` | SME questionnaire (117 q, areas A–AF, answer column) |

**The .docx/.xlsx files are generated, never hand-edited.** They are produced by
python-docx/openpyxl generator scripts (`gen_userguide.py`, `gen_uat.py`,
`gen_blueprint.py`, `gen_user_guide_flow.py`, `gen_sme_questions.py`). Style
constants: NAVY `#1F3964` (headers/custom modules), GREEN `#006A4E`
(subheaders/base), grey italic for caveats; Bahasa Indonesia content. If the
generator scripts are not present in your session (they lived in a scratchpad),
say so and offer to reconstruct the needed generator rather than editing the
binary file.

Known confirmed SME answers (do not re-ask; design against them): reporting
currency IDR only; reports monthly, per property AND consolidated per owner
(mandatory); no separate physical trust bank account (trust balance is a GL
concept); remittance split proportional to ownership %; budget is seasonal
per month with 3-level approval and revision history; deposit is a liability
("titipan"), refunded only after settlement + BAST; PPN 11% + PPh final 10%;
fiscal year Jan–Dec; periods locked after statements are issued; migration
from MRI data is expected; CORETAX faktur numbers: direction of integration
(export XML vs manual number entry) is still an open question — check
`docs/Daftar_Pertanyaan_SME_Komprehensif_Semua_Modul.docx` before building.

## 8. Git & PR workflow

- Work on the designated `claude/*` branch (currently
  `claude/gallant-curie-dpaatp`); never push elsewhere.
- Commit style: `feat:` / `docs:` / `fix:` prefix, concise English subject,
  Indonesian body listing what & why, then the harness trailers. One logical
  change per commit; docs regen may ride with the feature that caused it.
- `git push -u origin <branch>`; retry with backoff only on network failure.
- PR #1 is the long-running PR for this branch — **update its description**
  (title, module count, doc links) when scope grows; don't open a second PR
  for the same branch. Keep the "Dokumentasi Utama" link block and the honest
  "Status verifikasi" section current.
- GitHub access is via MCP tools (`mcp__github__*`), not `gh`.

## 9. When unsure

Prefer asking (in Indonesian) over inventing business rules — this project has
a live SME questionnaire process; unresolved rules go there. For technical
Odoo-19 uncertainty (view inherit ids, field renames between minor versions),
implement defensively, note it as a smoke-test item, and list it in the reply.

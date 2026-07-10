# Rental Management – CORETAX e-Faktur (Indonesia)

Indonesian VAT localisation helper for the TechKhedut **`rental_management`** addon.
Exports posted customer invoices to the DJP **CORETAX** *TaxInvoiceBulk* XML
(**Faktur PK template v1.4**) for bulk upload.

## What it adds

- **Partner** (`res.partner`): `CORETAX TIN / NPWP`, `ID TKU`, buyer document type
  (TIN / Passport / National ID / Other), document number, country (ISO3, e.g. `IND`).
- **Customer invoice** (`account.move`, *CORETAX e-Faktur* tab): transaction code
  (01–09), Normal/Replacement, additional-info code, customs document + month/year,
  reference, facility stamp, seller/buyer ID TKU, exported flag & date.
- **Product**: CORETAX type (A goods / B service), goods/service code, unit code.
- **Wizard** *CORETAX e-Faktur Export* (menu **Properties → CORETAX e-Faktur**, and a
  list/form action on Invoices): builds the `TaxInvoiceBulk` XML for a date range or a
  selection, returns it as a downloadable file, and flags the invoices as exported.

## XML mapping (Faktur PK v1.4)

`TaxInvoiceBulk/TIN` = company CORETAX TIN. Per invoice → `TaxInvoice` with
`TaxInvoiceDate, TaxInvoiceOpt, TrxCode, AddInfo, CustomDoc, CustomDocMonthYear,
RefDesc, FacilityStamp, SellerIDTKU, BuyerTin, BuyerDocument, BuyerCountry,
BuyerDocumentNumber, BuyerName, BuyerAdress, BuyerEmail, BuyerIDTKU`. Each invoice
line → `GoodService` with `Opt, Code, Name, Unit, Price, Qty, TotalDiscount, TaxBase,
OtherTaxBase, VATRate, VAT, STLGRate, STLG`.

- Amounts are whole Rupiah (rounded, no decimals).
- `OtherTaxBase` defaults to `TaxBase` (DPP); `VAT = round(OtherTaxBase × VATRate%)`.
- `Opt` falls back to `B` for service products, `A` otherwise; `Code`→`000000`,
  `Unit`→`UM.0001` unless overridden on the product.

## Setup

1. Set the **CORETAX TIN / NPWP** and **ID TKU** on the company contact and on each
   customer contact (CORETAX tab).
2. Set CORETAX type/unit codes on the products you invoice (rental = service / `B`).
3. On each customer invoice, review the **CORETAX e-Faktur** tab (transaction code
   defaults to `04 – Other Tax Base`).
4. Run **CORETAX e-Faktur Export**, download the XML and upload it to CORETAX.

## Export types (single wizard, `Export Type` selector)

- **Faktur Keluaran (PK)** — posted customer invoices/refunds → `TaxInvoiceBulk` (v1.4).
- **Retur Faktur Masukan (PM)** — posted **vendor credit notes** (`in_refund`) →
  `InputTaxInvoiceReturn` (v1.1). Per document: original faktur no. (set on the credit
  note), seller TIN, return date (DD-MM-YYYY), and a `Rows` line per item with
  `ReturnQuantity/ReturnTaxBase/ReturnVAT` plus a `FooterRow` total.
- **Lampiran C** — posted customer invoices that carry a *Type of VAT Collected*
  (001/002/003/100) → `VATandSTLGCollectedByOtherCollector` (v1.1) for the
  period (month/year of *From* date), with per-row seller/buyer TIN+name, billing
  document, selling price, VAT and grand totals.

## SPT / bookkeeping exports (same wizard)

- **Pencatatan** (`SimpleBookKeepingBulk`) — from customer invoices: transaction
  number/date, customer, per-item details (good/service, price/unit, qty), discount.
- **L9 Depreciation / Amortization** (`DepreciationAmortization`) — from the
  *L9 Depreciation/Amortization* register (Properties → CORETAX → SPT Registers),
  split into `ListOfDepreciation` / `ListOfAmortization` by kind. Amounts keep decimals.
- **L3B Withheld by Other Parties** (`OtherParties`) — from the L3B register, for the
  selected Tax Year.
- **L11A Uncollectible Debt** (`UncollectibleDebtBulk`) and **L11A Non-Performing
  Credit** (`NonPerforming`) — from their registers, for the selected Tax Year.
- **L11A Promotion Expense** (`PromotionExpense`) and **L11A Entertainment Expense**
  (`EntertainmentExpense`) — from their registers, for the selected Tax Year.
- **L10A Related-Party Transactions** (`DeclarationOfTransactionRelatedPartiesBulk`)
  — from the related-party register, for the selected Tax Year.

Register-based exports use the **Tax Year** field; document-based exports (PK / PM /
Lampiran C / Pencatatan) use the **From / To** period.

## Scope / notes

- Covers Faktur Keluaran (PK), Retur Faktur Masukan (PM), Lampiran C, Pencatatan,
  and SPT attachments L9, L3B, L11A (uncollectible & non-performing).
- L9/L3B/L11A have no natural Odoo source, so they are captured in dedicated
  data-entry registers and exported from there.
- Building depreciation tables (Tabel A/B Kelompok I & II) concern fixed-asset
  depreciation and are out of scope for the faktur export.
- Validate the generated XML against the official CORETAX XSD and the current DJP
  template version before production upload; tested for syntax/structure here but not
  run on a live Odoo 19 instance.

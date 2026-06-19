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

## Scope / notes

- Output tax invoices (Faktur Keluaran) only. Retur Faktur PM (input return) and
  Lampiran C exports can be added on the same pattern if needed.
- Building depreciation tables (Tabel A/B Kelompok I & II) concern fixed-asset
  depreciation and are out of scope for the faktur export.
- Validate the generated XML against the official CORETAX XSD and the current DJP
  template version before production upload; tested for syntax/structure here but not
  run on a live Odoo 19 instance.

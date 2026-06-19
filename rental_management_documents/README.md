# Rental Management – Documents (Property Folders)

Bridges the addon with the Odoo **Documents** app (Enterprise).

- One `documents.document` **folder per property** (`documents_folder_id`).
- **Open / Sync Documents** creates the folder if needed, pushes the property's
  `ir.attachment`s into Documents, and opens the folder.

Requires the Enterprise `documents` app; targets the Odoo 19 unified
`documents.document` model (folders = documents of type 'folder'). Document
operations are version-sensitive — smoke-test on your Odoo 19 Enterprise build.

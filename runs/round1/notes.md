# AI agent notes, round 1

Written by the agent alongside its `pmr.xml`. Excerpt: the test also included a separate business calculation that is not part of this repo, so the parts of the notes about it have been removed. Everything else is as the agent wrote it.

## Assumptions
1. **Product code clean-up.** `'40210.250` has a leading apostrophe and `40210.25` has lost its trailing zero. Both are spreadsheet artefacts. I normalised them to Northfield's `NNNNN.NNN` format, so `40210.25` became **40210.250**. That row's product name `VERDANT 540 2X2.5` also matches.
2. **GTIN to Northfield code.** INV-26-0907 uses GTIN `00812345000017` (qualifier `UK`), not a Northfield code. I mapped it to **40210.250** because the product name and pack (2 X 2.5 GAL) match. The PMR line carries both identifiers. **This GTIN fails the GS1 check digit. A valid one would end in ...0016.** Please confirm it against Northfield's product master.
3. **Unit conversion.** Pack sizes come from the PackSizeDescription column:
   - Verdant: 1 case = 2 x 2.5 = 5 US gal
   - Halcyon: 1 case = 4 x 1 = 4 US gal
   - Rootwise: 1 bag = 25 lb
   - `GA` means US gallons. Rootwise is treated as a dry product measured in LB.
4. **Returns** are the negative-quantity lines (0912 and 0925). The file doesn't link either return to its original invoice.
5. **SaleType codes.** `EN` = end-user sale. `IB` = inter-branch transfer.
6. **Identifier qualifiers** (X12-style codes mapped to Chem eStandards Agency values):
   - `9` → `AGIIS-EBID`. These 13-digit IDs fail the GS1 check digit, so they are not GLNs. In ag EDI, qualifier 9 normally carries the EBID.
   - `92` → `AssignedByBuyer` (Oakmere's `OAK-0193`, which looks like Prairie's own account number).
   - `C5` → `Other` (Hartley Farms' `70451220`). I could not find a confident mapping for C5. Please confirm which ID system this is; it may be an AGIIS or grower ID.
   - `MG` → `AssignedByManufacturer`. `UK` → `GTIN`.

## How the PMR is built
- **Header:** From = Prairie Ag Supply (sender). To = Northfield. Document ID `PAS-NCS-PMR-202609-001`, dated 2026-10-13. Currency USD, language eng.
- **Two `ProductMovementReportDetails` blocks**, both with Prairie as the reporting entity:
  - a `SalesReport` with the end-user sales and returns
  - a `ProductTransferReport` with the IB transfer, as `IntraCompanyTransferOut`. The schema requires a `SaleOrReturnType` attribute, so I set it to `Wholesale`.
- **Transactions.** There is one transaction per invoice, with InvoiceNumber, InvoiceDate, and the ShipDate taken from TransactionDate (ReturnDate for returns). ShipTo is the end customer and `OtherPartner ShipFrom` is the Prairie warehouse. Sales use `StockSale`; returns use `Return`.
- **Quantities.** `ProductQuantity` is in base units (UN Rec 20 `GLL` / `LBR`). Where the source was in cases or bags, the original count is also kept in `PackagingQuantity` (`CS` / `BG`). Returns keep their **negative** sign and are also typed `Return`. **Confirm with Northfield that this matches their convention, so a return isn't counted twice or flipped to positive.**
- **What is not mapped:**
  - `GS` = 4471.
  - `LocationType` = `DS`. I assumed a distributor stocking location. If it actually means drop-ship, the movement type should be `DropShipSale` instead of `StockSale`.
  - `ContainsError` (all `N`).
  - `ManufacturerRecord ID` (all blank).
- **All non-duplicate rows are in the PMR, including the out-of-period ones (Aug 29 and Oct 1 invoices).** It reports what the distributor sent.

## Things the team should look at
1. **The duplicate INV-26-0907 row.** Fix the extract so it isn't sent twice.
2. **INV-26-0829.** It may already have been in August's report, so check before resubmitting it, or Northfield may count it twice.
3. **INV-26-1001.** An October invoice doesn't belong in a September file. Make sure it goes in October's report and isn't sent twice.
4. **The Halcyon return on INV-26-0925 (-2 CA, Brook Valley Grain).** This file has no matching Halcyon sale to Brook Valley. Confirm it is legitimate and find the original invoice.
5. **Mixed units for one product in one file.** Verdant is reported in both GA and CA, and Rootwise in both BG and LB. Ask the source system to report one consistent unit.
6. **The invalid GTIN, and the EBIDs that aren't valid GLNs.** Fix the GTIN in master data, and confirm the IDs are registered AGIIS EBIDs.
7. **The IB transfer.** If the Ames branch later sells this 100 GA to growers, those sales should show up in a later report as Ames end-user sales.

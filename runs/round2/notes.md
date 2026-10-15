# AI agent notes, round 2

Written by the agent alongside its `pmr.xml`. Excerpt: the test also included a separate business calculation that is not part of this repo, so the parts of the notes about it have been removed. Everything else is as the agent wrote it.

## Assumptions

1. **Unit conversion.** I converted case and bag quantities using the pack size description: Verdant "2 X 2.5 GAL" is 5 gal per case, Halcyon "4 X 1 GAL" is 4 gal per case, and Rootwise "1 X 25 LB" is 25 lb per bag. GA and LB quantities were used as they are.
2. **Returns.** Some returns may not match a sale in this file (see the data issues below).
3. **The GTIN row is counted as Verdant 40210.250.** L4 (INV-26-0907) gives the product as GTIN `00812345000017` (qualifier UK), not as Northfield's code. The product name and pack ("VERDANT 540 HERBICIDE", "2 X 2.5 GAL") match 40210.250 exactly, so I counted it as that product. **But the GTIN's check digit is wrong** (the computed digit is 6 and the file has 7), so the code itself cannot be relied on. See the data issues below. If Northfield rejects this line, Verdant falls to 55 GAL.
4. **Product codes.** The leading apostrophe in values such as `'40210.250` is an Excel trick to keep the value as text, so I removed it. L10's `40210.25` (product name "VERDANT 540 2X2.5") is the same code with its trailing zero lost to Excel, so I changed it back to `40210.250`, in the XML as well.

## How the data was mapped to the XML

The 2004 implementation guide does not match the 7.1 schema in several places. Where they disagreed, I followed the schema:

- **SenderID and its qualifier.** The guide points the SenderID at `From/PartnerInformation` and the qualifier at `PartnerIdentifier`. The schema needs `PartnerIdentifier` text with an `@Agency` attribute, so that is what I used. The guide gives no exact element for Sender City, State and Zip; they went into `From/PartnerInformation/AddressInformation`.
- **Distributor block.** The guide's path is `ProductMovementReportProperties/PartnerInformation/ReportingEntity/PartnerAddressInformation`. That does not exist in 7.1. `ReportingEntity` sits directly under `ProductMovementReportDetails`, and the address goes in `PartnerInformation/AddressInformation`.
- **Warehouse address.** The guide's path is `OtherPartner/.../ContactInformation/AddressInformation`. In 7.1, `ContactInformation` has no address, so the address went in `PartnerInformation/AddressInformation`. I gave the warehouse `PartnerRole="ShipFrom"`, which the schema requires and the guide does not specify.
- **Code lists.** The schema uses words, not EDI codes:
  - Qualifier 9 became `AGIIS-EBID`, C5 became `AGIIS-NAPD` and 92 became `AssignedByBuyer`.
  - Product qualifier MG became `AssignedByManufacturer` and UK became `GTIN`.
  - LocationType DS became `ProductMovementReportType="SalesReport"`.
- **Units.** The schema fixes `UnitOfMeasureCode@Domain` to `UN-Rec-20`, so the guide's X12 355 codes had to be translated: GA → GLL, LB → LBR, CA → CS, BG → BG. I kept quantities in the unit the distributor reported, without converting them in the XML. **Please confirm Northfield accepts CS and BG.** Some revisions of Rec 20 treat packaging codes as deprecated. If Northfield doesn't accept them, we can restate those lines in GLL or LBR.
- **SaleType.** The schema's `SaleOrReturnType` only allows EndUser or Wholesale, and it also requires a `ProductMovementType`:
  - EN sales became `StockSale` / `EndUser`.
  - EN negative quantities became `Return` / `EndUser`.
  - IB became `IntraCompanyTransferOut` / `Wholesale`. I chose Wholesale because it is the closest value that is not EndUser.
- **Sign of returns.** Returns are marked by `ProductMovementType="Return"` and carry **positive** quantities, so the type gives the direction. **Confirm this with Northfield.** If their parser expects negative quantities for returns, the sign needs changing, or they may count the returns twice or not at all.
- **Values the file doesn't give.** I used `PostalCountry=US`, `CurrencyCode=USD` and `LanguageCode=eng`, because the schema requires them.
- **Dates.** They were converted from MM/DD/YYYY to xs:dateTime at midnight, with no timezone.
- **Header date.** `ThisDocumentDateTime` is 2026-10-02, the latest TransactionDate in the file (see the data issues below).
- **Grouping.** Rows are grouped into one `ProductMovementTransaction` per invoice. INV-26-0901 has 2 lines; every other invoice has 1.
- **Columns left out.** ContainsError (all N) and ManufacturerRecordID (all blank) were not mapped. The guide says they are not part of the PMR.
- **Rows in the XML.** The duplicate (L9) was left out. Every other row is in the XML, including the IB transfer and the August and October invoices, so the manufacturer sees the full movement file.

## Data issues the team should know about

1. **Duplicate line.** L4 and L9 are identical (INV-26-0907 line 1). Ask Prairie whether this was a mistake on resubmission. If there really were two shipments, they need separate invoice or line numbers.
2. **Invalid GTIN.** `00812345000017` on INV-26-0907 fails the GS1 check digit (it should end in 6). Ask Prairie to report Northfield's own code (MG 40210.250) or a correct GTIN. Also, this one sale uses UK while every other line uses MG.
3. **Product code mangled by Excel.** L10 has `40210.25` and a non-standard product name ("VERDANT 540 2X2.5"). The leading apostrophes on the other codes show the file passed through Excel. Ask Prairie to send codes as text.
4. **Units are not consistent.** The same product is reported in GA on some lines and CA on others (Verdant, Halcyon), and in BG on one line and LB on another (Rootwise). This is valid, but it is easy to get wrong when adding up.
5. **Unmatched return.** Brook Valley Grain returned 2 cases of Halcyon (INV-26-0925), but this file has no Halcyon sale to Brook Valley. It may be against an earlier period, so it may need checking against prior reports or the original invoice. Hartley's return of 15 gal of Verdant does match its 40 gal sale on INV-26-0901.
6. **Out-of-period rows in a "Sep 2026" file.** One August invoice (reported late) and one October invoice are included. Make sure neither is also claimed in the August or October reconciliation, so they are not counted twice.
7. **One document number, many transmission dates.** Every row has GS 4471, but TransactionDate varies from 09/03 to 10/02. The guide says GS must be unique per transmission. This looks like several transmissions combined under one control number. It could break Northfield's duplicate checking. A fresh, unique document number for this consolidated PMR may be needed.
8. **Interbranch transfer.** The 100 gal of Verdant moved from Clayton to Ames (INV-26-0915) is an inventory movement, not a sale. It is reported as IntraCompanyTransferOut.
9. **ShipTo identifiers.** OAKMERE PARTNERS uses a distributor-assigned code (OAK-0193, qualifier 92) rather than an EBID or NAPD.
10. **Header columns don't match the guide.** The file says "LocationType" where the guide says ReportLocationType, and some column names are spaced differently (for example "ManufacturerRecord ID" and "SenderID Qualifier"). This is harmless, but worth knowing for automated loaders.

# AgGateway mapping test

Can an AI agent map a distributor's sales reconciliation file into an AgGateway Product Movement Report, and how would you know if it got it right?

This is the test behind the blog post [The Mapping Took Four Minutes. The Testing Is Still the Job.](https://www.integrationguys.net/mapping-took-four-minutes.html) The short version: a fresh AI agent produced schema-valid XML in about four minutes and handled most of the planted problems. Building the test took far longer than the mapping, which is the point.

## What's here

| Path | What it is |
| --- | --- |
| `data/sales_reconciliation_sep2026.csv` | Synthetic input in the 2004 Ag eStandards Sales Reconciliation flat-file layout. All parties, products and IDs are invented. |
| `schema/Chem_eStandards-7.1.xsd` | The Chem eStandards 7.1 schema, which defines the ProductMovementReport. OAGi licence; see `schema/NOTICE.md`. |
| `grader/grade.py` | 16 automated checks on a `pmr.xml`: schema validity plus the semantic traps below. |
| `grader/reference_mapping.py` | A hand-written reference mapping, used to prove the grader passes a correct answer. |
| `reference/pmr.xml` | Output of the reference mapping (16/16). |
| `runs/round1/` | The AI agent's output and notes with only the file and the schema (14/16). |
| `runs/round2/` | The same, with the 2004 implementation guide added (15/16). |
| `prompts/` | The prompts given to the agent. |

## The planted problems

- A line sent twice
- Returns sent as negative quantities
- A transfer between the distributor's own branches (`IB`), which is not a sale
- Invoices from the months either side of the reporting month
- Quantities in cases and bags as well as gallons and pounds; the pack size is only in a description field
- The same product as a manufacturer code, a GTIN, and a code Excel has mangled (`40210.250` saved as `40210.25`), plus leading Excel apostrophes
- Ship-to ID qualifiers `9`, `C5` and `92`, which the schema expresses as words (`AGIIS-EBID`, `AGIIS-NAPD`, `AssignedByBuyer`)
- X12 unit codes (`GA`, `LB`) where the 7.1 schema fixes the code list to UN/ECE Rec 20 (`GLL`, `LBR`)

One problem was not planted: the two GTINs in the data have invalid check digits. That was a mistake in building the test, and both AI runs caught it.

## Run it

```bash
pip install lxml
python3 grader/grade.py schema/Chem_eStandards-7.1.xsd reference      # 16 / 16
python3 grader/grade.py schema/Chem_eStandards-7.1.xsd runs/round1    # your own output: any folder containing pmr.xml
```

To test your own model or tool, give it `data/` and `schema/` with the prompt in `prompts/round1.md`, put its `pmr.xml` in a folder, and point the grader at it.

## Results

| Check | Round 1 (file + schema) | Round 2 (+ 2004 guide) |
| --- | --- | --- |
| Valid against the 7.1 schema | Pass | Pass |
| Duplicate reported once | Pass | Pass |
| Returns and branch transfer typed correctly | Pass | Pass |
| Invoice dates read correctly | Pass | Pass |
| Cases and bags converted via pack size | Pass | Pass |
| Excel damage repaired, product ID qualifiers mapped | Pass | Pass |
| Ship-to qualifier `C5` mapped to `AGIIS-NAPD` | Fail: sent as `Other`, and flagged as unknown in its notes | Pass |
| Units use Rec 20 codes only | Pass | Fail: kept `CS`/`BG` for cases and bags |
| One `SalesReport` section | Fail: put the transfer in its own `ProductTransferReport` | Pass |

Two of the three failures are judgement calls rather than errors; the grader is deliberately strict.

The most important result is not in the table. The two runs encoded the same return differently: round 1 as `Return` with `-8 GLL`, round 2 as `Return` with `2 CS`. Both are valid against the schema. A receiving system would treat them differently. Only an agreed implementation guide, and a test that enforces it, decides which is right.

## Caveats

This is a demonstration, not a benchmark. Twelve rows of synthetic data, problems chosen by us, and an agent that could validate its own output against the schema. The test data and grader were built with AI assistance, and the agent under test came from the same family of models.

## Not included

- **The 2004 implementation guide** used in round 2. It is AgGateway material; members can obtain it from AgGateway.
- **A second task** from the original test, a business calculation over the same data, which is outside the scope of this repo. The prompts and agent notes have been trimmed accordingly.

## Licence

MIT for the code, data and documentation in this repo. The schema is redistributed under the OAGi licence; see `schema/NOTICE.md`.

---

[Integration Guys](https://www.integrationguys.net) · [Jeff Bradshaw](https://jgbradshaw.com)

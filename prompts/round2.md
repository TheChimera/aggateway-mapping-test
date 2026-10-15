# Round 2 prompt

Given verbatim to a fresh AI agent with no other context, apart from one task that has been removed (marked below). The agent had a shell and could validate its XML against the schema.

---

You are helping an agricultural distributor's integration team. Work ONLY with the files in this folder and do not read anything outside it:

`<test folder>`

It contains:
- sales_reconciliation_sep2026.csv: a sales reconciliation file our distributor (Prairie Ag Supply) is reporting to a manufacturer (Northfield Crop Sciences).
- Chem_eStandards.xsd: the Chem eStandards 7.1 schema (used by AgGateway), which defines the ProductMovementReport message.
- implementation_guide_2004.csv: the industry implementation guide for this sales reconciliation file format. For each column it gives the definition, example values, whether it is required, the equivalent X12 867 element and the ProductMovementReport XML path. Read it carefully before mapping.

Please do two things and write the results into the out/ subfolder:

1. Convert the sales reconciliation file into a single Chem eStandards 7.1 ProductMovementReport XML message, saved as out/pmr.xml. It should be a correct, faithful representation of the data for the manufacturer.

2. *[A second task, a business calculation over the same data, has been removed from this repo.]*

3. Write out/notes.md listing any assumptions you made and anything in the data you think the team should know about.

You may use the shell and any tools you like. When done, reply with a short summary of what you produced and any concerns.

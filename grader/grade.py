"""Grade a Product Movement Report produced from data/sales_reconciliation_sep2026.csv.

Usage: python3 grader/grade.py schema/Chem_eStandards-7.1.xsd <dir containing pmr.xml>
Needs: pip install lxml
"""
import sys, json, re
from lxml import etree
xsd_path, out = sys.argv[1], sys.argv[2]
N='{urn:cidx:names:specification:ces:schema:all:7.1}'
R=[]  # (id, check, passed, detail)
def chk(i, name, ok, detail=''): R.append((i, name, bool(ok), detail))
# expected per unique source line: invoice -> (product code, base qty signed, base unit, kind, iso date, shipto agency)
EXP={
 ('INV-26-0901','40210.250'):(40,'GAL','sale','2026-09-02','AGIIS-NAPD'),
 ('INV-26-0901','51133.100'):(24,'GAL','sale','2026-09-02','AGIIS-NAPD'),
 ('INV-26-0907','40210.250'):(50,'GAL','sale','2026-09-07','AGIIS-EBID'),
 ('INV-26-0912','40210.250'):(-15,'GAL','return','2026-09-12','AGIIS-NAPD'),
 ('INV-26-0915','40210.250'):(100,'GAL','transfer','2026-09-15','AGIIS-EBID'),
 ('INV-26-0829','51133.100'):(20,'GAL','sale','2026-08-29','AssignedByBuyer'),
 ('INV-26-0918','62001.025'):(200,'LB','sale','2026-09-18','AssignedByBuyer'),
 ('INV-26-0921','40210.250'):(30,'GAL','sale','2026-09-21','AGIIS-EBID'),
 ('INV-26-0925','51133.100'):(-8,'GAL','return','2026-09-25','AGIIS-EBID'),
 ('INV-26-0930','62001.025'):(400,'LB','sale','2026-09-30','AssignedByBuyer'),
 ('INV-26-1001','40210.250'):(50,'GAL','sale','2026-10-01','AGIIS-NAPD'),
}
GTIN={'00812345000017':'40210.250','00812345000024':'51133.100'}
PACK={'40210.250':5.0,'51133.100':4.0,'62001.025':25.0}  # base units per case/bag
UOM={'GLL':('GAL',1),'LBR':('LB',1),'GA':('GAL',1),'LB':('LB',1)}
def code(pid):
    p=pid.strip().lstrip("'")
    if p in GTIN: return GTIN[p]
    try: return '%.3f'%float(p)
    except: return p
try:
    doc=etree.parse(f'{out}/pmr.xml'); chk('A1','XML is well-formed',True)
except Exception as e:
    chk('A1','XML is well-formed',False,str(e)[:200]); doc=None
if doc is not None:
    schema=etree.XMLSchema(etree.parse(xsd_path))
    ok=schema.validate(doc)
    errs=[f'line {e.line}: {e.message}' for e in schema.error_log][:6]
    chk('A2','Valid against Chem eStandards 7.1 XSD',ok,'; '.join(errs))
    r=doc.getroot()
    fr=[e.text for e in r.iterfind(f'{N}Header/{N}From//{N}PartnerIdentifier')]
    to=[e.text for e in r.iterfind(f'{N}Header/{N}To//{N}PartnerIdentifier')]
    chk('B1','Distributor is the sender (From), manufacturer the receiver (To)','1001234560000' in fr and '1009876540000' in to, f'From={fr} To={to}')
    rt=[e.get('ProductMovementReportType') for e in r.iter(f'{N}ProductMovementTransactions')]
    chk('B2','Report type is SalesReport',rt and all(x=='SalesReport' for x in rt),str(rt))
    txs=list(r.iter(f'{N}ProductMovementTransaction'))
    got={}; dupes=0; uoms=set(); apos=False; agency_ok=True; agency_bad=[]; normalised=True
    for t in txs:
        p=t.find(f'{N}ProductMovementTransactionProperties')
        inv=next((d.text.strip() for d in t.iter(f'{N}DocumentIdentifier') if d.text and 'INV-' in d.text),None)
        dates={e.get('EventDateType'):(e.findtext(f'{N}DateTime') or '')[:10] for e in p.iter(f'{N}EventDateTime')} if p is not None else {}
        sh=[(e.get('Agency'),e.text) for e in t.iterfind(f'.//{N}ShipTo//{N}PartnerIdentifier')]
        for li in t.iter(f'{N}ProductMovementProductLineItem'):
            ids=[(e.get('Agency'),e.text or '') for e in li.iterfind(f'{N}ProductIdentification/{N}ProductIdentifier')]
            for ag,v in ids:
                if v.strip().startswith("'"): apos=True
                if v.strip() in GTIN and ag!='GTIN': agency_ok=False; agency_bad.append(f'{v}:{ag}')
                if re.fullmatch(r"'?\d+\.\d+",v.strip()) and ag!='AssignedByManufacturer': agency_ok=False; agency_bad.append(f'{v}:{ag}')
                if v.strip()=='40210.25': normalised=False
            c=code(ids[0][1]) if ids else None
            m=li.find(f'{N}ProductQuantity/{N}Measurement')
            q=float(m.findtext(f'{N}MeasurementValue')) if m is not None else None
            u=(m.findtext(f'{N}UnitOfMeasureCode') or '').strip() if m is not None else ''
            uoms.add(u)
            if u in UOM: base=q*UOM[u][1]; bu=UOM[u][0]
            elif u in ('CA','CS','CT','BG','BAG','XCS','XBG') and c in PACK: base=q*PACK[c]; bu='LB' if c=='62001.025' else 'GAL'
            else: base=None; bu=None
            key=(inv,c)
            if key in got: dupes+=1
            got[key]=dict(type=p.get('ProductMovementType') if p is not None else None, sr=p.get('SaleOrReturnType') if p is not None else None,
                          inv_date=dates.get('InvoiceDate'), base=base, bu=bu, uom=u, shipto=sh)
    chk('C1','Duplicate line sent twice is reported once',dupes==0 and len(got)==11,f'{len(txs)} transactions, {dupes} duplicates')
    miss=[k for k in EXP if k not in got]
    chk('C2','Every source line is present (matched by invoice + product)',not miss,f'missing {miss}' if miss else '')
    def each(i,name,f):
        bad=[f'{k[0]}/{k[1]}: {why}' for k,e in EXP.items() if k in got for why in [f(got[k],e)] if why]
        chk(i,name,not bad,'; '.join(bad[:5]))
    each('D1','Returns (negative quantity) mapped to ProductMovementType=Return',lambda g,e: None if e[2]!='return' or g['type']=='Return' else f"type={g['type']}")
    each('D2','Interbranch transfer (IB) mapped to an intra-company transfer, not a sale',lambda g,e: None if e[2]!='transfer' or (g['type'] or '').startswith('IntraCompanyTransfer') else f"type={g['type']}")
    each('D3','End-user sales typed as a sale with SaleOrReturnType=EndUser',lambda g,e: None if e[2]!='sale' or (g['type'] in ('StockSale','DropShipSale','ShipAndDebitSale') and g['sr']=='EndUser') else f"type={g['type']} sr={g['sr']}")
    each('D4','Invoice date carried as EventDateType=InvoiceDate, MM/DD read correctly',lambda g,e: None if g['inv_date']==e[3] else f"InvoiceDate={g['inv_date']}")
    each('D5','Quantities correct after units and pack size (cases x pack, bags x 25 lb)',lambda g,e: None if g['base'] is not None and abs(abs(g['base'])-abs(e[0]))<1e-6 and g['bu']==e[1] else f"{g['base']} {g['bu']} (uom {g['uom']}) expected {abs(e[0])} {e[1]}")
    each('D6','Ship-to ID qualifiers mapped (C5->AGIIS-NAPD, 9->AGIIS-EBID, 92->AssignedByBuyer)',lambda g,e: None if any(a==e[4] for a,_ in g['shipto']) else f"{g['shipto']}")
    chk('E1','Excel apostrophe stripped from product IDs',not apos)
    chk('E2','Product ID qualifiers mapped (UK->GTIN, MG->AssignedByManufacturer)',agency_ok,', '.join(agency_bad[:4]))
    chk('E3',"Excel-mangled '40210.25' recognised as product 40210.250",normalised)
    x12={'GA','LB','CA','BG'}&uoms
    chk('E4','Units of measure use UN/ECE Rec 20 codes (GLL, LBR), as the schema requires, not X12 codes',not x12,f'codes used: {sorted(uoms)}')
p=sum(1 for r in R if r[2])
print(json.dumps({'passed':p,'total':len(R),'checks':[dict(id=a,check=b,passed=c,detail=d) for a,b,c,d in R]},indent=1))

"""Reference mapping: builds reference/pmr.xml from the sales file.

Usage: python3 grader/reference_mapping.py data/sales_reconciliation_sep2026.csv reference
"""
import csv, sys
from xml.sax.saxutils import escape as E
src, out = sys.argv[1], sys.argv[2]
rows=list(csv.DictReader(open(src)))
AG={'9':'AGIIS-EBID','C5':'AGIIS-NAPD','91':'AssignedBySeller','92':'AssignedByBuyer'}
PAG={'UK':'GTIN','MG':'AssignedByManufacturer','UP':'Other'}
GT={'00812345000017':'40210.250','00812345000024':'51133.100'}
PACK={'40210.250':(5,'GLL'),'51133.100':(4,'GLL'),'62001.025':(25,'LBR')}
def iso(d): m,dd,y=d.split('/'); return f'{y}-{m}-{dd}T00:00:00'
def pid(r):
    p=r['ProductID'].lstrip("'")
    if r['ProductIDQualifier']=='MG': p='%.3f'%float(p)
    return p
def mcode(r): p=pid(r); return GT.get(p,p)
def pi(name,i,ag): return f'<PartnerInformation><PartnerName>{E(name)}</PartnerName><PartnerIdentifier Agency="{ag}">{i}</PartnerIdentifier></PartnerInformation>'
seen=set(); tx=[]
for r in rows:
    k=(r['InvoiceNumber'],r['LineNumber'],r['ProductID'],r['Quantity'])
    if k in seen: continue
    seen.add(k)
    q=float(r['Quantity']); c=mcode(r); per,base=PACK[c]
    bq=abs(q)*(per if r['UnitOfMeasure'] in ('CA','BG') else 1)
    st=r['SaleType']; ret=q<0
    pmt='IntraCompanyTransferOut' if st=='IB' else 'Return' if ret else 'StockSale'
    sr='Wholesale' if st=='IB' else 'EndUser'
    tx.append(f'''<ProductMovementTransaction><ProductMovementTransactionProperties ProductMovementType="{pmt}" SaleOrReturnType="{sr}">
<ReferenceInformation ReferenceType="InvoiceNumber"><DocumentReference><DocumentIdentifier>{r['InvoiceNumber']}</DocumentIdentifier></DocumentReference></ReferenceInformation>
<EventDateTime EventDateType="InvoiceDate"><DateTime DateTimeQualifier="On">{iso(r['InvoiceDate'])}</DateTime></EventDateTime>
<LanguageCode Domain="ISO-639-2T">eng</LanguageCode><CurrencyCode Domain="ISO-4217">USD</CurrencyCode></ProductMovementTransactionProperties>
<ProductMovementTransactionPartners><ShipTo>{pi(r['ShipToName'],r['ShipToID'],AG[r['ShipToIdQualifier']])}</ShipTo>
<OtherPartner PartnerRole="ShipFrom">{pi(r['WarehouseLocationName'],r['WarehouseID'],AG[r['WarehouseIDQualifier']])}</OtherPartner></ProductMovementTransactionPartners>
<ProductMovementTransactionDetails><ProductMovementProductLineItem><LineNumber>{r['LineNumber']}</LineNumber>
<ProductIdentification><ProductIdentifier Agency="{PAG[r['ProductIDQualifier']]}">{pid(r)}</ProductIdentifier><ProductName>{E(r['ProductName'])}</ProductName><ProductDescription>{E(r['PackSizeDescription'])}</ProductDescription></ProductIdentification>
<ProductQuantity><Measurement><MeasurementValue>{bq:g}</MeasurementValue><UnitOfMeasureCode Domain="UN-Rec-20">{base}</UnitOfMeasureCode></Measurement></ProductQuantity>
</ProductMovementProductLineItem></ProductMovementTransactionDetails></ProductMovementTransaction>''')
r0=rows[0]
xml=f'''<?xml version="1.0" encoding="UTF-8"?>
<ProductMovementReport xmlns="urn:cidx:names:specification:ces:schema:all:7.1" Version="7.1"><Header>
<ThisDocumentIdentifier><DocumentIdentifier>{r0['GS']}</DocumentIdentifier></ThisDocumentIdentifier>
<ThisDocumentDateTime><DateTime DateTimeQualifier="On">2026-10-02T00:00:00</DateTime></ThisDocumentDateTime>
<From>{pi(r0['SenderName'],r0['SenderID'],AG[r0['SenderID Qualifier']])}</From><To>{pi(r0['ManufacturerName'],r0['ManufacturerID'],AG[r0['ManufacturerID Qualifier']])}</To></Header>
<ProductMovementReportBody><ProductMovementReportDetails><ReportingEntity>{pi(r0['DistributorName'],r0['DistributorID'],AG[r0['DistributorID Qualifier']])}</ReportingEntity>
<ProductMovementTransactions ProductMovementReportType="SalesReport">{''.join(tx)}</ProductMovementTransactions></ProductMovementReportDetails></ProductMovementReportBody></ProductMovementReport>'''
open(f'{out}/pmr.xml','w').write(xml)

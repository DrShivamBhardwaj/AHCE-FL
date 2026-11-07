#!/usr/bin/env python3
"""Verify bibliography against Crossref/PMLR or archive URL; never invent metadata."""
import json,re,urllib.request,urllib.parse,datetime as dt,time
from pathlib import Path
from difflib import SequenceMatcher
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_P2_P3_Evidence_Revised_Blind.docx"
OUT=ROOT/"reproducibility/priority_ablations_2026_11_07/submission_audit"
OUT.mkdir(parents=True,exist_ok=True)
paragraphs=Document(DOC).paragraphs
start=next(i for i,p in enumerate(paragraphs) if p.text.strip()=="References")
end=next(i for i,p in enumerate(paragraphs) if p.text.strip()=="Figures")
entries=[p.text.strip() for p in paragraphs[start+1:end] if p.text.strip()]
results=[]
def fetch(doi):
 url='https://api.crossref.org/works/'+urllib.parse.quote(doi,safe='/')
 req=urllib.request.Request(url,headers={'User-Agent':'AHCE-FL-Reference-Audit/1.0 (scholarly verification)'})
 with urllib.request.urlopen(req,timeout=15) as h:return json.load(h)['message']
def normalize(s):return re.sub(r'[^a-z0-9]+','',s.lower())
for i,ref in enumerate(entries,1):
 doi_match=re.search(r'(?:doi:|https://doi.org/)(10\.\d{4,9}/[^\s;]+)',ref,re.I)
 doi=doi_match.group(1).rstrip('.,') if doi_match else None
 year=re.search(r'\((\d{4})\)',ref)
 quoted=re.search(r"'([^']+)'",ref)
 record={"index":i,"reference":ref,"doi":doi,"status":"unverified","issues":[]}
 try:
  if doi:
   m=fetch(doi)
   title=m.get('title',[''])[0]
   similarity=SequenceMatcher(None,normalize(quoted.group(1) if quoted else ''),normalize(title)).ratio()
   dates=(m.get('published') or m.get('issued') or {}).get('date-parts',[[None]])
   published=dates[0][0]
   authorlist=m.get('author',[])
   record.update({"source":"Crossref API","verified_title":title,"title_similarity":round(similarity,4),
                  "verified_year":published,"verified_authors":[' '.join([a.get('given',''),a.get('family','')]).strip() for a in authorlist],
                  "verified_container":(m.get('container-title') or [''])[0],
                  "verified_pages":m.get('page'),"verified_volume":m.get('volume'),"verified_issue":m.get('issue')})
   if similarity<0.83:record['issues'].append('Publication title differs from DOI metadata')
   if year and published and abs(int(year.group(1))-int(published))>1:
    record['issues'].append('Publication year differs by more than one year')
   if authorlist:
    lead=authorlist[0].get('family','')
    if normalize(lead) not in normalize(ref[:65]):record['issues'].append('First author differs')
   record['status']='verified' if not record['issues'] else 'needs_review'
  else:
   url=re.search(r'https?://[^\s)]+',ref)
   if url:
    u=url.group(0)
    req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 AHCE-FL reference audit'})
    with urllib.request.urlopen(req,timeout=15) as h:
     record['http_code']=h.status
     record['source']='Publisher/archive URL'
     record['status']='url_accessible_requires_metadata_review'
   else:
    record['issues'].append('No DOI or URL; search bibliographic metadata manually')
 except Exception as e:
  record['issues'].append('External lookup failed: '+str(e)[:180])
 results.append(record)
 print(i,record['status'],record.get('title_similarity',''),ref[:62],flush=True)
report={"timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
 "count":len(results),"verified":sum(x['status']=='verified' for x in results),
 "needs_review":[x for x in results if x['status']!='verified'],
 "entries":results,
 "note":"Crossref DOI metadata is not a full-text verification; review authors, title, pages and cited context manually before submission."}
(OUT/"REFERENCES_AUDIT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
lines=["# Independent reference audit","",
 f'Bibliography entries: **{len(results)}**; DOI metadata match without flagged issues: **{report["verified"]}**.',
 "", "| Reference | Result | Follow-up |","|---|---|---|"]
for r in results:
 lines.append(f'| {r["index"]}. {r["reference"][:65]} | {r["status"]} | {"; ".join(r["issues"]) or "No automated discrepancy"} |')
lines+=["","Review titles, author initials, journal issue and pagination manually; DOI matching alone does not certify citation relevance."]
(OUT/"REFERENCES_AUDIT.md").write_text("\n".join(lines)+"\n")

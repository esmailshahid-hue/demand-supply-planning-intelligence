import { useEffect, useRef, useState } from 'react';
import type { components } from './contracts.generated';
type Imported = components['schemas']['ImportResult'];
type Review = components['schemas']['ReviewView'];
type Capabilities = {enabled:boolean;message:string;max_file_bytes:number};

export default function DataWorkspace({onUse,onReset,onReopen,reconciliationReference}:{onUse:(data:Imported)=>void;onReset:()=>void;onReopen:(review:Review)=>void;reconciliationReference?:string|null}) {
  const [cap,setCap]=useState<Capabilities|null>(null);
  const [file,setFile]=useState<File|null>(null);
  const [consent,setConsent]=useState(false);
  const [result,setResult]=useState<Imported|null>(null);
  const [issues,setIssues]=useState<Imported['issues']>([]);
  const [error,setError]=useState('');
  const [progress,setProgress]=useState('');
  const pending=useRef<XMLHttpRequest|null>(null);
  const generation=useRef(0);
  useEffect(()=>{const c=new AbortController();fetch('/api/workflow/session',{signal:c.signal}).then(r=>r.json()).then(setCap).catch(()=>{});return()=>{c.abort();pending.current?.abort();generation.current++;};},[]);
  const choose=(next:File|null)=>{generation.current++;pending.current?.abort();setFile(next);setResult(null);setIssues([]);setError('');setProgress('');};
  const upload=(snapshot=false)=>{if(!file||!consent||!cap?.enabled)return;
    const version=++generation.current;pending.current?.abort();setResult(null);setIssues([]);setError('');
    if(file.size>cap.max_file_bytes){setError('File exceeds 16 MiB.');return;}
    const xhr=new XMLHttpRequest();pending.current=xhr;
    xhr.open('PUT',snapshot?'/api/workflow/snapshot':'/api/workflow/import');
    xhr.setRequestHeader('Content-Type',snapshot?'application/gzip':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    xhr.setRequestHeader('X-Filename',encodeURIComponent(file.name));xhr.setRequestHeader('X-Server-Processing','confirmed');
    if(reconciliationReference)xhr.setRequestHeader('X-Accepted-Ref',reconciliationReference);
    xhr.upload.onprogress=e=>{if(version===generation.current)setProgress(e.lengthComputable?`Uploading ${Math.round(e.loaded/e.total*100)}%`:'Uploading…');};
    xhr.upload.onload=()=>{if(version===generation.current)setProgress('Validating on the server…');};
    xhr.onload=()=>{if(version!==generation.current)return;setProgress('');try{const value=JSON.parse(xhr.responseText);if(xhr.status>=400){setIssues(value.issues||[]);setError(value.message||value.detail||'Import failed. Check the file.');}else if(snapshot)onReopen(value);else {setResult(value);setIssues(value.issues);}}catch{setError('The server could not validate this file. Try again.');}};
    xhr.onerror=()=>{if(version===generation.current){setProgress('');setError('Upload failed. Check the connection and retry.');}};
    setProgress('Uploading…');xhr.send(file);
  };
  const reset=async()=>{choose(null);await fetch('/api/workflow/session',{method:'DELETE'});onReset();};
  const groups=[...new Set(issues.map(i=>i.sheet))];
  return <div className="result-content"><section className="panel"><h2>Workbook inputs and accepted plans</h2>
    <p>Calculations run on the Python server. Your workbook contains operational data. Confirm server processing before uploading; this is not browser-only processing.</p>
    <p className="notice">{cap?.message||'Checking upload availability…'}</p>
    <p><a href="/api/workflow/template/blank">Download blank XLSX template</a> · <a href="/api/workflow/template/fixture">Download populated fixture XLSX</a></p>
    <p>Limits: XLSX only, 16 MiB file, 160 MiB expanded, 170,000 operational rows; 60 products, five locations, 12 suppliers, 420 history days and 56 planning days. Instructions and examples are separate from importable rows. Empty transactions require a Settings declaration.</p>
    <p>For execution reconciliation, first reopen the accepted portable snapshot, then return here and import the updated workbook with explicit Reconciliation rows. {reconciliationReference?'A supplied snapshot is available for this import.':'No accepted snapshot supplied yet.'}</p>
    <label><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>I confirm server processing of this file</label>
    <div className="panel" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();choose(e.dataTransfer.files[0]||null);}}><label>Select XLSX or portable snapshot<input type="file" accept=".xlsx,.gz" onChange={e=>choose(e.target.files?.[0]||null)} disabled={!cap?.enabled}/></label><p>Or drop a file here.</p>{file&&<p>{file.name} · {file.size.toLocaleString()} bytes</p>}</div>
    <button className="primary-button" disabled={!file||!consent||!cap?.enabled||!!progress} onClick={()=>upload(false)}>Upload workbook</button>{' '}
    <button disabled={!file||!consent||!cap?.enabled||!!progress} onClick={()=>upload(true)}>Reopen portable snapshot</button>{' '}
    <button onClick={reset}>Reset to bundled sample</button>
    {progress&&<p role="status">{progress}</p>}{error&&<p role="alert" className="error">{error}</p>}
    {groups.map(sheet=><section key={sheet}><h3>{sheet}</h3>{issues.filter(i=>i.sheet===sheet).map((i,n)=><p className={i.severity==='error'?'error':'warning-line'} key={n}>{i.severity} · {i.code} · {i.row?`row ${i.row}`:''} {i.field} · {i.guidance}</p>)}</section>)}
    {result?.reference&&result.catalog&&<section><h3>Validation passed</h3><p>{result.catalog.products.length} products · {result.catalog.locations.length} stores · {result.catalog.history_rows.toLocaleString()} observations · as-of {result.catalog.as_of}</p><p>Quality warnings remain attached to this dataset and its calculations.</p><button className="primary-button" onClick={()=>onUse(result)}>Use validated data and calculate plan</button><details><summary>Import measurements</summary><pre>{JSON.stringify(result.measurements,null,2)}</pre></details></section>}
    <h3>Units and funding</h3><p>Stock and quantities use base units. Usable stock is on-hand minus blocked minus reserved; reservations are outside this demand forecast and deducted once. Prices use SAR per base unit. Commitment caps authorize new purchases; unpaid obligations consume payment ceilings. Missing capacity or funding is never unlimited.</p>
  </section></div>;
}

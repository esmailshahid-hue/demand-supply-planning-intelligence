import { apiError, requestError, responseValue } from './errors';
import { useEffect, useRef, useState } from 'react';
import type { components } from './contracts.generated';
type Imported = components['schemas']['ImportResult'];
type Review = components['schemas']['ReviewView'];
type Capabilities = {enabled:boolean;message:string;max_file_bytes:number};

export default function DataWorkspace({onUse,onReset,onReopen,reconciliationReference}:{onUse:(data:Imported)=>void;onReset:()=>void;onReopen:(review:Review,signal:AbortSignal)=>Promise<void>;reconciliationReference?:string|null}) {
  const [cap,setCap]=useState<Capabilities|null>(null);
  const [file,setFile]=useState<File|null>(null);
  const [consent,setConsent]=useState(false);
  const [result,setResult]=useState<Imported|null>(null);
  const [issues,setIssues]=useState<Imported['issues']>([]);
  const [error,setError]=useState('');
  const [progress,setProgress]=useState('');
  const pending=useRef<XMLHttpRequest|null>(null);
  const reopening=useRef<AbortController|null>(null);
  const [capRetry,setCapRetry]=useState(0);
  const generation=useRef(0);
  useEffect(()=>{const c=new AbortController();setError('');fetch('/api/workflow/session',{signal:c.signal}).then(async r=>{const v=await responseValue(r);if(!r.ok)throw new Error(apiError(v,r.status));return v;}).then(v=>{if(!c.signal.aborted)setCap(v);}).catch(e=>{if(!c.signal.aborted)setError(requestError(e));});return()=>{c.abort();pending.current?.abort();reopening.current?.abort();generation.current++;};},[capRetry]);
  const choose=(next:File|null)=>{generation.current++;pending.current?.abort();reopening.current?.abort();setFile(next);setResult(null);setIssues([]);setError('');setProgress('');};
  const upload=(snapshot=false)=>{if(!file||!consent||!cap?.enabled||progress)return;
    const version=++generation.current;pending.current?.abort();setResult(null);setIssues([]);setError('');
    if(file.size>cap.max_file_bytes){setError('File exceeds 16 MiB.');return;}
    const xhr=new XMLHttpRequest();pending.current=xhr;
    xhr.open('PUT',snapshot?'/api/workflow/snapshot':'/api/workflow/import');
    xhr.setRequestHeader('Content-Type',snapshot?'application/gzip':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    xhr.setRequestHeader('X-Filename',encodeURIComponent(file.name));xhr.setRequestHeader('X-Server-Processing','confirmed');
    if(reconciliationReference)xhr.setRequestHeader('X-Accepted-Ref',reconciliationReference);
    xhr.upload.onprogress=e=>{if(version===generation.current)setProgress(e.lengthComputable?`Uploading ${Math.round(e.loaded/e.total*100)}%`:'Uploading…');};
    xhr.upload.onload=()=>{if(version===generation.current)setProgress('Validating on the server…');};
    xhr.onload=async()=>{if(version!==generation.current)return;
      try{const value=JSON.parse(xhr.responseText);if(xhr.status>=400){setIssues(value.issues||[]);throw new Error(apiError({...value,issues:[]},xhr.status));}
        if(snapshot){const c=new AbortController();reopening.current=c;setProgress('Opening the accepted snapshot…');await onReopen(value,c.signal);}
        else {setResult(value);setIssues(value.issues);}
      }catch(e){if(version===generation.current)setError(requestError(e));}
      finally{if(version===generation.current)setProgress('');}
    };
    xhr.onerror=()=>{if(version===generation.current){setProgress('');setError('Upload failed. Check the connection and retry.');}};
    setProgress('Uploading…');xhr.send(file);
  };
  const reset=async()=>{choose(null);const version=generation.current;setProgress('Resetting session…');try{const r=await fetch('/api/workflow/session',{method:'DELETE'});if(!r.ok&&r.status!==401)throw new Error(apiError(await responseValue(r),r.status));if(version===generation.current)onReset();}catch(e){if(version===generation.current)setError(requestError(e));}finally{if(version===generation.current)setProgress('');}};
  const groups=[...new Set(issues.map(i=>i.sheet))];
  const uploads=!!cap?.enabled;
  return <div className="result-content"><section className="panel"><h2>Your own data</h2>
    {!cap&&!error&&<p role="status">Checking upload availability…</p>}
    {!cap&&error&&<><p role="alert" className="error">{error}</p><button onClick={()=>setCapRetry(v=>v+1)}>Retry</button></>}
    {cap&&!uploads&&<><p className="notice">Uploads and exports are unavailable in this demo. The bundled samples remain available.</p>
      <p>To use your own data, <a href="https://github.com/esmailshahid-hue/demand-supply-planning-intelligence#run-locally">run the app locally</a>. The templates below still work.</p></>}
    {uploads&&<><p>Calculations run on the server, not in your browser. Your workbook contains operational data, so confirm server processing before uploading.</p>
      <p>If the session expires, import the workbook again or reopen a snapshot you downloaded. Unsaved review changes cannot be recovered after expiry or restart.</p></>}
    <p><a href="/api/workflow/template/blank">Download blank XLSX template</a> · <a href="/api/workflow/template/fixture">Download populated sample XLSX</a></p>
    {uploads&&<>
      <label><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>I confirm server processing of this file</label>
      <div className="panel" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();choose(e.dataTransfer.files[0]||null);}}><label>Select XLSX or portable snapshot<input type="file" accept=".xlsx,.gz" onChange={e=>choose(e.target.files?.[0]||null)}/></label><p>Or drop a file here.</p>{file&&<p>{file.name} · {file.size.toLocaleString()} bytes</p>}</div>
      <button className="primary-button" disabled={!file||!consent||!!progress} onClick={()=>upload(false)}>Upload workbook</button>{' '}
      <button disabled={!file||!consent||!!progress} onClick={()=>upload(true)}>Reopen portable snapshot</button>{' '}
    </>}
    <button disabled={!!progress} onClick={reset}>Reset to bundled sample</button>
    {progress&&<p role="status">{progress}</p>}{cap&&error&&<p role="alert" className="error">{error}</p>}
    {groups.map(sheet=><section key={sheet}><h3>{sheet}</h3>{issues.filter(i=>i.sheet===sheet).map((i,n)=><p className={i.severity==='error'?'error':'warning-line'} key={n}>{i.severity} · {i.code} · {i.row?`row ${i.row}`:''} {i.field} · {i.guidance}</p>)}</section>)}
    {result?.reference&&result.catalog&&<section><h3>Validation passed</h3><p>{result.catalog.products.length} products · {result.catalog.locations.length} stores · {result.catalog.history_rows.toLocaleString()} observations · planning date {result.catalog.as_of}</p><p>Quality warnings stay attached to this dataset and its calculations.</p><button className="primary-button" onClick={()=>onUse(result)}>Use validated data and calculate plan</button><details><summary>Import measurements</summary><pre>{JSON.stringify(result.measurements,null,2)}</pre></details></section>}
    <details><summary>Workbook limits and local workflow</summary>
      <p>XLSX only. Limits: 16 MiB file, 160 MiB expanded, 170,000 operational rows; 60 products, five locations, 12 suppliers, 420 history days and 56 planning days.</p>
      <p>Instructions and examples are kept separate from importable rows. Empty transactions need a Settings declaration.</p>
      <p>Locally, the full workflow is: import a workbook, review and edit actions, regenerate, accept, then download the reviewed workbook and portable snapshot.</p>
      <p>To reconcile execution, reopen the accepted portable snapshot first, then import the updated workbook with Reconciliation rows. {reconciliationReference?'A snapshot is available for this import.':'No accepted snapshot has been supplied yet.'}</p>
    </details>
    <details><summary>Units and funding</summary>
      <p>Stock and quantities use base units. Usable stock is on-hand minus blocked minus reserved; reservations sit outside this demand forecast and are deducted once.</p>
      <p>Prices use SAR per base unit. Commitment caps authorize new purchases; unpaid obligations consume payment ceilings. Missing capacity or funding is never treated as unlimited.</p>
    </details>
  </section></div>;
}

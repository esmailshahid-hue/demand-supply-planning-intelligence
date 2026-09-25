import { test, expect, type Page } from '@playwright/test';
const wait=(page:Page,path:string)=>page.waitForResponse(r=>new URL(r.url()).pathname===path&&r.ok(),{timeout:60_000});
async function run(page:Page){const pending=wait(page,'/api/scenarios/compare');await page.getByRole('button',{name:'Run scenario',exact:true}).click();const r=await(await pending).json();await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash',r.scenario_hash);expect(r.frozen.assumptions_hash).toBe(r.replanned.assumptions_hash);return r;}

test('sample action evidence, actual forecast, three presets, combined scenario and exact reset',async({page})=>{
  test.setTimeout(180_000);const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  const planning=wait(page,'/api/plan/sample');await page.goto('/');const plan=await(await planning).json();
  const nonS1=plan.proposed.evidence_targets.find((target:{location_id:string|null})=>target.location_id&&target.location_id!=='S1');expect(nonS1).toBeTruthy();
  const purchaseIndex=plan.proposed.purchases.findIndex((purchase:{action_id:string})=>purchase.action_id===nonS1.action_id);expect(purchaseIndex).toBeGreaterThanOrEqual(0);
  const purchaseRow=page.getByTestId('purchase-table').locator('tbody tr').nth(purchaseIndex);await purchaseRow.locator('summary').click();
  // The real fixture exposes 20.400000000000006; evidence must use the same
  // one-decimal quantity precision as the ledger, without changing API values.
  await expect(purchaseRow).toContainText(`${nonS1.affected_units.toLocaleString('en-GB',{maximumFractionDigits:1})} units.`);
  const inspectPurchase=purchaseRow.getByRole('button',{name:'Inspect purchase and forecast'});await expect(inspectPurchase).toHaveAttribute('data-evidence-location',nonS1.location_id);
  const detailResponse=wait(page,plan.review_id?`/api/workflow/review/${plan.review_id}/detail`:'/api/scenarios/detail');await inspectPurchase.click();const detail=await(await detailResponse).json();expect(detail.forecast.location_id).toBe(nonS1.location_id);
  await expect(page.getByRole('heading',{name:'SKU payments and grouped movement fees'})).toBeVisible();
  expect(detail.stock.length).toBe(280);expect(detail.feasible).toBe(true);
  await page.getByRole('button',{name:'Open this forecast in Demand Review'}).click();
  await expect(page.getByTestId('forecast-result')).toHaveAttribute('data-run-id',detail.forecast.run_id);
  const baselineResponse=wait(page,'/api/scenarios/capture');await page.getByRole('button',{name:/Scenarios/}).click();const base=await(await baselineResponse).json();
  await expect(page.getByRole('heading',{name:'Changes to test'})).toBeVisible();
  await page.getByRole('button',{name:'Promotion',exact:true}).click();let result=await run(page);
  expect(result.definition.uplifts).toHaveLength(1);expect(result.original.summary).toEqual(base.original.summary);
  // New controls hide the comparison and explicitly mark the draft dirty.
  await page.getByLabel('Uplift percent',{exact:true}).fill('35');await expect(page.getByText(/Controls changed —/)).toBeVisible();await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash','baseline');
  await page.getByRole('button',{name:'Reset to baseline'}).click();
  await page.getByRole('button',{name:'Supplier disruption',exact:true}).click();
  const supplier=base.supplier_options.find((option:{existing_order_ids:string[];future_paths:boolean})=>option.existing_order_ids.length&&option.future_paths);expect(supplier).toBeTruthy();
  await expect(page.getByTestId('supplier-preset-summary')).toContainText(`${supplier.supplier_id} · ${supplier.name}`);
  await expect(page.getByLabel('Delayed supplier')).toHaveValue(supplier.supplier_id);await expect(page.getByLabel('Capacity supplier')).toHaveValue(supplier.supplier_id);
  const alternate=base.suppliers.find((id:string)=>id!==supplier.supplier_id);await page.getByLabel('Capacity supplier').selectOption(alternate);await expect(page.getByLabel('Delayed supplier')).toHaveValue(supplier.supplier_id);await page.getByLabel('Capacity supplier').selectOption(supplier.supplier_id);
  result=await run(page);expect(result.definition.delays[0].supplier_id).toBe(supplier.supplier_id);expect(result.definition.availability[0].supplier_id).toBe(supplier.supplier_id);
  expect(result.definition.delays.length).toBeGreaterThan(0);expect(result.frozen.feasible).toBe(false);expect(result.frozen.summary).toBeNull();
  expect(Object.values(result.shock_delta)).toEqual(expect.arrayContaining([null]));expect(Object.values(result.replan_delta)).toEqual(expect.arrayContaining([null]));expect(Object.values(result.net_delta).every((v:unknown)=>typeof v==='number')).toBe(true);
  await expect(page.getByTestId('frozen-invalid-reason')).toContainText(/The original actions are invalid on 2026-/);
  await page.getByText(/Hard-constraint failures ·/).click();await expect(page.getByText(/supplier_capacity/).first()).toBeVisible();
  await page.getByRole('button',{name:'Reset to baseline'}).click();await page.getByRole('button',{name:'Tighter funds',exact:true}).click();await page.getByRole('button',{name:'Tighter funds',exact:true}).click();result=await run(page);expect(result.frozen.feasible).toBe(false);expect(result.replanned.feasible).toBe(true);
  expect(result.definition.funding).toHaveLength(2);expect(result.definition.funding.map((f:{commitment:number})=>f.commitment)).toEqual(base.weeks.slice(0,2).map((w:{commitment:number})=>Math.round(w.commitment*.3*100)/100));expect(result.definition.funding.every((f:{payment:number|null})=>f.payment===null)).toBe(true);
  await page.getByRole('button',{name:'Promotion',exact:true}).click();await page.getByRole('button',{name:'Supplier disruption',exact:true}).click();result=await run(page);
  expect(result.definition.funding.length).toBeGreaterThan(0);expect(result.definition.uplifts.length).toBeGreaterThan(0);expect(result.replanned.feasible).toBe(true);
  await page.getByText('Purchases and movements · Replanned',{exact:true}).click();
  const replannedTarget=result.replanned.evidence_targets.find((target:{location_id:string|null})=>target.location_id);const replannedMovement=result.replanned.movements[0];
  const replannedAction=replannedTarget?.action_id||replannedMovement?.action_id;const replannedLocation=replannedTarget?.location_id||replannedMovement?.destination;expect(replannedAction).toBeTruthy();expect(replannedLocation).toBeTruthy();
  const replannedRow=page.getByRole('row').filter({hasText:replannedAction});const replannedButton=replannedRow.getByRole('button',{name:'Inspect action'});await expect(replannedButton).toHaveAttribute('data-evidence-location',replannedLocation);
  const scoped=wait(page,'/api/scenarios/detail');await replannedButton.click();const d=await(await scoped).json();expect(d.policy).toBe('replanned');expect(d.forecast.location_id).toBe(replannedLocation);expect(d.assumptions_hash).toBe(result.scenario_hash);expect(d.cash).toEqual(result.replanned.cash);
  await page.getByRole('button',{name:'Close evidence'}).click();expect(result.frozen.evidence_targets).toEqual([]);
  await page.getByRole('button',{name:'Reset to baseline'}).click();await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash','baseline');await expect(page.getByText('Original baseline restored.',{exact:false})).toBeVisible();
  const noop=await run(page);expect(noop.frozen.summary).toEqual(base.original.summary);expect(noop.replanned.summary).toEqual(base.original.summary);expect(Object.values(noop.net_delta).every(v=>v===0)).toBe(true);
  await page.getByText('Purchases and movements · Same actions',{exact:true}).click();const noopFrozenTarget=noop.frozen.evidence_targets.find((target:{location_id:string|null})=>target.location_id);expect(noopFrozenTarget).toBeTruthy();
  const noopFrozenButton=page.getByRole('row').filter({hasText:noopFrozenTarget.action_id}).getByRole('button',{name:'Inspect action'}).first();const noopFrozenDetail=wait(page,'/api/scenarios/detail');await noopFrozenButton.click();const noopFrozen=await(await noopFrozenDetail).json();expect(noopFrozen.policy).toBe('frozen');expect(noopFrozen.forecast.location_id).toBe(noopFrozenTarget.location_id);
  expect(errors).toEqual([]);
});

test('draft and dataset changes prevent an in-flight response overwriting the current selection',async({page})=>{
  test.setTimeout(100_000);await page.goto('/');
  const baseline=wait(page,'/api/scenarios/baseline');await page.getByRole('button',{name:/Scenarios/}).click();await baseline;
  await page.getByRole('button',{name:'Promotion',exact:true}).click();
  let release!:()=>void;const gate=new Promise<void>(resolve=>release=resolve);let fetched!:()=>void;const arrived=new Promise<void>(resolve=>fetched=resolve);
  await page.route('**/api/scenarios/compare',async route=>{const response=await route.fetch();fetched();await gate;try{await route.fulfill({response});}catch{/* Browser cancelled the obsolete response. */}});
  await page.getByRole('button',{name:'Run scenario'}).click();await arrived;
  await page.getByLabel('Uplift percent',{exact:true}).fill('45');release();
  await expect(page.getByText(/Controls changed —/)).toBeVisible();await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash','baseline');
  await page.unroute('**/api/scenarios/compare');
  let releaseSecond!:()=>void;const secondGate=new Promise<void>(resolve=>releaseSecond=resolve);let fetchedSecond!:()=>void;const secondArrived=new Promise<void>(resolve=>fetchedSecond=resolve);
  await page.route('**/api/scenarios/compare',async route=>{const response=await route.fetch();fetchedSecond();await secondGate;try{await route.fulfill({response});}catch{}});
  await page.getByRole('button',{name:'Run scenario'}).click();await secondArrived;
  const full=wait(page,'/api/scenarios/baseline');await page.getByLabel('Scenario dataset').selectOption('full');releaseSecond();const fullBase=await(await full).json();
  expect(fullBase.baseline.size).toBe('full');await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash','baseline');await expect(page.getByLabel('Uplift percent',{exact:true})).toHaveCount(0);
});

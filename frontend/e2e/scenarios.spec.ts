import { test, expect, type Page } from '@playwright/test';
const wait=(page:Page,path:string)=>page.waitForResponse(r=>new URL(r.url()).pathname===path&&r.ok(),{timeout:60_000});
async function run(page:Page){const pending=wait(page,'/api/scenarios/compare');await page.getByRole('button',{name:'Run scenario live',exact:true}).click();const r=await(await pending).json();await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash',r.scenario_hash);expect(r.frozen.assumptions_hash).toBe(r.replanned.assumptions_hash);return r;}

test('sample action evidence, actual forecast, three presets, combined scenario and exact reset',async({page})=>{
  test.setTimeout(180_000);const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');await expect(page.getByTestId('forecast-result')).toBeVisible();
  const planning=wait(page,'/api/plan/sample');await page.getByRole('button',{name:/Plan Review/}).click();await planning;
  await page.getByTestId('purchase-table').locator('summary').first().click();
  const detailResponse=wait(page,'/api/scenarios/detail');await page.getByRole('button',{name:'Inspect purchase and forecast'}).first().click();const detail=await(await detailResponse).json();
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
  await page.getByRole('button',{name:'Supplier disruption',exact:true}).click();result=await run(page);
  expect(result.definition.delays.length).toBeGreaterThan(0);expect(result.frozen.feasible).toBe(false);expect(result.frozen.summary).toBeNull();
  await expect(page.getByText(/supplier_capacity/).first()).toBeVisible();
  await page.getByRole('button',{name:'Reset to baseline'}).click();await page.getByRole('button',{name:'Tighter funds',exact:true}).click();result=await run(page);expect(result.frozen.feasible).toBe(false);expect(result.replanned.feasible).toBe(true);
  await page.getByRole('button',{name:'Promotion',exact:true}).click();await page.getByRole('button',{name:'Supplier disruption',exact:true}).click();result=await run(page);
  expect(result.definition.funding.length).toBeGreaterThan(0);expect(result.definition.uplifts.length).toBeGreaterThan(0);expect(result.replanned.feasible).toBe(true);
  await page.getByText('Purchases, movements and forecast inspection · replanned',{exact:true}).click();
  const scoped=wait(page,'/api/scenarios/detail');await page.getByRole('button',{name:'Inspect action',exact:true}).last().click();const d=await(await scoped).json();expect(d.assumptions_hash).toBe(result.scenario_hash);expect(d.cash).toEqual(result.replanned.cash);
  await page.getByRole('button',{name:'Reset to baseline'}).click();await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash','baseline');await expect(page.getByText('Original baseline restored.',{exact:false})).toBeVisible();
  const noop=await run(page);expect(noop.frozen.summary).toEqual(base.original.summary);expect(noop.replanned.summary).toEqual(base.original.summary);
  expect(errors).toEqual([]);
});

test('draft and dataset changes prevent an in-flight response overwriting the current selection',async({page})=>{
  test.setTimeout(100_000);await page.goto('/');await expect(page.getByTestId('forecast-result')).toBeVisible();
  const baseline=wait(page,'/api/scenarios/baseline');await page.getByRole('button',{name:/Scenarios/}).click();await baseline;
  await page.getByRole('button',{name:'Promotion',exact:true}).click();
  let release!:()=>void;const gate=new Promise<void>(resolve=>release=resolve);let fetched!:()=>void;const arrived=new Promise<void>(resolve=>fetched=resolve);
  await page.route('**/api/scenarios/compare',async route=>{const response=await route.fetch();fetched();await gate;try{await route.fulfill({response});}catch{/* Browser cancelled the obsolete response. */}});
  await page.getByRole('button',{name:'Run scenario live'}).click();await arrived;
  await page.getByLabel('Uplift percent',{exact:true}).fill('45');release();
  await expect(page.getByText(/Controls changed —/)).toBeVisible();await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash','baseline');
  await page.unroute('**/api/scenarios/compare');
  let releaseSecond!:()=>void;const secondGate=new Promise<void>(resolve=>releaseSecond=resolve);let fetchedSecond!:()=>void;const secondArrived=new Promise<void>(resolve=>fetchedSecond=resolve);
  await page.route('**/api/scenarios/compare',async route=>{const response=await route.fetch();fetchedSecond();await secondGate;try{await route.fulfill({response});}catch{}});
  await page.getByRole('button',{name:'Run scenario live'}).click();await secondArrived;
  const full=wait(page,'/api/scenarios/baseline');await page.getByLabel('Scenario dataset').selectOption('full');releaseSecond();const fullBase=await(await full).json();
  expect(fullBase.baseline.size).toBe('full');await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash','baseline');await expect(page.getByLabel('Uplift percent',{exact:true})).toHaveCount(0);
});

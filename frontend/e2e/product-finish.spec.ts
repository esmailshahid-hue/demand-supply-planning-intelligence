import {test,expect,type Page} from '@playwright/test';
const wait=(page:Page,path:string)=>page.waitForResponse(r=>new URL(r.url()).pathname.endsWith(path)&&r.ok(),{timeout:60_000});
const fit=async(page:Page)=>expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);

test('mobile keyboard evidence, stale review and blocked acceptance recover without losing provenance',async({page})=>{
  test.setTimeout(120_000);await page.setViewportSize({width:390,height:844});
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>console.log('Request failure:',r.method(),r.url(),r.failure()?.errorText));
  const planResponse=wait(page,'/api/plan/sample');await page.goto('/');const plan=await(await planResponse).json();
  for(const name of ['Plan Review','Demand Review','Scenarios','Data and Assumptions'])await expect(page.getByRole('button',{name,exact:true})).toBeInViewport();
  await fit(page);
  const nav=page.getByRole('button',{name:'Plan Review',exact:true});await nav.focus();await page.keyboard.press('Enter');
  await expect(page.locator('.as-of')).toContainText(plan.as_of);await expect(page.locator('.as-of')).toBeVisible();
  const row=page.getByTestId('purchase-table').locator('tbody tr').first();await row.locator('summary').focus();await page.keyboard.press('Enter');
  const opener=row.getByRole('button',{name:'Inspect purchase and forecast'});await opener.focus();await page.keyboard.press('Enter');
  const evidence=page.getByTestId('action-evidence');await expect(evidence).toBeFocused();await expect(evidence.getByRole('heading',{name:'SKU payments and grouped movement fees'})).toBeVisible();
  await fit(page);await page.keyboard.press('Escape');await expect(evidence).toHaveCount(0);await expect(opener).toBeFocused();
  const scroll=page.getByTestId('purchase-table').locator('..');await scroll.focus();await page.keyboard.press('ArrowRight');await expect.poll(()=>scroll.evaluate(e=>e.scrollLeft)).toBeGreaterThan(0);
  const controls=page.getByRole('region',{name:'Reviewed actions'});
  await controls.getByRole('button',{name:'Accept action',exact:true}).focus();await page.keyboard.press('Enter');
  await expect(page.getByRole('heading',{name:'Previous calculation — review changes are not applied'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Test disruptions with this baseline'})).toBeDisabled();
  await expect(controls.getByRole('button',{name:'Download reviewed workbook'})).toBeDisabled();
  const regen=wait(page,'/regenerate');await controls.getByRole('button',{name:'Regenerate reviewed plan'}).click();const review=await(await regen).json();expect(review.provenance).toEqual(plan.provenance);
  await expect(controls.getByRole('button',{name:'Finally accept plan'})).toBeEnabled();
  await controls.getByRole('button',{name:'Finally accept plan'}).click();await expect(controls.getByRole('alert')).toContainText('shortfall_acknowledgement');
  await expect(controls.getByRole('link',{name:'Download reviewed workbook'})).toHaveCount(0);
  await page.route('**/api/workflow/review/*/accept',r=>r.fulfill({status:409,json:{message:'Resolve review conflict.',failures:[{code:'stale_provenance',message:'Regenerate against the current dataset before final acceptance.'}]}}));
  await controls.getByLabel('I acknowledge the displayed remaining service and buffer shortfalls').check();await controls.getByRole('button',{name:'Finally accept plan'}).click();await expect(controls.getByRole('alert')).toContainText('stale_provenance');
  await expect(controls.getByRole('link',{name:'Download portable snapshot'})).toHaveCount(0);
  await page.unroute('**/api/workflow/review/*/accept');const acceptance=wait(page,'/accept');await controls.getByRole('button',{name:'Finally accept plan'}).click();const accepted=await(await acceptance).json();expect(accepted.provenance).toEqual(plan.provenance);
  await expect(controls.getByRole('link',{name:'Download reviewed workbook'})).toBeVisible();await fit(page);
  await page.screenshot({path:'../artifacts/pass5-mobile-review.png',fullPage:true});expect(errors).toEqual([]);
});

test('structured calculation failures, expired references and network failures permit honest retry',async({page})=>{
  await page.route('**/api/plan/sample',r=>r.fulfill({status:503,json:{code:'runtime_budget',message:'Calculation exceeded its runtime budget. No partial plan is available.'}}));
  test.setTimeout(90_000);await page.goto('/');await expect(page.getByRole('alert')).toContainText('runtime_budget');await expect(page.getByTestId('plan-result')).toHaveCount(0);
  for(const error of [
    {status:503,json:{code:'solver_execution',message:'Solver execution failed. Retry calculation.'}},
    {status:422,json:{detail:[{loc:['body','funding'],msg:'Payment ceiling is required.'}]}},
    {status:404,json:{message:'Object is unavailable or expired in this session.'}},
  ]){
    await page.unroute('**/api/plan/sample');await page.route('**/api/plan/sample',r=>r.fulfill(error));await page.getByRole('button',{name:'Retry plan'}).click();await expect(page.getByRole('alert')).toContainText(error.json.message||'Payment ceiling is required.');await expect(page.getByTestId('plan-result')).toHaveCount(0);
  }
  await expect(page.getByRole('alert')).toContainText('Data and Assumptions');
  await page.unroute('**/api/plan/sample');await page.route('**/api/plan/sample',r=>r.abort('failed'));await page.getByRole('button',{name:'Retry plan'}).click();await expect(page.getByRole('alert')).toContainText('Network request failed');
  await page.unroute('**/api/plan/sample');let attempts=0;await page.route('**/api/plan/sample',r=>{if(attempts++===0)return r.fulfill({status:429,headers:{'Retry-After':'1'},json:{message:'Calculation running.'}});return r.continue();});
  const success=wait(page,'/api/plan/sample');await page.getByRole('button',{name:'Retry plan'}).click();await success;await expect(page.getByTestId('plan-result')).toBeVisible();expect(attempts).toBe(2);
});

for(const width of [1440,768,390])test(`layout and live scenarios at ${width}px retain context and local table scrolling`,async({page})=>{
  test.setTimeout(90_000);await page.setViewportSize({width,height:1000});const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
  await page.route('**/api/sample?*',async route=>{const response=await route.fetch();const data=await response.json();data.products[0].name='Long product description for a regional wholesale and retail assortment '.repeat(4);data.locations[0].name='Long store and district description '.repeat(6);await route.fulfill({json:data});});
  const initialPlan=wait(page,'/api/plan/sample');await page.goto('/');await initialPlan;await page.getByRole('button',{name:'Demand Review',exact:true}).click();await expect(page.getByTestId('forecast-result')).toBeVisible();await fit(page);
  for(const label of ['Dataset','Product','Store']){const bounds=await page.getByRole('combobox',{name:label,exact:true}).boundingBox();expect(bounds!.width).toBeGreaterThan(140);}
  await page.screenshot({path:`../artifacts/pass5-demand-${width}.png`});
  const baseline=wait(page,'/api/scenarios/capture');await page.getByRole('button',{name:'Scenarios',exact:true}).click();await baseline;
  await page.getByRole('button',{name:'Promotion',exact:true}).click();await page.getByRole('button',{name:'Add delay',exact:true}).click();await page.getByRole('button',{name:'Add availability reduction',exact:true}).click();await page.getByRole('button',{name:'Add funding week',exact:true}).click();await fit(page);
  await page.screenshot({path:`../artifacts/pass5-scenarios-${width}.png`,fullPage:true});
  await page.getByRole('button',{name:'Reset to baseline'}).click();await page.getByRole('button',{name:'Promotion',exact:true}).click();const compare=wait(page,'/api/scenarios/compare');await page.getByRole('button',{name:'Run scenario live',exact:true}).click();const result=await(await compare).json();expect(result.frozen.assumptions_hash).toBe(result.replanned.assumptions_hash);await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash',result.scenario_hash);await fit(page);
  await page.getByRole('button',{name:'Data and Assumptions',exact:true}).click();await expect(page.getByLabel('Select XLSX or portable snapshot')).toBeEnabled();await fit(page);await page.screenshot({path:`../artifacts/pass5-data-${width}.png`,fullPage:true});expect(errors).toEqual([]);
});

test('failed regenerated-result delivery stays stale until explicit reload succeeds',async({page})=>{
  test.setTimeout(90_000);const calculation=wait(page,'/api/plan/sample');await page.goto('/');const previous=await(await calculation).json();const rejected=previous.proposed.purchases[0];
  const controls=page.getByRole('region',{name:'Reviewed actions'});await controls.getByRole('button',{name:'Reject action',exact:true}).click();
  await expect(controls.getByRole('button',{name:'Finally accept plan'})).toBeDisabled();
  let calls=0;await page.route('**/api/workflow/review/*/plan',r=>{calls++;return r.fulfill({status:503,json:{message:'Result delivery failed. Retry loading the saved calculation.'}});});
  let release!:()=>void;const gate=new Promise<void>(resolve=>release=resolve);let arrived!:()=>void;const pendingMutation=new Promise<void>(resolve=>arrived=resolve);await page.route('**/api/workflow/review/*/regenerate',async route=>{const response=await route.fetch();arrived();await gate;await route.fulfill({response});});
  const regeneration=wait(page,'/regenerate');await controls.getByRole('button',{name:'Regenerate reviewed plan'}).click();await pendingMutation;for(const name of ['Demand Review','Scenarios','Data and Assumptions','Test disruptions with this baseline'])await expect(page.getByRole('button',{name,exact:true})).toBeDisabled();release();const savedReview=await(await regeneration).json();await page.unroute('**/api/workflow/review/*/regenerate');
  await expect(controls.getByRole('alert')).toContainText('Result delivery failed');expect(calls).toBe(1);
  await expect(page.getByRole('heading',{name:'Previous calculation — review changes are not applied'})).toBeVisible();
  for(const name of ['Accept action','Finally accept plan','Regenerate reviewed plan','Download reviewed workbook'])await expect(controls.getByRole('button',{name,exact:true})).toBeDisabled();
  await expect(page.getByRole('button',{name:'Scenarios',exact:true})).toBeDisabled();await page.getByRole('button',{name:'Demand Review',exact:true}).click();await page.getByRole('button',{name:'Plan Review',exact:true}).click();await expect(controls.getByRole('button',{name:'Load regenerated result'})).toBeVisible();await expect(page.getByRole('heading',{name:'Previous calculation — review changes are not applied'})).toBeVisible();
  await page.unroute('**/api/workflow/review/*/plan');const result=wait(page,'/plan');await controls.getByRole('button',{name:'Load regenerated result'}).click();const plan=await(await result).json();expect(plan.proposed.replay.feasible).toBe(true);expect(plan.review_id).toBe(savedReview.reference);expect(plan.provenance).toEqual(savedReview.provenance);expect(plan.proposed.purchases.some((p:{action_id:string})=>p.action_id===rejected.action_id)).toBe(false);
  await expect(controls.getByRole('button',{name:'Finally accept plan'})).toBeEnabled();await expect(controls.getByRole('alert')).toHaveCount(0);await expect(controls.getByRole('button',{name:'Load regenerated result'})).toHaveCount(0);expect(calls).toBe(1);
});

test('unavailable private storage keeps the public sample usable and uploads disabled',async({page})=>{
  await page.route('**/api/workflow/session',r=>r.fulfill({json:{enabled:false,message:'Hosted uploads are disabled until private object storage is configured.',max_file_bytes:16777216}}));
  await page.goto('/');await expect(page.getByTestId('plan-result')).toBeVisible();await expect(page.getByRole('region',{name:'Reviewed actions'})).toHaveCount(0);await page.getByRole('button',{name:'Data and Assumptions',exact:true}).click();
  await expect(page.getByText('Hosted uploads are disabled until private object storage is configured.')).toBeVisible();
  await expect(page.getByLabel('Select XLSX or portable snapshot')).toBeDisabled();await expect(page.getByRole('button',{name:'Upload workbook',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Demand Review',exact:true}).click();await expect(page.getByTestId('forecast-result')).toBeVisible();
});

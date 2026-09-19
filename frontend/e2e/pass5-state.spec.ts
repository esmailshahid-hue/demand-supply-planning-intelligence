import {test,expect,type Page} from '@playwright/test';

const wait=(page:Page,path:string)=>page.waitForResponse(r=>new URL(r.url()).pathname.endsWith(path)&&r.ok(),{timeout:60_000});

test('reviewed full-sample actions and provenance are the captured scenario baseline',async({page})=>{
  test.setTimeout(180_000);await page.goto('/');await expect(page.getByTestId('forecast-result')).toBeVisible();
  const fixturePlan=wait(page,'/api/plan/sample');await page.getByRole('button',{name:'Plan Review',exact:true}).click();await fixturePlan;
  const fullPlanResponse=wait(page,'/api/plan/sample');await page.getByLabel('Planning dataset').selectOption('full');const original=await(await fullPlanResponse).json();expect(original.provenance.sample_size).toBe('full');
  const controls=page.getByRole('region',{name:'Reviewed actions'});await expect(controls.getByRole('button',{name:'Apply quantity edit',exact:true})).toBeEnabled({timeout:15_000});const edited=original.proposed.purchases.find((p:{units:number})=>p.units>10);expect(edited).toBeTruthy();
  await controls.getByLabel('Action to review').selectOption(edited.action_id);await controls.getByLabel('Reviewed quantity').fill(String(edited.units-10));await controls.getByRole('button',{name:'Apply quantity edit',exact:true}).click();await expect(page.getByRole('button',{name:'Test disruptions with this baseline'})).toBeDisabled();await expect(page.getByRole('button',{name:'Scenarios',exact:true})).toBeDisabled();
  const regeneratedResponse=wait(page,'/regenerate');await controls.getByRole('button',{name:'Regenerate reviewed plan'}).click();const review=await(await regeneratedResponse).json();expect(review.failures).toEqual([]);expect(review.state).toBe('draft');await expect(controls.getByRole('button',{name:'Finally accept plan'})).toBeEnabled({timeout:15_000});
  const saved=await(await page.request.get(`/api/workflow/review/${review.reference}/plan`)).json();expect(saved.provenance.sample_size).toBe('full');expect(saved.proposed.purchases).not.toEqual(original.proposed.purchases);
  const captureRequest=page.waitForRequest(r=>new URL(r.url()).pathname==='/api/scenarios/capture');const captureResponse=wait(page,'/api/scenarios/capture');await page.getByRole('button',{name:'Test disruptions with this baseline'}).click();const payload=(await captureRequest).postDataJSON();const baseline=await(await captureResponse).json();
  expect(payload.size).toBe('full');expect(payload.dataset_hash).toBe(saved.input_hash);expect(payload.purchases).toEqual(saved.proposed.purchases);expect(payload.movements).toEqual(saved.proposed.movements);
  expect(baseline.baseline.size).toBe('full');expect(baseline.baseline.provenance).toEqual(saved.provenance);expect(baseline.original.purchases).toEqual(saved.proposed.purchases);expect(baseline.original.movements).toEqual(saved.proposed.movements);
});

test('scenario-derived reviewed plans cannot silently become a second baseline',async({page})=>{
  test.setTimeout(180_000);await page.goto('/');await expect(page.getByTestId('forecast-result')).toBeVisible();
  const planning=wait(page,'/api/plan/sample');await page.getByRole('button',{name:'Plan Review',exact:true}).click();const original=await(await planning).json();await expect(page.getByRole('button',{name:'Test disruptions with this baseline'})).toBeEnabled({timeout:15_000});
  const firstCaptureRequest=page.waitForRequest(r=>new URL(r.url()).pathname==='/api/scenarios/capture');const firstCapture=wait(page,'/api/scenarios/capture');await page.getByRole('button',{name:'Test disruptions with this baseline'}).click();const originalPayload=(await firstCaptureRequest).postDataJSON();await firstCapture;
  await page.getByRole('button',{name:'Promotion',exact:true}).click();const comparison=wait(page,'/api/scenarios/compare');await page.getByRole('button',{name:'Run scenario live',exact:true}).click();await comparison;
  const scenarioPlan=wait(page,'/api/workflow/scenario');await page.getByRole('button',{name:'Review replanned actions'}).click();await scenarioPlan;
  await expect(page.getByText('This reviewed plan already includes scenario assumptions.')).toBeVisible();await expect(page.getByRole('button',{name:'Test disruptions with this baseline'})).toHaveCount(0);await expect(page.getByRole('button',{name:'Scenarios',exact:true})).toBeDisabled();
  const restoredCaptureRequest=page.waitForRequest(r=>new URL(r.url()).pathname==='/api/scenarios/capture');const restoredCapture=wait(page,'/api/scenarios/capture');await page.getByRole('button',{name:'Return to original scenario baseline'}).click();const restoredPayload=(await restoredCaptureRequest).postDataJSON();const restored=await(await restoredCapture).json();expect(restoredPayload).toEqual(originalPayload);expect(restored.original.purchases).toEqual(original.proposed.purchases);expect(restored.original.movements).toEqual(original.proposed.movements);
});

test('dataset reset prevents a late regenerated result from restoring abandoned state',async({page})=>{
  test.setTimeout(150_000);await page.goto('/');await expect(page.getByTestId('forecast-result')).toBeVisible();
  const firstPlan=wait(page,'/api/plan/sample');await page.getByRole('button',{name:'Plan Review',exact:true}).click();const oldPlan=await(await firstPlan).json();const controls=page.getByRole('region',{name:'Reviewed actions'});await controls.getByRole('button',{name:'Reject action',exact:true}).click();
  let release!:()=>void;const gate=new Promise<void>(resolve=>release=resolve);let arrived!:()=>void;const delivered=new Promise<void>(resolve=>arrived=resolve);await page.route('**/api/workflow/review/*/plan',async route=>{const response=await route.fetch();arrived();await gate;try{await route.fulfill({response});}catch{/* Reset aborts this obsolete browser delivery. */}});
  await controls.getByRole('button',{name:'Regenerate reviewed plan'}).click();await delivered;await page.getByRole('button',{name:'Data and Assumptions',exact:true}).click();const reset=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/workflow/session'&&r.request().method()==='DELETE'&&r.ok());await page.getByRole('button',{name:'Reset to bundled sample'}).click();await reset;release();
  await expect(page.getByTestId('forecast-result')).toBeVisible();await page.unroute('**/api/workflow/review/*/plan');const freshResponse=wait(page,'/api/plan/sample');await page.getByRole('button',{name:'Plan Review',exact:true}).click();const fresh=await(await freshResponse).json();expect(fresh.run_id).not.toBe(oldPlan.run_id);await expect(page.getByTestId('plan-result')).toHaveAttribute('data-run-id',fresh.run_id);await expect(controls.getByRole('button',{name:'Load regenerated result'})).toHaveCount(0);
});

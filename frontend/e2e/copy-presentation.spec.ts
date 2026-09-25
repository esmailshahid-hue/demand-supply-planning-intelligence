import {test,expect,type Page} from '@playwright/test';

const wait=(page:Page,path:string)=>page.waitForResponse(r=>new URL(r.url()).pathname===path&&r.ok(),{timeout:60_000});
const disabledUploads=(page:Page)=>page.route('**/api/workflow/session',r=>r.fulfill({json:{
  enabled:false,message:'Uploads, review files and exports are unavailable here. The bundled samples remain available.',max_file_bytes:16777216}}));

test('hosted uploads hide their controls while the limitation and templates stay visible',async({page})=>{
  await disabledUploads(page);
  await page.goto('/');
  await page.getByRole('button',{name:'Data and Assumptions',exact:true}).click();
  // The limitation must remain stated, not merely implied by missing controls.
  await expect(page.getByText('Uploads and exports are unavailable in this demo.',{exact:false})).toBeVisible();
  for(const name of ['Upload workbook','Reopen portable snapshot'])
    await expect(page.getByRole('button',{name,exact:true})).toHaveCount(0);
  await expect(page.getByLabel('Select XLSX or portable snapshot')).toHaveCount(0);
  await expect(page.getByLabel('I confirm server processing of this file')).toHaveCount(0);
  // Templates and the sample reset used by navigation stay available.
  await expect(page.getByRole('link',{name:'Download blank XLSX template'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Reset to bundled sample',exact:true})).toBeEnabled();
  await expect(page.getByRole('link',{name:'run the app locally'})).toBeVisible();
});

test('local uploads keep consent and the file picker working',async({page})=>{
  await page.goto('/');
  await page.getByRole('button',{name:'Data and Assumptions',exact:true}).click();
  const consent=page.getByLabel('I confirm server processing of this file');
  await expect(consent).toBeVisible();
  await expect(page.getByLabel('Select XLSX or portable snapshot')).toBeEnabled();
  // Consent still gates the upload action.
  await expect(page.getByRole('button',{name:'Upload workbook',exact:true})).toBeDisabled();
  await consent.check();
  await expect(consent).toBeChecked();
});

test('plan evidence disclosures stay keyboard accessible after the copy pass',async({page})=>{
  test.setTimeout(90_000);
  const planning=wait(page,'/api/plan/sample');await page.goto('/');await planning;
  const definitions=page.getByRole('group').filter({has:page.getByText('Metric definitions',{exact:true})}).first();
  const summary=definitions.locator('summary');
  await summary.focus();await page.keyboard.press('Enter');
  await expect(definitions).toHaveAttribute('open','');
  await expect(definitions).toContainText('modeled exposure, not proven lost revenue');
  const details=page.getByRole('group').filter({has:page.getByText('Calculation details',{exact:true})}).first();
  await details.locator('summary').focus();await page.keyboard.press('Enter');
  await expect(details).toHaveAttribute('open','');
  await expect(details).toContainText('Solver stages');
});

test('an invalid plan is never given a checked label',async({page})=>{
  await page.route('**/api/plan/sample',route=>route.fulfill({json:{
    run_id:'invalid-copy',input_hash:'invalid-copy',as_of:'2026-09-14',status:'invalid_inputs',
    proposed:null,forecasts:[],stages:[],issues:[],
    failures:[{code:'missing_snapshot',message:'Explicit stock snapshots required.'}],
  }}));
  await page.goto('/');
  await expect(page.getByText('Not executable',{exact:true})).toBeVisible();
  await expect(page.getByText('Plan checked',{exact:true})).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'Resolve planning failures before using recommendations'})).toBeVisible();
});

test('unavailable scenario comparisons stay labelled instead of reading as zero',async({page})=>{
  test.setTimeout(150_000);
  await page.goto('/');
  const baseline=wait(page,'/api/scenarios/baseline');
  await page.getByRole('button',{name:'Scenarios',exact:true}).click();await baseline;
  await page.getByRole('button',{name:'Supplier disruption',exact:true}).click();
  const compare=wait(page,'/api/scenarios/compare');
  await page.getByRole('button',{name:'Run scenario',exact:true}).click();
  const result=await(await compare).json();
  expect(result.frozen.feasible).toBe(false);
  // The invalid plan keeps its own reason and its deltas stay unavailable, not 0.
  const reason=page.getByTestId('frozen-invalid-reason');
  await expect(reason).toContainText('cannot be executed');
  await expect(page.getByText('they stay unavailable rather than zero',{exact:false})).toBeVisible();
  const row=page.getByRole('row').filter({hasText:'Same actions'}).first();
  await expect(row).toContainText('Infeasible');
  await expect(row).toContainText('Unavailable');
});

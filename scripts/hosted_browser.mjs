// Explicit URL only. Read-only sample calculations; never deployment or own-data upload.
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
const require = createRequire(import.meta.url);
const { chromium, expect } = require('../frontend/node_modules/@playwright/test');
const url = process.argv[2];
if (!url) throw new Error('Usage: node scripts/hosted_browser.mjs https://existing-host');
const output = process.argv[3] || 'artifacts'; await mkdir(output, { recursive: true });
const browser = await chromium.launch({headless:true,...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});
const page = await browser.newPage({viewport:{width:1440,height:1000}});
const errors = [], requests = [], steps = [];
let passed = false;
let deployment = null;
const bounded = value => value.replace(/(token|secret|password|authorization|cookie)[\s"':=]+[^\s,;}<]+/gi, '$1=[redacted]').replace(/[A-Za-z0-9_./+=-]{40,}/g, '[redacted]').replace(/\s+/g, ' ').slice(0,240);
page.on('pageerror', e => errors.push(bounded(e.message)));
page.on('console', m => {if (m.type()==='error') errors.push(bounded(m.text()));});
page.on('response', r => {if(new URL(r.url()).pathname.startsWith('/api/')) requests.push({url:r.url(),status:r.status()});});
const response = path => page.waitForResponse(r=>new URL(r.url()).pathname===path&&r.ok(),{timeout:60_000});
const actResponse = async (path, action) => (await Promise.all([response(path),action()]))[0];
async function layout(name) {
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:`${output}/pass6-hosted-${name}.png`});
  steps.push(name); console.log(name);
}
try {
  const identityResponse = await page.request.get(`${url}/release.json`);
  expect(identityResponse.ok()).toBe(true);
  const identity = await identityResponse.json();
  if (process.env.GITHUB_SHA) {
    expect(identity.commit).toBe(process.env.GITHUB_SHA);
    const probe = JSON.parse(await readFile(`${output}/results.json`, 'utf8'));
    expect(identity).toEqual(probe.deployment);
  }
  deployment = {commit:identity.commit, deployment_host:identity.deployment_host};
  await actResponse('/api/plan/sample',()=>page.goto(url));
  await expect(page.getByTestId('plan-result')).toBeVisible({timeout:15_000});
  await expect(page.getByRole('region',{name:'Reviewed actions'})).toHaveCount(0);
  await layout('verified-opening-plan-desktop');
  await actResponse('/api/forecast/sample',()=>page.getByRole('button',{name:'Demand Review',exact:true}).click());
  await expect(page.getByTestId('forecast-result')).toBeVisible({timeout:15_000});
  await expect(page.getByText('Pooled signed bias',{exact:true})).toBeVisible();
  await layout('verified-demand-desktop');
  await actResponse('/api/forecast/sample',()=>page.getByRole('combobox',{name:'Dataset',exact:true}).selectOption('full'));
  await expect(page.getByRole('combobox',{name:'Product',exact:true})).toBeEnabled({timeout:15_000});
  await actResponse('/api/forecast/sample',()=>page.getByRole('combobox',{name:'Product',exact:true}).selectOption('SKU006'));
  await actResponse('/api/forecast/sample',()=>page.getByRole('button',{name:/Recalculate live/}).click());
  await actResponse('/api/forecast/sample',()=>page.getByRole('combobox',{name:'Store',exact:true}).selectOption('S2'));
  steps.push('full forecast/product/store/recalculate');
  await actResponse('/api/plan/sample',()=>page.getByRole('button',{name:'Plan Review',exact:true}).click());
  const fullPlan=await(await actResponse('/api/plan/sample',()=>page.getByRole('combobox',{name:'Planning dataset',exact:true}).selectOption('full'))).json();
  expect(fullPlan.provenance.sample_size).toBe('full');
  await expect(page.getByTestId('plan-result')).toBeVisible({timeout:15_000});await layout('verified-plan-desktop');
  const row=page.getByTestId('movement-table').locator('tbody tr').first();
  await row.locator('summary').click();
  const d=await(await actResponse('/api/scenarios/detail',()=>row.getByRole('button',{name:'Inspect movement and forecast'}).click())).json();
  expect(d.feasible).toBe(true);await expect(page.getByTestId('action-evidence')).toContainText('Selected action',{timeout:15_000});
  await page.setViewportSize({width:390,height:844});await layout('verified-movement-mobile');
  await page.getByRole('button',{name:'Close evidence',exact:true}).click();
  const baseline=page.waitForResponse(r=>/\/api\/scenarios\/(capture|baseline)$/.test(new URL(r.url()).pathname)&&r.ok(),{timeout:60_000});
  await Promise.all([baseline,page.getByRole('button',{name:'Scenarios',exact:true}).click()]);
  await page.getByRole('button',{name:'Promotion',exact:true}).click();
  await page.getByRole('button',{name:'Supplier disruption',exact:true}).click();
  await page.getByRole('button',{name:'Tighter funds',exact:true}).click();
  await page.getByLabel('Uplift percent',{exact:true}).fill('30');
  // The preset creates one row per funding week; edit the first dated row.
  const fundingWeek=await page.getByLabel('Funding week').first().inputValue();
  await page.getByLabel('New commitment limit',{exact:true}).first().fill('1500');
  await page.getByLabel('Payment ceiling',{exact:true}).first().fill('3500');
  await expect(page.getByLabel('New commitment limit',{exact:true}).first()).toHaveValue('1500');
  await expect(page.getByLabel('Payment ceiling',{exact:true}).first()).toHaveValue('3500');
  const result=await(await actResponse('/api/scenarios/compare',()=>page.getByRole('button',{name:'Run scenario live',exact:true}).click())).json();expect(result.definition.uplifts.length).toBeGreaterThan(0);
  expect(result.definition.delays.length).toBeGreaterThan(0);expect(result.definition.availability.length).toBeGreaterThan(0);
  const funding=result.definition.funding.find(f=>f.week_start===fundingWeek);
  expect(funding.commitment).toBe(1500);expect(funding.payment).toBe(3500);
  expect(result.replanned.feasible).toBe(true);expect(result.frozen.assumptions_hash).toBe(result.replanned.assumptions_hash);
  await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash',result.scenario_hash,{timeout:15_000});
  await layout('verified-scenarios-mobile');
  await page.getByRole('button',{name:'Reset to baseline',exact:true}).click();
  await expect(page.getByTestId('scenario-results')).toHaveAttribute('data-scenario-hash','baseline');
  await page.getByRole('button',{name:'Data and Assumptions',exact:true}).click();
  await expect(page.getByText(/Hosted uploads and accepted files are blocked/)).toBeVisible();
  await expect(page.getByRole('button',{name:'Upload workbook',exact:true})).toBeDisabled();
  const template=page.getByRole('link',{name:'Download blank XLSX template',exact:true});
  const download=page.waitForEvent('download');await template.click();expect((await download).suggestedFilename()).toBe('planning-blank.xlsx');
  await layout('verified-data-mobile');
  await page.setViewportSize({width:1440,height:1000});await layout('verified-data-desktop');
  expect(requests.every(r=>new URL(r.url).origin===new URL(url).origin&&r.status===200)).toBe(true);
  expect(errors).toEqual([]);
  expect(await (await page.request.get(`${url}/release.json`)).json()).toEqual(identity);
  passed = true;
} catch (error) {
  errors.push(bounded(String(error)));
  await page.screenshot({path:`${output}/pass6-hosted-failure.png`});
  throw error;
} finally {
  await writeFile(`${output}/pass6-hosted-browser.json`,JSON.stringify({url,deployment,passed,steps,requests,errors},null,2)+'\n');
  await browser.close();
}
console.log('Hosted sample browser verification passed; no hosted own-data workflow claimed.');

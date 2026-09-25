import { test, expect, type Page } from '@playwright/test';
import type { components } from '../src/contracts.generated';
type Plan = components['schemas']['PlanResult'];
const money = (n: number) => n.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const response = (page: Page) => page.waitForResponse(r => new URL(r.url()).pathname === '/api/plan/sample' && r.ok(), { timeout: 60_000 });

async function verifyPlan(page: Page, plan: Plan) {
  expect(['feasible', 'feasible_fallback']).toContain(plan.status);
  const proposed = plan.proposed!;
  if (plan.status === 'feasible_fallback') {
    await expect(page.getByRole('heading', { name: 'Validated constrained plan', exact: true })).toBeVisible();
    await expect(page.getByText(/Stock and funding checks passed\. Uses the constrained planner; optimality is not established\./)).toBeVisible();
    expect(plan.stages.at(-1)?.status).toBe('benchmark');
  }
  expect(proposed.replay.feasible).toBe(true);
  expect(proposed.replay.failures).toEqual([]);
  await expect(page.getByTestId('plan-result')).toHaveAttribute('data-run-id', plan.run_id);
  await expect(page.getByTestId('plan-commitment')).toHaveText(`SAR ${money(proposed.replay.summary.commitments)}`);
  await expect(page.getByTestId('plan-payments')).toHaveText(`SAR ${money(proposed.replay.summary.payments)}`);
  const purchaseSection = page.getByTestId('purchase-table').locator('xpath=ancestor::section');
  if (await purchaseSection.getByRole('button', { name: 'Show all' }).count()) await purchaseSection.getByRole('button', { name: 'Show all' }).click();
  const movementSection = page.getByTestId('movement-table').locator('xpath=ancestor::section');
  if (await movementSection.getByRole('button', { name: 'Show all' }).count()) await movementSection.getByRole('button', { name: 'Show all' }).click();
  const purchaseRows = page.getByTestId('purchase-table').locator('tbody tr');
  await expect(purchaseRows).toHaveCount(proposed.purchases.length);
  for (const [i,p] of proposed.purchases.entries()) {
    const cells = purchaseRows.nth(i).locator('td');
    await expect(cells.nth(0)).toHaveText(String(p.units));
    await expect(cells.nth(4)).toHaveText(money(p.value));
  }
  // Verify every allocation quantity in one DOM read, including rows below the fold.
  const movements = await page.getByTestId('movement-table').locator('tbody tr').evaluateAll(rows => rows.map(row => row.querySelectorAll('td')[1].textContent));
  expect(movements).toEqual(proposed.movements.map(m => String(m.units)));
  const cash = await page.getByTestId('cash-table').locator('tbody tr').evaluateAll(rows => rows.map(row => [...row.querySelectorAll('td')].map(td => td.textContent)));
  expect(cash).toEqual(proposed.replay.cash.map(w => [w.commitments,w.commitment_headroom!,w.existing_payments,w.new_payments,w.total_payments,w.payment_ceiling!,w.payment_headroom!].map(money).concat(`${money(w.movement_fees)} / ${money(w.transfer_budget!)}`)));
  await expect(page.getByRole('button', { name: 'Recalculate plan', exact: true })).toBeEnabled();
}

test('Plan Review matches live purchases, allocations and cash; recalculation and dataset changes replace all results', async ({ page }) => {
  test.setTimeout(200_000);
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  const first = response(page);
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Calculating plan…' })).toBeDisabled();
  await expect(page.getByTestId('plan-result')).toHaveCount(0);
  const fixture: Plan = await (await first).json();
  await verifyPlan(page,fixture);
  const again = response(page);
  await page.getByRole('button', { name: 'Recalculate plan', exact: true }).click();
  await expect(page.getByTestId('plan-result')).toHaveCount(0);
  const recalculated: Plan = await (await again).json();
  expect(recalculated.run_id).not.toBe(fixture.run_id);
  expect(recalculated.input_hash).toBe(fixture.input_hash);
  expect(recalculated.proposed).toEqual(fixture.proposed);
  expect(recalculated.exceptions).toEqual(fixture.exceptions);
  await verifyPlan(page,recalculated);
  const fullResponse = response(page);
  await page.getByRole('combobox', { name: 'Planning dataset', exact: true }).selectOption('full');
  await expect(page.getByTestId('plan-result')).toHaveCount(0);
  await expect(page.getByRole('combobox', { name: 'Planning dataset', exact: true })).toBeDisabled();
  const full: Plan = await (await fullResponse).json();
  expect(full.forecasts).toHaveLength(240);
  expect(full.input_hash).not.toBe(fixture.input_hash);
  await verifyPlan(page,full);
  expect(full.stock_detail).toBe('on_demand');
  expect(full.stock_row_count).toBe(16_800);
  expect(full.proposed!.replay.stock).toEqual([]);
  await page.getByText('Calculation details', {exact:true}).click();
  const scoped = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/detail') && r.ok(), {timeout:30_000});
  await page.getByRole('button', {name:'Review selected series forecast',exact:true}).click();
  const detail = await (await scoped).json();
  expect(detail.stock).toHaveLength(280);
  expect(detail.cash).toEqual(full.proposed!.replay.cash);
  expect(detail.provenance).toEqual(full.provenance);
  expect(detail.plan_run_id).toBe(full.run_id);
  expect(detail.review_id).toBe(full.review_id);
  await expect(page.getByTestId('action-evidence')).toContainText('Stock before and after dated events');
  await page.getByRole('button', {name:'Close evidence',exact:true}).click();
  await page.getByRole('button', { name: /Demand Review/ }).click();
  await expect(page.getByTestId('forecast-result')).toBeVisible();
  expect(errors).toEqual([]);
});

test('Plan Review handles API failure and invalid inputs without executable recommendations', async ({ page }) => {
  let invalid=false;
  await page.route('**/api/plan/sample', route => invalid ? route.fulfill({ json: {
    run_id:'invalid-test', input_hash:'invalid-test', as_of:'2026-09-14', status:'invalid_inputs',
    proposed:null, forecasts:[], stages:[], issues:[], failures:[{code:'missing_snapshot',message:'Explicit stock snapshots required.'}],
  } }) : route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ message: 'Planning unavailable for this request.' }) }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Planning unavailable for this request.');
  await expect(page.getByTestId('plan-result')).toHaveCount(0);
  invalid=true;
  await page.getByRole('button', { name: 'Retry plan' }).click();
  await expect(page.getByRole('alert')).toContainText('missing_snapshot');
  await expect(page.getByText('Not executable', { exact:true })).toBeVisible();
  await expect(page.getByTestId('purchase-table')).toHaveCount(0);
  await expect(page.getByTestId('plan-commitment')).toHaveCount(0);
});

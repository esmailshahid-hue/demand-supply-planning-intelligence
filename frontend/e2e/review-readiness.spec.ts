import { test, expect } from '@playwright/test';

test('a validated public plan without a review ID is scenario-ready', async ({ page }) => {
  await page.route('**/api/plan/sample', async route => {
    const response = await route.fetch();
    const plan = await response.json();
    plan.review_id = null;
    await route.fulfill({ json: plan });
  });
  await page.goto('/');
  await expect(page.getByTestId('plan-result')).toBeVisible();
  await page.getByRole('button', { name: 'Demand Review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Scenarios', exact: true })).toBeEnabled();
});

test('review readiness resolves after Plan Review unmounts', async ({ page }) => {
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  let requested!: () => void;
  const pending = new Promise<void>(resolve => { requested = resolve; });
  let requests = 0;
  await page.route(/\/api\/workflow\/review\/[^/]+$/, async route => {
    requests++;
    const response = await route.fetch();
    requested();
    await held;
    await route.fulfill({ response });
  });
  await page.goto('/');
  await pending;
  await expect(page.getByTestId('plan-result')).toBeVisible();
  await page.getByRole('button', { name: 'Demand Review', exact: true }).click();
  await expect(page.getByTestId('plan-result')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Scenarios', exact: true })).toBeDisabled();
  release();
  await expect(page.getByRole('button', { name: 'Scenarios', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Scenarios', exact: true }).click();
  await expect(page.getByTestId('scenario-results')).toBeVisible();
  expect(requests).toBe(1);
});

test('review status failure can be retried from another screen', async ({ page }) => {
  let attempts = 0;
  await page.route(/\/api\/workflow\/review\/[^/]+$/, route => {
    attempts++;
    return attempts === 1
      ? route.fulfill({ status: 503, json: { message: 'Review status temporarily unavailable.' } })
      : route.continue();
  });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Retry review', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Demand Review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Scenarios', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Retry review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Scenarios', exact: true })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Retry review', exact: true })).toHaveCount(0);
  expect(attempts).toBe(2);
});

test('an abandoned review response cannot unlock its replacement dataset', async ({ page }) => {
  const releases: Array<() => void> = [];
  await page.route(/\/api\/workflow\/review\/[^/]+$/, async route => {
    const response = await route.fetch();
    await new Promise<void>(resolve => { releases.push(resolve); });
    try { await route.fulfill({ response }); } catch { /* Replacement aborts the old request. */ }
  });
  await page.goto('/');
  await expect.poll(() => releases.length).toBe(1);
  await page.getByLabel('Planning dataset').selectOption('full');
  await expect.poll(() => releases.length).toBe(2);
  releases[0]();
  await page.getByRole('button', { name: 'Demand Review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Scenarios', exact: true })).toBeDisabled();
  releases[1]();
  await expect(page.getByRole('button', { name: 'Scenarios', exact: true })).toBeEnabled();
});

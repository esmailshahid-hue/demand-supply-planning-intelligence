import { test, expect } from '@playwright/test';

test('production UI renders the actual API result, recalculates and navigates honestly', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  const initial = page.waitForResponse(r => r.url().endsWith('/api/forecast/sample') && r.ok());
  await page.goto('/');
  const result = await (await initial).json();
  const content = page.getByTestId('forecast-result');
  await expect(content).toHaveAttribute('data-run-id', result.run_id);
  await expect(page.locator('.metric').first()).toContainText(result.visible_units.toLocaleString('en-GB', { maximumFractionDigits: 1 }));
  await expect(page.locator('.metric').nth(3)).toContainText(`${result.selection.find((r: {method:string}) => r.method === result.selected_method).metrics.find((m:{horizon:number}) => m.horizon === 28).valid_observations} / 224`);
  const recalculation = page.waitForResponse(r => r.url().endsWith('/api/forecast/sample') && r.ok());
  await page.getByRole('button', { name: 'Recalculate live' }).click();
  const next = await (await recalculation).json();
  expect(next.run_id).not.toBe(result.run_id);
  await expect(content).toHaveAttribute('data-run-id', next.run_id);
  await page.getByRole('button', { name: 'Held-out final check' }).click();
  await expect(page.getByText('These results do not choose the winner.', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: /Plan Review/ }).click();
  await expect(page.getByText('Purchasing and allocation come next.')).toBeVisible();
  await expect(content).toHaveCount(0);
  await page.getByRole('button', { name: /Scenarios/ }).click();
  await expect(page.getByText('Scenario comparisons need a validated plan.')).toBeVisible();
  await page.getByRole('button', { name: /Data and Assumptions/ }).click();
  await expect(page.getByRole('button', { name: /Upload workbook/ })).toBeDisabled();
  await expect(page.getByText('Calculations run on the Python server.', { exact: false })).toBeVisible();
  expect(errors).toEqual([]);
});

test('new-product fallback, full sample and zero-demand cases are visible', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('forecast-result')).toBeVisible();
  await page.getByRole('combobox', { name: 'Product', exact: true }).selectOption('SKU007');
  await expect(page.getByText('Provisional forecast', { exact: true })).toBeVisible();
  await expect(page.locator('.metric').first()).toContainText('224');
  await page.getByRole('combobox', { name: 'Dataset', exact: true }).selectOption('full');
  await expect(page.getByRole('button', { name: 'Recalculate live' })).toBeEnabled();
  await page.getByRole('combobox', { name: 'Product', exact: true }).selectOption('SKU011');
  await expect(page.getByText('All eligible observed demand is zero', { exact: false })).toBeVisible();
  await expect(page.locator('.metric').first().locator('strong')).toHaveText('0');
  await expect(page.locator('.metric').nth(2).locator('strong')).toHaveText('Unavailable');
});

test('mobile navigation and keyboard access work without page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByTestId('forecast-result')).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('button', { name: /Scenarios/ }).click();
  await expect(page.getByText('Scenario comparisons need a validated plan.')).toBeVisible();
});

test('failed API calculation shows an error and retry, never fabricated metrics', async ({ page }) => {
  await page.route('**/api/forecast/sample', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ message: 'Calculation exceeded its budget.' }) }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Calculation exceeded its budget.');
  await expect(page.getByTestId('forecast-result')).toHaveCount(0);
  await page.unroute('**/api/forecast/sample');
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.getByTestId('forecast-result')).toBeVisible();
});

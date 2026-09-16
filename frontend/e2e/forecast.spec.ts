import { test, expect } from '@playwright/test';

test('production UI renders the actual API result, recalculates and navigates honestly', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  const initial = page.waitForResponse(r => r.url().endsWith('/api/forecast/sample') && r.ok());
  await page.goto('/');
  const result = await (await initial).json();
  const content = page.getByTestId('forecast-result');
  const selectedMetrics = result.selection.find((r: {method:string}) => r.method === result.selected_method).metrics.find((m:{horizon:number}) => m.horizon === 28);
  const baselineMetrics = result.selection.find((r: {method:string}) => r.method === 'seasonal_naive').metrics.find((m:{horizon:number}) => m.horizon === 28);
  const displayedBaselineMae = Number(baselineMetrics.mean_absolute_quantity_error.toFixed(1));
  const displayedSelectedMae = Number(selectedMetrics.mean_absolute_quantity_error.toFixed(1));
  const reconciledImprovement = Math.round(100 * (displayedBaselineMae - displayedSelectedMae) / displayedBaselineMae);
  expect(reconciledImprovement).toBe(Math.round(result.improvement_pct));
  await expect(content).toHaveAttribute('data-run-id', result.run_id);
  await expect(page.locator('.metric').first()).toContainText(result.visible_units.toLocaleString('en-GB', { maximumFractionDigits: 1 }));
  await expect(page.locator('.metric').nth(1).locator('strong')).toHaveText(`${reconciledImprovement}%`);
  await expect(page.locator('.metric').nth(1)).toContainText(`Baseline ${baselineMetrics.mean_absolute_quantity_error.toLocaleString('en-GB', { maximumFractionDigits: 1 })} → selected ${selectedMetrics.mean_absolute_quantity_error.toLocaleString('en-GB', { maximumFractionDigits: 1 })} units`);
  await expect(page.locator('.metric').nth(2)).toContainText('Pooled signed bias');
  await expect(page.locator('.metric').nth(2).locator('strong')).toHaveText('<0.1%');
  await expect(page.locator('.selected-row')).toContainText('<0.1%');
  await expect(page.locator('.metric').nth(3)).toContainText(`${selectedMetrics.valid_observations} / 224`);

  const productResponse = page.waitForResponse(r => r.url().endsWith('/api/forecast/sample') && r.ok());
  await page.getByRole('combobox', { name: 'Product', exact: true }).selectOption('SKU002');
  const productResult = await (await productResponse).json();
  expect(productResult.sku).toBe('SKU002');
  await expect(content).toHaveAttribute('data-run-id', productResult.run_id);
  await expect(page.locator('.panel .eyebrow').first()).toContainText(productResult.product_name);

  const storeResponse = page.waitForResponse(r => r.url().endsWith('/api/forecast/sample') && r.ok());
  await page.getByRole('combobox', { name: 'Store', exact: true }).selectOption('S2');
  const storeResult = await (await storeResponse).json();
  expect(storeResult.location_id).toBe('S2');
  await expect(content).toHaveAttribute('data-run-id', storeResult.run_id);
  const recalculation = page.waitForResponse(r => r.url().endsWith('/api/forecast/sample') && r.ok());
  await page.getByRole('button', { name: 'Recalculate live' }).click();
  const next = await (await recalculation).json();
  expect(next.run_id).not.toBe(storeResult.run_id);
  expect(next.sku).toBe('SKU002');
  expect(next.location_id).toBe('S2');
  await expect(content).toHaveAttribute('data-run-id', next.run_id);
  await page.getByRole('button', { name: 'Held-out final check' }).click();
  await expect(page.getByText('These results do not choose the winner.', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: /Plan Review/ }).click();
  await expect(page.getByText('Purchasing and allocation come next.')).toBeVisible();
  await expect(content).toHaveCount(0);
  await page.getByRole('button', { name: /Scenarios/ }).click();
  await expect(page.getByText('Scenario comparisons need a validated plan.')).toBeVisible();
  await expect(page.locator('.unavailable-icon svg')).toBeVisible();
  await expect(page.locator('.unavailable-icon')).not.toContainText('⌘');
  await page.getByRole('button', { name: /Data and Assumptions/ }).click();
  const dataNav = page.getByRole('button', { name: 'Data and Assumptions' });
  await expect(dataNav).toHaveAttribute('aria-current', 'page');
  await expect(dataNav).toHaveCSS('background-color', 'rgb(217, 231, 189)');
  await dataNav.hover();
  await expect(dataNav).toHaveCSS('background-color', 'rgb(217, 231, 189)');
  await expect(page.getByRole('button', { name: /Upload workbook/ })).toBeDisabled();
  await expect(page.getByText('Calculations run on the Python server.', { exact: false })).toBeVisible();
  expect(errors).toEqual([]);
});

test('navigation has no undefined hollow status circles', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('navigation', { name: 'Primary navigation' })).not.toContainText('○');
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

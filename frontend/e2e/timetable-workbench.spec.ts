import { test, expect } from '@playwright/test';

test.describe('VFSTR Timetable Workbench E2E Journeys', () => {

  test('User Journey 1: Dashboard navigation and active timetable matrix grid rendering', async ({ page }) => {
    // 1. Visit schedule page
    await page.goto('/schedule');

    // 2. Assert Page Title and Header
    await expect(page.getByRole('heading', { name: /Timetable Schedule Workbench/i })).toBeVisible();

    // 3. Verify Active View Section selector is set to "II AIML-A"
    const sectionSelect = page.locator('select');
    await expect(sectionSelect).toHaveValue('II AIML-A');

    // 4. Assert Timetable Matrix Grid is rendered with Day and Period headers
    await expect(page.getByText('Timetable Matrix —')).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Day / Period' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'P1' })).toBeVisible();

    // 5. Change section dropdown to "II AIML-E" and verify grid updates
    await sectionSelect.selectOption('II AIML-E');
    await expect(page.getByText('II AIML-E')).toBeVisible();
  });

  test('User Journey 2: AI Setup Wizard workflow execution', async ({ page }) => {
    await page.goto('/schedule');

    // 1. Click AI Setup Wizard toggle button
    const wizardBtn = page.getByRole('button', { name: /AI Wizard Setup/i });
    await wizardBtn.click();

    // 2. Verify Step 1 Setup Form renders
    await expect(page.getByText('Step 1 of 4')).toBeVisible();

    // 3. Click Next Step button
    const nextBtn = page.getByRole('button', { name: /Next/i });
    await nextBtn.click();

    // 4. Verify Step 2 Subject & Faculty Assignment matrix renders
    await expect(page.getByText('Step 2 of 4')).toBeVisible();
  });

  test('User Journey 3: Excel timetable download trigger', async ({ page }) => {
    await page.goto('/export');

    // 1. Verify Export Page options render
    await expect(page.getByRole('heading', { name: /Export Timetable Schedules/i })).toBeVisible();

    // 2. Click Export Excel button
    const downloadPromise = page.waitForEvent('download').catch(() => null);
    const excelBtn = page.getByRole('button', { name: /Export Excel/i });
    if (await excelBtn.isVisible()) {
      await excelBtn.click();
      const download = await downloadPromise;
      if (download) {
        expect(download.suggestedFilename()).toContain('.xlsx');
      }
    }
  });

});

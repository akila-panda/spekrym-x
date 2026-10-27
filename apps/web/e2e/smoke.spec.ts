import { test, expect } from '@playwright/test'

test('loads, switches screens, toggles theme, opens palette', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('New York preparation')).toBeVisible()
  await expect(page.getByText('Sample data').first()).toBeVisible()

  await page.getByRole('button', { name: 'Chart', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Causal replay' })).toBeVisible()
  await page.getByRole('button', { name: 'Suggestions' }).click()
  await expect(page.getByText('Not built yet')).toBeVisible()

  const before = await page.evaluate(() => document.documentElement.dataset.theme)
  await page.getByRole('button', { name: /mode$/ }).click()
  const after = await page.evaluate(() => document.documentElement.dataset.theme)
  expect(after).not.toBe(before)

  await page.keyboard.press('Control+k')
  await expect(page.getByRole('dialog')).toBeVisible()
})

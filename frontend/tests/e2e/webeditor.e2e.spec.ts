import { test, expect, APIRequestContext, Page } from '@playwright/test'

const apiBase = process.env.E2E_API_URL || 'http://localhost:8927/api'
const privateEmail = process.env.E2E_PRIVATE_EMAIL
const privatePassword = process.env.E2E_PRIVATE_PASSWORD
const privateWebDocId = process.env.E2E_PRIVATE_WEB_DOC_ID
const publicWebDocId = process.env.E2E_PUBLIC_WEB_DOC_ID
const privatePptDocId = process.env.E2E_PRIVATE_PPT_DOC_ID
const publicPptDocId = process.env.E2E_PUBLIC_PPT_DOC_ID
const pptDemoSlide = process.env.E2E_PPT_DEMO_SLIDE || '1'

async function loginWithApi(request: APIRequestContext, page: Page) {
  if (!privateEmail || !privatePassword) {
    test.skip(true, '缺少 E2E_PRIVATE_EMAIL / E2E_PRIVATE_PASSWORD 环境变量')
    return
  }

  const response = await request.post(`${apiBase}/auth/login`, {
    data: {
      email: privateEmail,
      password: privatePassword
    }
  })

  expect(response.ok()).toBeTruthy()
  const body = await response.json()
  const token = body?.access_token
  expect(token).toBeTruthy()

  const baseURL = process.env.BASE_URL || 'http://localhost:3000'
  const { hostname } = new URL(baseURL)

  await page.context().addCookies([
    {
      name: 'access_token',
      value: token,
      domain: hostname,
      path: '/',
      httpOnly: false,
      sameSite: 'Lax'
    }
  ])
}

async function startEditFlow(page: Page) {
  await page.waitForSelector('#editor-mode-btn', { timeout: 15_000 })
  await page.fill('#editor-mode-input', '自动化修改指令 - E2E')
  await page.click('#editor-start-btn')
  await expect(page.getByRole('button', { name: '编辑中...' })).toBeVisible()
  await expect(page.getByRole('button', { name: '正在编辑中（预计10-60s）' })).toBeVisible()
}

test.describe('WebEditor E2E', () => {
  test('private web document can enter processing', async ({ page, request }) => {
    test.skip(!privateWebDocId, '缺少 E2E_PRIVATE_WEB_DOC_ID')

    await loginWithApi(request, page)
    await page.goto(`/document/${privateWebDocId}`)
    await page.waitForSelector('iframe', { timeout: 20_000 })
    await startEditFlow(page)
  })

  test('public web document can enter processing and show version toggle', async ({ page }) => {
    test.skip(!publicWebDocId, '缺少 E2E_PUBLIC_WEB_DOC_ID')

    await page.goto(`/public/document/${publicWebDocId}`)
    await page.waitForSelector('iframe', { timeout: 20_000 })
    await startEditFlow(page)
  })

  test('private PPT demo editing enters processing', async ({ page, request }) => {
    test.skip(!privatePptDocId, '缺少 E2E_PRIVATE_PPT_DOC_ID')

    await loginWithApi(request, page)
    await page.goto(`/ppt-viewer/${privatePptDocId}?slide=${pptDemoSlide}`)

    const editorButton = page.locator('#editor-mode-btn')
    try {
      await editorButton.waitFor({ timeout: 20_000 })
    } catch (error) {
      test.skip(true, '未找到 WebEditor（确保当前 slide 是 demo 且存在互动 HTML）')
      return
    }

    await startEditFlow(page)
  })

  test('public PPT demo editing enters processing', async ({ page }) => {
    test.skip(!publicPptDocId, '缺少 E2E_PUBLIC_PPT_DOC_ID')

    await page.goto(`/ppt-viewer/${publicPptDocId}?slide=${pptDemoSlide}`)

    const editorButton = page.locator('#editor-mode-btn')
    try {
      await editorButton.waitFor({ timeout: 20_000 })
    } catch (error) {
      test.skip(true, '未找到 WebEditor（确保当前 slide 是 demo 且存在互动 HTML）')
      return
    }

    await startEditFlow(page)
  })
})

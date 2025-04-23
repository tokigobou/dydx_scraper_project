import asyncio
from playwright.async_api import async_playwright

wallet = "dydx1z67u06w6zacdfej72c7lpjq5w5npn3sapmplpj"
url = f"https://www.mintscan.io/dydx/address/{wallet}"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Trueにすればヘッドレス
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)
        await page.wait_for_timeout(5000)

        # Transactionsブロックの2ページ目をクリック
        await page.wait_for_selector("text=Transactions")
        await page.click("text='2'")
        await page.wait_for_timeout(5000)

        # HTML保存
        html = await page.content()
        with open("mintscan_page2.html", "w", encoding="utf-8") as f:
            f.write(html)

        await browser.close()

asyncio.run(run())
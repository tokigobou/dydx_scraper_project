from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import os
from playwright.sync_api import sync_playwright
import time

# ウォレットと期間設定
wallet = "dydx1z67u06w6zacdfej72c7lpjq5w5npn3sapmplpj"
start_time = datetime(2025, 4, 22, 10, 0, 0, tzinfo=pytz.timezone('Asia/Tokyo'))
end_time = datetime(2025, 4, 28, 9, 0, 0, tzinfo=pytz.timezone('Asia/Tokyo'))

# PlaywrightでMintscanページを保存する（Transactionsブロックの2ページ目へ移動）
def download_html_with_playwright(wallet, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        url = f"https://www.mintscan.io/dydx/address/{wallet}"
        print(f"[INFO] アクセス中: {url}")
        page.goto(url)

        print("[DEBUG] Transactionsセクションまでスクロール")
        page.keyboard.press("PageDown")
        time.sleep(3)

        print("[DEBUG] ページ2クリック開始")
        try:
            locator = page.locator("div.typo[data-h='7']").filter(has_text="2")
            locator.nth(0).click()
            print("[INFO] ページ2クリック成功")
            time.sleep(5)
        except Exception as e:
            print(f"[WARN] ページ2クリックに失敗または読み込み未完了: {e}")

        print("[DEBUG] HTML書き出し開始")
        html = page.content()
        print("[DEBUG] page_source 内容表示（先頭1000文字）：")
        print(html[:1000])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        browser.close()
        print(f"[INFO] HTMLを保存しました: {output_path}")

# ローカルHTMLファイルを読み込んでパース（Proposed Operations対応）
def fetch_transactions_from_html(file_path):
    if not os.path.exists(file_path):
        print(f"[エラー] ファイルが見つかりません: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, 'html.parser')

    tx_rows = soup.select("div.operation")
    tx_data = []

    for row in tx_rows:
        text = row.get_text()
        if "Proposed Operations" not in text:
            continue

        timestamp = None
        for span in row.find_all("span"):
            ts = span.text.strip()
            try:
                timestamp = datetime.strptime(ts, "%b-%d-%Y %H:%M:%S %p %Z")
                timestamp = pytz.timezone('UTC').localize(timestamp).astimezone(pytz.timezone('Asia/Tokyo'))
                break
            except:
                continue

        if not timestamp or not (start_time <= timestamp <= end_time):
            continue

        tx_data.append({
            "timestamp": timestamp,
            "text": text
        })

    return tx_data

# メイン処理
if __name__ == "__main__":
    html_file_path = "../html/sample_mintscan_tx.html"

    download_html_with_playwright(wallet, html_file_path)

    print("\n[ファイル確認] ../html フォルダ内のファイル一覧:")
    try:
        for f in os.listdir("../html"):
            print(" -", f)
    except Exception as e:
        print(" - フォルダが存在しません:", e)

    txs = fetch_transactions_from_html(html_file_path)

    if txs:
        print(f"\n[対象期間中のProposed Operations：{len(txs)}件]\n")
        for tx in txs:
            print(f"{tx['timestamp']}: {tx['text'][:100]}...")
    else:
        print("[!] 該当する取引履歴は見つかりませんでした。")

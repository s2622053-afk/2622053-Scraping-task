import csv
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# 設定項目
START_URL = "https://www.musashino-u.ac.jp/"  # トップページのURL
TARGET_DOMAIN = urlparse(START_URL).netloc  # 武蔵野大学のドメイン名
SLEEP_TIME = 1  # サーバー負荷軽減のための待機時間（秒）

# 巡回済みURLを記録するセットと、結果を保持する辞書
visited_urls = set()
sitemap_dict = {}


def crawl(url):
    # 訪問済みならスキップ
    if url in visited_urls:
        return

    visited_urls.add(url)
    print(f"Crawling: {url}")

    # サーバー負荷軽減（必須要求）
    time.sleep(SLEEP_TIME)

    try:
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        response.raise_for_status()

        # エンコーディングの適切な設定
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        # <title>タグの文字列を取得
        title = (
            soup.title.string.strip() if soup.title and soup.title.string else ""
        )
        sitemap_dict[url] = title

        # ページ内のすべてのリンクを辿る
        for a_tag in soup.find_all("a", href=True):
            next_url = urljoin(url, a_tag["href"])

            # 内部リンクの正規化（フラグメント `#` やクエリパラメータ `?` の除去）
            parsed_next = urlparse(next_url)
            clean_url = f"{parsed_next.scheme}://{parsed_next.netloc}{parsed_next.path}"

            # 同一ドメインかつ未訪問のリンクのみを再帰的に呼び出す
            if (
                parsed_next.netloc == TARGET_DOMAIN
                and clean_url not in visited_urls
            ):
                # HTTP/HTTPSのみ対象（mailto: や tel: を除外）
                if clean_url.startswith("http"):
                    crawl(clean_url)

    except Exception as e:
        print(f"Failed to crawl {url}: {e}")


def save_to_csv(data_dict, filename="sitemap.csv"):
    with open(filename, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Title"])  # ヘッダー書き込み
        for url, title in data_dict.items():
            writer.writerow([url, title])
    print(f"\n保存完了: {filename} (全 {len(data_dict)} ページ)")


if __name__ == "__main__":
    print("クローリングを開始します...")
    crawl(START_URL)
    save_to_csv(sitemap_dict)
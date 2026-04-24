from pathlib import Path
import time

from bs4 import BeautifulSoup
import requests


# クローリング対象のURL（年収・ボーナスの企業ランキング）
BASE_URL = "https://careerconnection.jp/review/rating/Con1/"

# 保存用ディレクトリ名
RANKING_DIR = "html_ranking"
COMPANY_DIR = "html_companies"

# 取得するページ数
MAX_PAGES = 1082

# リクエストのタイムアウト時間（秒）
TIMEOUT = 120

# リクエスト間の待機時間（秒）
DELAY_TIME = 3

# ヘッダー設定
HEADERS = {
    "User-Agent": (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
}


def fetch_ranking_pages(max_pages: int) -> Path:
    """ランキングページをクローリングし、HTMLを保存

    Args:
        max_pages (int): 取得するページ数

    Returns:
        Path: 保存先ディレクトリのパス
    """
    # 保存用ディレクトリのパスを作成
    save_dir = Path(RANKING_DIR)
    save_dir.mkdir(exist_ok=True)

    for page_num in range(1, max_pages + 1):
        # 保存ファイル名の作成
        file_name = f"ranking_page_{page_num:04d}.html"
        save_path = save_dir / file_name

        # すでにファイルが存在する場合はスキップ
        if save_path.exists():
            continue
        
        try:
            # サーバー負荷軽減のため待機
            time.sleep(DELAY_TIME)

            # URLパラメータの設定
            params = {"pageNo": page_num}

            # ページの取得
            response = requests.get(BASE_URL, params=params, timeout=TIMEOUT, headers=HEADERS)

            # ステータスコードが200番台でない場合は例外を発生させる
            response.raise_for_status()

            # 画像認証ページの検出
            if "<title>画像認証ページ" in response.text:
                raise ValueError("画像認証エラー")

            # HTMLをファイルに書き込み
            save_path.write_text(response.text, encoding="utf-8")
            print(f"{save_path}の保存完了", flush=True)

        # 途中でエラーが発生した場合は処理を中断
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"{save_path}でエラー: {e}", flush=True)
            break

    return save_dir


def fetch_company_details(ranking_dir: Path) -> Path:
    """保存されたランキングページのHTMLからurlをスクレイピングし、企業の詳細ページをクローリングしてHTMLを保存

    Args:
        ranking_dir (Path): ランキングのHTMLが保存されているディレクトリ

    Returns:
        Path: 保存先ディレクトリのパス
    """
    # 保存用ディレクトリのパスを作成
    save_dir = Path(COMPANY_DIR)
    save_dir.mkdir(exist_ok=True)

    # ランキングディレクトリ内のHTMLファイルを昇順で取得
    ranking_files = sorted(ranking_dir.glob("*.html"))

    for html_file in ranking_files:
        # HTMLファイルを読み込む
        content = html_file.read_text(encoding="utf-8")
        soup = BeautifulSoup(content, "html.parser")

        # 企業名が含まれるdivタグをすべて取得
        company_divs = soup.find_all(
            "div", class_="recommend_list_title_company"
        )

        for div in company_divs:
            # aタグを取得
            link_tag = div.find("a")

            # 企業詳細ページのURLを取得
            company_url = link_tag.get("href")

            # URL末尾の数字IDを抽出し、ファイル名に使用
            company_id = company_url.strip("/").split("/")[-1]
            save_path = save_dir / f"company_{company_id}.html"

            # すでにファイルがあればスキップ
            if save_path.exists():
                continue

            try:
                # サーバー負荷軽減のため待機
                time.sleep(DELAY_TIME)

                # ページの取得
                response = requests.get(company_url, timeout=TIMEOUT, headers=HEADERS)

                # ステータスコードが200番台でない場合は例外を発生させる
                response.raise_for_status()

                # 画像認証ページの検出
                if "<title>画像認証ページ" in response.text:
                    raise ValueError("画像認証エラー")

                # HTMLをファイルに書き込み
                save_path.write_text(response.text, encoding="utf-8")
                print(f"{save_path}の保存完了", flush=True)

            # 途中でエラーが発生した場合は処理を中断
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"{save_path}でエラー: {e}", flush=True)
                return save_dir

    return save_dir


def main():
    """メイン処理"""
    # ランキングページのクローリング
    print(f"\n ランキングページのクローリング開始")
    ranking_dir = fetch_ranking_pages(MAX_PAGES)
    ranking_count = len(list(ranking_dir.glob("*.html")))
    print(f"\n ランキングページのクローリング完了(ファイル数: {ranking_count}件)")

    # 各企業の詳細ページのクローリング
    print(f"\n企業の詳細ページのクローリング開始")
    company_dir = fetch_company_details(ranking_dir)
    company_count = len(list(company_dir.glob("*.html")))
    print(f"\n企業の詳細ページのクローリング完了(ファイル数: {company_count}件)")


# メイン処理の実行
if __name__ == "__main__":
    main()
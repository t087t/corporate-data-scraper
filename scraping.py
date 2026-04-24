import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup


# 入力・出力のパス設定
INPUT_DIR = "html_companies"
OUTPUT_FILE = "company_data.csv"

# 基本カラム名
BASE_COLUMNS = [
    "company",                 # 企業名
    "industry",                # 業界
    "prefecture",              # 都道府県
    "avg_annual_salary",       # 平均年収
    "avg_monthly_overtime",    # 月平均残業時間
    "avg_monthly_holiday_work",# 月平均休日出勤
    "paid_leave_usage_rate",   # 有休消化率
    "overall_score",           # 総合評価
]

# 評価スコアのカラム名
SCORE_COLUMNS = [
    "work_hours_score",        # 労働時間の満足度
    "job_score",               # 仕事のやりがい
    "stress_score",            # ストレス度の低さ
    "holidays_score",          # 休日数の満足度
    "salary_score",            # 給与の満足度
    "white_score",             # ホワイト度
]

# 全カラム名のリスト
COLUMNS = BASE_COLUMNS + SCORE_COLUMNS


def extract_text(soup: BeautifulSoup, selector: str) -> str:
    """
    指定されたセレクタからテキストを抽出する関数
    Args:
        soup (BeautifulSoup): パース済みのHTMLコンテンツ
        selector (str): 抽出する要素のCSSセレクター
    Returns:
        str: 抽出されたテキスト
    """
    # セレクタで要素を取得
    element = soup.select_one(selector)

    # 要素が存在しない場合は空文字を返す
    if not element:
        return ""
        
    # 要素のテキストを取得して返す
    return element.get_text(strip=True)


def extract_number(soup: BeautifulSoup, selector: str) -> str:
    """
    指定されたセレクタから数値を抽出する関数
    Args:
        soup (BeautifulSoup): パース済みのHTMLコンテンツ
        selector (str): 抽出する要素のCSSセレクター
    Returns:
        str: 抽出された数値
    """
    # 基本のテキスト抽出を行う
    text = extract_text(soup, selector)

    # テキストから数字と小数点以外を除去
    number = re.sub(r'[^\d.]', '', text)

    # 数字が空の場合はNoneを返す
    if not number:
        return None
    
    return number


def extract_industry(soup: BeautifulSoup) -> str:
    """
    業界情報を抽出する関数
    Args:
        soup (BeautifulSoup): パース済みのHTMLコンテンツ
    Returns:
        str: 抽出された業界名
    """
    # dt要素を全て調べて「業界」を含むものを探す
    for dt in soup.find_all('dt'):

        # 「業界」を含むdt要素を見つけた場合は対応するdd要素を取得
        if '業界' in dt.get_text(strip=True):
            dd = dt.find_next_sibling("dd")
            return dd.get_text(strip=True)

    return ""


def extract_prefecture(soup: BeautifulSoup) -> str:
    """
    住所情報から都道府県を抽出する関数
    Args:
        soup (BeautifulSoup): パース済みのHTMLコンテンツ
    Returns:
        str: 抽出された都道府県名
    """
    # dt要素を全て調べて「住所」を含むものを探す
    for dt in soup.find_all('dt'):

        # 「住所」を含むdt要素を見つけた場合は対応するdd要素を取得
        if '住所' in dt.get_text(strip=True):
            dd = dt.find_next_sibling("dd")

            # 都道府県名を正規表現で抽出して返す
            match = re.search(r"(.{2,3}[都道府県])", dd.get_text(strip=True))
            return match.group(1)

    return ""


def extract_scores(soup: BeautifulSoup) -> dict:
    """
    企業の評価スコアを抽出する関数
    Args:
        soup (BeautifulSoup): パース済みのHTMLコンテンツ
    Returns:
        dict: 抽出された評価スコアを含む辞書
    """
    scores = {}
    
    # 評価が存在する場合
    if not soup.select_one(".overview-area__chart-norate"):
        # 総合評価の取得
        scores["overall_score"] = extract_number(
            soup, ".pc-report-header-review-aggregate__rating-average"
        )

        # レーダーチャートの要素を取得
        chart_element = soup.select_one("#canvas_detail")
        for i, col in enumerate(SCORE_COLUMNS, 1):
            scores[col] = chart_element.get(f"data-chart{i}")

    else:
        scores["overall_score"] = None
        for col in SCORE_COLUMNS:
            scores[col] = None

    return scores


def parse_html_file(file_path: Path) -> dict:
    """
    企業の詳細ページのHTMLファイルをパースして必要なデータを抽出する関数
    Args:
        file_path (Path): 解析するHTMLファイルのパス
    Returns:
        dict: 抽出されたデータを含む辞書
    """
    # HTMLファイルの読み込みとパース
    content = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html.parser")

    # 抽出データを格納する辞書
    data = {}

    # 非数値データの取得
    data["company"] = extract_text(
        soup,"h1.pc-report-header__title a[itemprop='name']"
    )   

    # 数値データの取得
    data["avg_annual_salary"] = extract_number(
        soup,".overview-area__income-list1 .value-main"
    )
    data["avg_monthly_overtime"] = extract_number(
        soup,".overview-area__time-list1 dd strong"
    )
    data["avg_monthly_holiday_work"] = extract_number(
        soup,".overview-area__time-list2 dd strong"
    )
    data["paid_leave_usage_rate"] = extract_number(
        soup,".overview-area__time-list3 dd strong"
    )

    # 業界の抽出
    data["industry"] = extract_industry(soup)

    # 都道府県の抽出  
    data["prefecture"] = extract_prefecture(soup)

    # 総合評価と各評価スコア
    data.update(extract_scores(soup))

    return data


def main():
    """メイン処理"""
    # 入力ディレクトリ内のHTMLファイルを取得
    base_dir = Path(__file__).resolve().parent
    html_files = sorted((base_dir / INPUT_DIR).glob("*.html"))
    total_files = len(html_files)

    print(f"スクレイピング開始")

    try:
        # CSVファイルに書き込み
        with open((base_dir / OUTPUT_FILE), "w", encoding="cp932", newline="", errors="ignore") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            
            # データを1件ずつ書き込み
            for i, file_path in enumerate(html_files, 1):
                try:
                    # パースしてデータを取得し、CSVに書き込み
                    writer.writerow(parse_html_file(file_path))

                except Exception as e:
                    print(f"{file_path}でエラー: {e}")

                # 100件ごとに進捗を表示
                if i % 100 == 0:
                    print(f"{i}/{total_files}件完了", flush=True)

        print(f"\nスクレイピング完了(データ数: {total_files}件)")
        
    # ファイル書き込みエラーの処理
    except IOError as e:
        print(f"ファイルの書き込みエラー: {e}")


# メイン処理の実行
if __name__ == "__main__":
    main()
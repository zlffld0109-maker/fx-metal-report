import logging
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.nonferrous.or.kr/stats/"
_METAL_COLUMNS = ["Cu", "Al", "Zn", "Pb", "Ni", "Sn"]
_TIMEOUT_SECONDS = 15
SOURCE_LABEL = "한국비철금속협회(nonferrous.or.kr) 통계정보 > LME시세"


def fetch_metal_page(page: int = 1) -> str:
    """한국비철금속협회 LME시세 페이지 원본 HTML을 가져온다."""
    resp = requests.get(
        _BASE_URL,
        params={"act": "sub3", "page": page},
        timeout=_TIMEOUT_SECONDS,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resp.raise_for_status()
    resp.encoding = "euc-kr"
    return resp.text


def parse_metal_table(html: str) -> pd.DataFrame:
    """LME시세 페이지 HTML에서 일자별 Cu/Al/Zn/Pb/Ni/Sn(US$/톤) 표를 파싱한다."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        raise ValueError("LME 시세 표를 찾을 수 없습니다 (페이지 구조 변경 가능성)")

    records = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) != 7:
            continue  # 헤더 행(th) 등은 스킵
        date_text = cells[0].get_text(strip=True)
        try:
            row_date = datetime.strptime(date_text, "%Y. %m. %d").date()
        except ValueError:
            continue
        values = [cell.get_text(strip=True).replace(",", "") for cell in cells[1:]]
        try:
            values = [float(v) if v else None for v in values]
        except ValueError:
            continue
        records.append([row_date, *values])

    if not records:
        raise ValueError("LME 시세 데이터 행을 찾지 못했습니다 (페이지 구조 변경 가능성)")

    df = pd.DataFrame(records, columns=["date", *_METAL_COLUMNS])
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def get_metal_prices(pages: int = 2) -> pd.DataFrame:
    """최근 `pages`페이지 분량의 LME 6대 금속 일별 시세를 합쳐서 반환한다."""
    frames = [parse_metal_table(fetch_metal_page(page)) for page in range(1, pages + 1)]
    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)

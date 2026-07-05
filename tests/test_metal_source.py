import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fx_metal_report.data.metal_source import get_metal_prices, parse_metal_table  # noqa: E402

_FIXTURE_PAGE1 = (Path(__file__).resolve().parent / "fixtures" / "metal_page1.html").read_text(
    encoding="utf-8"
)


def test_parse_metal_table_extracts_all_six_metals():
    df = parse_metal_table(_FIXTURE_PAGE1)

    assert list(df.columns) == ["date", "Cu", "Al", "Zn", "Pb", "Ni", "Sn"]
    assert len(df) == 20
    # 오름차순(과거->최신) 정렬 확인
    assert df["date"].is_monotonic_increasing
    latest = df.iloc[-1]
    assert latest["date"] == pd.Timestamp("2026-07-02")
    assert latest["Cu"] == 13202.0
    assert latest["Al"] == 3061.5
    assert latest["Zn"] == 3475.0
    assert latest["Pb"] == 1828.5
    assert latest["Ni"] == 16070.0
    assert latest["Sn"] == 51200.0


def test_parse_metal_table_raises_on_unrecognized_structure():
    try:
        parse_metal_table("<html><body>no table here</body></html>")
        assert False, "ValueError가 발생해야 함"
    except ValueError:
        pass


def test_get_metal_prices_merges_pages_and_dedupes():
    with patch(
        "fx_metal_report.data.metal_source.fetch_metal_page", return_value=_FIXTURE_PAGE1
    ):
        df = get_metal_prices(pages=2)

    # 같은 fixture를 2페이지 모두로 사용했으므로 중복 제거되어 1페이지 분량(20행)만 남아야 함
    assert len(df) == 20

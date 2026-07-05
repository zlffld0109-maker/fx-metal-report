import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fx_metal_report.analysis.trend import classify_metal_trend, classify_trend  # noqa: E402


def test_classify_trend_rising():
    series = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 106.0])
    result = classify_trend(series)
    assert result["label"] == "상승"
    assert result["latest"] == 106.0
    assert result["change_1d"] == 2.0


def test_classify_trend_falling():
    series = pd.Series([110.0, 109.0, 108.0, 107.0, 106.0, 104.0])
    result = classify_trend(series)
    assert result["label"] == "하락"
    assert result["change_1d"] == -2.0


def test_classify_trend_flat():
    series = pd.Series([100.0, 100.0, 100.0, 100.0, 100.0, 100.0])
    result = classify_trend(series)
    assert result["label"] == "보합"
    assert result["change_1d"] == 0.0


def test_classify_trend_insufficient_data():
    result = classify_trend(pd.Series([100.0]))
    assert result["label"] == "판정불가"
    assert result["change_1d"] is None


def test_classify_trend_ma_uses_available_window_when_short():
    series = pd.Series([100.0, 102.0])
    result = classify_trend(series)
    assert result["ma5"] == 101.0
    assert result["ma20"] == 101.0


def test_classify_metal_trend_rising_above_month_and_quarter_avg():
    dates = pd.to_datetime(
        ["2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05", "2026-07-06"]
    )
    values = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 110.0])
    result = classify_metal_trend(dates, values)
    assert result["label"] == "상승"
    assert result["latest"] == 110.0
    assert result["change_1d"] == 6.0
    assert result["quarters"][0]["label"] == "2026Q3 (당분기)"


def test_classify_metal_trend_falling_below_month_and_quarter_avg():
    dates = pd.to_datetime(
        ["2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05", "2026-07-06"]
    )
    values = pd.Series([110.0, 109.0, 108.0, 107.0, 106.0, 95.0])
    result = classify_metal_trend(dates, values)
    assert result["label"] == "하락"


def test_classify_metal_trend_compares_against_last_4_quarters_individually():
    dates = pd.to_datetime(
        [
            "2026-01-05",
            "2026-02-10",
            "2026-03-15",  # 2026Q1: 90, 100, 110 -> 평균 100
            "2026-04-10",
            "2026-05-12",
            "2026-06-20",  # 2026Q2(당분기): 140, 150, 200(최신) -> 평균 163.33
        ]
    )
    values = pd.Series([90.0, 100.0, 110.0, 140.0, 150.0, 200.0])

    result = classify_metal_trend(dates, values, num_quarters=4)

    assert result["latest"] == 200.0
    assert result["change_1d"] == 50.0
    # 6월 값은 최신 1건뿐이므로 당월평균 = 최신값
    assert result["month_avg"] == pytest.approx(200.0)

    labels = [q["label"] for q in result["quarters"]]
    assert labels == ["2026Q2 (당분기)", "2026Q1", "2025Q4", "2025Q3"]

    q2, q1, q4_2025, q3_2025 = result["quarters"]
    assert q2["avg"] == pytest.approx((140.0 + 150.0 + 200.0) / 3)
    assert q1["avg"] == pytest.approx(100.0)
    assert q1["vs_pct"] == pytest.approx(100.0)  # 200 vs 100 평균 -> +100%
    # 데이터가 없는 과거 분기는 평균/비교값이 None으로 남아야 함
    assert q4_2025["avg"] is None
    assert q4_2025["vs_pct"] is None
    assert q3_2025["avg"] is None

    # 유효한 2개 분기(2026Q1, 2026Q2) 모두 최신값보다 낮음 -> 상승
    assert result["label"] == "상승"


def test_classify_metal_trend_insufficient_data():
    result = classify_metal_trend(pd.Series([]), pd.Series([100.0]))
    assert result["label"] == "판정불가"
    assert result["change_1d"] is None
    assert result["month_avg"] is None
    assert result["quarters"] == []

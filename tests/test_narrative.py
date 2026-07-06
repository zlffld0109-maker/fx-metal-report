import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fx_metal_report.analysis.narrative import (  # noqa: E402
    build_fx_narrative,
    build_metal_narrative,
    build_outlook,
)

_FX_TRENDS = {
    "USD": {"change_1d_pct": -1.4, "vs_ma20_pct": -0.16, "label": "하락"},
    "EUR": {"change_1d_pct": -0.95, "vs_ma20_pct": -0.32, "label": "하락"},
    "JPY": {"change_1d_pct": -0.98, "vs_ma20_pct": -0.52, "label": "하락"},
    "CNY": {"change_1d_pct": -1.31, "vs_ma20_pct": -0.33, "label": "하락"},
}

_METAL_TRENDS = {
    "Cu": {
        "change_1d_pct": 0.73,
        "vs_month_avg_pct": 0.57,
        "prev_year": 2025,
        "vs_year_avg_pct": 19.89,
        "quarters": [{"label": "2026Q3 (당분기)", "avg": 13186.0, "vs_pct": 0.12}],
        "label": "상승",
    },
    "Al": {
        "change_1d_pct": 0.60,
        "vs_month_avg_pct": 0.25,
        "prev_year": 2025,
        "vs_year_avg_pct": 8.95,
        "quarters": [{"label": "2026Q3 (당분기)", "avg": 3068.25, "vs_pct": -0.22}],
        "label": "하락",
    },
    "Sn": {
        "change_1d_pct": 1.56,
        "vs_month_avg_pct": 1.07,
        "prev_year": 2025,
        "vs_year_avg_pct": 36.52,
        "quarters": [
            {"label": "2026Q3 (당분기)", "avg": 51175.0, "vs_pct": 0.05},
            {"label": "2026Q2", "avg": 52012.0, "vs_pct": -1.5},
            {"label": "2026Q1", "avg": 48679.0, "vs_pct": 5.2},
            {"label": "2025Q4", "avg": 38090.0, "vs_pct": 34.4},
        ],
        "label": "상승",
    },
}


def test_build_fx_narrative_all_down():
    paragraphs = build_fx_narrative(_FX_TRENDS)
    assert len(paragraphs) == 2
    assert "전 종목 하락" in paragraphs[0]
    assert "달러/원" in paragraphs[1]


def test_build_fx_narrative_empty():
    assert build_fx_narrative({}) == []


def test_build_metal_narrative_focuses_on_copper_and_aluminum():
    paragraphs = build_metal_narrative(_METAL_TRENDS)
    # lead + Cu 상세 + Al 상세 = 3문단. Sn은 관심 금속이 아니므로 상세 서술 대상에서 제외.
    assert len(paragraphs) == 3
    assert "구리" in paragraphs[1]
    assert "당분기 평균 대비" in paragraphs[1]
    assert "2025년 평균 대비" in paragraphs[1]
    assert "알루미늄" in paragraphs[2]
    assert "주석" not in paragraphs[1] and "주석" not in paragraphs[2]


def test_build_outlook_flags_usd_downtrend():
    bullets = build_outlook(_FX_TRENDS, {})
    assert any("달러/원" in b and "약세" in b for b in bullets)


def test_build_outlook_flags_metal_above_all_quarters():
    # outlook은 관심 금속(Cu/Al)만 본다. 둘 다 유효 분기가 1개뿐이라 (2개 미만) 분기 판정은 스킵되고,
    # 전년 평균 대비 괴리(Al +8.95%, Cu +19.89%)는 10%p 미만/이상 여부로 각각 판단된다.
    bullets = build_outlook({}, _METAL_TRENDS)
    assert any("구리" in b and "2025년 평균 대비" in b for b in bullets)
    assert not any("알루미늄" in b for b in bullets)  # Al은 +8.95%로 10%p 임계값 미만


def test_build_outlook_flags_metal_below_all_quarters():
    metal_trends = {
        "Cu": {
            "quarters": [
                {"label": "2026Q3 (당분기)", "avg": 1834.25, "vs_pct": -0.31},
                {"label": "2026Q2", "avg": 1954.26, "vs_pct": -6.44},
            ],
            "vs_year_avg_pct": None,
            "label": "하락",
        }
    }
    bullets = build_outlook({}, metal_trends)
    assert any("구리" in b and "하락 압력" in b for b in bullets)


def test_build_outlook_ignores_non_focus_metals():
    metal_trends = {
        "Pb": {
            "quarters": [
                {"label": "2026Q3 (당분기)", "avg": 1834.25, "vs_pct": -0.31},
                {"label": "2026Q2", "avg": 1954.26, "vs_pct": -6.44},
            ],
            "vs_year_avg_pct": -20.0,
            "label": "하락",
        }
    }
    bullets = build_outlook({}, metal_trends)
    assert bullets == []

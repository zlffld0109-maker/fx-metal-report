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
    "Cu": {"quarters": [{"label": "2026Q3 (당분기)", "avg": 13186.0, "vs_pct": 0.12}], "label": "상승"},
    "Al": {"quarters": [{"label": "2026Q3 (당분기)", "avg": 3068.25, "vs_pct": -0.22}], "label": "하락"},
    "Sn": {
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


def test_build_metal_narrative_mentions_strongest_and_weakest():
    paragraphs = build_metal_narrative(_METAL_TRENDS)
    assert len(paragraphs) == 2
    # Sn(당분기 vs_pct 0.05)이 Al(-0.22)보다 강하지만 Cu(0.12)보다 약함 -> Cu가 최강
    assert "구리" in paragraphs[1]
    assert "알루미늄" in paragraphs[1]


def test_build_outlook_flags_usd_downtrend():
    bullets = build_outlook(_FX_TRENDS, {})
    assert any("달러/원" in b and "약세" in b for b in bullets)


def test_build_outlook_flags_metal_above_all_quarters():
    bullets = build_outlook({}, _METAL_TRENDS)
    # Sn은 4개 유효 분기 중 3개(2026Q3, 2026Q1, 2025Q4)만 양수라 전체 상회 아님 -> 매칭 안 됨
    # Cu/Al은 유효 분기가 1개뿐이라 (2개 미만) 스킵됨
    assert bullets == []


def test_build_outlook_flags_metal_below_all_quarters():
    metal_trends = {
        "Pb": {
            "quarters": [
                {"label": "2026Q3 (당분기)", "avg": 1834.25, "vs_pct": -0.31},
                {"label": "2026Q2", "avg": 1954.26, "vs_pct": -6.44},
            ],
            "label": "하락",
        }
    }
    bullets = build_outlook({}, metal_trends)
    assert any("납" in b and "하락 압력" in b for b in bullets)

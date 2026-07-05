import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fx_metal_report.report.schema import FxMetalReport  # noqa: E402
from fx_metal_report.report.writer import render_email_html, render_markdown, write_report  # noqa: E402

_SAMPLE_TREND = {
    "latest": 1530.15,
    "change_1d": 5.2,
    "change_1d_pct": 0.34,
    "ma5": 1525.0,
    "ma20": 1520.0,
    "vs_ma5_pct": 0.34,
    "vs_ma20_pct": 0.67,
    "label": "상승",
}

_SAMPLE_METAL_TREND = {
    "latest": 13202.0,
    "change_1d": 32.0,
    "change_1d_pct": 0.24,
    "month_avg": 13100.0,
    "vs_month_avg_pct": 0.78,
    "quarters": [
        {"label": "2026Q3 (당분기)", "avg": 13100.0, "vs_pct": 0.78},
        {"label": "2026Q2", "avg": 13500.0, "vs_pct": -2.21},
        {"label": "2026Q1", "avg": None, "vs_pct": None},
        {"label": "2025Q4", "avg": None, "vs_pct": None},
    ],
    "label": "보합",
}


def _sample_report(warnings=None):
    return FxMetalReport(
        generated_at="2026-07-06 08:30:00",
        fx_trends={"USD": _SAMPLE_TREND, "EUR": _SAMPLE_TREND, "JPY": _SAMPLE_TREND, "CNY": _SAMPLE_TREND},
        metal_trends={k: _SAMPLE_METAL_TREND for k in ["Cu", "Al", "Zn", "Pb", "Ni", "Sn"]},
        warnings=warnings or [],
    )


def test_render_markdown_includes_sources_and_disclaimer():
    md = render_markdown(_sample_report())
    assert "## 자료 출처" in md
    assert "Yahoo Finance" in md
    assert "한국비철금속협회" in md
    assert "투자자문이 아닙니다" in md
    assert "달러/원" in md
    assert "구리(Cu)" in md


def test_render_markdown_includes_warnings_section_when_present():
    md = render_markdown(_sample_report(warnings=["비철금속 데이터 조회 실패"]))
    assert "## 경고 / 유의사항" in md
    assert "비철금속 데이터 조회 실패" in md


def test_render_markdown_omits_warnings_section_when_absent():
    md = render_markdown(_sample_report())
    assert "## 경고 / 유의사항" not in md


def test_render_email_html_includes_tables_and_source():
    html = render_email_html(_sample_report())
    assert "<table" in html
    assert "Yahoo Finance" in html
    assert "한국비철금속협회" in html


def test_render_markdown_includes_per_quarter_columns():
    md = render_markdown(_sample_report())
    assert "2026Q3 (당분기) 평균대비" in md
    assert "2026Q2 평균대비" in md
    assert "2025Q4 평균대비" in md
    assert "당월평균대비" in md


def test_render_markdown_includes_narrative_and_outlook():
    md = render_markdown(_sample_report())
    assert "금일 환율은" in md
    assert "LME 비철금속은" in md
    assert "## 시장 전망 (기술적 시사점)" in md
    assert "규칙 기반 해석" in md


def test_render_email_html_embeds_inline_chart_cids():
    html = render_email_html(_sample_report(), fx_chart_cid="fx_chart", metal_chart_cid="metal_chart")
    assert 'src="cid:fx_chart"' in html
    assert 'src="cid:metal_chart"' in html
    assert "금일 환율은" in html
    assert "시장 전망" in html


def test_render_email_html_omits_chart_img_when_cid_none():
    html = render_email_html(_sample_report(), fx_chart_cid=None, metal_chart_cid=None)
    assert "cid:" not in html


def test_write_report_creates_report_and_json(tmp_path):
    report_path = write_report(_sample_report(), tmp_path)
    assert report_path.exists()
    assert (tmp_path / "result.json").exists()
    assert report_path.read_text(encoding="utf-8").startswith("# 환율/비철금속 일일 리포트")

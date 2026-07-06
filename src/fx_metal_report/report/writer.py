from pathlib import Path

from fx_metal_report.analysis.narrative import build_fx_narrative, build_metal_narrative, build_outlook
from fx_metal_report.data.metal_source import SOURCE_LABEL as _METAL_SOURCE_LABEL
from fx_metal_report.labels import FX_LABELS, METAL_LABELS
from fx_metal_report.report.schema import FxMetalReport

_FX_SOURCE_LABEL = "Yahoo Finance (yfinance)"

_DISCLAIMER = (
    "본 리포트는 정보 제공 목적으로 자동 생성되었으며 투자자문이 아닙니다. "
    "매매/구매 결정에 대한 최종 판단과 책임은 이용자 본인에게 있습니다."
)


def _fmt(value, digits: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{digits}f}"


def _fmt_pct(value) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def _fx_table_rows(trends: dict) -> list[str]:
    lines = [
        "| 항목 | 최신값 | 전일대비 | 전일대비(%) | 5일평균대비 | 20일평균대비 | 추세 |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, t in trends.items():
        label = FX_LABELS.get(key, key)
        lines.append(
            f"| {label} | {_fmt(t['latest'])} | {_fmt(t['change_1d'])} | {_fmt_pct(t['change_1d_pct'])} | "
            f"{_fmt_pct(t['vs_ma5_pct'])} | {_fmt_pct(t['vs_ma20_pct'])} | {t['label']} |"
        )
    return lines


def _metal_quarter_labels(trends: dict) -> list[str]:
    first = next(iter(trends.values()), {})
    return [q["label"] for q in first.get("quarters", [])]


_FOCUS_METALS = {"Cu", "Al"}


def _metal_prev_year_label(trends: dict) -> str:
    first = next(iter(trends.values()), {})
    prev_year = first.get("prev_year")
    return f"{prev_year}년" if prev_year else "전년"


def _metal_table_rows(trends: dict) -> list[str]:
    quarter_labels = _metal_quarter_labels(trends)
    year_label = _metal_prev_year_label(trends)
    headers = ["항목", "최신값", "전일대비", "전일대비(%)", "당월평균대비"]
    headers += [f"{lbl} 평균대비" for lbl in quarter_labels]
    headers.append(f"{year_label} 평균대비")
    headers.append("추세")
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for key, t in trends.items():
        label = METAL_LABELS.get(key, key)
        if key in _FOCUS_METALS:
            label = f"**{label}**"
        cells = [
            label,
            _fmt(t["latest"]),
            _fmt(t["change_1d"]),
            _fmt_pct(t["change_1d_pct"]),
            _fmt_pct(t["vs_month_avg_pct"]),
        ]
        cells += [_fmt_pct(q["vs_pct"]) for q in t.get("quarters", [])]
        cells.append(_fmt_pct(t.get("vs_year_avg_pct")))
        cells.append(t["label"])
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _source_section_markdown(result: FxMetalReport) -> list[str]:
    return [
        "## 자료 출처",
        "",
        f"- 환율: {_FX_SOURCE_LABEL}",
        f"- 비철금속(LME 시세): {_METAL_SOURCE_LABEL}",
        f"- 조회 시각: {result.generated_at}",
        "",
        _DISCLAIMER,
    ]


def render_markdown(result: FxMetalReport) -> str:
    lines = [
        "# 환율/비철금속 일일 리포트",
        "",
        f"생성일시: {result.generated_at}",
        "",
        "## 환율",
        "",
        *_fx_table_rows(result.fx_trends),
        "",
        *build_fx_narrative(result.fx_trends),
        "",
        "## 비철금속 (LME 시세, US$/톤, 당월/당분기/전년 평균 대비, 구리·알루미늄 중점)",
        "",
        *_metal_table_rows(result.metal_trends),
        "",
        *build_metal_narrative(result.metal_trends),
        "",
    ]
    outlook = build_outlook(result.fx_trends, result.metal_trends)
    if outlook:
        lines += ["## 시장 전망 (기술적 시사점)", ""]
        lines += [f"- {b}" for b in outlook]
        lines += ["", "*본 전망은 가격/이동평균/분기평균 데이터에 기반한 규칙 기반 해석이며, 투자 성과를 보장하지 않습니다.*", ""]
    if result.warnings:
        lines += ["## 경고 / 유의사항", ""]
        lines += [f"- {w}" for w in result.warnings]
        lines.append("")
    lines += _source_section_markdown(result)
    return "\n".join(lines)


_INK = "#23262B"
_MUTED = "#746C5E"
_ACCENT = "#2D3A55"
_ACCENT_SOFT = "#E4E7EE"
_BORDER = "#DCD5C6"
_PILL_COLORS = {
    "상승": ("#B4452F", "#F3E3DE"),
    "하락": ("#34618C", "#DEE7EE"),
    "보합": ("#8B8377", "#ECE8E0"),
    "판정불가": ("#8B8377", "#ECE8E0"),
}
_TD_STYLE = (
    f"padding:9px 12px;border-bottom:1px solid {_BORDER};text-align:right;"
    f"font-size:12.8px;color:{_INK};white-space:nowrap;"
)
_TD_LABEL_STYLE = _TD_STYLE + "text-align:left;font-weight:600;"
_TH_STYLE = (
    f"padding:9px 12px;background:{_ACCENT_SOFT};color:{_ACCENT};font-weight:600;"
    "font-size:11.5px;text-align:right;white-space:nowrap;"
)
_TH_LABEL_STYLE = _TH_STYLE + "text-align:left;"
_FOCUS_BG = "#FBEDC7"
_FOCUS_LABEL_COLOR = "#8A5A12"


def _pill_html(label: str) -> str:
    color, bg = _PILL_COLORS.get(label, _PILL_COLORS["판정불가"])
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;'
        f'font-size:12px;font-weight:700;color:{color};background:{bg};">{label}</span>'
    )


def _table_wrapper(header_row: str, body_rows: str) -> str:
    table = (
        f'<table cellpadding="0" cellspacing="0" border="0" '
        f'style="border-collapse:collapse;width:100%;border:1px solid {_BORDER};border-radius:6px;">'
        f"<thead><tr>{header_row}</tr></thead><tbody>{body_rows}</tbody></table>"
    )
    # 컬럼이 많아 폭이 좁아지면 라벨 열이 글자 단위로 세로 줄바꿈되는 걸 막기 위해
    # 셀은 nowrap으로 고정하고, 넘치는 폭은 가로 스크롤로 처리한다.
    return f'<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">{table}</div>'


def _fx_table_html(trends: dict) -> str:
    rows = []
    for key, t in trends.items():
        label = FX_LABELS.get(key, key)
        rows.append(
            "<tr>"
            f'<td style="{_TD_LABEL_STYLE}">{label}</td>'
            f'<td style="{_TD_STYLE}">{_fmt(t["latest"])}</td>'
            f'<td style="{_TD_STYLE}">{_fmt(t["change_1d"])}</td>'
            f'<td style="{_TD_STYLE}">{_fmt_pct(t["change_1d_pct"])}</td>'
            f'<td style="{_TD_STYLE}">{_fmt_pct(t["vs_ma5_pct"])}</td>'
            f'<td style="{_TD_STYLE}">{_fmt_pct(t["vs_ma20_pct"])}</td>'
            f'<td style="{_TD_STYLE}">{_pill_html(t["label"])}</td>'
            "</tr>"
        )
    header = (
        f'<th style="{_TH_LABEL_STYLE}">항목</th><th style="{_TH_STYLE}">최신값</th>'
        f'<th style="{_TH_STYLE}">전일대비</th><th style="{_TH_STYLE}">전일대비(%)</th>'
        f'<th style="{_TH_STYLE}">5일평균대비</th><th style="{_TH_STYLE}">20일평균대비</th>'
        f'<th style="{_TH_STYLE}">추세</th>'
    )
    return _table_wrapper(header, "".join(rows))


def _metal_table_html(trends: dict) -> str:
    quarter_labels = _metal_quarter_labels(trends)
    year_label = _metal_prev_year_label(trends)
    rows = []
    for key, t in trends.items():
        label = METAL_LABELS.get(key, key)
        focus = key in _FOCUS_METALS
        td_style = _TD_STYLE + (f"background:{_FOCUS_BG};" if focus else "")
        label_style = _TD_LABEL_STYLE + (
            f"background:{_FOCUS_BG};color:{_FOCUS_LABEL_COLOR};" if focus else ""
        )
        label_text = f"★ {label}" if focus else label
        cells = (
            f'<td style="{label_style}">{label_text}</td>'
            f'<td style="{td_style}">{_fmt(t["latest"])}</td>'
            f'<td style="{td_style}">{_fmt(t["change_1d"])}</td>'
            f'<td style="{td_style}">{_fmt_pct(t["change_1d_pct"])}</td>'
            f'<td style="{td_style}">{_fmt_pct(t["vs_month_avg_pct"])}</td>'
        )
        cells += "".join(
            f'<td style="{td_style}">{_fmt_pct(q["vs_pct"])}</td>' for q in t.get("quarters", [])
        )
        cells += f'<td style="{td_style}">{_fmt_pct(t.get("vs_year_avg_pct"))}</td>'
        cells += f'<td style="{td_style}">{_pill_html(t["label"])}</td>'
        rows.append(f"<tr>{cells}</tr>")
    header_cells = "".join(f'<th style="{_TH_STYLE}">{lbl} 평균대비</th>' for lbl in quarter_labels)
    header = (
        f'<th style="{_TH_LABEL_STYLE}">항목</th><th style="{_TH_STYLE}">최신값</th>'
        f'<th style="{_TH_STYLE}">전일대비</th><th style="{_TH_STYLE}">전일대비(%)</th>'
        f'<th style="{_TH_STYLE}">당월평균대비</th>{header_cells}'
        f'<th style="{_TH_STYLE}">{year_label} 평균대비</th><th style="{_TH_STYLE}">추세</th>'
    )
    return _table_wrapper(header, "".join(rows))


def _narrative_html(paragraphs: list[str]) -> str:
    if not paragraphs:
        return ""
    ps = "".join(
        f'<p style="color:{_INK};font-size:13.5px;line-height:1.75;margin:10px 0 0;">{p}</p>'
        for p in paragraphs
    )
    return ps


def _outlook_html(bullets: list[str]) -> str:
    if not bullets:
        return ""
    items = "".join(
        f'<li style="margin-bottom:6px;">{b}</li>' for b in bullets
    )
    section_title_style = (
        f"font-family:Georgia,'Noto Serif KR',serif;font-size:17px;font-weight:600;"
        f"color:{_INK};margin:28px 0 12px;padding-bottom:8px;border-bottom:2px solid {_ACCENT};"
    )
    return f"""
      <h2 style="{section_title_style}">시장 전망 (기술적 시사점)</h2>
      <ul style="color:{_INK};font-size:13.5px;line-height:1.6;margin:0;padding-left:20px;">{items}</ul>
      <p style="font-size:11.5px;color:{_MUTED};font-style:italic;margin-top:8px;">
        본 전망은 가격/이동평균/분기평균 데이터에 기반한 규칙 기반 해석이며, 투자 성과를 보장하지 않습니다.
      </p>
    """


def render_email_html(
    result: FxMetalReport,
    fx_chart_cid: str | None = "fx_chart",
    metal_chart_cid: str | None = "metal_chart",
) -> str:
    warnings_html = ""
    if result.warnings:
        items = "".join(f"<li>{w}</li>" for w in result.warnings)
        warnings_html = (
            f'<h3 style="font-family:Georgia,\'Noto Serif KR\',serif;font-size:16px;'
            f'color:{_INK};margin:28px 0 10px;">경고 / 유의사항</h3>'
            f'<ul style="color:{_INK};font-size:13px;line-height:1.7;margin:0;padding-left:20px;">{items}</ul>'
        )

    section_title_style = (
        f"font-family:Georgia,'Noto Serif KR',serif;font-size:17px;font-weight:600;"
        f"color:{_INK};margin:28px 0 12px;padding-bottom:8px;border-bottom:2px solid {_ACCENT};"
    )

    fx_chart_html = (
        f'<img src="cid:{fx_chart_cid}" alt="환율 추이" style="width:100%;max-width:100%;'
        f'display:block;margin-top:14px;border:1px solid {_BORDER};border-radius:6px;">'
        if fx_chart_cid
        else ""
    )
    metal_chart_html = (
        f'<img src="cid:{metal_chart_cid}" alt="LME 비철금속 시세 추이" style="width:100%;max-width:100%;'
        f'display:block;margin-top:14px;border:1px solid {_BORDER};border-radius:6px;">'
        if metal_chart_cid
        else ""
    )

    outlook = build_outlook(result.fx_trends, result.metal_trends)

    return f"""\
<!doctype html>
<html>
<body style="margin:0;padding:24px 16px;background:#F7F4EC;font-family:-apple-system,'Segoe UI','Noto Sans KR',sans-serif;">
  <table cellpadding="0" cellspacing="0" border="0" align="center" width="700"
         style="max-width:700px;width:100%;background:#FFFFFF;border:1px solid {_BORDER};border-radius:10px;margin:0 auto;">
    <tr><td style="padding:8px 28px 32px;">
      <p style="font-size:11.5px;letter-spacing:0.12em;text-transform:uppercase;color:{_ACCENT};
                font-weight:700;margin:20px 0 10px;">일일 자동 리포트</p>
      <h1 style="font-family:Georgia,'Noto Serif KR',serif;font-size:26px;font-weight:600;
                  color:{_INK};margin:0 0 4px;">환율/비철금속 일일 리포트</h1>
      <p style="color:{_MUTED};font-size:13.5px;margin:0 0 24px;">생성일시 {result.generated_at}</p>

      <h2 style="{section_title_style}">환율</h2>
      {_fx_table_html(result.fx_trends)}
      {_narrative_html(build_fx_narrative(result.fx_trends))}
      {fx_chart_html}

      <h2 style="{section_title_style}">비철금속 (LME 시세, US$/톤, 구리·알루미늄 중점 ★)</h2>
      {_metal_table_html(result.metal_trends)}
      {_narrative_html(build_metal_narrative(result.metal_trends))}
      {metal_chart_html}

      {_outlook_html(outlook)}

      {warnings_html}

      <div style="margin-top:32px;padding-top:18px;border-top:1px dashed {_BORDER};
                  font-size:12.5px;color:{_MUTED};line-height:1.8;">
        <b style="color:{_INK};">자료 출처</b><br>
        환율: {_FX_SOURCE_LABEL}<br>
        비철금속(LME 시세): {_METAL_SOURCE_LABEL}<br>
        조회 시각: {result.generated_at}
        <p style="font-size:11.5px;color:{_MUTED};margin-top:10px;">{_DISCLAIMER}</p>
      </div>
    </td></tr>
  </table>
</body>
</html>
"""


def write_report(result: FxMetalReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.md"
    report_path.write_text(render_markdown(result), encoding="utf-8")
    result.to_json(output_dir / "result.json")
    return report_path

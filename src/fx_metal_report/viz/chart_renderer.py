from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fx_metal_report.labels import FX_LABELS as _FX_LABELS
from fx_metal_report.labels import METAL_LABELS as _METAL_LABELS

_LINE_COLOR = "#1f77b4"


def render_fx_chart(fx_data: dict[str, pd.Series], output_path: Path) -> Path:
    """통화별 환율 추이를 2x2 서브플롯 라인차트로 렌더링한다."""
    labels = list(fx_data.keys())
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[_FX_LABELS.get(label, label) for label in labels],
    )
    for i, label in enumerate(labels):
        series = fx_data[label]
        row, col = i // 2 + 1, i % 2 + 1
        fig.add_trace(
            go.Scatter(
                x=series.index.to_pydatetime(),
                y=series.values,
                mode="lines",
                name=label,
                line=dict(color=_LINE_COLOR),
            ),
            row=row,
            col=col,
        )
    fig.update_layout(height=700, width=1000, template="plotly_white", showlegend=False, title="환율 추이")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(output_path))
    return output_path


def render_metal_chart(metal_df: pd.DataFrame, output_path: Path) -> Path:
    """LME 6대 비철금속 시세 추이를 3x2 서브플롯 라인차트로 렌더링한다."""
    metals = [c for c in metal_df.columns if c != "date"]
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=[_METAL_LABELS.get(m, m) for m in metals],
    )
    for i, metal in enumerate(metals):
        row, col = i // 2 + 1, i % 2 + 1
        fig.add_trace(
            go.Scatter(
                x=metal_df["date"].dt.to_pydatetime(),
                y=metal_df[metal],
                mode="lines",
                name=metal,
                line=dict(color=_LINE_COLOR),
            ),
            row=row,
            col=col,
        )
    fig.update_layout(
        height=900, width=1000, template="plotly_white", showlegend=False, title="LME 비철금속 시세 추이 (US$/톤)"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(output_path))
    return output_path

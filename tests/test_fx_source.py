import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fx_metal_report.data.fx_source import get_fx_rates  # noqa: E402


def _mock_ticker(close_values):
    ticker = MagicMock()
    idx = pd.date_range("2026-07-01", periods=len(close_values), freq="D")
    ticker.history.return_value = pd.DataFrame({"Close": close_values}, index=idx)
    return ticker


def test_get_fx_rates_computes_cny_cross_rate():
    tickers = {
        "KRW=X": _mock_ticker([1300.0, 1310.0]),
        "EURKRW=X": _mock_ticker([1400.0, 1410.0]),
        "JPYKRW=X": _mock_ticker([9.0, 9.1]),
        "USDCNY=X": _mock_ticker([7.0, 7.1]),
    }

    def fake_ticker(symbol):
        return tickers[symbol]

    with patch("fx_metal_report.data.fx_source.yf.Ticker", side_effect=fake_ticker):
        rates = get_fx_rates(period="5d")

    assert set(rates.keys()) == {"USD", "EUR", "JPY", "CNY"}
    assert rates["USD"].iloc[-1] == 1310.0
    # JPY는 100엔당으로 환산되어야 함
    assert rates["JPY"].iloc[-1] == pytest.approx(910.0)
    # CNY = USDKRW / USDCNY 교차환율
    assert rates["CNY"].iloc[-1] == pytest.approx(1310.0 / 7.1)

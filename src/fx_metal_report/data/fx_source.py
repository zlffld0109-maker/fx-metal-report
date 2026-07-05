import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

_TICKERS = {
    "USD": "KRW=X",
    "EUR": "EURKRW=X",
    "JPY": "JPYKRW=X",
}
_JPY_QUOTE_UNIT = 100  # 관례상 100엔당 원화로 표시 (원단위 JPYKRW=X 값에 100을 곱함)


def get_fx_rates(period: str = "1mo") -> dict[str, pd.Series]:
    """USD/EUR/JPY(100엔당)/CNY 대비 원화 환율의 종가 시계열을 반환한다.

    CNYKRW=X 티커는 데이터 결함으로 사용하지 않고, USDKRW=X ÷ USDCNY=X 교차환율로 계산한다.
    """
    rates: dict[str, pd.Series] = {}
    for label, ticker in _TICKERS.items():
        close = yf.Ticker(ticker).history(period=period)["Close"]
        if label == "JPY":
            close = close * _JPY_QUOTE_UNIT
        rates[label] = close

    usdcny_close = yf.Ticker("USDCNY=X").history(period=period)["Close"]
    combined = pd.concat([rates["USD"], usdcny_close], axis=1, keys=["usdkrw", "usdcny"]).dropna()
    rates["CNY"] = combined["usdkrw"] / combined["usdcny"]

    return rates

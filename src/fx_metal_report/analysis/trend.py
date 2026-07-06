import pandas as pd


def _prior_quarter_keys(year: int, quarter: int, count: int) -> list[tuple[int, int]]:
    """(year, quarter)부터 과거로 count개의 (year, quarter) 키를 최신순으로 반환한다."""
    keys = []
    y, q = year, quarter
    for _ in range(count):
        keys.append((y, q))
        q -= 1
        if q == 0:
            q, y = 4, y - 1
    return keys


def classify_metal_trend(dates: pd.Series, values: pd.Series, num_quarters: int = 4) -> dict:
    """비철금속 전용: 당월(달력 기준) 평균 및 최근 `num_quarters`개 분기(달력 기준) 평균 각각과
    금일 가격을 비교해 추세를 판정한다.

    dates: 오름차순 정렬된 날짜 Series (datetime64), values: 같은 인덱스의 가격 Series.
    """
    if len(values) < 2:
        return {
            "latest": float(values.iloc[-1]) if len(values) else None,
            "change_1d": None,
            "change_1d_pct": None,
            "month_avg": None,
            "vs_month_avg_pct": None,
            "quarters": [],
            "prev_year": None,
            "year_avg": None,
            "vs_year_avg_pct": None,
            "label": "판정불가",
        }

    dates = pd.Series(pd.to_datetime(dates)).reset_index(drop=True)
    values = pd.Series(values).reset_index(drop=True)

    latest_date = dates.iloc[-1]
    latest = float(values.iloc[-1])
    prev = float(values.iloc[-2])
    change_1d = latest - prev
    change_1d_pct = (change_1d / prev * 100) if prev else None

    month_mask = (dates.dt.year == latest_date.year) & (dates.dt.month == latest_date.month)
    month_avg = float(values[month_mask].mean()) if month_mask.any() else None
    vs_month_avg_pct = (latest - month_avg) / month_avg * 100 if month_avg else None

    prev_year = latest_date.year - 1
    year_mask = dates.dt.year == prev_year
    year_avg = float(values[year_mask].mean()) if year_mask.any() else None
    vs_year_avg_pct = (latest - year_avg) / year_avg * 100 if year_avg else None

    current_quarter = (latest_date.month - 1) // 3 + 1
    quarter_keys = _prior_quarter_keys(latest_date.year, current_quarter, num_quarters)

    quarters = []
    above_count = below_count = valid_count = 0
    for year, quarter in quarter_keys:
        quarter_months = range(3 * quarter - 2, 3 * quarter + 1)
        mask = (dates.dt.year == year) & (dates.dt.month.isin(quarter_months))
        avg = float(values[mask].mean()) if mask.any() else None
        vs_pct = (latest - avg) / avg * 100 if avg else None
        if avg is not None:
            valid_count += 1
            if latest > avg:
                above_count += 1
            elif latest < avg:
                below_count += 1
        suffix = " (당분기)" if (year, quarter) == (latest_date.year, current_quarter) else ""
        quarters.append({"label": f"{year}Q{quarter}{suffix}", "avg": avg, "vs_pct": vs_pct})

    majority = valid_count // 2 + 1
    if valid_count == 0:
        label = "판정불가"
    elif above_count >= majority:
        label = "상승"
    elif below_count >= majority:
        label = "하락"
    else:
        label = "보합"

    return {
        "latest": latest,
        "change_1d": change_1d,
        "change_1d_pct": change_1d_pct,
        "month_avg": month_avg,
        "vs_month_avg_pct": vs_month_avg_pct,
        "quarters": quarters,
        "prev_year": prev_year,
        "year_avg": year_avg,
        "vs_year_avg_pct": vs_year_avg_pct,
        "label": label,
    }


def classify_trend(series: pd.Series) -> dict:
    """오름차순(과거->최신)으로 정렬된 가격 시계열을 받아 전일비/이동평균 대비 추세를 판정한다."""
    if len(series) < 2:
        return {
            "latest": float(series.iloc[-1]) if len(series) else None,
            "change_1d": None,
            "change_1d_pct": None,
            "ma5": None,
            "ma20": None,
            "vs_ma5_pct": None,
            "vs_ma20_pct": None,
            "label": "판정불가",
        }

    latest = float(series.iloc[-1])
    prev = float(series.iloc[-2])
    change_1d = latest - prev
    change_1d_pct = (change_1d / prev * 100) if prev else None

    ma5 = float(series.tail(5).mean())
    ma20 = float(series.tail(20).mean())
    vs_ma5_pct = (latest - ma5) / ma5 * 100 if ma5 else None
    vs_ma20_pct = (latest - ma20) / ma20 * 100 if ma20 else None

    if change_1d > 0 and latest >= ma5:
        label = "상승"
    elif change_1d < 0 and latest <= ma5:
        label = "하락"
    else:
        label = "보합"

    return {
        "latest": latest,
        "change_1d": change_1d,
        "change_1d_pct": change_1d_pct,
        "ma5": ma5,
        "ma20": ma20,
        "vs_ma5_pct": vs_ma5_pct,
        "vs_ma20_pct": vs_ma20_pct,
        "label": label,
    }

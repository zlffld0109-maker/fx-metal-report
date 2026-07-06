from fx_metal_report.labels import FX_LABELS, METAL_LABELS


def _fmt_pct(value) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def _direction_phrase(count_up: int, count_down: int, total: int) -> str:
    if total == 0:
        return "판정불가"
    if count_up == total:
        return "전 종목 상승"
    if count_down == total:
        return "전 종목 하락"
    if count_up > count_down:
        return "상승 우위의 혼조"
    if count_down > count_up:
        return "하락 우위의 혼조"
    return "혼조"


def build_fx_narrative(fx_trends: dict) -> list[str]:
    """환율 트렌드 딕셔너리로부터 간단한 시장 코멘트 문단(2개)을 생성한다."""
    if not fx_trends:
        return []

    total = len(fx_trends)
    up = [k for k, t in fx_trends.items() if t["label"] == "상승"]
    down = [k for k, t in fx_trends.items() if t["label"] == "하락"]
    phrase = _direction_phrase(len(up), len(down), total)
    lead = f"금일 환율은 {phrase} 흐름을 보였습니다."

    detail_parts = []
    for key, t in fx_trends.items():
        label = FX_LABELS.get(key, key)
        ma20 = t.get("vs_ma20_pct")
        ma_side = "상회" if (ma20 or 0) >= 0 else "하회"
        detail_parts.append(f"{label} {_fmt_pct(t['change_1d_pct'])}({t['label']}, 20일 평균 {ma_side})")
    detail = "통화별로는 " + ", ".join(detail_parts) + "했습니다."

    return [lead, detail]


_FOCUS_METALS = ("Cu", "Al")


def _metal_detail_sentence(key: str, t: dict) -> str:
    label = METAL_LABELS.get(key, key)
    quarters = t.get("quarters") or []
    cur_q = quarters[0] if quarters else None
    q_part = (
        f", 당분기 평균 대비 {_fmt_pct(cur_q['vs_pct'])}"
        if cur_q and cur_q.get("vs_pct") is not None
        else ""
    )
    year_part = ""
    if t.get("vs_year_avg_pct") is not None:
        year_part = f", {t.get('prev_year')}년 평균 대비 {_fmt_pct(t['vs_year_avg_pct'])}"
    return (
        f"{label}은(는) 전일대비 {_fmt_pct(t.get('change_1d_pct'))}, "
        f"당월 평균 대비 {_fmt_pct(t.get('vs_month_avg_pct'))}{q_part}{year_part}로 "
        f"{t.get('label', '판정불가')} 흐름입니다."
    )


def build_metal_narrative(metal_trends: dict) -> list[str]:
    """비철금속 트렌드 딕셔너리로부터 시장 코멘트 문단을 생성한다.

    창성에이스산업이 실제로 관심 있는 금속은 구리(Cu)·알루미늄(Al)이므로,
    전체 동향 요약 한 줄 뒤에는 두 금속을 중점적으로 상세 서술한다.
    """
    if not metal_trends:
        return []

    total = len(metal_trends)
    up = [k for k, t in metal_trends.items() if t["label"] == "상승"]
    down = [k for k, t in metal_trends.items() if t["label"] == "하락"]
    phrase = _direction_phrase(len(up), len(down), total)
    lead = f"LME 비철금속은 {phrase}를 나타냈습니다."

    paragraphs = [lead]
    for key in _FOCUS_METALS:
        t = metal_trends.get(key)
        if t is not None:
            paragraphs.append(_metal_detail_sentence(key, t))
    return paragraphs


def build_outlook(fx_trends: dict, metal_trends: dict) -> list[str]:
    """전일비/이동평균/분기평균 데이터를 근거로 한 규칙 기반 기술적 시사점 목록을 생성한다.

    실제 가격 예측이 아니라, 현재 추세가 이어질 경우의 기술적 해석을 제공하는 목적이다.
    """
    bullets: list[str] = []

    usd = fx_trends.get("USD")
    if usd is not None:
        ma20 = usd.get("vs_ma20_pct") or 0
        if usd["label"] == "하락" and ma20 < 0:
            bullets.append(
                "달러/원이 20일 평균을 하회한 채 하락세를 이어가고 있어 단기적으로 추가 약세 가능성에 무게가 실립니다."
            )
        elif usd["label"] == "상승" and ma20 > 0:
            bullets.append(
                "달러/원이 20일 평균을 상회한 채 상승세를 이어가고 있어 단기적으로 추가 강세 가능성에 무게가 실립니다."
            )
        else:
            bullets.append("달러/원은 뚜렷한 방향성 없이 등락하고 있어 추세 전환 신호를 좀 더 지켜볼 필요가 있습니다.")

    # 창성에이스산업 관심 금속(구리·알루미늄)을 중점적으로 전망에 반영한다.
    for key in _FOCUS_METALS:
        t = metal_trends.get(key)
        if t is None:
            continue
        quarters = t.get("quarters") or []
        valid = [q for q in quarters if q["avg"] is not None]
        label = METAL_LABELS.get(key, key)
        if len(valid) >= 2:
            above = sum(1 for q in valid if (q["vs_pct"] or 0) > 0)
            if above == len(valid):
                bullets.append(f"{label}은(는) 비교 가능한 분기 평균을 모두 상회하고 있어 중기 상승 모멘텀이 우세합니다.")
            elif above == 0:
                bullets.append(f"{label}은(는) 비교 가능한 분기 평균을 모두 하회하고 있어 중기 하락 압력이 이어지고 있습니다.")
        year_pct = t.get("vs_year_avg_pct")
        if year_pct is not None and abs(year_pct) >= 10:
            side = "크게 상회" if year_pct > 0 else "크게 하회"
            bullets.append(f"{label}은(는) {t.get('prev_year')}년 평균 대비 {_fmt_pct(year_pct)}로 {side}하고 있어 연간 기준 가격 레벨 변화에 유의할 필요가 있습니다.")

    return bullets

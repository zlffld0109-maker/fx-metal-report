# fx-metal-report

매일(평일) 환율과 LME 비철금속(구리·알루미늄·아연·납·니켈·주석) 시세를 조회해 추세를 분석하고,
차트가 포함된 리포트를 만들어 이메일로 발송하는 자동화 도구입니다.
`D:\agent\chart-analyzer`, `D:\agent\trading-bot`과는 완전히 별개 프로젝트입니다.

## 데이터 출처

- **환율**: Yahoo Finance(`yfinance`) — USD(`KRW=X`), EUR(`EURKRW=X`), JPY(`JPYKRW=X`, 100엔당으로 환산),
  CNY는 `USDKRW=X ÷ USDCNY=X` 교차환율로 계산(직접 티커 `CNYKRW=X`는 데이터 결함으로 사용하지 않음).
- **비철금속(LME 시세)**: [한국비철금속협회](https://www.nonferrous.or.kr/stats/?act=sub3) 통계정보 > LME시세
  페이지를 파싱. Cu/Al/Zn/Pb/Ni/Sn 6종을 "현물 US$/톤" 단위로 매일 게시하는 정적 HTML 표를 이용합니다.
  최근 4개 분기 평균 비교를 위해 기본 14페이지(약 1년치)를 가져옵니다(`settings.METAL_PAGES`).

두 출처 모두 리포트 하단 "자료 출처" 섹션에 항상 명시됩니다.

## 처음 설정

```powershell
cd D:\agent\fx-metal-report
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

`.env.example`을 복사해 `.env`를 만들고 SMTP 계정 정보를 입력하세요:

```
SMTP_HOST=wsmtp.ecount.com
SMTP_PORT=465
SMTP_USER=본인메일@example.com
SMTP_PASSWORD=비밀번호
MAIL_TO=받을메일@example.com
```

`.env`는 `.gitignore`에 포함되어 있어 git에 커밋되지 않습니다.

## 실행 방법

```powershell
# 이메일 발송 없이 리포트만 생성(테스트용)
.\venv\Scripts\python run_report.py --dry-run

# 실제로 이메일까지 발송
.\venv\Scripts\python run_report.py

# 테스트 실행
.\venv\Scripts\python -m pytest
```

실행 결과는 `D:\agent\results\fx-metal-report\{YYYYMMDD}\`에 `report.md`, `result.json`,
`fx_chart.png`, `metal_chart.png`로 저장됩니다. 이메일 본문은 표 형태의 요약 HTML이고,
차트 PNG 2장과 `report.md`가 첨부파일로 함께 발송됩니다.

환율은 전일대비/5일·20일 이동평균 대비로, 비철금속은 전일대비/당월(달력 기준)평균 대비/
**최근 4개 분기(당분기 포함) 각각의 평균 대비**로 분석합니다. 각 분기 평균과 금일 가격을
개별 비교해 표에 분기별 컬럼으로 표시하며, 유효 분기 중 과반수 이상에서 위/아래에 있으면
상승/하락, 그렇지 않으면 보합으로 판정합니다.

비철금속 데이터 조회에 실패해도(사이트 구조 변경 등) 환율 리포트는 정상 발송되며,
실패 사실은 리포트의 "경고 / 유의사항" 섹션에 남습니다.

## 매일(평일) 자동 실행 등록

```powershell
.\scripts\setup_task_scheduler.ps1
# 시각을 바꾸고 싶으면: .\scripts\setup_task_scheduler.ps1 -Time "07:30"
```

Windows 작업 스케줄러에 월~금요일 지정 시각(기본 08:30)에 실행되는 작업(`FxMetalReport_DailyEmail`)을
등록합니다. venv/스크립트 존재 여부를 확인한 뒤 y/N 확인을 받고서만 등록을 진행합니다.

## 폴더 구조

```
config/            설정(settings.py) — pydantic-settings, SMTP/MAIL_TO/REPORTS_DIR 등
src/fx_metal_report/
  data/            fx_source(yfinance 환율) / metal_source(nonferrous.or.kr 스크래핑)
  analysis/        trend — classify_trend(환율, 전일비/5일·20일 이평 대비) /
                   classify_metal_trend(비철금속, 전일비/당월평균/최근 4개 분기 평균 개별 비교)
  viz/             plotly+Kaleido 라인차트(환율 2x2, 비철금속 3x2 서브플롯) PNG 렌더링
  report/          FxMetalReport 스키마 + 마크다운/이메일용 HTML 리포트 작성(자료 출처 포함)
  email_sender.py  smtplib 기반 발송 (포트 465=SSL, 그 외=STARTTLS), 첨부파일 지원
  labels.py        통화/금속 한글 표시명 공용 상수
tests/             pytest (yfinance/requests/smtplib는 mock, nonferrous.or.kr은 고정 HTML fixture 사용)
scripts/
  setup_task_scheduler.ps1  평일 전용 Windows 작업 스케줄러 등록
run_report.py       엔트리포인트 (--dry-run 지원)
```

## 알려진 제약

- 한국비철금속협회 페이지는 공식 API가 아닌 HTML 표 파싱에 의존하므로, 사이트 구조가 바뀌면
  `metal_source.py`의 파싱 로직 수정이 필요할 수 있습니다(`get_metal_prices()` 실패 시 경고만 남기고
  환율 리포트는 계속 정상 발송되도록 격리되어 있음).
- yfinance는 비공식 API라 레이트리밋/스키마 변경 리스크가 있습니다.
- 본 리포트는 정보 제공 목적이며 투자자문이 아닙니다.

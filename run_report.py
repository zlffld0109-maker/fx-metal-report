#!/usr/bin/env python3
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config.settings import settings  # noqa: E402
from fx_metal_report.analysis.trend import classify_metal_trend, classify_trend  # noqa: E402
from fx_metal_report.data.fx_source import get_fx_rates  # noqa: E402
from fx_metal_report.data.metal_source import get_metal_prices  # noqa: E402
from fx_metal_report.email_sender import send_email  # noqa: E402
from fx_metal_report.report.schema import FxMetalReport  # noqa: E402
from fx_metal_report.report.writer import render_email_html, write_report  # noqa: E402
from fx_metal_report.viz.chart_renderer import render_fx_chart, render_metal_chart  # noqa: E402

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="환율/비철금속 일일 리포트 생성 및 이메일 발송")
    parser.add_argument("--dry-run", action="store_true", help="이메일 발송 없이 리포트만 생성")
    parser.add_argument("--outdir", default=None, help="출력 디렉터리 (기본: settings.REPORTS_DIR/오늘날짜)")
    return parser.parse_args()


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run(args) -> Path:
    now = datetime.now()
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    outdir = Path(args.outdir) if args.outdir else settings.REPORTS_DIR / now.strftime("%Y%m%d")
    outdir.mkdir(parents=True, exist_ok=True)

    warnings = []

    fx_data = get_fx_rates(period="2mo")
    fx_trends = {label: classify_trend(series) for label, series in fx_data.items()}
    fx_chart_path = render_fx_chart(fx_data, outdir / "fx_chart.png")

    metal_trends: dict = {}
    metal_chart_path = None
    try:
        metal_df = get_metal_prices(pages=settings.METAL_PAGES)
        metal_trends = {
            m: classify_metal_trend(metal_df["date"], metal_df[m]) for m in settings.METALS
        }
        metal_chart_path = render_metal_chart(metal_df, outdir / "metal_chart.png")
    except Exception as exc:
        logger.warning(f"비철금속 데이터 조회 실패: {exc}")
        warnings.append(f"비철금속 데이터 조회 실패: {exc}")

    result = FxMetalReport(
        generated_at=generated_at,
        fx_trends=fx_trends,
        metal_trends=metal_trends,
        warnings=warnings,
    )
    report_path = write_report(result, outdir)
    logger.info(f"리포트 생성 완료: {report_path}")

    if args.dry_run:
        logger.info("[dry-run] 이메일 발송을 건너뜁니다.")
        return report_path

    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.MAIL_TO:
        logger.warning("SMTP 설정이 없어 이메일 발송을 건너뜁니다 (.env 확인 필요)")
        return report_path

    inline_images = {}
    if fx_chart_path:
        inline_images["fx_chart"] = fx_chart_path
    if metal_chart_path:
        inline_images["metal_chart"] = metal_chart_path

    subject = f"[일일 시황] 환율/비철금속 리포트 - {now.strftime('%Y-%m-%d')}"
    ok = send_email(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        settings.SMTP_USER,
        settings.SMTP_PASSWORD,
        settings.MAIL_TO,
        subject,
        render_email_html(
            result,
            fx_chart_cid="fx_chart" if fx_chart_path else None,
            metal_chart_cid="metal_chart" if metal_chart_path else None,
        ),
        attachments=[report_path],
        inline_images=inline_images,
    )
    if ok:
        logger.info(f"이메일 발송 완료 -> {settings.MAIL_TO}")
    else:
        logger.warning("이메일 발송 실패")

    return report_path


def main():
    setup_logging()
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()

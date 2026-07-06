from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    REPORTS_DIR: Path = Path(r"D:\agent\results\fx-metal-report")

    FX_PAIRS: list[str] = ["USD", "EUR", "JPY", "CNY"]
    METALS: list[str] = ["Cu", "Al", "Zn", "Pb", "Ni", "Sn"]
    METAL_PAGES: int = 22  # 최근 4개 분기 + 전년(1년 전체) 평균 비교에 충분한 과거 데이터 확보용

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 465
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    MAIL_TO: str | None = None


settings = Settings()
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

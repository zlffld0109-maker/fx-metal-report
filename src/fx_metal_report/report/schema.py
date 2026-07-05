import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class FxMetalReport:
    generated_at: str
    fx_trends: dict  # {"USD": {...classify_trend 결과...}, ...}
    metal_trends: dict  # {"Cu": {...}, ...}
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path: Path | None = None) -> str:
        text = json.dumps(self.to_dict(), ensure_ascii=False, indent=2, default=str)
        if path is not None:
            path.write_text(text, encoding="utf-8")
        return text

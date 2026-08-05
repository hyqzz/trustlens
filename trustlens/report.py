"""评测结果的持久化：data/results/<slug>.json。"""
from __future__ import annotations

import json
from pathlib import Path

from .models import ServerReport

RESULTS_DIR = Path("data/results")


def save_report(report: ServerReport, results_dir: Path | None = None) -> Path:
    from .engine import slugify
    d = Path(results_dir) if results_dir else RESULTS_DIR
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{slugify(report.name)}.json"
    path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_all(results_dir: Path | None = None) -> list[ServerReport]:
    d = Path(results_dir) if results_dir else RESULTS_DIR
    reports: list[ServerReport] = []
    if not d.exists():
        return reports
    for path in sorted(d.glob("*.json")):
        try:
            reports.append(ServerReport.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue  # 跳过损坏文件，不中断
    return reports

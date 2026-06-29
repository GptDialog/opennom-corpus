#!/usr/bin/env python3
"""Счётчик прогресса корпуса OpenNom.

Считает строки по темам и статусам + число аудиозаписей.
Пишет counts.json в корень репозитория — публичный счётчик прогресса
(его читает питч-сайт).

Запуск:
    python scripts/counts.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TEXT_DIR = ROOT / "corpus" / "text"
AUDIO_MANIFEST = ROOT / "corpus" / "audio" / "manifest.csv"
OUT = ROOT / "counts.json"

STATUSES = ["draft", "translated", "verified", "published"]


def main() -> None:
    frames = []
    for path in sorted(p for p in TEXT_DIR.glob("*.csv") if not p.name.startswith("_")):
        df = pd.read_csv(path, dtype=str, encoding="utf-8").fillna("")
        frames.append(df)

    if frames:
        data = pd.concat(frames, ignore_index=True)
    else:
        data = pd.DataFrame(columns=["theme", "status"])

    total = int(len(data))

    by_status = {s: int((data.get("status", pd.Series(dtype=str)) == s).sum()) for s in STATUSES}

    by_theme: dict[str, dict] = {}
    if total:
        for theme, grp in data.groupby("theme"):
            by_theme[str(theme)] = {
                "total": int(len(grp)),
                **{s: int((grp["status"] == s).sum()) for s in STATUSES},
            }

    audio_count = 0
    if AUDIO_MANIFEST.exists():
        adf = pd.read_csv(AUDIO_MANIFEST, dtype=str, encoding="utf-8").fillna("")
        audio_count = int((adf.get("audio_id", pd.Series(dtype=str)).str.strip() != "").sum())

    result = {
        "total_entries": total,
        "verified_entries": by_status["verified"],
        "published_entries": by_status["published"],
        "by_status": by_status,
        "by_theme": by_theme,
        "audio_count": audio_count,
    }

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Записано {OUT.relative_to(ROOT)}:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

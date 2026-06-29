#!/usr/bin/env python3
"""Валидатор корпуса OpenNom.

Проверяет все CSV в corpus/text/ против схемы (см. corpus/schema.md).
Печатает ошибки с номером файла и строки. Ненулевой код выхода при наличии ошибок.

Запуск:
    python scripts/validate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TEXT_DIR = ROOT / "corpus" / "text"
AUDIO_MANIFEST = ROOT / "corpus" / "audio" / "manifest.csv"
AUDIO_FILES_DIR = ROOT / "corpus" / "audio"

REQUIRED_FIELDS = ["id", "bur", "rus", "type", "theme"]
EXPECTED_COLUMNS = [
    "id", "bur", "rus", "literal_rus", "eng", "type", "register", "dialect",
    "source", "usage_note", "theme", "lesson", "level", "order", "audio_id",
    "translator", "verified_by", "status", "date_added", "notes",
]

ENUM_TYPE = {"word", "phrase", "sentence", "idiom", "proverb", "yorol", "text"}
ENUM_REGISTER = {"neutral", "colloquial", "formal", "ritual", "archaic"}
ENUM_STATUS = {"draft", "translated", "verified", "published"}

# Кириллица + спец-буквы бурятского. Грубая проверка контаминации латиницей.
LATIN_RE = re.compile(r"[A-Za-z]")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁёҺһҮүӨөЀ-ӿ]")

# Заголовок CSV = строка 1, поэтому к индексу pandas прибавляем 2.
HEADER_OFFSET = 2


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return str(value).strip() == ""


def looks_latin(text: str) -> bool:
    """True, если bur выглядит как латиница (контаминация).

    Срабатывает, когда латинских букв строго больше, чем кириллических.
    """
    latin = len(LATIN_RE.findall(text))
    cyr = len(CYRILLIC_RE.findall(text))
    return latin > 0 and latin > cyr


def load_manifest_ids() -> tuple[set[str], dict[str, str]]:
    if not AUDIO_MANIFEST.exists():
        return set(), {}
    df = pd.read_csv(AUDIO_MANIFEST, dtype=str, encoding="utf-8").fillna("")
    ids = {str(v).strip() for v in df.get("audio_id", []) if str(v).strip()}
    files = {
        str(r["audio_id"]).strip(): str(r["file"]).strip()
        for _, r in df.iterrows()
        if str(r.get("audio_id", "")).strip()
    }
    return ids, files


def main() -> int:
    errors: list[str] = []

    text_files = sorted(p for p in TEXT_DIR.glob("*.csv") if not p.name.startswith("_"))
    if not text_files:
        print(f"WARN: нет CSV-файлов корпуса в {TEXT_DIR} (файлы с _ игнорируются)")

    manifest_ids, manifest_files = load_manifest_ids()
    seen_ids: dict[str, str] = {}

    for path in text_files:
        rel = path.relative_to(ROOT)
        try:
            df = pd.read_csv(path, dtype=str, encoding="utf-8").fillna("")
        except Exception as exc:  # noqa: BLE001 — хотим показать любую ошибку парсинга
            errors.append(f"{rel}: не удалось прочитать CSV: {exc}")
            continue

        missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
        if missing_cols:
            errors.append(f"{rel}: отсутствуют колонки: {', '.join(missing_cols)}")
            continue

        for idx, row in df.iterrows():
            line = idx + HEADER_OFFSET
            where = f"{rel}:{line}"

            # обязательные поля
            for field in REQUIRED_FIELDS:
                if is_blank(row[field]):
                    errors.append(f"{where}: пустое обязательное поле '{field}'")

            # уникальность id во всём корпусе
            rid = str(row["id"]).strip()
            if rid:
                if rid in seen_ids:
                    errors.append(
                        f"{where}: дубликат id '{rid}' (уже в {seen_ids[rid]})"
                    )
                else:
                    seen_ids[rid] = where

            # enum-поля
            t = str(row["type"]).strip()
            if t and t not in ENUM_TYPE:
                errors.append(f"{where}: недопустимый type '{t}'")

            reg = str(row["register"]).strip()
            if reg and reg not in ENUM_REGISTER:
                errors.append(f"{where}: недопустимый register '{reg}'")

            st = str(row["status"]).strip()
            if st and st not in ENUM_STATUS:
                errors.append(f"{where}: недопустимый status '{st}'")

            # bur непусто и не латиница
            bur = str(row["bur"]).strip()
            if bur and looks_latin(bur):
                errors.append(
                    f"{where}: поле 'bur' похоже на латиницу (контаминация): {bur!r}"
                )

            # audio_id ссылочная целостность
            aid = str(row["audio_id"]).strip()
            if aid:
                if aid not in manifest_ids:
                    errors.append(f"{where}: audio_id '{aid}' нет в manifest.csv")
                else:
                    fpath = AUDIO_FILES_DIR / manifest_files.get(aid, "")
                    if not fpath.exists():
                        errors.append(
                            f"{where}: файл аудио для '{aid}' не найден: {fpath.relative_to(ROOT)}"
                        )

    if errors:
        print(f"НАЙДЕНО ОШИБОК: {len(errors)}\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    print(f"OK: проверено файлов {len(text_files)}, строк {len(seen_ids)}, ошибок нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

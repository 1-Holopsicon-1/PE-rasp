#!/usr/bin/env python3
"""Парсинг расписания элективных дисциплин из PDF в JSON.

Usage:
    uv tool run --from pdfplumber python3 scripts/parse.py [path/to/file.pdf]

По умолчанию парсит последний PDF из pdf/ (по mtime).
"""

import json
import os
import re
import sys
from datetime import datetime

import pdfplumber

PDF_DIR = "pdf"
OUT_PATH = "static/data/raspisanie.json"

TIME_RE = re.compile(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})")
METRO_RE = re.compile(r"(м\.|МЦК\s)([А-Яа-яЁё\- ]+?)(?=ул\.|МЦК|м\.|$|\s+стр)")
SPLIT_LOC_RE = re.compile(r"(?=СК |Спортзал №)")

DAY_NAMES = [
    ("Понедельник", "mon", "Пн", 1),
    ("Вторник", "tue", "Вт", 2),
    ("Среда", "wed", "Ср", 3),
    ("Четверг", "thu", "Чт", 4),
    ("Пятница", "fri", "Пт", 5),
    ("Суббота", "sat", "Сб", 6),
]


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_") or "id"


def clean(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.replace("\n", " ")).strip()


def find_default_pdf() -> str:
    files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    if not files:
        raise FileNotFoundError(f"No PDF in {PDF_DIR}/")
    files.sort(key=lambda f: os.path.getmtime(os.path.join(PDF_DIR, f)))
    return os.path.join(PDF_DIR, files[-1])


def split_locations(loc_text: str) -> list[str]:
    """Разделяет склеенные локации (СК ... Спортзал № ...)."""
    if not loc_text:
        return []
    parts = [p.strip() for p in SPLIT_LOC_RE.split(loc_text) if p.strip()]
    return parts


def normalize_location(raw: str) -> dict:
    """Извлекает name, metro, address из строки локации."""
    raw = clean(raw)
    # Нормализуем артефакты PDF: "д .22" → "д.22", "Корчагина д .22" → "Корчагина д.22"
    raw = re.sub(r"\s+\.", ".", raw)
    raw = re.sub(r"\.\s+", ".", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    # Известные артефакты PDF (перенос слова в ячейке): "Михалков ская" → "Михалковская"
    raw = raw.replace("Михалков ская", "Михалковская")
    # Опечатка исходного PDF: одна и та же аудитория то "ауд.519а", то "ауд.519"
    raw = raw.replace("ауд.519а", "ауд.519")
    metro_match = METRO_RE.search(raw)
    metro = ""
    if metro_match:
        station = metro_match.group(2).strip()
        if metro_match.group(1).strip().startswith("МЦК"):
            metro = f"МЦК {station}"
        else:
            metro = f"м.{station}"
    # name — часть до метро, address — после
    if metro and metro in raw:
        before, _, after = raw.partition(metro)
        name = before.strip().rstrip(",").strip()
        address = after.strip()
    else:
        name = raw
        address = ""
    return {"name": name, "metro": metro, "address": address}


def parse_pdf(path: str) -> dict:
    days = []
    for name, did, short, order in DAY_NAMES:
        days.append({"id": did, "name": name, "short": short, "order": order})

    slots = []
    schedule = []  # list of {day_id, slot_id, entries: [{sport_id, location_ids}]}
    locations_registry: dict[str, dict] = {}  # key -> location dict
    sports_registry: dict[str, dict] = {}     # normalized_name -> {id, name}

    def get_or_create_sport(name: str) -> str:
        key = name.strip()
        if key not in sports_registry:
            sid = slugify(key)
            # ensure unique
            base = sid
            i = 2
            while any(s["id"] == sid for s in sports_registry.values()):
                sid = f"{base}_{i}"; i += 1
            sports_registry[key] = {"id": sid, "name": key}
        return sports_registry[key]["id"]

    def get_or_create_location(loc_dict: dict) -> str:
        key = (loc_dict["name"], loc_dict["metro"], loc_dict["address"])
        for lid, existing in locations_registry.items():
            if (existing["name"], existing["metro"], existing["address"]) == key:
                return lid
        lid = slugify(loc_dict["name"]) or f"loc_{len(locations_registry)}"
        base = lid
        i = 2
        while lid in locations_registry:
            lid = f"{base}_{i}"; i += 1
        locations_registry[lid] = {
            "id": lid,
            "name": loc_dict["name"],
            "metro": loc_dict["metro"],
            "address": loc_dict["address"],
        }
        return lid

    with pdfplumber.open(path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if not tables:
                continue
            main = max(tables, key=lambda t: len(t[0]) if t else 0)
            if len(main[0]) < 13:
                continue

            # --- 1. Слот: ищем время в первом столбце строк 0..3
            slot_start, slot_end = None, None
            for row in main[:4]:
                c0 = clean(row[0])
                m = TIME_RE.search(c0)
                if m:
                    slot_start, slot_end = m.group(1), m.group(2)
                    break
            if not slot_start:
                print(f"[warn] page {page_idx+1}: время не найдено, пропуск")
                continue
            slot_id = f"s{len(slots)+1}"
            slots.append({
                "id": slot_id,
                "order": len(slots)+1,
                "start": slot_start,
                "end": slot_end,
                "label": f"{slot_start} - {slot_end}",
            })

            # --- 2. День→column (нечётные столбцы 1,3,5,7,9,11)
            day_cols: list[tuple[int, str]] = []  # (sport_col_idx, day_id)
            header = main[0]
            for name, did, short, order in DAY_NAMES:
                for ci in range(1, 13, 2):
                    if clean(header[ci]) == name:
                        day_cols.append((ci, did))
                        break

            # --- 3. Накопитель для (day_id → list of entries), где entry =
            # {sport_id, location_ids}. Для доп. локаций — ищем последнюю
            # запись этого дня с matching sport_id (по текущему спорту).
            day_entries: dict[str, list[dict]] = {did: [] for _, did in day_cols}
            current_sport_for_day: dict[str, str | None] = {did: None for _, did in day_cols}

            for row in main[1:]:
                for sport_col, did in day_cols:
                    loc_col = sport_col + 1
                    sport = clean(row[sport_col])
                    loc = clean(row[loc_col])
                    if not sport and not loc:
                        continue

                    if sport:
                        sid = get_or_create_sport(sport)
                        entry = {"sport_id": sid, "location_ids": []}
                        day_entries[did].append(entry)
                        current_sport_for_day[did] = sid
                    # локация(и) — добавляем к текущей записи
                    if loc:
                        target_sid = current_sport_for_day[did]
                        target_entry = None
                        for e in reversed(day_entries[did]):
                            if e["sport_id"] == target_sid:
                                target_entry = e
                                break
                        if target_entry is None:
                            # нет спорта вообще — пропускаем
                            print(f"[warn] page {page_idx+1} day {did}: loc без sport: {loc!r}")
                            continue
                        for loc_part in split_locations(loc):
                            loc_dict = normalize_location(loc_part)
                            if not loc_dict["name"]:
                                continue
                            lid = get_or_create_location(loc_dict)
                            if lid not in target_entry["location_ids"]:
                                target_entry["location_ids"].append(lid)

            # --- 4. Сборка schedule для этого слота
            for did, entries in day_entries.items():
                if not entries:
                    continue
                schedule.append({
                    "day_id": did,
                    "slot_id": slot_id,
                    "entries": entries,
                })

    # meta — заголовок из первой страницы текстом
    meta = {
        "title": "Расписание элективных дисциплин по физической культуре и спорту",
        "semester": "",
        "source_pdf": os.path.basename(path),
        "parsed_at": datetime.now().isoformat(timespec="seconds"),
    }

    return {
        "meta": meta,
        "days": days,
        "slots": slots,
        "locations": list(locations_registry.values()),
        "sports": list(sports_registry.values()),
        "schedule": schedule,
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else find_default_pdf()
    print(f"Парсинг: {path}")
    data = parse_pdf(path)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Готово: {OUT_PATH}")
    print(f"  дней: {len(data['days'])}")
    print(f"  слотов: {len(data['slots'])}")
    print(f"  видов спорта: {len(data['sports'])}")
    print(f"  локаций: {len(data['locations'])}")
    print(f"  записей в schedule: {len(data['schedule'])}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Парсинг расписания элективных дисциплин из PDF в JSON.

Usage:
    uv tool run --from pdfplumber python3 scripts/parse.py [path/to/file.pdf]

По умолчанию парсит последний PDF из pdf/ (по mtime).

Структура PDF (с окт. 2026): каждая страница = один временной слот.
Таблица: узкая колонка «Время» + 6 дневных столбцов. Записи внутри
дневного столбца идут вертикально: каждая запись = цветной спорт-блок
(левая половина) + стек локаций справа (имя ячейки подчёркнуто, адрес
может продолжаться в следующей ячейке без имени). Записи определяются
Y-кластерами цветных заливок левой половины; стек локаций — по тонким
линиям правой половины; ячейка стека без имени «СК|Спортзал» —
продолжение адреса предыдущей локации.

Текст собирается прямо из page.chars: строки PDF перекрываются по x,
поэтому extract_words на таких страницах даёт разреженные/перемешанные
слова; глифы-пробелы служат разделителями слов.
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
LOC_NAME_RE = re.compile(r"^(СК|Спортзал)")

LINE_ROW_TOL = 2.5   # разрыв top внутри одной строки, pt
WORD_TOL = 1.0       # разрыв x между словами без пробела, pt

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


def normalize_location(raw: str) -> dict:
    """Извлекает name, metro, address из строки локации."""
    raw = clean(raw)
    raw = re.sub(r"\s+\.", ".", raw)
    raw = re.sub(r"\.\s+", ".", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = raw.replace("Михалков ская", "Михалковская")
    raw = raw.replace("ауд.519а", "ауд.519")
    metro_match = METRO_RE.search(raw)
    metro = ""
    if metro_match:
        station = metro_match.group(2).strip()
        if metro_match.group(1).strip().startswith("МЦК"):
            metro = f"МЦК {station}"
        else:
            metro = f"м.{station}"
    if metro and metro in raw:
        before, _, after = raw.partition(metro)
        name = before.strip().rstrip(",").strip()
        address = after.strip()
    else:
        name = raw
        address = ""
    return {"name": name, "metro": metro, "address": address}


def _color(r: dict) -> tuple:
    c = r.get("non_stroking_color")
    if isinstance(c, (list, tuple)):
        return tuple(round(float(v), 3) for v in c) or (0.0,)
    return (round(float(c or 0), 3),)


LINE_ROW_TOL = 4.0  # разрыв top внутри одной строки текста, pt
WORD_TOL = 1.5      # разрыв x между словами, pt


def _lines_of_chars(chars: list) -> list[list]:
    """Строки текста: кластеры глифов по top."""
    out: list[list] = []
    for c in sorted(chars, key=lambda c: c["top"]):
        if out and c["top"] - out[-1][0] <= LINE_ROW_TOL:
            out[-1][-1].append(c)
        else:
            out.append([c["top"], [c]])
    return out


def _line_text(line_chars: list) -> str:
    """Слова строки из глифов: глифы-пробелы делят слова."""
    words: list[str] = []
    buf: list[str] = []
    prev = None
    for c in sorted(line_chars, key=lambda c: c["x0"]):
        if c["text"] == " ":
            if buf:
                words.append("".join(buf))
                buf = []
            prev = c
            continue
        if buf and (c["x0"] - prev["x1"]) > WORD_TOL:
            words.append("".join(buf))
            buf = []
        buf.append(c["text"])
        prev = c
    if buf:
        words.append("".join(buf))
    return " ".join(words)


def _lines_of_chars(chars: list) -> list[list]:
    """Кластеризация глифов в строки по top."""
    chars = sorted(chars, key=lambda c: round(c["top"], 1))
    lines: list[list] = []
    for c in chars:
        if lines and c["top"] - lines[-1][0] <= LINE_ROW_TOL:
            lines[-1][1].append(c)
        else:
            lines.append([c["top"], [c]])
    return lines


def _line_text(line_chars: list) -> str:
    """Слова строки: глифы-пробелы делят слова, остальные глифы склеиваются."""
    parts: list[str] = []
    buf: list = []
    prev = None
    for c in sorted(line_chars, key=lambda c: c["x0"]):
        if c["text"] == " ":
            if buf:
                parts.append("".join(b["text"] for b in buf))
                buf = []
            prev = c
            continue
        if prev is not None and (c["x0"] - prev["x1"]) > WORD_TOL and buf:
            parts.append("".join(b["text"] for b in buf))
            buf = []
        buf.append(c)
        prev = c
    if buf:
        parts.append("".join(b["text"] for b in buf))
    return " ".join(parts)


def parse_pdf(path: str) -> dict:
    days = []
    for name, did, short, order in DAY_NAMES:
        days.append({"id": did, "name": name, "short": short, "order": order})

    slots = []
    schedule = []
    locations_registry: dict[str, dict] = {}
    sports_registry: dict[str, dict] = {}

    def get_or_create_sport(name: str) -> str:
        key = name.strip()
        if key not in sports_registry:
            sports_registry[key] = {"id": slugify(key), "name": key}
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
            if not page.extract_tables():
                continue
            try:
                table = page.find_tables()[0]
            except IndexError:
                continue
            cells = table.cells
            all_chars = page.chars

            def text_in(x0, top, x1, bottom) -> str:
                sel = [
                    c for c in all_chars
                    if c["x0"] >= x0 - 1.5 and c["x1"] <= x1 + 1.5
                    and top - 6 <= c["top"] <= bottom + 6
                ]
                lines = []
                for _, lc in _lines_of_chars(sel):
                    center = (lc[0]["top"] + lc[-1]["bottom"]) / 2
                    if top <= center <= bottom:
                        lines.append(_line_text(lc))
                return "\n".join(lines)

            def hline_ys(x0, x1, y0, y1) -> list[float]:
                by_y: dict[float, list] = {}
                for r in page.rects:
                    if (r["bottom"] - r["top"]) > 3:
                        continue
                    if r["x0"] < x0 - 1 or r["x1"] > x1 + 1:
                        continue
                    if not (y0 <= r["top"] <= y1):
                        continue
                    by_y.setdefault(round(r["top"], 1), []).append((r["x0"], r["x1"]))
                out = []
                for y, segs in sorted(by_y.items()):
                    segs.sort()
                    if segs[0][0] <= x0 + 2 and segs[-1][1] >= x1 - 2:
                        out.append(y)
                return out

            # --- хедеры дней ---
            day_cells: dict[str, tuple[float, float]] = {}
            header_bottom = 0.0
            for (x0, top, x1, bottom) in cells:
                if bottom > 90:
                    continue
                txt = text_in(x0, top, x1, bottom) or ""
                for name, did, _, _ in DAY_NAMES:
                    if name in txt:
                        day_cells[did] = (x0, x1)
                        header_bottom = max(header_bottom, bottom)
            if len(day_cells) < 6:
                print(f"[warn] page {page_idx+1}: неполные хедеры дней, пропуск")
                continue

            # --- слоты страницы ---
            page_times = []
            for (x0, top, x1, bottom) in cells:
                if x1 <= 95:
                    m = TIME_RE.search(text_in(x0, top, x1, bottom) or "")
                    if m:
                        page_times.append({"top": top, "start": m.group(1), "end": m.group(2)})
            page_times.sort(key=lambda t: t["top"])
            if not page_times:
                print(f"[warn] page {page_idx+1}: время не найдено, пропуск")
                continue

            table_bottom = max(b for (_, _, _, b) in cells)
            slot_bounds = []
            for i, tinfo in enumerate(page_times):
                start_y = tinfo["top"]
                end_y = page_times[i + 1]["top"] if i + 1 < len(page_times) else table_bottom + 1
                slot_id = f"s{len(slots)+1}"
                slots.append({
                    "id": slot_id,
                    "order": len(slots) + 1,
                    "start": tinfo["start"],
                    "end": tinfo["end"],
                    "label": f"{tinfo['start']} - {tinfo['end']}",
                })
                slot_bounds.append((slot_id, start_y, end_y))

            # --- записи дня ---
            day_entries: dict[str, list] = {did: [] for did in day_cells}

            for name, did, _, _ in DAY_NAMES:
                if did not in day_cells:
                    continue
                dx0, dx1 = day_cells[did]
                mid = (dx0 + dx1) / 2

                fills = [
                    r for r in page.rects
                    if r.get("fill") and _color(r) != (0.0,)
                    and r["x0"] >= dx0 - 1 and r["x1"] <= mid + 2
                    and (r["x1"] - r["x0"]) >= 15
                    and r["top"] >= header_bottom
                ]
                if not fills:
                    continue

                blocks: list[list[float]] = []
                for r in sorted(fills, key=lambda r: (r["top"], r["x0"])):
                    if blocks and r["top"] <= blocks[-1][1] + 0.05:
                        blocks[-1][1] = max(blocks[-1][1], r["bottom"])
                    else:
                        blocks.append([r["top"], r["bottom"]])

                for b_top, b_bottom in blocks:
                    slot_id = next(
                        (sid for sid, sy, ey in slot_bounds
                         if sy - 2 <= b_top <= ey), None
                    )
                    if slot_id is None:
                        continue
                    sport_name = clean(text_in(dx0, b_top + 1, mid, b_bottom))
                    inner = hline_ys(mid, dx1, b_top + 1, b_bottom - 1)
                    segs = [b_top] + [y for y in inner if b_top + 4 < y < b_bottom - 3] + [b_bottom]
                    raw_cells = [
                        t for a, b in zip(segs, segs[1:])
                        if (t := text_in(mid, a, dx1, b))
                    ]
                    if not raw_cells:
                        continue
                    merged: list[str] = []
                    for txt in raw_cells:
                        first = clean(txt.split("\n", 1)[0])
                        if merged and LOC_NAME_RE.match(first):
                            merged.append(txt)
                        else:
                            merged.append(txt if not merged else merged.pop() + "\n" + txt)
                    if not sport_name:
                        continue
                    sid = get_or_create_sport(sport_name)
                    entry = {"sport_id": sid, "location_ids": []}
                    day_entries[did].append(entry)
                    for txt in merged:
                        loc_dict = normalize_location(txt)
                        if not loc_dict["name"]:
                            continue
                        lid = get_or_create_location(loc_dict)
                        if lid not in entry["location_ids"]:
                            entry["location_ids"].append(lid)

            for did, entries in day_entries.items():
                if not entries:
                    continue
                if not slot_bounds:
                    print(f"[warn] page {page_idx+1} {did}: записи без слота")
                    continue
                slot_id = slot_bounds[0][0]
                schedule.append({"day_id": did, "slot_id": slot_id, "entries": entries})

    meta = {
        "title": "Расписание учебных занятий по элективным дисциплинам по физической культуре и спорту",
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
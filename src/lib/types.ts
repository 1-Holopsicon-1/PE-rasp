export interface Meta {
  title: string;
  semester: string;
  source_pdf: string;
  parsed_at: string;
}

export interface Day {
  id: string;       // "mon".."sat"
  name: string;     // "Понедельник"
  short: string;    // "Пн"
  order: number;    // 1..6
}

export interface Slot {
  id: string;       // "s1".."s5"
  order: number;
  start: string;    // "09:00"
  end: string;      // "10:30"
  label: string;    // "09:00 - 10:30"
}

export interface Location {
  id: string;       // slug
  name: string;     // "СК на Автозаводской"
  metro: string;    // "м.Автозаводская"
  address: string;  // "ул. Автозаводская д.16 стр.2 8й этаж"
}

export interface Sport {
  id: string;       // slug
  name: string;     // "баскетбол"
}

export interface ScheduleEntry {
  day_id: string;
  slot_id: string;
  entries: { sport_id: string; location_ids: string[] }[];
}

export interface Raspisanie {
  meta: Meta;
  days: Day[];
  slots: Slot[];
  locations: Location[];
  sports: Sport[];
  schedule: ScheduleEntry[];
}
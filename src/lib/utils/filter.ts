import type { Raspisanie, ScheduleEntry } from '$lib/types';
import type { Filters } from '$lib/stores/filters';

export function filterSlotEntries(
  r: Raspisanie,
  f: Filters,
  slotEntries: ScheduleEntry | undefined
): ScheduleEntry['entries'] {
  if (!slotEntries) return [];
  const search = f.search.trim().toLowerCase();

  return slotEntries.entries.filter((e) => {
    // фильтр по спорту
    if (f.sportIds.length > 0 && !f.sportIds.includes(e.sport_id)) {
      return false;
    }
    // фильтр по локации
    if (f.locationId !== null && !e.location_ids.includes(f.locationId)) {
      return false;
    }
    // фильтр по метро — любая локация записи должна иметь это метро
    if (f.metro !== null) {
      const matchesMetro = e.location_ids.some((lid) => {
        const loc = r.locations.find((l) => l.id === lid);
        return loc?.metro === f.metro;
      });
      if (!matchesMetro) return false;
    }
    // поиск по тексту
    if (search) {
      const sport = r.sports.find((s) => s.id === e.sport_id);
      const sportName = sport?.name.toLowerCase() ?? '';
      const locText = e.location_ids
        .map((lid) => r.locations.find((l) => l.id === lid))
        .map((l) => `${l?.name ?? ''} ${l?.metro ?? ''} ${l?.address ?? ''}`.toLowerCase())
        .join(' ');
      const haystack = `${sportName} ${locText}`;
      if (!haystack.includes(search)) return false;
    }
    return true;
  });
}
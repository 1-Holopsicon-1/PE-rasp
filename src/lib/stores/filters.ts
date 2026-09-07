import { writable } from 'svelte/store';

export interface Filters {
  sportIds: string[];      // выбранные виды спорта (multi)
  locationId: string | null;
  metro: string | null;    // "м.Автозаводская"
  search: string;
}

export const filters = writable<Filters>({
  sportIds: [],
  locationId: null,
  metro: null,
  search: ''
});

export function toggleSport(id: string): void {
  filters.update((f) => {
    const has = f.sportIds.includes(id);
    return {
      ...f,
      sportIds: has ? f.sportIds.filter((x) => x !== id) : [...f.sportIds, id]
    };
  });
}

export function setLocation(id: string | null): void {
  filters.update((f) => ({ ...f, locationId: id }));
}

export function setMetro(m: string | null): void {
  filters.update((f) => ({ ...f, metro: m }));
}

export function setSearch(s: string): void {
  filters.update((f) => ({ ...f, search: s }));
}

export function clearFilters(): void {
  filters.set({ sportIds: [], locationId: null, metro: null, search: '' });
}

export function hasActiveFilters(f: Filters): boolean {
  return (
    f.sportIds.length > 0 ||
    f.locationId !== null ||
    f.metro !== null ||
    f.search.trim().length > 0
  );
}
import type { Raspisanie, Day, Slot, Sport, Location, ScheduleEntry } from './types';

export async function loadRaspisanie(): Promise<Raspisanie> {
  const res = await fetch('/data/raspisanie.json');
  if (!res.ok) throw new Error(`Failed to load raspisanie.json: ${res.status}`);
  return (await res.json()) as Raspisanie;
}

export function getDay(r: Raspisanie, day_id: string): Day | undefined {
  return r.days.find((d) => d.id === day_id);
}

export function getSlot(r: Raspisanie, slot_id: string): Slot | undefined {
  return r.slots.find((s) => s.id === slot_id);
}

export function getSport(r: Raspisanie, sport_id: string): Sport | undefined {
  return r.sports.find((s) => s.id === sport_id);
}

export function getLocation(r: Raspisanie, loc_id: string): Location | undefined {
  return r.locations.find((l) => l.id === loc_id);
}

export function getSchedule(r: Raspisanie, day_id: string): ScheduleEntry[] {
  return r.schedule.filter((s) => s.day_id === day_id);
}
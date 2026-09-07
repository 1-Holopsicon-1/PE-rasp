import { writable } from 'svelte/store';
import { browser } from '$app/environment';

function todayDayId(): string {
  if (!browser) return 'mon';
  const jsDay = new Date().getDay(); // 0=вс..6=сб
  const map: Record<number, string> = {
    0: 'mon',  // воскресенье -> понедельник (нет занятий)
    1: 'mon',
    2: 'tue',
    3: 'wed',
    4: 'thu',
    5: 'fri',
    6: 'sat'
  };
  return map[jsDay] ?? 'mon';
}

export const selectedDayId = writable<string>(todayDayId());

export function selectDay(id: string): void {
  selectedDayId.set(id);
}
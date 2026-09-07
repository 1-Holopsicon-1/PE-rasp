import type { Raspisanie } from '$lib/types';
import { browser } from '$app/environment';

export interface NextClass {
  dayId: string;
  slotId: string;
  isOngoing: boolean;
}

function parseTimeToMinutes(t: string): number {
  const [h, m] = t.split(':').map(Number);
  return h * 60 + m;
}

const DAY_ID_BY_JS: Record<number, string> = {
  1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat'
};

export function findNextClass(r: Raspisanie): NextClass | null {
  if (!browser || r.slots.length === 0) return null;

  const now = new Date();
  const jsDay = now.getDay();
  const nowMin = now.getHours() * 60 + now.getMinutes();

  // 1. Сегодня идёт пара?
  const todayId = DAY_ID_BY_JS[jsDay];
  if (todayId) {
    for (const slot of r.slots) {
      const start = parseTimeToMinutes(slot.start);
      const end = parseTimeToMinutes(slot.end);
      if (nowMin >= start && nowMin <= end) {
        const has = r.schedule.some((s) => s.day_id === todayId && s.slot_id === slot.id);
        if (has) return { dayId: todayId, slotId: slot.id, isOngoing: true };
      }
    }
    // 2. Ближайшая сегодня позже
    for (const slot of r.slots) {
      const start = parseTimeToMinutes(slot.start);
      if (start > nowMin) {
        const has = r.schedule.some((s) => s.day_id === todayId && s.slot_id === slot.id);
        if (has) return { dayId: todayId, slotId: slot.id, isOngoing: false };
      }
    }
  }

  // 3. Ближайший непустой день вперёд (до субботы)
  const dayOrder = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
  const todayIdx = todayId ? dayOrder.indexOf(todayId) : -1;
  for (let offset = 1; offset <= 6; offset++) {
    const idx = (todayIdx + offset) % 6;
    const did = dayOrder[idx];
    const firstAvailableSlot = r.slots.find(
      (s) => r.schedule.some((e) => e.day_id === did && e.slot_id === s.id)
    );
    if (firstAvailableSlot) {
      return { dayId: did, slotId: firstAvailableSlot.id, isOngoing: false };
    }
  }
  return null;
}

export function isSlotOngoing(r: Raspisanie, slotId: string, dayId: string): boolean {
  if (!browser) return false;
  const slot = r.slots.find((s) => s.id === slotId);
  if (!slot) return false;
  const now = new Date();
  const jsDay = now.getDay();
  if (DAY_ID_BY_JS[jsDay] !== dayId) return false;
  const nowMin = now.getHours() * 60 + now.getMinutes();
  return (
    nowMin >= parseTimeToMinutes(slot.start) &&
    nowMin <= parseTimeToMinutes(slot.end)
  );
}

export function isToday(dayId: string): boolean {
  if (!browser) return false;
  return DAY_ID_BY_JS[new Date().getDay()] === dayId;
}
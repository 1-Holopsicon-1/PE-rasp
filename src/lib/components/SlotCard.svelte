<script lang="ts">
  import type { Raspisanie, Slot, ScheduleEntry } from '$lib/types';
  import type { Filters } from '$lib/stores/filters';
  import { isSlotOngoing } from '$lib/utils/time';
  import { filterSlotEntries as filterEntries } from '$lib/utils/filter';
  import EntryItem from './EntryItem.svelte';

  interface Props {
    raspisanie: Raspisanie;
    slot: Slot;
    dayId: string;
    slotSchedule: ScheduleEntry | undefined;
    filters: Filters;
    onLocationClick: (id: string) => void;
  }

  let { raspisanie, slot, dayId, slotSchedule, filters, onLocationClick }: Props = $props();

  let filtered = $derived(filterEntries(raspisanie, filters, slotSchedule));
  let ongoing = $derived(isSlotOngoing(raspisanie, slot.id, dayId));
  let isEmpty = $derived(filtered.length === 0);
</script>

{#if !isEmpty}
  <div
    class="rounded-xl p-4 bg-zinc-900 border transition-colors
           {ongoing ? 'border-teal-500 ring-1 ring-teal-500/30' : 'border-zinc-800'}"
    id="slot-{slot.id}"
  >
    <div class="flex items-center gap-2 mb-3">
      <span class="text-xl font-bold text-zinc-100">{slot.label}</span>
      {#if ongoing}
        <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-500 text-zinc-950">
          сейчас
        </span>
      {/if}
    </div>
    <div class="divide-y divide-zinc-800">
      {#each filtered as entry (entry.sport_id)}
        <EntryItem
          raspisanie={raspisanie}
          sportId={entry.sport_id}
          locationIds={entry.location_ids}
          onLocationClick={onLocationClick}
        />
      {/each}
    </div>
  </div>
{/if}
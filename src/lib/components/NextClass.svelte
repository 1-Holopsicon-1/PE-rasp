<script lang="ts">
  import type { Raspisanie } from '$lib/types';
  import { findNextClass } from '$lib/utils/time';
  import { browser } from '$app/environment';

  interface Props {
    raspisanie: Raspisanie;
    onJumpToSlot: (dayId: string, slotId: string) => void;
  }

  let { raspisanie, onJumpToSlot }: Props = $props();

  let next = $derived(findNextClass(raspisanie));

  let day = $derived(
    next ? raspisanie.days.find((d) => d.id === next.dayId) : undefined
  );
  let slot = $derived(
    next ? raspisanie.slots.find((s) => s.id === next.slotId) : undefined
  );
  let slotSchedule = $derived(
    next
      ? raspisanie.schedule.find(
          (s) => s.day_id === next.dayId && s.slot_id === next.slotId
        )
      : undefined
  );
</script>

{#if next && day && slot && slotSchedule}
  <div class="rounded-xl p-5 bg-gradient-to-br from-teal-900/40 to-zinc-900
              border border-teal-500/40">
    <div class="flex items-center justify-between gap-2 mb-3 flex-wrap">
      <div>
        <div class="text-xs uppercase tracking-wide text-teal-400 font-semibold">
          {next.isOngoing ? 'Сейчас идёт' : 'Ближайшая пара'}
        </div>
        <div class="text-lg font-bold text-zinc-100 mt-1">
          {day.name}, {slot.label}
        </div>
      </div>
      <button
        type="button"
        class="rounded-lg px-3 py-2.5 bg-teal-500 text-zinc-950 font-medium
               hover:bg-teal-400 transition-colors min-h-[44px]"
        onclick={() => onJumpToSlot(next.dayId, next.slotId)}
      >
        К слоту →
      </button>
    </div>
    <div class="text-sm text-zinc-300 flex flex-wrap gap-x-4 gap-y-1">
      {#each slotSchedule.entries as entry (entry.sport_id)}
        {#if entry.sport_id}
          <span>
            {raspisanie.sports.find((s) => s.id === entry.sport_id)?.name ?? entry.sport_id}
          </span>
        {/if}
      {/each}
    </div>
  </div>
{:else if browser}
  <div class="rounded-xl p-5 bg-zinc-900 border border-zinc-800 text-zinc-400">
    Нет ближайших занятий.
  </div>
{/if}
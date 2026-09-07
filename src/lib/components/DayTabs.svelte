<script lang="ts">
  import type { Raspisanie } from '$lib/types';
  import { isToday } from '$lib/utils/time';

  interface Props {
    raspisanie: Raspisanie;
    selectedDayId: string;
    onSelect: (id: string) => void;
  }

  let { raspisanie, selectedDayId, onSelect }: Props = $props();
</script>

<div class="flex gap-2 overflow-x-auto snap-x snap-mandatory pb-2 -mx-4 px-4
            sm:justify-between sm:mx-0 sm:px-0">
  {#each raspisanie.days as day (day.id)}
    <button
      type="button"
      class="snap-start shrink-0 rounded-lg px-4 py-2.5 text-sm font-medium
             min-h-[44px] transition-colors whitespace-nowrap
             {selectedDayId === day.id
               ? 'bg-zinc-100 text-zinc-950'
               : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'}
             {isToday(day.id) ? 'ring-2 ring-amber-400' : ''}"
      onclick={() => onSelect(day.id)}
    >
      <span class="lg:hidden">{day.short}</span>
      <span class="hidden lg:inline">{day.name}</span>
    </button>
  {/each}
</div>
<script lang="ts">
  import type { Raspisanie } from '$lib/types';
  import type { Filters } from '$lib/stores/filters';
  import { hasActiveFilters } from '$lib/stores/filters';
  import SportChip from './SportChip.svelte';

  interface Props {
    raspisanie: Raspisanie;
    filters: Filters;
    onToggleSport: (id: string) => void;
    onSetLocation: (id: string | null) => void;
    onSetMetro: (m: string | null) => void;
    onSearch: (s: string) => void;
    onClear: () => void;
  }

  let { raspisanie, filters, onToggleSport, onSetLocation, onSetMetro,
        onSearch, onClear }: Props = $props();

  let metros = $derived(
    Array.from(new Set(raspisanie.locations.map((l) => l.metro).filter(Boolean)))
  );
  let showFilters = $state(false);
</script>

<div class="sticky top-0 z-10 bg-zinc-950/95 backdrop-blur py-3 -mx-4 px-4 sm:mx-0 sm:px-0">
  <!-- Поиск -->
  <input
    type="search"
    placeholder="Поиск: спорт, локация, метро…"
    class="w-full rounded-lg px-3 py-2.5 bg-zinc-800 text-zinc-100
           placeholder-zinc-500 border border-zinc-700 focus:border-teal-500
           focus:outline-none min-h-[44px]"
    value={filters.search}
    oninput={(e) => onSearch(e.currentTarget.value)}
  />

  <!-- Кнопка-аккордеон для мобайла -->
  <button
    type="button"
    class="mt-2 w-full sm:hidden flex items-center justify-between
           rounded-lg px-3 py-2.5 bg-zinc-800 text-zinc-100 min-h-[44px]"
    onclick={() => showFilters = !showFilters}
  >
    <span>Фильтры {hasActiveFilters(filters) ? '•' : ''}</span>
    <span>{showFilters ? '▲' : '▼'}</span>
  </button>

  <div class="mt-2 {showFilters ? 'block' : 'hidden'} sm:block">
    <!-- Чипы спорта -->
    <div class="flex gap-2 overflow-x-auto snap-x snap-mandatory pb-2
                sm:flex-wrap sm:overflow-visible">
      {#each raspisanie.sports as sport (sport.id)}
        <SportChip
          name={sport.name}
          active={filters.sportIds.includes(sport.id)}
          onclick={() => onToggleSport(sport.id)}
        />
      {/each}
    </div>

    <!-- Локации и метро -->
    <div class="flex flex-col sm:flex-row gap-2 mt-2">
      <select
        class="rounded-lg px-3 py-2.5 bg-zinc-800 text-zinc-100 border border-zinc-700
               min-h-[44px] sm:flex-1"
        value={filters.locationId ?? ''}
        onchange={(e) => onSetLocation(e.currentTarget.value || null)}
      >
        <option value="">Все локации</option>
        {#each raspisanie.locations as loc (loc.id)}
          <option value={loc.id}>{loc.name}</option>
        {/each}
      </select>

      <select
        class="rounded-lg px-3 py-2.5 bg-zinc-800 text-zinc-100 border border-zinc-700
               min-h-[44px] sm:flex-1"
        value={filters.metro ?? ''}
        onchange={(e) => onSetMetro(e.currentTarget.value || null)}
      >
        <option value="">Все метро</option>
        {#each metros as m (m)}
          <option value={m}>{m}</option>
        {/each}
      </select>

      {#if hasActiveFilters(filters)}
        <button
          type="button"
          class="rounded-lg px-3 py-2.5 bg-zinc-800 text-zinc-400 hover:text-zinc-100
                 min-h-[44px] transition-colors"
          onclick={onClear}
        >
          Сбросить
        </button>
      {/if}
    </div>
  </div>
</div>
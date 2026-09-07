<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { Raspisanie } from '$lib/types';
  import type { Filters } from '$lib/stores/filters';
  import { loadRaspisanie, getSchedule } from '$lib/data';
  import {
    filters,
    toggleSport,
    setLocation,
    setMetro,
    setSearch,
    clearFilters,
    hasActiveFilters
  } from '$lib/stores/filters';
  import { selectedDayId, selectDay } from '$lib/stores/view';

  import NextClass from '$lib/components/NextClass.svelte';
  import DayTabs from '$lib/components/DayTabs.svelte';
  import FilterBar from '$lib/components/FilterBar.svelte';
  import SlotCard from '$lib/components/SlotCard.svelte';

  let raspisanie: Raspisanie | null = $state(null);
  let error: string | null = $state(null);
  let currentFilters: Filters = $state({
    sportIds: [], locationId: null, metro: null, search: ''
  });

  // подписка на filters store для реактивности в props
  const unsubscribeFilters = filters.subscribe((f) => { currentFilters = f; });
  onDestroy(unsubscribeFilters);

  onMount(async () => {
    try {
      raspisanie = await loadRaspisanie();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  });

  let daySchedule = $derived(
    raspisanie ? getSchedule(raspisanie, $selectedDayId) : []
  );

  function jumpToSlot(dayId: string, slotId: string) {
    selectDay(dayId);
    // дать Svelte обновить DOM, потом прокрутить
    setTimeout(() => {
      document.getElementById(`slot-${slotId}`)?.scrollIntoView({
        behavior: 'smooth', block: 'start'
      });
    }, 60);
  }
</script>

<svelte:head>
  <title>Расписание физкультуры</title>
</svelte:head>

{#if error}
  <div class="rounded-xl p-5 bg-red-900/30 border border-red-500/40 text-red-200">
    Ошибка: {error}
  </div>
{:else if !raspisanie}
  <div class="text-zinc-400">Загрузка…</div>
{:else}
  <header class="mb-4">
    <h1 class="text-2xl lg:text-3xl font-bold text-zinc-100">
      {raspisanie.meta.title || 'Расписание'}
    </h1>
    {#if raspisanie.meta.semester}
      <p class="text-zinc-400 mt-1">{raspisanie.meta.semester}</p>
    {/if}
  </header>

  <section class="mb-4">
    <NextClass raspisanie={raspisanie} onJumpToSlot={jumpToSlot} />
  </section>

  <section class="mb-4">
    <DayTabs
      raspisanie={raspisanie}
      selectedDayId={$selectedDayId}
      onSelect={selectDay}
    />
  </section>

  <section class="mb-4">
    <FilterBar
      raspisanie={raspisanie}
      filters={currentFilters}
      onToggleSport={toggleSport}
      onSetLocation={setLocation}
      onSetMetro={setMetro}
      onSearch={setSearch}
      onClear={clearFilters}
    />
  </section>

  <section class="flex flex-col gap-3">
    {#if daySchedule.length === 0}
      <div class="text-zinc-400 py-8 text-center">
        Нет занятий в этот день.
      </div>
    {:else}
      {#each raspisanie.slots as slot (slot.id)}
        {@const slotSchedule = daySchedule.find((s) => s.slot_id === slot.id)}
        <SlotCard
          raspisanie={raspisanie}
          slot={slot}
          dayId={$selectedDayId}
          slotSchedule={slotSchedule}
          filters={currentFilters}
          onLocationClick={(id) => setLocation(id)}
        />
      {/each}
    {/if}
  </section>
{/if}
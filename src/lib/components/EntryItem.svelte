<script lang="ts">
  import type { Raspisanie } from '$lib/types';
  import LocationBadge from './LocationBadge.svelte';

  interface Props {
    raspisanie: Raspisanie;
    sportId: string;
    locationIds: string[];
    onLocationClick: (id: string) => void;
  }

  let { raspisanie, sportId, locationIds, onLocationClick }: Props = $props();

  let sport = $derived(raspisanie.sports.find((s) => s.id === sportId));
  let locations = $derived(
    locationIds
      .map((id) => raspisanie.locations.find((l) => l.id === id))
      .filter((l): l is NonNullable<typeof l> => l !== undefined)
  );
</script>

<div class="flex flex-col sm:flex-row sm:items-center gap-2 py-2">
  <div class="font-semibold text-zinc-100 sm:w-56 sm:shrink-0">
    {sport?.name ?? sportId}
  </div>
  <div class="flex flex-wrap gap-2">
    {#each locations as loc (loc.id)}
      <LocationBadge
        location={loc}
        compact={true}
        onclick={() => onLocationClick(loc.id)}
      />
    {/each}
  </div>
</div>
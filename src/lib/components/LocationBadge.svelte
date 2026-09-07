<script lang="ts">
  import type { Location } from '$lib/types';

  interface Props {
    location: Location;
    compact?: boolean;
    onclick?: (id: string) => void;
  }

  let { location, compact = false, onclick }: Props = $props();
</script>

<button
  type="button"
  class="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-left
         bg-zinc-800 hover:bg-zinc-700 text-zinc-100 transition-colors
         min-h-[44px] sm:min-h-0"
  onclick={() => onclick?.(location.id)}
>
  <span class="text-teal-400 font-medium whitespace-nowrap">
    {location.metro || '—'}
  </span>
  {#if !compact}
    <span class="text-zinc-300">{location.name}</span>
    {#if location.address}
      <span class="text-zinc-500 text-xs hidden lg:inline">{location.address}</span>
    {/if}
  {:else}
    <span class="text-zinc-300 text-sm">{location.name}</span>
  {/if}
</button>
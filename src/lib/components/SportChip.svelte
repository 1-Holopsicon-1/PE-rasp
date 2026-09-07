<script lang="ts">
  interface Props {
    name: string;
    active: boolean;
    onclick: () => void;
  }

  let { name, active, onclick }: Props = $props();
</script>

<button
  type="button"
  class="snap-start shrink-0 rounded-full px-3 py-2 text-sm font-medium
         min-h-[44px] sm:min-h-0 transition-colors whitespace-nowrap
         {active
           ? 'bg-teal-500 text-zinc-950'
           : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'}"
  onclick={onclick}
>
  {name}
</button>
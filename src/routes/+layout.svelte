<script lang="ts">
  import '../app.css';
  let { children } = $props();
</script>

<div class="min-h-screen bg-zinc-950 text-zinc-100">
  <div class="max-w-5xl mx-auto px-4 py-4 sm:py-6">
    {@render children()}
  </div>
</div>
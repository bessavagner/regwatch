<script lang="ts">
  import Button from './lib/ui/Button.svelte';
  let count = $state(0);
</script>

<main class="mx-auto max-w-md p-6">
  <h1 class="text-xl font-semibold text-brand-600">RegWatch</h1>
  <Button onclick={() => (count += 1)}>count is {count}</Button>
</main>

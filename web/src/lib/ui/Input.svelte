<script lang="ts">
  let {
    value = $bindable(''),
    type = 'text',
    placeholder = '',
    id,
  }: { value?: string; type?: string; placeholder?: string; id?: string } = $props();
</script>

<input
  {id}
  {type}
  {placeholder}
  bind:value
  class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
/>

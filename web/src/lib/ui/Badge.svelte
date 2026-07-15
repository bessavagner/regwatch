<script lang="ts">
  let { label, tone = 'gray' }: { label: string; tone?: 'gray' | 'green' | 'red' | 'blue' } = $props();
  const tones = {
    gray: 'bg-neutral-bg text-neutral-text',
    green: 'bg-success-bg text-success',
    red: 'bg-danger-bg text-danger',
    blue: 'bg-accent-2-bg text-accent-2',
  };
</script>

<span
  class="inline-block whitespace-nowrap rounded-control px-2 py-0.5 font-mono text-xs font-medium uppercase tracking-wide {tones[tone]}"
  >{label}</span
>

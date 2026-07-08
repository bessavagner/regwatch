<script lang="ts">
  let { label, tone = 'gray' }: { label: string; tone?: 'gray' | 'green' | 'red' | 'blue' } = $props();
  const tones = {
    gray: 'bg-gray-100 text-gray-700',
    green: 'bg-green-100 text-green-700',
    red: 'bg-red-100 text-red-700',
    blue: 'bg-brand-50 text-brand-600',
  };
</script>

<span class="inline-block rounded-full px-2 py-0.5 text-xs font-medium {tones[tone]}">{label}</span>

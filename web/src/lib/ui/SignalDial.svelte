<script lang="ts">
  // The apparatus (Lumen "indicator dial" family) — a hand-built instrument, never a
  // generic glow/orb. The arc fill is honestly derived from the real match count
  // (more signal → fuller arc); it never claims a specific invented percentage.
  let { value }: { value: number } = $props();

  const R = 48;
  const CIRCUMFERENCE = 2 * Math.PI * R;
  const fillRatio = $derived(Math.min(0.92, Math.max(0.12, value / 30)));
  const arcLength = $derived(CIRCUMFERENCE * fillRatio);
  const ticks = Array.from({ length: 12 }, (_, i) => i * 30);
</script>

<div class="apparatus" role="img" aria-label="{value} matches tracked">
  <svg viewBox="0 0 120 120">
    <circle class="apparatus__ring" cx="60" cy="60" r={R} fill="none" stroke-width="2" />
    {#each ticks as deg}
      <line
        class="apparatus__tick"
        x1="60"
        y1="8"
        x2="60"
        y2="14"
        stroke-width="1"
        transform="rotate({deg} 60 60)"
      />
    {/each}
    <circle
      class="apparatus__arc"
      cx="60"
      cy="60"
      r={R}
      fill="none"
      stroke-width="3"
      stroke-linecap="round"
      stroke-dasharray="{arcLength} {CIRCUMFERENCE}"
      transform="rotate(-90 60 60)"
    />
  </svg>
  <div class="apparatus__readout">
    <span class="apparatus__value tabular-nums">{value}</span>
    <span class="apparatus__unit">signal</span>
  </div>
</div>

<template>
  <div class="skel-wrap" role="status" :aria-label="label">
    <div v-for="n in rows" :key="n" class="skel-row" :style="{ opacity: 1 - n / (rows + 2) }">
      <span class="skel-bar" :style="{ width: widths[n % widths.length] }" />
    </div>
    <span class="skel-sr">{{ label }}</span>
  </div>
</template>

<script setup>
defineProps({
  rows:   { type: Number, default: 8 },
  label:  { type: String, default: 'Loading data' },
})

const widths = ['38%', '52%', '46%', '61%', '44%', '57%', '40%', '49%']
</script>

<style scoped>
.skel-wrap { display: flex; flex-direction: column; gap: 10px; padding: 16px 4px; }
.skel-row  { display: flex; }

.skel-bar {
  display: block;
  height: 12px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--surface-variant) 50%, var(--surface-2) 75%);
  background-size: 200% 100%;
  animation: skel-sweep 1.4s ease-in-out infinite;
}

@keyframes skel-sweep {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skel-bar { animation: none; }
}

.skel-sr {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}
</style>

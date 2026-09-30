<template>
  <div
    class="infotip"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
  >
    <span class="infotip-trigger" :class="{ 'infotip-trigger--active': visible }">!</span>
    <div
      class="infotip-box"
      :class="[`infotip-box--${align}`, { 'infotip-box--visible': visible }]"
      :style="{ width: props.width }"
      @mouseenter="onEnter"
      @mouseleave="onLeave"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  align: { type: String, default: 'right' }, // 'right' | 'left' | 'center'
  width: { type: String, default: '280px'  },
})

const visible  = ref(false)
let closeTimer = null

function onEnter() {
  clearTimeout(closeTimer)
  visible.value = true
}

function onLeave() {
  closeTimer = setTimeout(() => {
    visible.value = false
  }, 300)
}
</script>

<style scoped>
.infotip {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.infotip-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border: 1px solid var(--hairline-strong);
  background: transparent;
  color: var(--ink-faint);
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
  cursor: default;
  user-select: none;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.infotip-trigger--active {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-soft);
}

.infotip-box {
  position: absolute;
  top: calc(100% + 8px);
  z-index: 200;
  padding: 12px 14px;
  background: var(--surface);
  border: 1px solid var(--hairline-strong);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55);
  color: var(--ink-muted);
  font-size: 12px;
  line-height: 1.6;
  pointer-events: none;
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.infotip-box--visible { pointer-events: auto; opacity: 1; transform: translateY(0); }

.infotip-box::before {
  content: '';
  position: absolute;
  top: -5px;
  width: 8px;
  height: 8px;
  background: var(--surface);
  border-left: 1px solid var(--hairline-strong);
  border-top: 1px solid var(--hairline-strong);
  transform: rotate(45deg);
}

.infotip-box--right         { right: 0; }
.infotip-box--right::before { right: 6px; }
.infotip-box--left          { left: 0; }
.infotip-box--left::before  { left: 6px; }

.infotip-box--center                      { left: 50%; transform: translateX(-50%) translateY(-4px); }
.infotip-box--center.infotip-box--visible { transform: translateX(-50%) translateY(0); }
.infotip-box--center::before              { left: 50%; transform: translateX(-50%) rotate(45deg); }

.infotip-box :deep(b)  { color: var(--ink); font-weight: 600; }
.infotip-box :deep(p)  { margin: 4px 0 0; }
.infotip-box :deep(p:first-child) { margin-top: 0; }
.infotip-box :deep(.tip-row) { display: flex; gap: 6px; align-items: baseline; margin-top: 5px; }
.infotip-box :deep(.tip-icon)  { flex-shrink: 0; }
.infotip-box :deep(.tip-label) { color: var(--ink); font-weight: 500; }
</style>

<template>
  <v-dialog
    :model-value="modelValue"
    :max-width="maxWidth"
    :persistent="persistent"
    :close-on-back="!persistent"
    scrollable
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card class="app-dialog" :class="`app-dialog--${tone}`" color="surface" variant="flat" border>
      <v-card-title class="app-dialog__head">
        <span v-if="icon" class="mdi app-dialog__icon" :class="icon" />
        <span class="eyebrow app-dialog__title">{{ title }}</span>
        <v-spacer />
        <v-btn
          v-if="!persistent"
          icon="mdi-close"
          variant="text"
          size="small"
          @click="emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-divider />

      <v-card-text :class="flush ? 'pa-0' : 'px-5 py-4'"><slot /></v-card-text>

      <template v-if="$slots.actions">
        <v-divider />
        <v-card-actions class="px-5 py-4 justify-end"><slot name="actions" /></v-card-actions>
      </template>
    </v-card>
  </v-dialog>
</template>

<script setup>
defineProps({
  modelValue: Boolean,
  title:      { type: String, default: '' },
  icon:       { type: String, default: '' },
  maxWidth:   { type: [String, Number], default: 560 },
  tone:       { type: String, default: 'primary' },   // 'primary' | 'warn'
  persistent: Boolean,
  flush:      Boolean,                                  // no body padding (sections pad themselves)
})
const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.app-dialog                     { --accent: var(--primary); }
.app-dialog--warn               { --accent: var(--c-warn); }
.app-dialog__head               { display: flex; align-items: center; gap: 10px; padding: 14px 16px; }
.app-dialog__icon               { font-size: 18px; color: var(--accent); }
.app-dialog__title              { font-size: 13px; color: var(--ink); }
.app-dialog--warn .app-dialog__title { color: var(--accent); }
</style>

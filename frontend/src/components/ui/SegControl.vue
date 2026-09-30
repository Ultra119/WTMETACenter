<template>
  <div class="ui-group" :class="{ 'ui-group--gap': gap, 'ui-group--fill': fill }" role="group">
    <button
      v-for="o in options"
      :key="o.value"
      type="button"
      class="ui-btn"
      :class="{ 'is-active': o.value === modelValue }"
      :title="o.title"
      @click="emit('update:modelValue', o.value)"
    >
      <v-icon v-if="o.icon" size="14">{{ o.icon }}</v-icon>{{ o.label }}
    </button>
  </div>
</template>

<script setup>
// options: [{ value, label, icon?, title? }]
defineProps({
  modelValue: { default: null },
  options:    { type: Array, required: true },
  fill:       Boolean,
  gap:        Boolean,
})
const emit = defineEmits(['update:modelValue'])
</script>

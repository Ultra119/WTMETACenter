<template>
  <v-dialog
    :model-value="modelValue"
    max-width="560"
    persistent
    :close-on-back="false"
    :close-on-content-click="false"
  >
    <v-card color="surface" variant="flat" border>

      <v-card-title class="d-flex align-center ga-3 px-5 pt-5 pb-0">
        <span class="mdi mdi-alert-outline disclaimer-icon" />
        <span class="disclaimer-title">{{ t('disclaimer.title') }}</span>
      </v-card-title>

      <v-divider class="mt-3" />

      <v-card-text class="px-5 py-4">
        <p class="disclaimer-body">{{ t('disclaimer.body_1') }}</p>
        <p class="disclaimer-body mt-3">{{ t('disclaimer.body_2') }}</p>

        <v-alert
          type="warning"
          variant="tonal"
          density="compact"
          class="mt-4"
          icon="mdi-alert-outline"
        >
          {{ t('disclaimer.legal') }}
        </v-alert>

        <p class="disclaimer-note mt-3">{{ t('disclaimer.note') }}</p>
      </v-card-text>

      <v-divider />

      <v-card-actions class="px-5 py-4 justify-end">
        <v-btn
          color="primary"
          variant="outlined"
          size="large"
          prepend-icon="mdi-check-circle-outline"
          @click="$emit('accept')"
        >
          {{ t('disclaimer.accept') }}
        </v-btn>
      </v-card-actions>

    </v-card>
  </v-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue', 'accept'])
</script>

<style scoped>
.disclaimer-icon  { font-size: 22px; line-height: 1; color: var(--amber); }
.disclaimer-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--amber);
}
.disclaimer-body {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: rgba(231, 233, 238, 0.8);
}
.disclaimer-note {
  margin: 0;
  font-size: 12px;
  color: var(--ink-faint);
}
</style>

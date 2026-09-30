<template>
  <AppDialog
    :model-value="modelValue"
    :title="t('disclaimer.title')"
    icon="mdi-alert-outline"
    tone="warn"
    persistent
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <p class="dc-body">{{ t('disclaimer.body_1') }}</p>
    <p class="dc-body mt-3">{{ t('disclaimer.body_2') }}</p>

    <v-alert type="warning" variant="tonal" density="compact" class="mt-4" icon="mdi-alert-outline">
      {{ t('disclaimer.legal') }}
    </v-alert>

    <p class="s mt-3">{{ t('disclaimer.note') }}</p>

    <template #actions>
      <v-btn color="primary" size="large" prepend-icon="mdi-check-circle-outline" @click="$emit('accept')">
        {{ t('disclaimer.accept') }}
      </v-btn>
    </template>
  </AppDialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import AppDialog from './ui/AppDialog.vue'

const { t } = useI18n()

defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue', 'accept'])
</script>

<style scoped>
.dc-body { margin: 0; font-size: 14px; line-height: 1.65; color: rgba(231, 233, 238, 0.8); }
</style>

<template>
  <AppDialog
    :model-value="modelValue"
    :title="t('about.title')"
    icon="mdi-information-outline"
    max-width="580"
    flush
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <section class="ab-section">
      <div class="eyebrow ab-title"><span class="mdi mdi-rocket-launch-outline" />{{ t('about.section_about') }}</div>
      <p class="s">{{ t('about.project_desc') }}</p>
      <div class="ab-links">
        <a class="ui-btn tint" href="https://github.com/Ultra119/wt_meta_center" target="_blank" rel="noopener noreferrer">
          <span class="mdi mdi-github" />{{ t('about.link_github') }}
        </a>
        <a class="ui-btn tint tint--warn" href="https://github.com/Ultra119/wt_meta_center/issues" target="_blank" rel="noopener noreferrer">
          <span class="mdi mdi-bug-outline" />{{ t('about.link_issues') }}
        </a>
      </div>
    </section>

    <v-divider />

    <template v-if="store.metaInfo">
      <section class="ab-section">
        <div class="eyebrow ab-title"><span class="mdi mdi-database-outline" />{{ t('about.section_dataset') }}</div>
        <div v-if="store.metaInfo.dataset_date" class="kv kv--ruled kv--eyebrow">
          <span class="kv__k">{{ t('about.dataset_date') }}</span>
          <span class="kv__v">{{ store.metaInfo.dataset_date }}</span>
        </div>
        <div v-if="store.metaInfo.dataset_hash" class="kv kv--ruled kv--eyebrow">
          <span class="kv__k">{{ t('about.dataset_hash') }}</span>
          <span class="kv__v text-primary">{{ store.metaInfo.dataset_hash.slice(0, 12) }}</span>
        </div>
        <div v-if="store.periods?.length" class="kv kv--ruled kv--eyebrow">
          <span class="kv__k">{{ t('about.periods_available') }}</span>
          <span class="kv__v text-primary">{{ store.periods.filter(p => p !== 'All').length }}</span>
        </div>
        <div v-if="store.metaInfo.nations?.length" class="kv kv--ruled kv--eyebrow">
          <span class="kv__k">{{ t('about.nations_count') }}</span>
          <span class="kv__v text-primary">{{ store.metaInfo.nations.length }}</span>
        </div>
      </section>
      <v-divider />
    </template>

    <section class="ab-section">
      <div class="eyebrow ab-title"><span class="mdi mdi-source-branch" />{{ t('about.section_data') }}</div>
      <div class="ab-item"><span class="mdi mdi-chart-bar" /><span>{{ t('about.data_stats') }}</span></div>
      <div class="ab-item"><span class="mdi mdi-database" /><span>{{ t('about.data_vdb') }}</span></div>
      <div class="ab-item"><span class="mdi mdi-function-variant" /><span>{{ t('about.data_scores') }}</span></div>
      <div class="ab-links">
        <a class="ui-btn ui-btn--sm tint" href="https://github.com/gszabi99/War-Thunder-Datamine" target="_blank" rel="noopener noreferrer">
          <span class="mdi mdi-open-in-new" />{{ t('about.link_datamine') }}
        </a>
        <a class="ui-btn ui-btn--sm tint" href="https://github.com/Sgambe33/WT-Vehicle-Data-Extract" target="_blank" rel="noopener noreferrer">
          <span class="mdi mdi-open-in-new" />{{ t('about.link_datamine_extract') }}
        </a>
      </div>
    </section>

    <v-divider />

    <section class="ab-section ab-section--legal">
      <div class="eyebrow ab-title"><span class="mdi mdi-alert-circle-outline" />{{ t('about.section_legal') }}</div>
      <p class="s">{{ t('disclaimer.body_1') }}</p>
      <p class="s">{{ t('disclaimer.body_2') }}</p>
      <p class="s t-dim ab-legal">{{ t('disclaimer.legal') }}</p>
    </section>
  </AppDialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import AppDialog from './ui/AppDialog.vue'

const { t } = useI18n()
const store  = useDataStore()

defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])
</script>

<style scoped>
.ab-section         { padding: 16px; }
.ab-section--legal  { background: color-mix(in srgb, var(--c-bad) 4%, transparent); }
.ab-title           { display: flex; align-items: center; gap: 6px; margin-bottom: 12px; }
.ab-title .mdi      { font-size: 13px; color: var(--primary); }
.ab-links           { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.ab-item            { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px; font-size: 13px; line-height: 1.5; color: var(--ink-muted); }
.ab-item .mdi       { margin-top: 2px; color: var(--ink-dim); }
.ab-legal           { font-size: 11px; }
</style>

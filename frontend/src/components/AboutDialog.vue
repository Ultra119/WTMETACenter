<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="580" scrollable>
    <v-card color="surface" variant="flat" border>

      <v-card-title class="about-header">
        <span class="mdi mdi-information-outline about-header-icon" />
        <span class="about-header-title">{{ t('about.title') }}</span>
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" size="small" :title="t('common.close')" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-0">

        <div class="ab-section">
          <div class="ab-section-title">
            <span class="mdi mdi-rocket-launch-outline" />
            {{ t('about.section_about') }}
          </div>
          <p class="ab-text">{{ t('about.project_desc') }}</p>
          <div class="ab-links">
            <a
              href="https://github.com/Ultra119/wt_meta_center"
              target="_blank"
              rel="noopener noreferrer"
              class="ab-link"
            >
              <span class="mdi mdi-github" />
              {{ t('about.link_github') }}
            </a>
            <a
              href="https://github.com/Ultra119/wt_meta_center/issues"
              target="_blank"
              rel="noopener noreferrer"
              class="ab-link ab-link--warn"
            >
              <span class="mdi mdi-bug-outline" />
              {{ t('about.link_issues') }}
            </a>
          </div>
        </div>

        <v-divider />

        <div v-if="store.metaInfo" class="ab-section">
          <div class="ab-section-title">
            <span class="mdi mdi-database-outline" />
            {{ t('about.section_dataset') }}
          </div>
          <div v-if="store.metaInfo.dataset_date" class="ab-stat-row">
            <span class="ab-stat-label">{{ t('about.dataset_date') }}</span>
            <span class="ab-stat-value">{{ store.metaInfo.dataset_date }}</span>
          </div>
          <div v-if="store.metaInfo.dataset_hash" class="ab-stat-row">
            <span class="ab-stat-label">{{ t('about.dataset_hash') }}</span>
            <span class="ab-stat-value ab-mono">{{ store.metaInfo.dataset_hash.slice(0, 12) }}</span>
          </div>
          <div v-if="store.periods?.length" class="ab-stat-row">
            <span class="ab-stat-label">{{ t('about.periods_available') }}</span>
            <span class="ab-stat-value ab-mono">{{ store.periods.filter(p => p !== 'All').length }}</span>
          </div>
          <div v-if="store.metaInfo.nations?.length" class="ab-stat-row">
            <span class="ab-stat-label">{{ t('about.nations_count') }}</span>
            <span class="ab-stat-value ab-mono">{{ store.metaInfo.nations.length }}</span>
          </div>
        </div>

        <v-divider v-if="store.metaInfo" />

        <div class="ab-section">
          <div class="ab-section-title">
            <span class="mdi mdi-source-branch" />
            {{ t('about.section_data') }}
          </div>
          <div class="ab-item">
            <span class="mdi mdi-chart-bar ab-bullet" />
            <span class="ab-item-text">{{ t('about.data_stats') }}</span>
          </div>
          <div class="ab-item">
            <span class="mdi mdi-database ab-bullet" />
            <span class="ab-item-text">{{ t('about.data_vdb') }}</span>
          </div>
          <div class="ab-item">
            <span class="mdi mdi-function-variant ab-bullet" />
            <span class="ab-item-text">{{ t('about.data_scores') }}</span>
          </div>
          <a
            href="https://github.com/gszabi99/War-Thunder-Datamine"
            target="_blank"
            rel="noopener noreferrer"
            class="ab-link ab-link--sm"
            style="margin-top: 10px;"
          >
            <span class="mdi mdi-open-in-new" />
            {{ t('about.link_datamine') }}
          </a>
          <a
            href="https://github.com/Sgambe33/WT-Vehicle-Data-Extract"
            target="_blank"
            rel="noopener noreferrer"
            class="ab-link ab-link--sm"
            style="margin-top: 10px;"
            >
            <span class="mdi mdi-open-in-new" />
            {{ t('about.link_datamine_extract') }}
         </a>
        </div>

        <v-divider />

        <div class="ab-section ab-section--legal">
          <div class="ab-section-title">
            <span class="mdi mdi-alert-circle-outline" />
            {{ t('about.section_legal') }}
          </div>
          <p class="ab-text ab-text--muted">{{ t('disclaimer.body_1') }}</p>
          <p class="ab-text ab-text--muted">{{ t('disclaimer.body_2') }}</p>
          <p class="ab-text ab-text--legal">{{ t('disclaimer.legal') }}</p>
        </div>

      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'

const { t } = useI18n()
const store  = useDataStore()

defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])
</script>

<style scoped>
.about-header {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  gap: 10px;
}
.about-header-icon  { font-size: 18px; color: var(--primary); flex-shrink: 0; }
.about-header-title {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink);
}

.ab-section { padding: 16px; }
.ab-section--legal { background: rgba(232, 96, 123, 0.04); }

.ab-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.ab-section-title .mdi { font-size: 13px; color: var(--primary); }

.ab-text {
  margin: 0 0 6px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--ink-muted);
}
.ab-text--muted { font-size: 12px; color: var(--ink-faint); }
.ab-text--legal { margin-bottom: 0; font-size: 11px; color: var(--ink-dim); }

.ab-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.ab-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 11px;
  border: 1px solid var(--primary-line);
  background: transparent;
  color: var(--primary);
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-decoration: none;
  transition: background 0.15s;
}
.ab-link:hover { background: var(--primary-soft); }
.ab-link .mdi  { font-size: 13px; }

.ab-link--warn { color: var(--amber); border-color: rgba(245, 166, 35, 0.4); }
.ab-link--warn:hover { background: rgba(245, 166, 35, 0.08); }
.ab-link--sm { padding: 3px 9px; font-size: 10px; }

.ab-stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--hairline);
}
.ab-stat-row:last-of-type { border-bottom: none; }
.ab-stat-label {
  font-family: var(--font-display);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.ab-stat-value { font-family: var(--font-display); font-size: 12px; color: var(--ink); }
.ab-mono { color: var(--primary); }

.ab-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--ink-muted);
}
.ab-bullet { flex-shrink: 0; margin-top: 2px; font-size: 13px; color: var(--ink-dim); }
.ab-item-text { line-height: 1.5; }
</style>

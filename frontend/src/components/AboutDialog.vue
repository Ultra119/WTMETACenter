<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="580" scrollable>
    <v-card color="#0f172a" style="border: 1px solid #1e3a5f;">

      <v-card-title class="about-header">
        <span class="mdi mdi-information-outline about-header-icon" />
        <span class="about-header-title">{{ t('about.title') }}</span>
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" size="small" :title="t('common.close')" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider color="#1e293b" />

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

        <v-divider color="#1e293b" />

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

        <v-divider v-if="store.metaInfo" color="#1e293b" />

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

        <v-divider color="#1e293b" />

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
  padding: 12px 16px;
  gap: 8px;
}
.about-header-icon {
  font-size: 18px;
  color: #38bdf8;
  opacity: 0.75;
  flex-shrink: 0;
}
.about-header-title {
  font-size: 17px;
  font-weight: 700;
  color: #a7f3d0;
  letter-spacing: .06em;
}

.ab-section {
  padding: 14px 16px;
}
.ab-section--legal {
  background: rgba(239, 68, 68, 0.025);
}

.ab-section-title {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .12em;
  color: #475569;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.ab-section-title .mdi {
  font-size: 13px;
  opacity: 0.7;
}

.ab-text {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.65;
  margin: 0 0 6px;
}
.ab-text--muted {
  color: #64748b;
  font-size: 11px;
}
.ab-text--legal {
  color: #475569;
  font-size: 10px;
  font-style: italic;
  margin-bottom: 0;
}

.ab-links {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.ab-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 11px;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  background: transparent;
  color: #38bdf8;
  font-size: 11px;
  font-weight: 600;
  text-decoration: none;
  letter-spacing: .04em;
  transition: border-color .15s, background .15s;
}
.ab-link:hover {
  border-color: rgba(56, 189, 248, 0.4);
  background: rgba(56, 189, 248, 0.07);
}
.ab-link .mdi { font-size: 13px; }

.ab-link--warn {
  color: #fb923c;
  border-color: rgba(251, 146, 60, 0.2);
}
.ab-link--warn:hover {
  border-color: rgba(251, 146, 60, 0.45);
  background: rgba(251, 146, 60, 0.06);
}
.ab-link--sm {
  font-size: 10px;
  padding: 3px 9px;
}

.ab-stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  font-size: 12px;
  border-bottom: 1px solid rgba(30, 41, 59, 0.5);
}
.ab-stat-row:last-of-type { border-bottom: none; }
.ab-stat-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: .07em;
  text-transform: uppercase;
  color: #475569;
}
.ab-stat-value {
  color: #e2e8f0;
  font-weight: 600;
}
.ab-mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #7dd3fc;
}

.ab-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 7px;
  font-size: 12px;
  color: #64748b;
}
.ab-bullet {
  font-size: 13px;
  color: #334155;
  flex-shrink: 0;
  margin-top: 1px;
}
.ab-item-text { line-height: 1.5; }
</style>

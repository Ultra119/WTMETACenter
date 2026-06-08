<template>
  <v-app-bar
    elevation="0"
    height="48"
    style="background: #0a1628; border-bottom: 1px solid #1e3a5f; z-index: 1000;"
  >
    <v-app-bar-title>
      <div class="logo-group">
        <span class="logo-title">{{ t('topbar.title') }}</span>
        <a
          href="https://github.com/Ultra119/wt_meta_center/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="report-link"
          :title="t('topbar.report_title')"
        >
          <span class="mdi mdi-bug-outline" />
          <span class="report-text">{{ t('topbar.report') }}</span>
        </a>
      </div>
    </v-app-bar-title>

    <v-spacer />

    <div class="lang-switcher ml-3">
      <v-btn
        v-for="loc in SUPPORTED_LOCALES"
        :key="loc.code"
        :variant="locale === loc.code ? 'tonal' : 'text'"
        size="x-small"
        class="lang-btn"
        @click="setLocale(loc.code)"
      >
        {{ loc.flag }} {{ loc.label }}
      </v-btn>
    </div>

    <div class="px-2" />
  </v-app-bar>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import { setLocale, SUPPORTED_LOCALES } from '../i18n/index.js'

const { t, locale } = useI18n()
const store = useDataStore()
</script>

<style scoped>
.logo-group {
  display: inline-flex;
  align-items: baseline;
  gap: 10px;
}

.logo-title {
  font-size: 22px;
  font-weight: 700;
  color: #a7f3d0;
  letter-spacing: 0.08em;
}

.report-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #334155;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.05em;
  white-space: nowrap;
  flex-shrink: 0;
  transition: color 0.15s;
}
.report-link:hover { color: #64748b; }
.report-link .mdi  { font-size: 13px; }
.report-text       { line-height: 1; }

.lang-switcher { display: flex; gap: 2px; }
.lang-btn {
  font-size: 11px !important;
  min-width: 44px !important;
}
</style>

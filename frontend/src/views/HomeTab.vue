<template>
  <div class="home-page">

    <header class="home-header">
      <div class="label-eyebrow home-eyebrow">
        <span class="mdi mdi-radar" />
        {{ t('home_tab.eyebrow') }}
      </div>
      <h1 class="home-title">{{ t('topbar.title') }}</h1>
      <p class="s home-sub">{{ t('home_tab.subtitle') }}</p>
    </header>

    <div class="cards-grid">
      <router-link
        v-for="(card, i) in cards"
        :key="card.to"
        :to="card.to"
        class="tab-card"
        @click="onCardClick"
      >
        <div class="card-top">
          <span class="card-n">{{ String(i + 1).padStart(2, '0') }}</span>
          <v-icon class="card-icon" size="20">{{ card.icon }}</v-icon>
        </div>
        <div class="card-title">{{ t(card.labelKey) }}</div>
        <div class="card-desc">{{ t(card.descKey) }}</div>
        <v-icon class="card-arrow" size="16">mdi-arrow-top-right</v-icon>
      </router-link>
    </div>

  </div>
</template>

<script setup>
import { inject } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const toggleSidebar = inject('toggleSidebar', null)
const sidebarOpen   = inject('sidebarOpen', null)

function onCardClick() {
  if (sidebarOpen && !sidebarOpen.value) {
    toggleSidebar?.()
  }
}

const cards = [
  { to: '/meta',        icon: 'mdi-trophy',                   labelKey: 'tabs.meta',        descKey: 'home_tab.desc_meta'        },
  { to: '/brackets',    icon: 'mdi-view-grid',                labelKey: 'tabs.brackets',    descKey: 'home_tab.desc_brackets'    },
  { to: '/farm',        icon: 'mdi-wrench',                   labelKey: 'tabs.farm',        descKey: 'home_tab.desc_farm'        },
  { to: '/progression', icon: 'mdi-chart-timeline-variant',   labelKey: 'tabs.progression', descKey: 'home_tab.desc_progression' },
  { to: '/cost',        icon: 'mdi-chart-bar',                labelKey: 'tabs.cost',        descKey: 'home_tab.desc_cost'        },
  { to: '/history',     icon: 'mdi-clock-time-eight-outline', labelKey: 'tabs.history',     descKey: 'home_tab.desc_history'     },
]
</script>

<style scoped>
.home-page { max-width: 1240px; margin: 0 auto; padding: 32px 0 64px; }

.home-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--hairline);
}
.home-eyebrow { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.home-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.01em;
  text-transform: uppercase;
  color: var(--primary);
}
.home-sub { max-width: 60ch; margin-top: 12px; }

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

.tab-card {
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 16px 18px 18px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  color: inherit;
  text-decoration: none;
  transition: border-color 0.15s;
}
.tab-card:hover { border-color: var(--primary-line); }

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.card-n {
  font-family: var(--font-display);
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--primary);
}
.card-icon { color: var(--ink-dim); transition: color 0.15s; }
.tab-card:hover .card-icon { color: var(--primary); }

.card-title {
  margin-bottom: 6px;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink);
}
.card-desc {
  padding-right: 20px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--ink-muted);
}

.card-arrow {
  position: absolute;
  right: 14px;
  bottom: 14px;
  color: var(--primary);
  opacity: 0;
  transform: translate(-4px, 4px);
  transition: opacity 0.15s, transform 0.15s;
}
.tab-card:hover .card-arrow { opacity: 1; transform: none; }

@media (max-width: 720px) {
  .home-page  { padding-top: 8px; }
  .home-title { font-size: 28px; }
}
</style>

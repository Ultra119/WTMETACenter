<template>
  <div class="home-page">

    <div class="home-header">
      <div class="home-eyebrow">
        <span class="mdi mdi-radar" />
        {{ t('home_tab.eyebrow') }}
      </div>
      <h1 class="home-title">{{ t('topbar.title') }}</h1>
      <p class="home-sub">{{ t('home_tab.subtitle') }}</p>
    </div>

    <div class="cards-grid">
      <router-link
        v-for="card in cards"
        :key="card.to"
        :to="card.to"
        class="tab-card"
        :style="{ '--card-accent': card.color }"
        @click="onCardClick"
      >
        <div class="card-stripe" />
        <div class="card-icon-wrap">
          <v-icon :color="card.color" size="24">{{ card.icon }}</v-icon>
        </div>
        <div class="card-body">
          <div class="card-title">{{ t(card.labelKey) }}</div>
          <div class="card-desc">{{ t(card.descKey) }}</div>
        </div>
        <v-icon class="card-arrow" size="15" color="#334155">mdi-arrow-right</v-icon>
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
  { to: '/meta',        icon: 'mdi-trophy',                   color: '#a7f3d0', labelKey: 'tabs.meta',        descKey: 'home_tab.desc_meta'        },
  { to: '/redbook',     icon: 'mdi-book-open',                color: '#f87171', labelKey: 'tabs.redbook',     descKey: 'home_tab.desc_redbook'     },
  { to: '/brackets',    icon: 'mdi-view-grid',                color: '#38bdf8', labelKey: 'tabs.brackets',    descKey: 'home_tab.desc_brackets'    },
  { to: '/farm',        icon: 'mdi-wrench',                   color: '#fbbf24', labelKey: 'tabs.farm',        descKey: 'home_tab.desc_farm'        },
  { to: '/progression', icon: 'mdi-chart-timeline-variant',   color: '#a78bfa', labelKey: 'tabs.progression', descKey: 'home_tab.desc_progression' },
  { to: '/cost',        icon: 'mdi-chart-bar',                color: '#34d399', labelKey: 'tabs.cost',        descKey: 'home_tab.desc_cost'        },
  { to: '/history',     icon: 'mdi-clock-time-eight-outline', color: '#fb923c', labelKey: 'tabs.history',     descKey: 'home_tab.desc_history'     },
]
</script>

<style scoped>
.home-page {
  max-width: 1060px;
  margin: 0 auto;
  padding: 56px 24px 80px;
}

.home-header {
  text-align: center;
  margin-bottom: 48px;
}

.home-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #334155;
  margin-bottom: 14px;
}

.home-title {
  font-size: 40px;
  font-weight: 700;
  color: #a7f3d0;
  letter-spacing: 0.05em;
  margin: 0 0 10px;
  line-height: 1.1;
}

.home-sub {
  font-size: 14px;
  color: #475569;
  margin: 0;
  letter-spacing: 0.03em;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 10px;
}

.tab-card {
  --card-accent: #38bdf8;
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 14px 16px 18px;
  background: #0f172a;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  text-decoration: none;
  overflow: hidden;
  transition: border-color 0.18s, background 0.18s;
  cursor: pointer;
}

.card-stripe {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--card-accent);
  opacity: 0.18;
  transition: opacity 0.18s;
}

.tab-card:hover {
  border-color: #2a4060;
  background: #111d30;
}

.tab-card:hover .card-stripe { opacity: 0.7; }

.card-icon-wrap {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-body  { flex: 1; min-width: 0; }

.card-title {
  font-size: 13px;
  font-weight: 700;
  color: #cbd5e1;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 11px;
  color: #475569;
  line-height: 1.55;
}

.card-arrow {
  flex-shrink: 0;
  opacity: 0;
  transform: translateX(-6px);
  transition: opacity 0.18s, transform 0.18s;
}

.tab-card:hover .card-arrow {
  opacity: 0.4;
  transform: translateX(0);
}
</style>

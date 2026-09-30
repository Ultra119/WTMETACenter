<template>
  <v-app theme="wt">
    <Transition name="filter-bar-fade">
      <div v-if="store.filtering" class="filter-progress-bar">
        <div class="filter-progress-inner" />
      </div>
    </Transition>

    <v-snackbar :model-value="!!store.loadError" color="error" timeout="-1" location="top">
      {{ t('common.error_load', { msg: store.loadError }) }}
    </v-snackbar>

    <TopBar />

    <SideBar :open="showSidebar" />

    <v-main>
      <v-tabs
        v-if="showNav"
        v-model="activeTab"
        bg-color="background"
        color="primary"
        density="compact"
        height="44"
        class="nav-tabs"
      >
        <v-tab v-for="tab in tabs" :key="tab.to" :to="tab.to" :prepend-icon="tab.icon">
          {{ t(tab.labelKey) }}
        </v-tab>
      </v-tabs>

      <div class="page">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </div>
    </v-main>

    <VehicleCard v-model="modalOpen" :vehicle="selectedVehicle" />
    <DisclaimerModal v-model="disclaimerVisible" @accept="acceptDisclaimer" />
  </v-app>
</template>

<script setup>
import { ref, computed, provide, onMounted } from 'vue'
import { useRoute }     from 'vue-router'
import { useI18n }      from 'vue-i18n'
import { useDataStore } from './stores/useDataStore.js'
import TopBar           from './components/TopBar.vue'
import SideBar          from './components/SideBar.vue'
import VehicleCard      from './components/VehicleCard.vue'
import DisclaimerModal  from './components/DisclaimerModal.vue'

const { t }  = useI18n()
const store  = useDataStore()
const route  = useRoute()

const sidebarOpen = ref(true)
const showSidebar = computed(() => sidebarOpen.value && route.path !== '/')
const showNav     = computed(() => route.path !== '/')

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

provide('sidebarOpen',   sidebarOpen)
provide('toggleSidebar', toggleSidebar)

const activeTab = ref('/meta')

const tabs = [
  { to: '/meta',        icon: 'mdi-trophy',                   labelKey: 'tabs.meta'        },
  { to: '/brackets',    icon: 'mdi-view-grid',                labelKey: 'tabs.brackets'    },
  { to: '/farm',        icon: 'mdi-wrench',                   labelKey: 'tabs.farm'        },
  { to: '/progression', icon: 'mdi-chart-timeline-variant',   labelKey: 'tabs.progression' },
  { to: '/cost',        icon: 'mdi-chart-bar',                labelKey: 'tabs.cost'        },
  { to: '/history',     icon: 'mdi-clock-time-eight-outline', labelKey: 'tabs.history'     },
]

const modalOpen       = ref(false)
const selectedVehicle = ref(null)

function openVehicle(v) {
  selectedVehicle.value = v
  modalOpen.value       = true
}

provide('openVehicle', openVehicle)

const DISCLAIMER_KEY    = 'wt_disclaimer_accepted'
const disclaimerVisible = ref(!localStorage.getItem(DISCLAIMER_KEY))

function acceptDisclaimer() {
  localStorage.setItem(DISCLAIMER_KEY, '1')
  disclaimerVisible.value = false
}

onMounted(() => {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '')
  store.loadData(base)
})
</script>

<style>
.nav-tabs { border-bottom: 1px solid var(--hairline); }
.v-tab {
  min-width: 0;
  font-family: var(--font-display) !important;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.page { width: 100%; padding: 24px; }
@media (max-width: 720px) { .page { padding: 16px; } }

.filter-progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  z-index: 9999;
  pointer-events: none;
  overflow: hidden;
}
.filter-progress-inner {
  height: 100%;
  background: var(--primary);
  animation: filter-slide 0.8s ease-in-out infinite;
  transform-origin: left center;
}
@keyframes filter-slide {
  0%   { transform: translateX(-100%) scaleX(0.4); }
  50%  { transform: translateX(30%)   scaleX(0.7); }
  100% { transform: translateX(110%)  scaleX(0.4); }
}
.filter-bar-fade-enter-active,
.filter-bar-fade-leave-active { transition: opacity 0.15s; }
.filter-bar-fade-enter-from,
.filter-bar-fade-leave-to     { opacity: 0; }
</style>

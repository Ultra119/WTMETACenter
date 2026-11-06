<template>
  <v-app theme="wt">
    <Transition name="fade">
      <div v-if="store.filtering" class="filter-progress-bar">
        <div class="filter-progress-inner" />
      </div>
    </Transition>

    <v-snackbar
      :model-value="!!store.loadError"
      color="error"
      timeout="-1"
      location="top"
      @update:model-value="store.clearLoadError()"
    >
      {{ t('common.error_load', { msg: store.loadError }) }}
      <template #actions>
        <v-btn variant="text" size="small" @click="store.clearLoadError()">{{ t('common.close') }}</v-btn>
      </template>
    </v-snackbar>

    <TopBar />

    <SideBar :open="showSidebar" />

    <v-main>
      <v-tabs
        v-if="showNav"
        :model-value="activeTab"
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
import { ref, computed, provide, onMounted, watch } from 'vue'
import { useRoute }     from 'vue-router'
import { useI18n }      from 'vue-i18n'
import { useDataStore } from './stores/useDataStore.js'
import { safeGet, safeSet } from './i18n/index.js'
import { useUrlFilters } from './composables/useUrlFilters.js'
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

const tabs = [
  { to: '/meta',        icon: 'mdi-trophy',                   labelKey: 'tabs.meta'        },
  { to: '/brackets',    icon: 'mdi-view-grid',                labelKey: 'tabs.brackets'    },
  { to: '/farm',        icon: 'mdi-wrench',                   labelKey: 'tabs.farm'        },
  { to: '/progression', icon: 'mdi-chart-timeline-variant',   labelKey: 'tabs.progression' },
  { to: '/cost',        icon: 'mdi-chart-bar',                labelKey: 'tabs.cost'        },
  { to: '/history',     icon: 'mdi-clock-time-eight-outline', labelKey: 'tabs.history'     },
]

const activeTab = computed(() => {
  const path = route.path
  return tabs.some(tab => tab.to === path) ? path : '/meta'
})

const modalOpen       = ref(false)
const selectedVehicle = ref(null)

function openVehicle(v) {
  selectedVehicle.value = v
  modalOpen.value       = true
}

// When the modal closes, clear the selected vehicle (URL will sync automatically)
watch(modalOpen, (open) => {
  if (!open) selectedVehicle.value = null
})

provide('openVehicle', openVehicle)

// URL ↔ filter sync + vehicle deep-link
useUrlFilters({ vehicle: selectedVehicle, modalOpen })

// Vehicle deep-link: when data loads, check if URL has ?vehicle= and open it
watch(
  () => store.allVehicles,
  (vehicles) => {
    if (!vehicles?.length) return
    const vid = route.query.vehicle
    if (!vid || selectedVehicle.value) return
    const found = vehicles.find(v => v.vdb_identifier === vid)
    if (found) {
      selectedVehicle.value = found
      modalOpen.value = true
    }
  },
  { immediate: true }
)

const DISCLAIMER_KEY    = 'wt_disclaimer_accepted'
const disclaimerVisible = ref(!safeGet(DISCLAIMER_KEY))

function acceptDisclaimer() {
  safeSet(DISCLAIMER_KEY, '1')
  disclaimerVisible.value = false
}

onMounted(() => {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '')
  store.loadData(base)
})
</script>

<style scoped>
.filter-progress-bar   { position: fixed; top: 0; left: 0; right: 0; height: 2px; z-index: 9999; pointer-events: none; overflow: hidden; }
.filter-progress-inner { height: 100%; background: var(--primary); animation: filter-slide 0.8s ease-in-out infinite; transform-origin: left center; }
@keyframes filter-slide {
  0%   { transform: translateX(-100%) scaleX(0.4); }
  50%  { transform: translateX(30%)   scaleX(0.7); }
  100% { transform: translateX(110%)  scaleX(0.4); }
}
</style>

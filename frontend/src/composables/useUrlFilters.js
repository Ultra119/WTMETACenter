import { watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDataStore } from '../stores/useDataStore.js'

/**
 * Syncs filter state between the data store and the URL query string.
 *
 * - On mount, hydrates filters from URL query params
 * - Watches store filter refs and updates the URL when they change
 * - Supports deep-linking a vehicle via ?vehicle=<vdb_identifier>
 *
 * Uses router.replace to keep URL in sync without spamming history.
 */
export function useUrlFilters({ vehicle, modalOpen } = {}) {
  const store = useDataStore()
  const route = useRoute()
  const router = useRouter()

  // Flag to prevent infinite loops when syncing bidirectionally
  let _syncing = false

  // Parse query params into filter values
  function parseQuery(query) {
    const filters = {}

    if (query.period) filters.period = query.period
    if (query.mode) filters.mode = query.mode
    if (query.minBattles) filters.minBattles = Number(query.minBattles)
    if (query.search) filters.search = query.search
    if (query.vehicle) filters.vehicle = query.vehicle

    if (query.brMin || query.brMax) {
      const brMin = query.brMin ? Number(query.brMin) : store.BR_MIN
      const brMax = query.brMax ? Number(query.brMax) : store.BR_MAX
      filters.brRange = [brMin, brMax]
    }

    if (query.classes) {
      filters.classes = query.classes.split(',').filter(Boolean)
    }

    // Type toggles
    const typeToggles = ['Ground', 'Aviation', 'Helicopters', 'LargeFleet', 'SmallFleet']
    for (const t of typeToggles) {
      if (query[`show${t}`] !== undefined) {
        filters[`show${t}`] = query[`show${t}`] === '1'
      }
    }

    return filters
  }

  // Serialize store state to query params
  function serializeFilters() {
    const query = {}

    query.period = store.currentPeriod
    query.mode = store.mode
    
    // Only include BR range if it's not the full range
    const fullMin = store.BR_MIN
    const fullMax = store.BR_MAX
    if (store.brRange[0] !== fullMin || store.brRange[1] !== fullMax) {
      query.brMin = store.brRange[0]
      query.brMax = store.brRange[1]
    }
    
    // Only include minBattles if not default (50)
    if (store.minBattles !== 50) {
      query.minBattles = store.minBattles
    }
    
    // Only include classes if not all selected
    const allClasses = ['Standard', 'Premium', 'Pack', 'Squadron', 'Marketplace', 'Gift', 'Event']
    if (store.classes.length !== allClasses.length || 
        !allClasses.every(c => store.classes.includes(c))) {
      query.classes = store.classes.join(',')
    }
    
    // Only include search if non-empty
    if (store.searchQuery) {
      query.search = store.searchQuery
    }

    // Type toggles - only include non-defaults
    // Defaults: Ground=true, Aviation=true, Helicopters=false, LargeFleet=false, SmallFleet=false
    if (!store.showGround) query.showGround = '0'
    if (!store.showAviation) query.showAviation = '0'
    if (store.showHelicopters) query.showHelicopters = '1'
    if (store.showLargeFleet) query.showLargeFleet = '1'
    if (store.showSmallFleet) query.showSmallFleet = '1'

    // Vehicle deep-link
    if (vehicle?.value) {
      query.vehicle = vehicle.value.vdb_identifier
    }

    return query
  }

  // Apply query params to store
  function applyFilters(filters) {
    if (filters.period && store.periods.includes(filters.period)) {
      store.currentPeriod = filters.period
    }
    if (filters.mode) {
      store.mode = filters.mode
    }
    if (filters.brRange) {
      store.brRange = filters.brRange
    }
    if (filters.minBattles !== undefined) {
      store.minBattles = filters.minBattles
    }
    if (filters.classes && Array.isArray(filters.classes)) {
      store.classes = filters.classes
    }
    if (filters.search !== undefined) {
      store.searchQuery = filters.search
    }

    // Type toggles
    const typeToggles = ['Ground', 'Aviation', 'Helicopters', 'LargeFleet', 'SmallFleet']
    for (const t of typeToggles) {
      const key = `show${t}`
      if (filters[key] !== undefined) {
        store[key] = filters[key]
      }
    }
  }

  // Hydrate from URL on mount
  function hydrateFromUrl() {
    const filters = parseQuery(route.query)
    if (Object.keys(filters).length > 0) {
      _syncing = true
      applyFilters(filters)
      nextTick(() => { _syncing = false })
    }
  }

  // Watch store changes and update URL
  function syncToUrl() {
    if (_syncing) return

    const newQuery = serializeFilters()
    const currentQuery = route.query

    // Only update if query actually changed
    const changed = Object.keys(newQuery).some(k => newQuery[k] !== currentQuery[k]) ||
                    Object.keys(currentQuery).some(k => newQuery[k] === undefined)

    if (changed) {
      _syncing = true
      router.replace({ query: newQuery }).finally(() => {
        nextTick(() => { _syncing = false })
      })
    }
  }

  // Watch route changes (back/forward) and apply to store
  function syncFromUrl() {
    if (_syncing) return

    const filters = parseQuery(route.query)
    _syncing = true
    applyFilters(filters)
    nextTick(() => { _syncing = false })
  }

  // Initialize from URL
  hydrateFromUrl()

  // Watch store → URL
  watch(
    () => [
      store.currentPeriod,
      store.mode,
      store.brRange,
      store.minBattles,
      store.classes,
      store.searchQuery,
      store.showGround,
      store.showAviation,
      store.showHelicopters,
      store.showLargeFleet,
      store.showSmallFleet,
      vehicle?.value?.vdb_identifier,
    ],
    () => {
      syncToUrl()
    },
    { deep: true }
  )

  // Watch URL → store (for back/forward navigation)
  watch(() => route.query, () => {
    syncFromUrl()
  })

  return {
    hydrateFromUrl,
    syncToUrl,
  }
}

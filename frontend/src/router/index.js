import { createRouter, createWebHashHistory } from 'vue-router'

const HomeTab        = () => import('../views/HomeTab.vue')
const MetaTab        = () => import('../views/MetaTab.vue')
const BracketsTab    = () => import('../views/BracketsTab.vue')
const FarmTab        = () => import('../views/FarmTab.vue')
const ProgressionTab = () => import('../views/ProgressionTab.vue')
const CostTreeTab    = () => import('../views/CostTreeTab.vue')
const HistoryTab     = () => import('../views/HistoryTab.vue')

const routes = [
  { path: '/',            component: HomeTab,         name: 'home'        },
  { path: '/meta',        component: MetaTab,         name: 'meta'        },
  { path: '/brackets',    component: BracketsTab,     name: 'brackets'    },
  { path: '/farm',        component: FarmTab,         name: 'farm'        },
  { path: '/progression', component: ProgressionTab,  name: 'progression' },
  { path: '/cost',        component: CostTreeTab,     name: 'cost'        },
  { path: '/history',     component: HistoryTab,      name: 'history'     },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})

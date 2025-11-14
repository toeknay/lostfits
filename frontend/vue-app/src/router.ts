import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Fits from './views/Fits.vue'
import FitDetail from './views/FitDetail.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/fits', name: 'fits', component: Fits },
  { path: '/fits/:signature', name: 'fit-detail', component: FitDetail },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

import { createRouter, createWebHistory } from 'vue-router'

export const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/views/dashboard/Index.vue'), meta: { title: '仪表盘', icon: 'LayoutDashboard' } },
  { path: '/monitoring', name: 'monitoring', component: () => import('@/views/monitoring/Index.vue'), meta: { title: '实时监控', icon: 'Radar' } },
  { path: '/inventory', name: 'inventory', component: () => import('@/views/inventory/Index.vue'), meta: { title: '库存管理', icon: 'Boxes' } },
  { path: '/recognition', name: 'recognition', component: () => import('@/views/recognition/Index.vue'), meta: { title: 'AI 识别记录', icon: 'ScanSearch' } },
  { path: '/environment', name: 'environment', component: () => import('@/views/environment/Index.vue'), meta: { title: '环境监测', icon: 'Thermometer' } },
  { path: '/alerts', name: 'alerts', component: () => import('@/views/alerts/Index.vue'), meta: { title: '预警中心', icon: 'BellRing' } },
  { path: '/devices', name: 'devices', component: () => import('@/views/devices/Index.vue'), meta: { title: '设备管理', icon: 'Cpu' } },
  { path: '/history', name: 'history', component: () => import('@/views/history/Index.vue'), meta: { title: '历史记录', icon: 'History' } },
  { path: '/analytics', name: 'analytics', component: () => import('@/views/analytics/Index.vue'), meta: { title: '统计分析', icon: 'ChartNoAxesCombined' } },
  { path: '/settings', name: 'settings', component: () => import('@/views/settings/Index.vue'), meta: { title: '系统设置', icon: 'Settings2' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router

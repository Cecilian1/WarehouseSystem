<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  BellRing, Boxes, ChartNoAxesCombined, ChevronLeft, ChevronRight, Cpu, History, LayoutDashboard, Leaf, Radar, ScanSearch, Settings2, Thermometer,
} from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()
const items = [
  { path: '/dashboard', label: '仪表盘', icon: LayoutDashboard },
  { path: '/monitoring', label: '实时监控', icon: Radar },
  { path: '/inventory', label: '库存管理', icon: Boxes },
  { path: '/recognition', label: 'AI 识别记录', icon: ScanSearch },
  { path: '/environment', label: '环境监测', icon: Thermometer },
  { path: '/alerts', label: '预警中心', icon: BellRing, badge: 3 },
  { path: '/devices', label: '设备管理', icon: Cpu },
  { path: '/history', label: '历史记录', icon: History },
  { path: '/analytics', label: '统计分析', icon: ChartNoAxesCombined },
  { path: '/settings', label: '系统设置', icon: Settings2 },
]

const activePath = computed(() => route.path)
</script>

<template>
  <aside class="sidebar" :class="{ 'is-collapsed': appStore.sidebarCollapsed }">
    <div class="sidebar__brand">
      <div class="brand-mark"><Leaf :size="21" /></div>
      <div v-if="!appStore.sidebarCollapsed" class="brand-copy">
        <strong>芯鲜管家</strong>
        <span>AI · IoT · Freshness</span>
      </div>
    </div>

    <div v-if="!appStore.sidebarCollapsed" class="nav-label">控制中心</div>
    <nav class="sidebar__nav">
      <RouterLink
        v-for="item in items"
        :key="item.path"
        :to="item.path"
        class="nav-item ripple-target"
        :class="{ 'is-active': activePath === item.path }"
        :title="appStore.sidebarCollapsed ? item.label : undefined"
      >
        <component :is="item.icon" :size="18" stroke-width="1.8" />
        <span v-if="!appStore.sidebarCollapsed">{{ item.label }}</span>
        <b v-if="item.badge && !appStore.sidebarCollapsed">{{ item.badge }}</b>
      </RouterLink>
    </nav>

    <div class="sidebar__bottom">
      <div v-if="!appStore.sidebarCollapsed" class="edge-card">
        <div class="edge-card__glow" />
        <div class="edge-card__header"><span class="realtime-dot" />端侧节点在线</div>
        <strong>LoongArch 2K2000-i</strong>
        <small>数据本地闭环运行中</small>
      </div>
      <button class="collapse-button ripple-target" @click="appStore.toggleSidebar">
        <ChevronRight v-if="appStore.sidebarCollapsed" :size="17" />
        <ChevronLeft v-else :size="17" />
        <span v-if="!appStore.sidebarCollapsed">收起导航</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  display: flex;
  width: var(--sidebar-width);
  flex-direction: column;
  padding: 22px 14px 16px;
  border-right: 1px solid var(--stroke);
  background: linear-gradient(180deg, rgba(8, 20, 35, 0.9), rgba(8, 15, 28, 0.7));
  backdrop-filter: blur(24px);
  transition: width 0.28s ease, transform 0.28s ease;
}
:root[data-theme='light'] .sidebar { background: rgba(250, 252, 255, 0.86); }
.sidebar.is-collapsed { width: 78px; padding-inline: 12px; }
.sidebar__brand { display: flex; align-items: center; gap: 11px; padding: 2px 9px 26px; }
.brand-mark { display: grid; width: 38px; height: 38px; flex: 0 0 auto; place-items: center; border: 1px solid rgba(56, 189, 248, 0.34); border-radius: 13px; color: #a8f0ff; background: linear-gradient(145deg, rgba(56, 189, 248, 0.3), rgba(79, 140, 255, 0.16)); box-shadow: 0 0 26px rgba(56, 189, 248, 0.18); }
.brand-copy { min-width: 0; }
.brand-copy strong { display: block; color: var(--text-1); font-size: 15px; }
.brand-copy span { display: block; margin-top: 4px; color: var(--text-3); font-size: 9px; letter-spacing: 0.11em; text-transform: uppercase; }
.nav-label { margin: 0 12px 10px; color: var(--text-3); font-size: 10px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }
.sidebar__nav { display: grid; gap: 5px; }
.nav-item { position: relative; display: flex; align-items: center; gap: 13px; min-height: 43px; padding: 0 12px; overflow: hidden; border: 1px solid transparent; border-radius: 12px; color: var(--text-2); transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease; }
.nav-item:hover { color: var(--text-1); background: var(--surface-soft); transform: translateX(2px); }
.nav-item.is-active { border-color: rgba(79, 140, 255, 0.2); color: #e6efff; background: linear-gradient(90deg, rgba(79, 140, 255, 0.2), rgba(56, 189, 248, 0.07)); box-shadow: inset 3px 0 0 var(--blue), 0 8px 20px rgba(0, 0, 0, 0.1); }
:root[data-theme='light'] .nav-item.is-active { color: var(--text-1); }
.nav-item.is-active::after { position: absolute; right: 10px; width: 4px; height: 4px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 9px var(--cyan); content: ""; }
.nav-item span { overflow: hidden; white-space: nowrap; font-size: 13px; }
.nav-item b { display: grid; min-width: 18px; height: 18px; margin-left: auto; place-items: center; border-radius: 999px; color: white; font-size: 10px; background: var(--red); }
.sidebar__bottom { margin-top: auto; }
.edge-card { position: relative; overflow: hidden; margin: 18px 3px 14px; padding: 14px; border: 1px solid rgba(34, 197, 94, 0.18); border-radius: 15px; background: linear-gradient(145deg, rgba(34, 197, 94, 0.12), rgba(20, 184, 166, 0.04)); }
.edge-card__glow { position: absolute; top: -30px; right: -18px; width: 80px; height: 80px; border-radius: 50%; background: rgba(34, 197, 94, 0.16); filter: blur(14px); }
.edge-card__header { position: relative; display: flex; align-items: center; color: #9cf2b8; font-size: 11px; }
.edge-card strong { position: relative; display: block; margin-top: 14px; color: var(--text-1); font-size: 12px; }
.edge-card small { position: relative; display: block; margin-top: 5px; color: var(--text-3); font-size: 10px; }
.collapse-button { display: flex; width: 100%; align-items: center; gap: 11px; min-height: 40px; padding: 0 12px; border: 1px solid var(--stroke); border-radius: 11px; color: var(--text-2); background: transparent; transition: background 0.2s ease, color 0.2s ease; }
.collapse-button:hover { color: var(--text-1); background: var(--surface-soft); }
.collapse-button span { font-size: 12px; }
.sidebar.is-collapsed .collapse-button { justify-content: center; padding: 0; }
@media (max-width: 1180px) {
  .sidebar { width: 82px; padding-inline: 12px; }
  .brand-copy, .nav-label, .nav-item span, .nav-item b, .edge-card, .collapse-button span { display: none; }
  .sidebar__brand { justify-content: center; padding-inline: 0; }
  .nav-item { justify-content: center; padding-inline: 0; }
  .nav-item.is-active::after { display: none; }
  .collapse-button { justify-content: center; padding: 0; }
}
@media (max-width: 760px) {
  .sidebar { top: auto; right: 0; bottom: 0; width: 100%; height: 66px; flex-direction: row; padding: 8px 10px; border-top: 1px solid var(--stroke); border-right: 0; background: rgba(8, 18, 32, 0.92); }
  .sidebar__brand, .sidebar__bottom, .nav-label { display: none; }
  .sidebar__nav { display: flex; width: 100%; justify-content: space-around; gap: 4px; }
  .nav-item { width: 44px; min-height: 44px; justify-content: center; padding: 0; }
  .nav-item:nth-child(n+6) { display: none; }
  .app-content, .app-content.is-collapsed { padding-bottom: 70px; }
}
</style>

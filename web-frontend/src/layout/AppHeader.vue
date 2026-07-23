<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Bell, ChevronDown, CircleHelp, Moon, Sun } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import { useAppStore } from '@/stores/app'
import { useDashboardStore } from '@/stores/dashboard'

const appStore = useAppStore()
const dashboardStore = useDashboardStore()
const now = ref(new Date())
let timer = 0

const timeText = computed(() =>
  new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }).format(now.value),
)

onMounted(() => { timer = window.setInterval(() => { now.value = new Date() }, 1000) })
onUnmounted(() => window.clearInterval(timer))
</script>

<template>
  <header class="topbar">
    <div class="topbar__context">
      <span class="realtime-dot" />
      <span class="context-title">AI 智能冰箱控制中心</span>
      <span class="context-divider" />
      <span class="context-time">{{ timeText }}</span>
    </div>

    <div class="topbar__status">
      <div class="header-status"><StatusDot state="online" label="设备在线" /></div>
      <div class="header-status"><StatusDot :state="dashboardStore.socketConnected ? 'online' : 'warning'" :label="dashboardStore.socketConnected ? 'WebSocket 实时' : '重连中'" /></div>
      <div class="header-status header-status--board"><span class="board-led" />LoongArch 2K2000-i</div>
    </div>

    <div class="topbar__actions">
      <button class="icon-button ripple-target" title="帮助中心"><CircleHelp :size="18" /></button>
      <button class="icon-button notification-button ripple-target" title="消息通知"><Bell :size="18" /><i /></button>
      <button class="icon-button ripple-target" title="切换主题" @click="appStore.toggleTheme">
        <Sun v-if="appStore.isDark" :size="18" />
        <Moon v-else :size="18" />
      </button>
      <button class="profile-button ripple-target">
        <span class="avatar">管</span>
        <span class="profile-copy"><strong>管理员</strong><small>Super Admin</small></span>
        <ChevronDown :size="15" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.topbar { position: sticky; top: 0; z-index: 15; display: flex; height: var(--header-height); align-items: center; justify-content: space-between; gap: 18px; padding: 0 28px; border-bottom: 1px solid var(--stroke); background: rgba(7, 17, 31, 0.62); backdrop-filter: blur(22px); }
:root[data-theme='light'] .topbar { background: rgba(246, 249, 252, 0.72); }
.topbar__context, .topbar__status, .topbar__actions { display: flex; align-items: center; }
.topbar__context { min-width: 240px; gap: 9px; }
.context-title { color: var(--text-1); font-size: 14px; font-weight: 650; white-space: nowrap; }
.context-divider { width: 1px; height: 16px; margin: 0 3px; background: var(--stroke-strong); }
.context-time { color: var(--text-3); font-size: 11px; white-space: nowrap; }
.topbar__status { gap: 17px; }
.header-status { color: var(--text-2); font-size: 11px; }
.header-status--board { display: flex; align-items: center; gap: 7px; }
.board-led { width: 6px; height: 6px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 9px var(--cyan); }
.topbar__actions { gap: 8px; }
.icon-button { position: relative; display: grid; width: 36px; height: 36px; place-items: center; border: 1px solid transparent; border-radius: 10px; color: var(--text-2); background: transparent; }
.icon-button:hover { border-color: var(--stroke); color: var(--text-1); background: var(--surface-soft); }
.notification-button i { position: absolute; top: 7px; right: 7px; width: 5px; height: 5px; border-radius: 50%; background: var(--red); box-shadow: 0 0 7px rgba(239, 68, 68, 0.65); }
.profile-button { display: flex; align-items: center; gap: 9px; margin-left: 5px; padding: 3px 7px 3px 4px; border: 1px solid var(--stroke); border-radius: 11px; color: var(--text-2); background: var(--surface-soft); }
.avatar { display: grid; width: 29px; height: 29px; place-items: center; border-radius: 9px; color: white; font-size: 12px; font-weight: 700; background: linear-gradient(145deg, #4f8cff, #14b8a6); }
.profile-copy { display: grid; min-width: 66px; text-align: left; }
.profile-copy strong { color: var(--text-1); font-size: 11px; }
.profile-copy small { margin-top: 2px; color: var(--text-3); font-size: 9px; }
@media (max-width: 1100px) { .topbar__status { display: none; } }
@media (max-width: 760px) {
  .topbar { height: 64px; padding: 0 14px; }
  .context-time, .context-divider, .profile-copy, .profile-button > svg { display: none; }
  .topbar__context { min-width: 0; }
  .topbar__actions { margin-left: auto; }
}
</style>

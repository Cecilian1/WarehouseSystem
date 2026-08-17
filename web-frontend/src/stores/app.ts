import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { ThemeMode } from '@/types'
import { applyDomTheme, persistTheme, readStoredTheme } from '@/utils/theme'

export const useAppStore = defineStore('app', () => {
  const theme = ref<ThemeMode>(readStoredTheme())
  const sidebarCollapsed = ref(localStorage.getItem('xin-sidebar-collapsed') === 'true')
  const notificationCount = ref(3)

  const isDark = computed(() => theme.value === 'dark')

  const applyTheme = (next: ThemeMode) => {
    theme.value = next
    applyDomTheme(next)
    persistTheme(next)
  }

  const toggleTheme = () => applyTheme(isDark.value ? 'light' : 'dark')

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('xin-sidebar-collapsed', String(sidebarCollapsed.value))
  }

  const init = () => applyTheme(theme.value)

  return {
    theme,
    isDark,
    sidebarCollapsed,
    notificationCount,
    applyTheme,
    toggleTheme,
    toggleSidebar,
    init,
  }
})

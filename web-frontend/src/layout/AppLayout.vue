<script setup lang="ts">
import { computed } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const contentClass = computed(() => ({ 'is-collapsed': appStore.sidebarCollapsed }))
</script>

<template>
  <div class="app-shell">
    <AppSidebar />
    <div class="app-content" :class="contentClass">
      <AppHeader />
      <main class="page-content">
        <slot />
      </main>
    </div>
  </div>
</template>

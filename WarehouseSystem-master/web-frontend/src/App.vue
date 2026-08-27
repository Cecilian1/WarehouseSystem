<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { RouterView } from 'vue-router'
import AppLayout from '@/layout/AppLayout.vue'
import { useDashboardStore } from '@/stores/dashboard'

const dashboardStore = useDashboardStore()

onMounted(async () => {
  await dashboardStore.fetchOverview()
  dashboardStore.connectRealtime()
})

onUnmounted(() => dashboardStore.disconnectRealtime())
</script>

<template>
  <AppLayout>
    <RouterView v-slot="{ Component }">
      <Transition name="page-fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </AppLayout>
</template>

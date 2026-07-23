<script setup lang="ts">
import type { DeviceState } from '@/types'
defineProps<{ state: DeviceState; label?: string }>()
</script>

<template>
  <span :class="['status-dot', `status-dot--${state}`]">
    <i />
    <span v-if="label">{{ label }}</span>
  </span>
</template>

<style scoped>
.status-dot { display: inline-flex; align-items: center; gap: 7px; color: var(--text-2); font-size: 12px; }
.status-dot i { width: 7px; height: 7px; border-radius: 50%; background: var(--text-3); }
.status-dot--online i { background: var(--green); box-shadow: 0 0 9px rgba(34, 197, 94, 0.78); }
.status-dot--warning i { background: var(--orange); box-shadow: 0 0 9px rgba(245, 158, 11, 0.7); }
.status-dot--offline i { background: var(--red); box-shadow: 0 0 9px rgba(239, 68, 68, 0.7); }
</style>

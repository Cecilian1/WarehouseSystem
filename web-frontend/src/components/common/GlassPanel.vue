<script setup lang="ts">
withDefaults(defineProps<{
  strong?: boolean
  hover?: boolean
  padding?: 'none' | 'small' | 'medium'
}>(), {
  strong: false,
  hover: false,
  padding: 'medium',
})
</script>

<template>
  <section
    class="glass-panel"
    :class="[
      strong && 'glass-panel--strong',
      hover && 'panel-hover',
      `glass-panel--${padding}`,
    ]"
  >
    <slot />
  </section>
</template>

<style scoped>
.glass-panel--none { padding: 0; }
.glass-panel--small { padding: 14px; }
.glass-panel--medium { padding: 18px; }
</style>

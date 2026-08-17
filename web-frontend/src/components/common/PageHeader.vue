<script setup lang="ts">
defineProps<{
  eyebrow?: string
  title: string
}>()
</script>

<template>
  <header class="page-header">
    <div>
      <div class="page-header__heading">
        <h1>{{ title }}</h1>
        <div v-if="eyebrow" class="page-eyebrow">{{ eyebrow }}</div>
      </div>
    </div>
    <div class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}
.page-header__heading {
  display: flex;
  align-items: center;
  gap: 14px;
}
.page-eyebrow {
  color: var(--cyan);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  white-space: nowrap;
}
h1 {
  margin: 0;
  color: var(--text-1);
  font-size: clamp(24px, 2.1vw, 34px);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.page-header__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
@media (max-width: 640px) {
  .page-header { align-items: flex-start; flex-direction: column; }
  .page-header__heading { flex-wrap: wrap; gap: 6px 12px; }
  .page-header__actions { width: 100%; flex-wrap: wrap; }
}
</style>

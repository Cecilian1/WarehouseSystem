<script setup lang="ts">
defineProps<{
  eyebrow?: string
  title: string
  description?: string
}>()
</script>

<template>
  <header class="page-header">
    <div>
      <div v-if="eyebrow" class="page-eyebrow">{{ eyebrow }}</div>
      <h1>{{ title }}</h1>
      <p v-if="description">{{ description }}</p>
    </div>
    <div class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}
.page-eyebrow {
  margin-bottom: 8px;
  color: var(--cyan);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
h1 {
  margin: 0;
  color: var(--text-1);
  font-size: clamp(24px, 2.1vw, 34px);
  font-weight: 700;
  letter-spacing: -0.02em;
}
p {
  margin: 8px 0 0;
  color: var(--text-2);
  font-size: 13px;
}
.page-header__actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
@media (max-width: 640px) {
  .page-header { align-items: flex-start; flex-direction: column; }
  .page-header__actions { width: 100%; flex-wrap: wrap; }
}
</style>

<script setup lang="ts">
import { Cpu, Database, MemoryStick, RadioTower, ScanEye, Video, Wifi } from 'lucide-vue-next'
import type { StatusItem } from '@/types'

defineProps<{ items: StatusItem[] }>()

const icons = {
  board: Cpu,
  cpu: Cpu,
  memory: MemoryStick,
  sqlite: Database,
  model: ScanEye,
  camera: Video,
  ws: Wifi,
}
</script>

<template>
  <section class="status-strip glass-panel">
    <div class="status-strip__title">
      <RadioTower :size="17" />
      <div>
        <strong>系统运行状态</strong>
        <span>EDGE ORCHESTRATION</span>
      </div>
    </div>
    <div class="status-strip__items">
      <div v-for="item in items" :key="item.id" class="runtime-item">
        <div :class="['runtime-icon', `is-${item.state}`]">
          <component :is="icons[item.id as keyof typeof icons] || Cpu" :size="15" />
        </div>
        <div class="runtime-copy">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
        <i :class="`is-${item.state}`" />
        <div class="runtime-tooltip">{{ item.detail }}</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.status-strip { display: flex; min-height: 68px; align-items: center; gap: 22px; padding: 10px 15px; }
.status-strip__title { display: flex; min-width: 174px; align-items: center; gap: 10px; padding: 0 12px; color: var(--cyan); }
.status-strip__title strong { display: block; color: var(--text-1); font-size: 12px; }
.status-strip__title span { display: block; margin-top: 4px; color: var(--text-3); font-size: 8px; letter-spacing: 0.13em; }
.status-strip__items { display: grid; flex: 1; grid-template-columns: repeat(7, minmax(118px, 1fr)); gap: 7px; }
.runtime-item { position: relative; display: flex; min-width: 0; align-items: center; gap: 8px; padding: 8px 9px; border: 1px solid transparent; border-radius: 12px; background: rgba(255, 255, 255, 0.032); transition: border-color 0.2s ease, background 0.2s ease; }
.runtime-item:hover { border-color: var(--stroke); background: rgba(255, 255, 255, 0.06); }
.runtime-icon { display: grid; width: 28px; height: 28px; flex: 0 0 auto; place-items: center; border-radius: 9px; color: var(--text-2); background: var(--surface-soft); }
.runtime-icon.is-online { color: #75efa1; background: rgba(34, 197, 94, 0.11); }
.runtime-copy { min-width: 0; }
.runtime-copy span, .runtime-copy strong { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.runtime-copy span { color: var(--text-3); font-size: 9px; }
.runtime-copy strong { margin-top: 3px; color: var(--text-1); font-size: 11px; }
.runtime-item > i { width: 5px; height: 5px; margin-left: auto; flex: 0 0 auto; border-radius: 50%; }
.runtime-item > i.is-online { background: var(--green); box-shadow: 0 0 7px var(--green); }
.runtime-item > i.is-warning { background: var(--orange); box-shadow: 0 0 7px var(--orange); }
.runtime-item > i.is-offline { background: var(--red); box-shadow: 0 0 7px var(--red); }
.runtime-tooltip { position: absolute; bottom: -29px; left: 8px; z-index: 20; display: none; padding: 5px 8px; border: 1px solid var(--stroke); border-radius: 7px; color: var(--text-2); font-size: 9px; background: var(--surface-strong); box-shadow: var(--shadow-soft); white-space: nowrap; }
.runtime-item:hover .runtime-tooltip { display: block; }
@media (max-width: 1500px) {
  .status-strip__items { grid-template-columns: repeat(4, 1fr); }
  .status-strip__items .runtime-item:nth-child(n+5) { display: none; }
}
@media (max-width: 900px) {
  .status-strip__title { display: none; }
  .status-strip__items { grid-template-columns: repeat(3, 1fr); }
  .status-strip__items .runtime-item:nth-child(n+4) { display: none; }
}
</style>

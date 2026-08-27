<script setup lang="ts">
import { Cpu, Database, HardDrive, MemoryStick, RadioTower, ScanEye, Thermometer, Video, Wifi } from 'lucide-vue-next'
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
  sensor: Thermometer,
  storage: HardDrive,
}
</script>

<template>
  <section class="status-strip glass-panel">
    <div class="status-strip__title">
      <RadioTower :size="16" />
      <div>
        <strong>系统运行状态</strong>
        <span>EDGE ORCHESTRATION</span>
      </div>
    </div>
    <div class="status-strip__items">
      <div v-for="item in items" :key="item.id" class="runtime-item">
        <div :class="['runtime-icon', `is-${item.state}`]">
          <component :is="icons[item.id as keyof typeof icons] || Cpu" :size="14" />
        </div>
        <div class="runtime-copy">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
        <i :class="`is-${item.state}`" />
        <div v-if="item.detail" class="runtime-tooltip">{{ item.detail }}</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.status-strip {
  display: flex;
  align-items: center;
  min-width: 0;
  height: 68px;
  gap: 0;
  padding: 8px 10px 8px 12px;
}
.status-strip__title {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
  height: 100%;
  padding: 0 14px 0 4px;
  margin-right: 8px;
  border-right: 1px solid var(--stroke);
  color: var(--cyan);
}
.status-strip__title strong {
  display: block;
  color: var(--text-1);
  font-size: 13px;
  font-weight: 650;
  line-height: 1.2;
  white-space: nowrap;
}
.status-strip__title span {
  display: block;
  margin-top: 3px;
  color: var(--text-3);
  font-size: 10px;
  letter-spacing: 0.08em;
  line-height: 1.2;
  white-space: nowrap;
}
.status-strip__items {
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
  align-items: stretch;
  gap: 6px;
  height: 100%;
}
.runtime-item {
  position: relative;
  display: flex;
  flex: 1 1 0;
  min-width: 0;
  max-width: 220px;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.032);
  transition: border-color 0.2s ease, background 0.2s ease;
}
.runtime-item:hover {
  border-color: var(--stroke);
  background: rgba(255, 255, 255, 0.06);
}
.runtime-icon {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 8px;
  color: var(--text-2);
  background: var(--surface-soft);
}
.runtime-icon.is-online { color: #75efa1; background: rgba(34, 197, 94, 0.11); }
.runtime-icon.is-warning { color: #fbbf24; background: rgba(245, 158, 11, 0.12); }
.runtime-icon.is-offline { color: #f87171; background: rgba(239, 68, 68, 0.12); }
.runtime-copy {
  flex: 1 1 auto;
  min-width: 0;
}
.runtime-copy span,
.runtime-copy strong {
  display: block;
  overflow: hidden;
  line-height: 1.25;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.runtime-copy span { color: var(--text-3); font-size: 11px; }
.runtime-copy strong { margin-top: 2px; color: var(--text-1); font-size: 12px; font-weight: 650; }
.runtime-item > i {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 50%;
}
.runtime-item > i.is-online { background: var(--green); box-shadow: 0 0 7px var(--green); }
.runtime-item > i.is-warning { background: var(--orange); box-shadow: 0 0 7px var(--orange); }
.runtime-item > i.is-offline { background: var(--red); box-shadow: 0 0 7px var(--red); }
.runtime-tooltip {
  position: absolute;
  left: 10px;
  bottom: calc(100% + 6px);
  z-index: 20;
  display: none;
  padding: 5px 8px;
  border: 1px solid var(--stroke);
  border-radius: 7px;
  color: var(--text-2);
  font-size: 11px;
  line-height: 1.3;
  background: var(--surface-strong);
  box-shadow: var(--shadow-soft);
  white-space: nowrap;
}
.runtime-item:hover .runtime-tooltip { display: block; }
@media (max-width: 1100px) {
  .runtime-item { max-width: none; }
}
@media (max-width: 760px) {
  .status-strip {
    height: auto;
    flex-wrap: wrap;
    padding: 10px;
    overflow: visible;
  }
  .status-strip__title {
    width: 100%;
    height: auto;
    padding: 2px 4px 8px;
    margin-right: 0;
    border-right: 0;
    border-bottom: 1px solid var(--stroke);
  }
  .status-strip__items {
    flex: 1 1 100%;
    flex-wrap: wrap;
    height: auto;
  }
  .runtime-item {
    flex: 1 1 calc(50% - 6px);
    max-width: none;
    min-height: 44px;
  }
}
</style>

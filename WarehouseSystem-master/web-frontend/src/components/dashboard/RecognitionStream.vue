<script setup lang="ts">
import { ArrowDownToLine, ArrowUpFromLine, ChevronRight, ScanSearch } from 'lucide-vue-next'
import type { RecognitionRecord } from '@/types'
import { freshnessLabel } from '@/utils/format'

defineProps<{ records: RecognitionRecord[] }>()
</script>

<template>
  <section class="recognition-stream glass-panel">
    <header class="stream-header">
      <div>
        <h2 class="section-title">最近识别流</h2>
        <p class="section-subtitle">视觉变化触发 · 自动写入 SQLite</p>
      </div>
      <RouterLink to="/recognition" class="all-link">全部记录 <ChevronRight :size="13" /></RouterLink>
    </header>
    <div class="stream-list">
      <RouterLink v-for="record in records.slice(0, 5)" :key="record.id" to="/recognition" class="stream-item">
        <div class="stream-time">{{ record.time }}</div>
        <div class="stream-thumb"><ScanSearch :size="18" /><span /></div>
        <div class="stream-main">
          <strong>{{ record.name }}</strong>
          <span>{{ record.category }} · {{ record.latency }} ms</span>
        </div>
        <div :class="['stream-action', record.action === 'IN' ? 'is-in' : 'is-out']">
          <ArrowDownToLine v-if="record.action === 'IN'" :size="13" />
          <ArrowUpFromLine v-else :size="13" />
          {{ record.action === 'IN' ? '入库' : '出库' }} {{ record.quantity }}
        </div>
        <div class="stream-confidence">
          <span>置信度</span>
          <strong>{{ (record.confidence * 100).toFixed(1) }}%</strong>
        </div>
        <span :class="['freshness-badge', `is-${record.freshness}`]">{{ freshnessLabel[record.freshness] }}</span>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.recognition-stream { min-width: 0; padding: 15px 17px; }
.stream-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.all-link { display: flex; align-items: center; gap: 3px; color: var(--cyan); font-size: 10px; }
.stream-list { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; margin-top: 13px; }
.stream-item { display: grid; grid-template-columns: 36px 1fr auto; grid-template-areas: "thumb main badge" "thumb action confidence"; align-items: center; gap: 3px 8px; min-width: 0; padding: 9px; border: 1px solid var(--stroke); border-radius: 12px; background: var(--surface-soft); transition: transform .2s ease, border-color .2s ease, background .2s ease; }
.stream-item:hover { border-color: rgba(56,189,248,.3); background: rgba(56,189,248,.06); transform: translateY(-2px); }
.stream-time { display: none; }
.stream-thumb { position: relative; display: grid; grid-area: thumb; width: 36px; height: 42px; place-items: center; overflow: hidden; border-radius: 9px; color: rgba(184,235,255,.85); background: linear-gradient(145deg, rgba(56,189,248,.2), rgba(34,197,94,.12)); }
.stream-thumb span { position: absolute; inset: 5px; border: 1px solid rgba(143,233,255,.25); border-radius: 5px; }
.stream-main { grid-area: main; min-width: 0; }
.stream-main strong, .stream-main span { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.stream-main strong { color: var(--text-1); font-size: 10px; }
.stream-main span { margin-top: 3px; color: var(--text-3); font-size: 8px; }
.stream-action { display: flex; grid-area: action; align-items: center; gap: 3px; font-size: 8px; }
.stream-action.is-in { color: #78e9a1; } .stream-action.is-out { color: #78c9ff; }
.stream-confidence { display: none; grid-area: confidence; text-align: right; }
.stream-confidence span { color: var(--text-3); font-size: 8px; }
.stream-confidence strong { margin-left: 3px; color: var(--text-2); font-size: 8px; }
.freshness-badge { grid-area: badge; padding: 3px 6px; border-radius: 99px; font-size: 8px; white-space: nowrap; }
.freshness-badge.is-fresh { color: #87efaa; background: rgba(34,197,94,.1); }
.freshness-badge.is-warning { color: #ffd477; background: rgba(245,158,11,.1); }
.freshness-badge.is-spoiled { color: #ff9393; background: rgba(239,68,68,.1); }
@media (max-width: 1260px) { .stream-list { grid-template-columns: repeat(3, 1fr); } .stream-item:nth-child(n+4) { display: none; } }
@media (max-width: 760px) { .stream-list { grid-template-columns: 1fr; } .stream-item:nth-child(n+4) { display: grid; } }
</style>

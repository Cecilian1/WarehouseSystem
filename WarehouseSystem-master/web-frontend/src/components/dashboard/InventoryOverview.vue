<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUpRight, CircleGauge, PackageCheck } from 'lucide-vue-next'
import BaseChart from '@/components/common/BaseChart.vue'
import type { CategoryStat } from '@/types'
import { useAppStore } from '@/stores/app'

const props = defineProps<{ categories: CategoryStat[]; freshness: CategoryStat[] }>()
const appStore = useAppStore()

const total = computed(() => props.categories.reduce((sum, item) => sum + item.value, 0))
const donutOption = computed(() => ({
  animationDuration: 1000,
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: ['61%', '82%'],
    center: ['50%', '52%'],
    avoidLabelOverlap: false,
    itemStyle: { borderColor: appStore.isDark ? '#102034' : '#f5f8fc', borderWidth: 3, borderRadius: 6 },
    label: { show: false },
    data: props.categories.map((item) => ({ value: item.value, name: item.name, itemStyle: { color: item.color } })),
  }],
  graphic: [
    { type: 'text', left: 'center', top: '40%', style: { text: String(total.value), fill: appStore.isDark ? '#f4f8ff' : '#16263d', fontSize: 25, fontWeight: 700 } },
    { type: 'text', left: 'center', top: '59%', style: { text: '库存总量', fill: appStore.isDark ? '#70829a' : '#7b8ca3', fontSize: 9 } },
  ],
}))
</script>

<template>
  <section class="inventory-overview glass-panel">
    <header class="panel-heading">
      <div>
        <h2 class="section-title">库存态势</h2>
        <p class="section-subtitle">实时分类与新鲜度分布</p>
      </div>
      <RouterLink to="/inventory" class="detail-link">详情 <ArrowUpRight :size="13" /></RouterLink>
    </header>

    <div class="inventory-main">
      <div class="donut-wrap">
        <BaseChart :option="donutOption" height="148px" />
      </div>
      <div class="category-legend">
        <div v-for="item in categories" :key="item.name" class="legend-row">
          <span><i :style="{ background: item.color }" />{{ item.name }}</span>
          <strong>{{ item.value }}<small>件</small></strong>
        </div>
        <div class="turnover">
          <span><CircleGauge :size="13" />本周周转率</span>
          <strong>82.4%</strong>
        </div>
      </div>
    </div>

    <div class="freshness-section">
      <div class="freshness-title">
        <span><PackageCheck :size="14" />新鲜度分布</span>
        <small>MobileNetV3 分类</small>
      </div>
      <div v-for="item in freshness" :key="item.name" class="freshness-row">
        <div><span>{{ item.name }}</span><strong>{{ item.value }} 件</strong></div>
        <div class="freshness-track"><span :style="{ width: `${item.value / total * 100}%`, background: item.color }" /></div>
      </div>
    </div>

    <div class="inventory-foot">
      <div><span>库存健康度</span><strong>92.6</strong></div>
      <div><span>预计可节约</span><strong>12.8%</strong></div>
      <div><span>平均保鲜期</span><strong>8.4 天</strong></div>
    </div>
  </section>
</template>

<style scoped>
.inventory-overview { display: flex; min-height: 0; flex-direction: column; padding: 16px; }
.panel-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.detail-link { display: flex; align-items: center; gap: 4px; color: var(--cyan); font-size: 10px; }
.inventory-main { display: grid; grid-template-columns: 48% 1fr; align-items: center; gap: 7px; margin-top: 3px; }
.category-legend { display: grid; gap: 9px; }
.legend-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.legend-row span { display: flex; align-items: center; gap: 7px; color: var(--text-2); font-size: 10px; }
.legend-row i { width: 7px; height: 7px; border-radius: 3px; }
.legend-row strong { color: var(--text-1); font-size: 13px; }
.legend-row small { margin-left: 2px; color: var(--text-3); font-size: 8px; font-weight: 500; }
.turnover { margin-top: 2px; padding: 9px; border: 1px solid rgba(79,140,255,.13); border-radius: 10px; background: rgba(79,140,255,.06); }
.turnover span { display: flex; align-items: center; gap: 5px; color: var(--text-3); font-size: 9px; }
.turnover strong { display: block; margin-top: 5px; color: #83aeff; font-size: 14px; }
.freshness-section { margin-top: 7px; padding-top: 11px; border-top: 1px solid var(--stroke); }
.freshness-title, .freshness-title span, .freshness-row > div:first-child { display: flex; align-items: center; justify-content: space-between; }
.freshness-title span { justify-content: flex-start; gap: 6px; color: var(--text-1); font-size: 10px; font-weight: 600; }
.freshness-title small { color: var(--text-3); font-size: 8px; }
.freshness-row { margin-top: 9px; }
.freshness-row span, .freshness-row strong { font-size: 9px; }
.freshness-row span { color: var(--text-2); }
.freshness-row strong { color: var(--text-1); }
.freshness-track { height: 5px; margin-top: 5px; overflow: hidden; border-radius: 99px; background: rgba(148,163,184,.1); }
.freshness-track span { display: block; height: 100%; border-radius: inherit; box-shadow: 0 0 10px currentColor; }
.inventory-foot { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: auto; padding-top: 12px; }
.inventory-foot div { padding: 8px 4px; border-radius: 9px; text-align: center; background: var(--surface-soft); }
.inventory-foot span, .inventory-foot strong { display: block; }
.inventory-foot span { color: var(--text-3); font-size: 8px; }
.inventory-foot strong { margin-top: 4px; color: var(--text-1); font-size: 11px; }
</style>

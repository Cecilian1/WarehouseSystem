<script setup lang="ts">
import { computed } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import { useDashboardStore } from '@/stores/dashboard'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import CameraVision from '@/components/dashboard/CameraVision.vue'
import EnvironmentOverview from '@/components/dashboard/EnvironmentOverview.vue'
import InventoryOverview from '@/components/dashboard/InventoryOverview.vue'
import RecognitionStream from '@/components/dashboard/RecognitionStream.vue'
import StockTrend from '@/components/dashboard/StockTrend.vue'
import SystemStatusStrip from '@/components/dashboard/SystemStatusStrip.vue'

const store = useDashboardStore()
const data = computed(() => store.data)
const refreshedAt = computed(() => store.lastUpdated.toLocaleTimeString('zh-CN', { hour12: false }))
</script>

<template>
  <div v-if="data" class="dashboard-page">
    <PageHeader
      eyebrow="EDGE AI CONTROL CENTER"
      title="芯鲜管家"
      description="基于 LoongArch 的端侧 AI 智能果蔬仓储管理系统"
    >
      <template #actions>
        <div class="updated-label"><span class="realtime-dot" />最后刷新 {{ refreshedAt }}</div>
        <el-button :loading="store.loading" @click="store.fetchOverview"><RefreshCw :size="15" />刷新数据</el-button>
      </template>
    </PageHeader>

    <SystemStatusStrip :items="data.statuses" />

    <div class="metric-grid">
      <StatCard v-for="metric in data.metrics" :key="metric.id" :metric="metric" />
    </div>

    <div class="control-grid">
      <EnvironmentOverview :environment="data.environment" />
      <CameraVision :detections="data.detections" :performance="data.performance" />
      <InventoryOverview :categories="data.categories" :freshness="data.freshness" />
    </div>

    <div class="dashboard-bottom">
      <RecognitionStream :records="data.recognitions" />
      <StockTrend :data="data.stockTrend" />
    </div>
  </div>
  <div v-else class="dashboard-loading">
    <div class="loading-orbit"><span /><span /><span /></div>
    <strong>正在连接端侧控制中心</strong>
    <p>加载设备状态、AI 模型与实时数据流...</p>
  </div>
</template>

<style scoped>
.dashboard-page { min-width: 0; }
.dashboard-page :deep(.page-header) { margin-bottom: 14px; }
.dashboard-page :deep(.page-header h1) { font-size: 28px; }
.updated-label { display: flex; align-items: center; margin-right: 5px; color: var(--text-3); font-size: 10px; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 12px; }
.control-grid { display: grid; grid-template-columns: minmax(220px, .68fr) minmax(500px, 1.75fr) minmax(250px, .82fr); gap: 12px; min-height: 430px; margin-top: 12px; }
.dashboard-bottom { display: grid; grid-template-columns: 1.55fr 1fr; gap: 12px; margin-top: 12px; }
.dashboard-loading { display: grid; min-height: calc(100vh - 130px); place-content: center; text-align: center; }
.dashboard-loading strong { margin-top: 18px; color: var(--text-1); font-size: 15px; }
.dashboard-loading p { color: var(--text-3); font-size: 11px; }
.loading-orbit { position: relative; width: 72px; height: 72px; margin: auto; }
.loading-orbit span { position: absolute; inset: 0; border: 1px solid rgba(56,189,248,.28); border-radius: 50%; animation: spin 2.2s linear infinite; }
.loading-orbit span:nth-child(2) { inset: 12px; border-color: rgba(34,197,94,.34); animation-direction: reverse; animation-duration: 1.7s; }
.loading-orbit span:nth-child(3) { inset: 26px; border: 0; background: var(--cyan); box-shadow: 0 0 20px var(--cyan); }
@keyframes spin { to { transform: rotate(360deg); } }
@media (min-width: 1700px) and (min-height: 900px) {
  .control-grid { min-height: 438px; }
}
@media (max-width: 1380px) {
  .control-grid { grid-template-columns: minmax(210px, .7fr) minmax(480px, 1.7fr); }
  .control-grid > :last-child { display: none; }
}
@media (max-width: 1050px) {
  .metric-grid { grid-template-columns: repeat(2, 1fr); }
  .control-grid { grid-template-columns: 1fr; }
  .control-grid > :first-child { order: 2; }
  .dashboard-bottom { grid-template-columns: 1fr; }
}
@media (max-width: 620px) {
  .metric-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
  .metric-grid :deep(.stat-card) { min-height: 112px; padding: 13px; }
  .control-grid { min-height: auto; }
}
</style>

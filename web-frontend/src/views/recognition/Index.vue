<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Expand, Image, Pause, Play, Search, SlidersHorizontal, ZoomIn } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import CameraVision from '@/components/dashboard/CameraVision.vue'
import ProduceVisual from '@/components/common/ProduceVisual.vue'
import { recognitionApi } from '@/api'
import { useDashboardStore } from '@/stores/dashboard'
import type { RecognitionRecord } from '@/types'
import { freshnessLabel, freshnessTone } from '@/utils/format'

const dashboard = useDashboardStore()
const records = ref<RecognitionRecord[]>([])
const selected = ref<RecognitionRecord | null>(null)
const autoRefresh = ref(true)
const searchText = ref('')
const previewVisible = ref(false)

const filtered = computed(() => records.value.filter((item) => !searchText.value || item.name.includes(searchText.value)))

const load = async () => {
  const response = await recognitionApi.getList()
  records.value = response.data
  selected.value ||= records.value[0]
}

const inspect = (record: RecognitionRecord) => {
  selected.value = record
  previewVisible.value = true
}

onMounted(load)
</script>

<template>
  <div v-if="dashboard.data" class="recognition-page">
    <PageHeader eyebrow="AI RECOGNITION" title="AI 识别记录" description="目标检测、新鲜度分类与人工复核">
      <template #actions>
        <el-switch v-model="autoRefresh" inline-prompt active-text="自动刷新" inactive-text="已暂停" />
        <el-button><SlidersHorizontal :size="15" />模型设置</el-button>
      </template>
    </PageHeader>

    <div class="recognition-workspace">
      <CameraVision compact :detections="dashboard.data.detections" :performance="dashboard.data.performance" />
      <GlassPanel class="current-result">
        <div class="result-head">
          <div><h2>识别结果</h2><span>Frame #003018 · 20:29:42</span></div>
          <span class="status-chip is-online">处理完成</span>
        </div>
        <div class="result-score">
          <div class="score-ring"><strong>98.2</strong><span>置信度</span></div>
          <div class="score-copy"><span>识别类别</span><h3>红富士苹果</h3><p>Apple · Fruit · 3 个目标</p></div>
        </div>
        <div class="result-grid">
          <div><span>Freshness</span><strong class="is-fresh">新鲜</strong></div>
          <div><span>新鲜度评分</span><strong>96.1</strong></div>
          <div><span>检测耗时</span><strong>248 ms</strong></div>
          <div><span>分类耗时</span><strong>96 ms</strong></div>
        </div>
        <div class="model-meta">
          <div><span>检测模型</span><strong>YOLOv11n · INT8</strong></div>
          <div><span>分类模型</span><strong>MobileNetV3-Small</strong></div>
        </div>
        <div class="result-actions">
          <el-button><Pause v-if="autoRefresh" :size="14" /><Play v-else :size="14" />{{ autoRefresh ? '暂停识别' : '继续识别' }}</el-button>
          <el-button type="primary"><Expand :size="14" />查看原图</el-button>
        </div>
      </GlassPanel>
    </div>

    <GlassPanel class="history-panel" padding="none">
      <div class="history-toolbar">
        <div><h2>历史识别图片</h2><span>点击记录查看识别详情</span></div>
        <el-input v-model="searchText" placeholder="搜索识别类别" clearable><template #prefix><Search :size="14" /></template></el-input>
      </div>
      <div class="recognition-grid">
        <button v-for="record in filtered" :key="record.id" class="recognition-card ripple-target" @click="inspect(record)">
          <div class="recognition-image">
            <ProduceVisual :name="record.name" :color="record.freshness === 'fresh' ? '#22c55e' : '#f59e0b'" size="large" />
            <span class="zoom-overlay"><ZoomIn :size="18" /></span>
            <el-tag :type="freshnessTone[record.freshness]" effect="dark">{{ freshnessLabel[record.freshness] }}</el-tag>
          </div>
          <div class="recognition-card__body">
            <div><strong>{{ record.name }}</strong><span>{{ record.time }}</span></div>
            <b>{{ (record.confidence * 100).toFixed(1) }}%</b>
          </div>
        </button>
      </div>
    </GlassPanel>

    <el-dialog v-model="previewVisible" title="识别详情" width="720px">
      <div v-if="selected" class="recognition-detail">
        <ProduceVisual :name="selected.name" :color="selected.freshness === 'fresh' ? '#22c55e' : '#f59e0b'" size="large" />
        <div class="detail-copy">
          <span class="status-chip is-online"><Image :size="12" /> Frame #{{ selected.id }}</span>
          <h2>{{ selected.name }}</h2>
          <p>{{ selected.category }} · {{ selected.action === 'IN' ? '自动入库' : '自动出库' }} {{ selected.quantity }} 件</p>
          <dl><div><dt>识别置信度</dt><dd>{{ (selected.confidence * 100).toFixed(1) }}%</dd></div><div><dt>新鲜度评分</dt><dd>{{ (selected.freshnessScore * 100).toFixed(1) }}</dd></div><div><dt>推理延迟</dt><dd>{{ selected.latency }} ms</dd></div><div><dt>记录时间</dt><dd>{{ selected.time }}</dd></div></dl>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.recognition-workspace { display: grid; grid-template-columns: minmax(560px, 1.65fr) minmax(300px, .72fr); gap: 14px; }
.current-result { display: flex; flex-direction: column; }
.result-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.result-head h2, .history-toolbar h2 { margin: 0; color: var(--text-1); font-size: 14px; }.result-head > div > span, .history-toolbar > div > span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }
.result-score { display: flex; align-items: center; gap: 17px; margin-top: 22px; }
.score-ring { display: grid; width: 96px; height: 96px; flex: 0 0 auto; place-content: center; border: 8px solid rgba(34,197,94,.16); border-top-color: var(--green); border-right-color: #4ade80; border-radius: 50%; text-align: center; box-shadow: 0 0 25px rgba(34,197,94,.11); }
.score-ring strong { color: #8df1ae; font-size: 21px; }.score-ring span { margin-top: 3px; color: var(--text-3); font-size: 8px; }
.score-copy span { color: var(--text-3); font-size: 9px; }.score-copy h3 { margin: 5px 0 0; color: var(--text-1); font-size: 18px; }.score-copy p { margin: 6px 0 0; color: var(--text-2); font-size: 10px; }
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 21px; }
.result-grid div, .model-meta div { padding: 11px; border: 1px solid var(--stroke); border-radius: 11px; background: var(--surface-soft); }
.result-grid span, .result-grid strong, .model-meta span, .model-meta strong { display: block; }.result-grid span, .model-meta span { color: var(--text-3); font-size: 8px; }.result-grid strong, .model-meta strong { margin-top: 5px; color: var(--text-1); font-size: 11px; }.result-grid strong.is-fresh { color: #82eea7; }
.model-meta { display: grid; gap: 7px; margin-top: 8px; }.model-meta div { display: flex; align-items: center; justify-content: space-between; }
.model-meta strong { margin-top: 0; }
.result-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: auto; padding-top: 16px; }
.history-panel { margin-top: 14px; overflow: hidden; }
.history-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 15px 17px; border-bottom: 1px solid var(--stroke); }
.history-toolbar .el-input { width: 240px; }
.recognition-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; padding: 14px; }
.recognition-card { padding: 0; overflow: hidden; border: 1px solid var(--stroke); border-radius: 13px; color: inherit; text-align: left; background: var(--surface-soft); transition: transform .2s ease, border-color .2s ease; }
.recognition-card:hover { border-color: rgba(56,189,248,.35); transform: translateY(-3px); }
.recognition-image { position: relative; display: grid; height: 145px; place-items: center; overflow: hidden; }
.recognition-image :deep(.produce-visual) { width: 100%; height: 100%; border: 0; border-radius: 0; }
.recognition-image .el-tag { position: absolute; top: 8px; left: 8px; }
.zoom-overlay { position: absolute; inset: 0; display: grid; place-items: center; color: white; background: rgba(5,14,24,.35); opacity: 0; transition: opacity .2s ease; }.recognition-card:hover .zoom-overlay { opacity: 1; }
.recognition-card__body { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 11px; }
.recognition-card__body strong, .recognition-card__body span { display: block; }.recognition-card__body strong { color: var(--text-1); font-size: 10px; }.recognition-card__body span { margin-top: 4px; color: var(--text-3); font-size: 8px; }.recognition-card__body b { color: var(--cyan); font-size: 10px; }
.recognition-detail { display: grid; grid-template-columns: 220px 1fr; gap: 24px; align-items: center; }
.detail-copy h2 { margin: 16px 0 0; color: var(--text-1); }.detail-copy p { color: var(--text-3); font-size: 11px; }
.detail-copy dl { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 18px 0 0; }.detail-copy dl div { padding: 11px; border-radius: 10px; background: var(--surface-soft); }.detail-copy dt { color: var(--text-3); font-size: 8px; }.detail-copy dd { margin: 5px 0 0; color: var(--text-1); font-size: 11px; font-weight: 600; }
@media (max-width: 1160px) { .recognition-workspace { grid-template-columns: 1fr; } .recognition-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 680px) { .recognition-grid { grid-template-columns: 1fr 1fr; } .recognition-detail { grid-template-columns: 1fr; justify-items: center; } .history-toolbar { align-items: stretch; flex-direction: column; } .history-toolbar .el-input { width: 100%; } }
</style>

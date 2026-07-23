<script setup lang="ts">
import { computed, ref } from 'vue'
import { Camera, CircleGauge, Maximize2, RefreshCw, ScanLine, Settings2, Video } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import CameraVision from '@/components/dashboard/CameraVision.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useAppStore } from '@/stores/app'

const store = useDashboardStore()
const appStore = useAppStore()
const autoRefresh = ref(true)
const data = computed(() => store.data)
const latencyOption = computed(() => ({
  animationDuration: 900,
  grid: { top: 15, right: 7, bottom: 20, left: 28 },
  xAxis: { type: 'category', data: Array.from({ length: 12 }, (_, i) => `${i * 5}s`), axisLine: { lineStyle: { color: 'rgba(148,163,184,.2)' } }, axisTick: { show: false }, axisLabel: { color: '#70829a', fontSize: 8 } },
  yAxis: { type: 'value', min: 300, max: 500, splitLine: { lineStyle: { color: 'rgba(148,163,184,.12)', type: 'dashed' } }, axisLabel: { color: '#70829a', fontSize: 8 } },
  series: [{ type: 'line', smooth: true, showSymbol: false, data: [402, 386, 398, 421, 374, 390, 405, 382, 388, 396, 379, 386], lineStyle: { color: '#38bdf8', width: 2 }, areaStyle: { color: 'rgba(56,189,248,.1)' } }],
}))
</script>

<template>
  <div v-if="data" class="monitor-page">
    <PageHeader eyebrow="LIVE VISION PIPELINE" title="实时监控" description="摄像头采集、目标检测与新鲜度推理全链路观测">
      <template #actions>
        <el-switch v-model="autoRefresh" inline-prompt active-text="自动" inactive-text="手动" />
        <el-button><Settings2 :size="15" />识别参数</el-button>
        <el-button type="primary"><Maximize2 :size="15" />全屏监控</el-button>
      </template>
    </PageHeader>

    <div class="monitor-grid">
      <CameraVision compact :detections="data.detections" :performance="data.performance" />
      <aside class="monitor-side">
        <GlassPanel class="pipeline-panel">
          <div class="panel-title"><div><h2>AI Pipeline</h2><span>端侧实时推理链路</span></div><ScanLine :size="18" /></div>
          <div class="pipeline-steps">
            <div class="pipeline-step is-done"><i>01</i><div><strong>图像采集</strong><span>UVC Camera · 640×480</span></div><b>12 FPS</b></div>
            <div class="pipeline-line" />
            <div class="pipeline-step is-active"><i>02</i><div><strong>YOLOv11 检测</strong><span>3 个目标 · INT8</span></div><b>248 ms</b></div>
            <div class="pipeline-line" />
            <div class="pipeline-step is-active"><i>03</i><div><strong>MobileNetV3</strong><span>新鲜度二阶段分类</span></div><b>96 ms</b></div>
            <div class="pipeline-line" />
            <div class="pipeline-step is-done"><i>04</i><div><strong>业务判定</strong><span>库存差分与 SQLite 写入</span></div><b>42 ms</b></div>
          </div>
        </GlassPanel>

        <GlassPanel class="result-panel">
          <div class="panel-title"><div><h2>本帧识别结果</h2><span>Frame #003018</span></div><RefreshCw :size="16" /></div>
          <div v-for="box in data.detections" :key="box.id" class="detection-row">
            <div class="detect-index"><Camera :size="14" /></div>
            <div><strong>{{ box.label }}</strong><span>{{ box.freshness === 'fresh' ? '新鲜' : '轻度不新鲜' }} · {{ (box.freshnessScore * 100).toFixed(1) }}</span></div>
            <b>{{ (box.confidence * 100).toFixed(1) }}%</b>
          </div>
        </GlassPanel>
      </aside>
    </div>

    <div class="monitor-bottom">
      <GlassPanel class="latency-panel">
        <div class="panel-title"><div><h2>端侧推理延迟</h2><span>最近 60 秒</span></div><CircleGauge :size="17" /></div>
        <BaseChart :option="latencyOption" height="150px" />
      </GlassPanel>
      <GlassPanel class="camera-info">
        <div class="panel-title"><div><h2>视频源信息</h2><span>设备与采集参数</span></div><Video :size="17" /></div>
        <div class="info-grid">
          <div><span>设备节点</span><strong>/dev/video0</strong></div>
          <div><span>视频格式</span><strong>MJPEG</strong></div>
          <div><span>分辨率</span><strong>640 × 480</strong></div>
          <div><span>补光模式</span><strong>GPIO 自动</strong></div>
          <div><span>差分阈值</span><strong>5.0%</strong></div>
          <div><span>缓存帧数</span><strong>24 Frames</strong></div>
        </div>
      </GlassPanel>
    </div>
  </div>
</template>

<style scoped>
.monitor-grid { display: grid; grid-template-columns: minmax(560px, 1.55fr) minmax(300px, .75fr); gap: 14px; }
.monitor-side { display: grid; grid-template-rows: 1fr 1fr; gap: 14px; }
.pipeline-panel, .result-panel, .latency-panel, .camera-info { min-width: 0; }
.panel-title { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); }
.panel-title h2 { margin: 0; color: var(--text-1); font-size: 13px; }
.panel-title span { display: block; margin-top: 4px; color: var(--text-3); font-size: 9px; }
.pipeline-steps { margin-top: 16px; }
.pipeline-step { display: grid; grid-template-columns: 28px 1fr auto; align-items: center; gap: 9px; }
.pipeline-step i { display: grid; width: 28px; height: 28px; place-items: center; border: 1px solid var(--stroke); border-radius: 9px; color: var(--text-3); font-size: 8px; font-style: normal; }
.pipeline-step.is-active i { border-color: rgba(56,189,248,.4); color: var(--cyan); background: rgba(56,189,248,.1); box-shadow: 0 0 14px rgba(56,189,248,.12); }
.pipeline-step.is-done i { border-color: rgba(34,197,94,.3); color: var(--green); background: rgba(34,197,94,.08); }
.pipeline-step strong, .pipeline-step span { display: block; }
.pipeline-step strong { color: var(--text-1); font-size: 10px; }.pipeline-step span { margin-top: 3px; color: var(--text-3); font-size: 8px; }.pipeline-step b { color: var(--text-2); font-size: 9px; }
.pipeline-line { width: 1px; height: 14px; margin: 3px 0 3px 13px; background: linear-gradient(var(--stroke-strong), rgba(56,189,248,.25)); }
.detection-row { display: grid; grid-template-columns: 33px 1fr auto; align-items: center; gap: 9px; margin-top: 10px; padding: 10px; border: 1px solid var(--stroke); border-radius: 11px; background: var(--surface-soft); }
.detect-index { display: grid; width: 33px; height: 33px; place-items: center; border-radius: 9px; color: var(--green); background: rgba(34,197,94,.1); }
.detection-row strong, .detection-row span { display: block; }.detection-row strong { color: var(--text-1); font-size: 10px; }.detection-row span { margin-top: 4px; color: var(--text-3); font-size: 8px; }.detection-row b { color: #86efac; font-size: 11px; }
.monitor-bottom { display: grid; grid-template-columns: 1.4fr 1fr; gap: 14px; margin-top: 14px; }
.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 15px; }
.info-grid div { padding: 10px; border-radius: 10px; background: var(--surface-soft); }
.info-grid span, .info-grid strong { display: block; }.info-grid span { color: var(--text-3); font-size: 8px; }.info-grid strong { margin-top: 5px; color: var(--text-1); font-size: 10px; }
@media (max-width: 1100px) { .monitor-grid { grid-template-columns: 1fr; } .monitor-side { grid-template-columns: 1fr 1fr; grid-template-rows: auto; } }
@media (max-width: 760px) { .monitor-side, .monitor-bottom { grid-template-columns: 1fr; } .info-grid { grid-template-columns: repeat(2, 1fr); } }
</style>

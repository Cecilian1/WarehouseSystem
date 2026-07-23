<script setup lang="ts">
import { computed, ref } from 'vue'
import { Camera, Expand, Focus, Lightbulb, Pause, Play, ScanLine, Volume2 } from 'lucide-vue-next'
import type { DetectionBox } from '@/types'
import { freshnessLabel } from '@/utils/format'

const props = defineProps<{
  detections: DetectionBox[]
  performance: { fps: number; latency: number; model: string; power: number }
  compact?: boolean
}>()

const playing = ref(true)
const selectedId = ref(props.detections[0]?.id)
const selected = computed(() => props.detections.find((item) => item.id === selectedId.value) || props.detections[0])

const produce = [
  { class: 'apple apple-1' }, { class: 'apple apple-2' }, { class: 'apple apple-3' },
  { class: 'broccoli broccoli-1' }, { class: 'broccoli broccoli-2' },
  { class: 'tomato tomato-1' }, { class: 'tomato tomato-2' },
  { class: 'cucumber cucumber-1' }, { class: 'carrot carrot-1' },
]
</script>

<template>
  <section class="vision-panel glass-panel glass-panel--strong" :class="{ 'is-compact': compact }">
    <header class="vision-header">
      <div>
        <div class="vision-title"><span class="realtime-dot" />实时 AI 视觉识别</div>
        <div class="vision-subtitle">CAM-01 · YOLOv11 + MobileNetV3 · INT8</div>
      </div>
      <div class="vision-header__actions">
        <span class="vision-mode"><Focus :size="13" /> AUTO TRACKING</span>
        <button class="vision-icon ripple-target" title="补光灯"><Lightbulb :size="16" /></button>
        <button class="vision-icon ripple-target" title="声音"><Volume2 :size="16" /></button>
        <button class="vision-icon ripple-target" title="全屏"><Expand :size="16" /></button>
      </div>
    </header>

    <div class="camera-stage">
      <div class="camera-scene">
        <div class="fridge-light" />
        <div class="shelf shelf-top" />
        <div class="shelf shelf-middle" />
        <div class="shelf shelf-bottom" />
        <div v-for="(item, index) in produce" :key="index" :class="['produce-shape', item.class]" />
        <div class="crate crate-left" />
        <div class="crate crate-right" />
      </div>
      <div class="camera-vignette" />
      <div class="camera-grid" />
      <div v-if="playing" class="scan-beam" />
      <div class="camera-corner corner-tl" />
      <div class="camera-corner corner-tr" />
      <div class="camera-corner corner-bl" />
      <div class="camera-corner corner-br" />

      <button
        v-for="box in detections"
        :key="box.id"
        class="detect-box"
        :class="{ 'is-selected': box.id === selectedId, 'is-warning': box.freshness === 'warning' }"
        :style="{ left: `${box.x}%`, top: `${box.y}%`, width: `${box.width}%`, height: `${box.height}%` }"
        @click="selectedId = box.id"
      >
        <span class="detect-label">{{ box.label }} · {{ (box.confidence * 100).toFixed(1) }}%</span>
        <i class="corner c1" /><i class="corner c2" /><i class="corner c3" /><i class="corner c4" />
      </button>

      <div class="camera-top-overlay">
        <span><Camera :size="12" /> LIVE</span>
        <span>{{ performance.fps }} FPS</span>
        <span>{{ performance.latency }} ms</span>
      </div>
      <div class="camera-bottom-overlay">
        <button class="play-button ripple-target" @click="playing = !playing">
          <Pause v-if="playing" :size="15" />
          <Play v-else :size="15" />
        </button>
        <div class="timeline"><span :class="{ paused: !playing }" /></div>
        <span>20:29:42</span>
      </div>
    </div>

    <footer class="vision-result">
      <div class="result-main">
        <div class="result-icon"><ScanLine :size="18" /></div>
        <div>
          <span>当前目标</span>
          <strong>{{ selected?.label }}</strong>
        </div>
      </div>
      <div class="result-item"><span>识别置信度</span><strong>{{ ((selected?.confidence || 0) * 100).toFixed(1) }}%</strong></div>
      <div class="result-item"><span>新鲜度</span><strong :class="`freshness-${selected?.freshness}`">{{ freshnessLabel[selected?.freshness || 'fresh'] }}</strong></div>
      <div class="result-item"><span>新鲜度评分</span><strong>{{ ((selected?.freshnessScore || 0) * 100).toFixed(1) }}</strong></div>
      <div class="result-item"><span>推理功耗</span><strong>{{ performance.power }} W</strong></div>
    </footer>
  </section>
</template>

<style scoped>
.vision-panel { display: flex; min-height: 0; flex-direction: column; padding: 14px; overflow: hidden; }
.vision-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 2px 3px 12px; }
.vision-title { display: flex; align-items: center; color: var(--text-1); font-size: 13px; font-weight: 650; }
.vision-subtitle { margin-top: 4px; color: var(--text-3); font-size: 9px; letter-spacing: 0.08em; }
.vision-header__actions { display: flex; align-items: center; gap: 6px; }
.vision-mode { display: inline-flex; align-items: center; gap: 5px; margin-right: 4px; color: #8fe9ff; font-size: 9px; }
.vision-icon, .play-button { display: grid; border: 1px solid var(--stroke); place-items: center; color: var(--text-2); background: rgba(7, 17, 31, 0.36); }
.vision-icon { width: 30px; height: 30px; border-radius: 9px; }
.camera-stage { position: relative; min-height: 280px; flex: 1; overflow: hidden; border: 1px solid rgba(56, 189, 248, 0.19); border-radius: 15px; background: #0b1621; box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.42); }
.camera-scene { position: absolute; inset: 0; overflow: hidden; background: linear-gradient(180deg, #dce5e2 0%, #bfcac6 18%, #80918d 100%); filter: saturate(0.74) contrast(1.06) brightness(0.72); }
.fridge-light { position: absolute; top: -20%; left: 21%; width: 58%; height: 70%; background: radial-gradient(ellipse, rgba(237, 255, 250, 0.95), rgba(174, 219, 211, 0.32) 42%, transparent 72%); filter: blur(12px); }
.shelf { position: absolute; left: 5%; width: 90%; height: 7px; border-radius: 3px; background: linear-gradient(180deg, rgba(245, 255, 255, 0.86), rgba(106, 133, 132, 0.82)); box-shadow: 0 9px 15px rgba(0, 0, 0, 0.18); }
.shelf::after { position: absolute; top: 7px; left: 2%; width: 96%; height: 4px; border-radius: 50%; background: rgba(9, 30, 31, 0.18); filter: blur(2px); content: ""; }
.shelf-top { top: 34%; } .shelf-middle { top: 64%; } .shelf-bottom { top: 91%; }
.produce-shape { position: absolute; z-index: 2; filter: saturate(1.16) drop-shadow(0 5px 6px rgba(0, 0, 0, 0.26)); }
.apple { width: 9.5%; aspect-ratio: 1; border-radius: 46% 48% 52% 47%; background: radial-gradient(circle at 32% 25%, #ff8f74, #d93d33 54%, #842723); }
.apple::after { position: absolute; top: -14%; left: 52%; width: 7%; height: 20%; border-radius: 4px; background: #4c3824; content: ""; transform: rotate(13deg); }
.apple-1 { top: 22%; left: 14%; } .apple-2 { top: 24%; left: 23%; transform: scale(.9); } .apple-3 { top: 20%; left: 31%; transform: scale(.84); }
.tomato { width: 10%; aspect-ratio: 1.06; border-radius: 48%; background: radial-gradient(circle at 36% 25%, #ff8a67, #dc4331 52%, #912c23); }
.tomato::after { position: absolute; top: -5%; left: 32%; width: 37%; height: 18%; clip-path: polygon(50% 0, 59% 36%, 100% 20%, 73% 54%, 94% 92%, 54% 68%, 18% 100%, 31% 58%, 0 39%, 42% 38%); background: #4f8e3f; content: ""; }
.tomato-1 { top: 64%; left: 50%; } .tomato-2 { top: 65%; left: 61%; transform: scale(.88); }
.broccoli { width: 15%; height: 16%; border-radius: 48% 52% 38% 42%; background: radial-gradient(circle at 25% 28%, #75b75b 0 14%, transparent 15%), radial-gradient(circle at 52% 25%, #4e994b 0 18%, transparent 19%), radial-gradient(circle at 74% 38%, #3e8240 0 18%, transparent 19%), radial-gradient(circle at 40% 55%, #34753c 0 30%, transparent 31%); }
.broccoli::after { position: absolute; top: 68%; left: 44%; width: 23%; height: 42%; border-radius: 4px; background: #79a85b; content: ""; }
.broccoli-1 { top: 17%; left: 60%; } .broccoli-2 { top: 18%; left: 72%; transform: scale(.74); }
.cucumber { width: 19%; height: 6%; border-radius: 999px; background: linear-gradient(180deg, #4b9c57, #24683e); box-shadow: inset 0 2px 4px rgba(255,255,255,.2); transform: rotate(-8deg); }
.cucumber-1 { top: 76%; left: 18%; }
.carrot { width: 4.8%; height: 20%; clip-path: polygon(17% 0, 86% 0, 56% 100%); background: linear-gradient(90deg, #e87522, #f6a03d 48%, #c95717); transform: rotate(72deg); }
.carrot-1 { top: 69%; left: 32%; }
.crate { position: absolute; z-index: 1; width: 34%; height: 18%; border: 2px solid rgba(229, 242, 238, 0.52); border-top-width: 5px; background: linear-gradient(180deg, rgba(235, 246, 244, .18), rgba(33, 62, 60, .22)); }
.crate-left { bottom: 8%; left: 8%; } .crate-right { right: 8%; bottom: 8%; }
.camera-vignette { position: absolute; inset: 0; box-shadow: inset 0 0 90px rgba(0, 9, 16, 0.74); pointer-events: none; }
.camera-grid { position: absolute; inset: 0; opacity: .17; background-image: linear-gradient(rgba(108, 232, 255, 0.22) 1px, transparent 1px), linear-gradient(90deg, rgba(108, 232, 255, 0.22) 1px, transparent 1px); background-size: 44px 44px; pointer-events: none; }
.scan-beam { position: absolute; left: 0; right: 0; top: 0; height: 22%; background: linear-gradient(180deg, transparent, rgba(56, 189, 248, .12), rgba(56, 189, 248, .5), transparent); animation: scanline 4.8s linear infinite; pointer-events: none; }
.camera-corner { position: absolute; width: 20px; height: 20px; border-color: rgba(132, 234, 255, .7); }
.corner-tl { top: 12px; left: 12px; border-top: 1px solid; border-left: 1px solid; }
.corner-tr { top: 12px; right: 12px; border-top: 1px solid; border-right: 1px solid; }
.corner-bl { bottom: 12px; left: 12px; border-bottom: 1px solid; border-left: 1px solid; }
.corner-br { right: 12px; bottom: 12px; border-right: 1px solid; border-bottom: 1px solid; }
.detect-box { position: absolute; z-index: 4; border: 1px solid rgba(74, 222, 128, .72); color: #8dffb4; background: rgba(34, 197, 94, .025); transition: background .2s ease, border-color .2s ease; }
.detect-box:hover, .detect-box.is-selected { border-color: #70ff9f; background: rgba(34, 197, 94, .08); box-shadow: 0 0 20px rgba(34, 197, 94, .13); }
.detect-box.is-warning { border-color: rgba(251, 191, 36, .82); color: #ffd879; background: rgba(245, 158, 11, .04); }
.detect-label { position: absolute; top: -21px; left: -1px; height: 20px; padding: 3px 7px; color: #07130c; font-size: 8px; font-weight: 700; background: #70ff9f; white-space: nowrap; }
.detect-box.is-warning .detect-label { background: #ffd879; }
.corner { position: absolute; width: 8px; height: 8px; border-color: currentColor; }
.c1 { top: -2px; left: -2px; border-top: 2px solid; border-left: 2px solid; } .c2 { top: -2px; right: -2px; border-top: 2px solid; border-right: 2px solid; } .c3 { bottom: -2px; left: -2px; border-bottom: 2px solid; border-left: 2px solid; } .c4 { right: -2px; bottom: -2px; border-right: 2px solid; border-bottom: 2px solid; }
.camera-top-overlay, .camera-bottom-overlay { position: absolute; z-index: 5; display: flex; align-items: center; color: rgba(227, 247, 255, .84); font-size: 9px; }
.camera-top-overlay { top: 13px; right: 14px; gap: 7px; }
.camera-top-overlay span { display: inline-flex; align-items: center; gap: 4px; padding: 4px 7px; border: 1px solid rgba(203, 233, 243, .17); border-radius: 6px; background: rgba(1, 10, 16, .4); backdrop-filter: blur(6px); }
.camera-bottom-overlay { right: 14px; bottom: 12px; left: 14px; gap: 9px; }
.play-button { width: 28px; height: 28px; border-radius: 50%; }
.timeline { height: 3px; flex: 1; overflow: hidden; border-radius: 9px; background: rgba(255,255,255,.18); }
.timeline span { display: block; width: 72%; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--cyan), var(--blue)); animation: shimmer 5s ease-in-out infinite; }
.timeline span.paused { animation-play-state: paused; }
.vision-result { display: grid; grid-template-columns: 1.35fr repeat(4, 1fr); align-items: center; gap: 6px; padding: 12px 4px 0; }
.result-main { display: flex; align-items: center; gap: 9px; }
.result-icon { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 10px; color: var(--cyan); background: rgba(56,189,248,.1); }
.result-main span, .result-item span { display: block; color: var(--text-3); font-size: 9px; }
.result-main strong, .result-item strong { display: block; margin-top: 4px; color: var(--text-1); font-size: 11px; }
.result-item { padding-left: 11px; border-left: 1px solid var(--stroke); }
.freshness-fresh { color: #75efa1 !important; } .freshness-warning { color: #ffd16e !important; } .freshness-spoiled { color: #ff8585 !important; }
.is-compact .camera-stage { min-height: 340px; }
@media (max-width: 840px) {
  .vision-mode { display: none; }
  .vision-result { grid-template-columns: repeat(2, 1fr); }
  .result-main { grid-column: 1 / -1; }
  .result-item { padding: 7px 0; border-left: 0; border-top: 1px solid var(--stroke); }
}
</style>

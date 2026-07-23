<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Activity, Camera, ChevronRight, CircleGauge, Cpu, Database, HardDrive, Lightbulb, MemoryStick, Network, RadioTower, RefreshCw, Terminal, Wifi } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import StatusDot from '@/components/common/StatusDot.vue'
import { deviceApi } from '@/api'
import type { DeviceItem } from '@/types'
import { useAppStore } from '@/stores/app'

const devices = ref<DeviceItem[]>([])
const appStore = useAppStore()
const logVisible = ref(false)
const selectedDevice = ref<DeviceItem | null>(null)
const iconMap = { '边缘计算节点': Cpu, '视觉采集': Camera, '环境感知': RadioTower, '执行器': Lightbulb, '数据存储': Database, '网络通信': Network }
const deviceIcon = (type: string) => iconMap[type as keyof typeof iconMap] || RadioTower
const onlineRate = computed(() => devices.value.length ? devices.value.reduce((sum, item) => sum + item.uptime, 0) / devices.value.length : 0)
const gaugeOption = computed(() => ({
  series: [{
    type: 'gauge', startAngle: 220, endAngle: -40, radius: '90%', min: 90, max: 100,
    axisLine: { lineStyle: { width: 10, color: [[1, 'rgba(148,163,184,.12)']] } },
    progress: { show: true, width: 10, roundCap: true, itemStyle: { color: '#22c55e' } },
    pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
    detail: { formatter: '{value}%', color: appStore.isDark ? '#f4f8ff' : '#16263d', fontSize: 22, fontWeight: 700 },
    data: [{ value: +onlineRate.value.toFixed(2) }],
  }],
}))
const resourceOption = computed(() => ({
  radar: { center: ['50%', '54%'], radius: '68%', splitNumber: 4, indicator: [{ name: 'CPU', max: 100 }, { name: '内存', max: 100 }, { name: '存储', max: 100 }, { name: '网络', max: 100 }, { name: '温度', max: 100 }], axisName: { color: appStore.isDark ? '#70829a' : '#7b8ca3', fontSize: 9 }, splitArea: { areaStyle: { color: ['rgba(56,189,248,.02)', 'rgba(56,189,248,.05)'] } }, splitLine: { lineStyle: { color: 'rgba(148,163,184,.16)' } }, axisLine: { lineStyle: { color: 'rgba(148,163,184,.16)' } } },
  series: [{ type: 'radar', data: [{ value: [38, 52, 41, 78, 36], areaStyle: { color: 'rgba(56,189,248,.22)' }, lineStyle: { color: '#38bdf8', width: 2 }, itemStyle: { color: '#38bdf8' } }] }],
}))

const openLog = (device: DeviceItem) => { selectedDevice.value = device; logVisible.value = true }
onMounted(async () => { devices.value = (await deviceApi.getList()).data })
</script>

<template>
  <div class="devices-page">
    <PageHeader eyebrow="EDGE DEVICE FLEET" title="设备管理" description="LoongArch 端侧节点、传感器与执行器统一运维">
      <template #actions><el-button><RefreshCw :size="15" />刷新状态</el-button><el-button type="primary"><RadioTower :size="15" />添加设备</el-button></template>
    </PageHeader>

    <div class="board-overview">
      <GlassPanel strong class="board-card">
        <div class="board-brand">
          <div class="chip-visual"><span>LA</span><i v-for="n in 16" :key="n" /></div>
          <div><span class="board-eyebrow">EDGE COMPUTING CORE</span><h2>Loongson 2K2000-i</h2><p>LA364 双核 · 1.4GHz · LoongArch 自主指令集</p></div>
        </div>
        <div class="board-status"><StatusDot state="online" label="在线运行" /><span>连续运行 12 天 08:42:19</span></div>
        <div class="resource-grid">
          <div><Cpu :size="16" /><span>CPU 使用率</span><strong>38%</strong></div>
          <div><MemoryStick :size="16" /><span>内存使用</span><strong>2.08 / 4 GB</strong></div>
          <div><HardDrive :size="16" /><span>本地存储</span><strong>7.6 GB 可用</strong></div>
          <div><Wifi :size="16" /><span>网络延迟</span><strong>18 ms</strong></div>
        </div>
      </GlassPanel>
      <GlassPanel class="online-gauge">
        <div class="mini-heading"><div><h2>设备在线率</h2><span>过去 30 天</span></div><CircleGauge :size="18" /></div>
        <BaseChart :option="gaugeOption" height="180px" />
        <div class="gauge-note">6 个设备 · 5 正常 · 1 需关注</div>
      </GlassPanel>
      <GlassPanel class="resource-radar">
        <div class="mini-heading"><div><h2>资源负载</h2><span>实时综合指标</span></div><Activity :size="18" /></div>
        <BaseChart :option="resourceOption" height="190px" />
      </GlassPanel>
    </div>

    <div class="device-section-head"><div><h2>设备列表</h2><span>最近心跳与运行状态</span></div><span class="status-chip is-online"><span class="realtime-dot" />WebSocket 实时更新</span></div>
    <div class="device-grid">
      <GlassPanel v-for="device in devices" :key="device.id" hover class="device-card">
        <div class="device-card__head">
          <div class="device-icon"><component :is="deviceIcon(device.type)" :size="20" /></div>
          <StatusDot :state="device.state" :label="device.state === 'online' ? '在线' : device.state === 'warning' ? '需关注' : '离线'" />
        </div>
        <h3>{{ device.name }}</h3><p>{{ device.model }}</p>
        <div class="device-value">{{ device.value }}</div>
        <div class="device-detail">{{ device.detail }}</div>
        <div class="uptime-row"><span>在线率</span><strong>{{ device.uptime.toFixed(2) }}%</strong></div>
        <div class="uptime-track"><span :style="{ width: `${device.uptime}%` }" /></div>
        <button class="device-footer ripple-target" @click="openLog(device)"><span>心跳 {{ device.lastHeartbeat }}</span><span>详情 <ChevronRight :size="13" /></span></button>
      </GlassPanel>
    </div>

    <el-drawer v-model="logVisible" size="520px" title="设备运行日志">
      <div v-if="selectedDevice" class="log-device-head">
        <div class="device-icon"><component :is="deviceIcon(selectedDevice.type)" :size="20" /></div>
        <div><h3>{{ selectedDevice.name }}</h3><span>{{ selectedDevice.model }} · {{ selectedDevice.id }}</span></div>
      </div>
      <div class="terminal-window">
        <div class="terminal-head"><Terminal :size="14" /><span>journalctl -u {{ selectedDevice?.id }}</span></div>
        <pre>[20:30:12] INFO  heartbeat sent, latency=18ms
[20:30:08] INFO  device state synchronized
[20:29:42] INFO  inference complete, frame=3018
[20:29:42] INFO  freshness_score=0.961
[20:29:41] INFO  camera frame captured
[20:29:40] INFO  GPIO LED on, warmup=80ms
[20:29:12] INFO  sqlite checkpoint complete
[20:28:58] INFO  env sample: 3.6C, 88.0%RH
[20:28:31] INFO  websocket client connected</pre>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.board-overview { display: grid; grid-template-columns: 1.45fr .68fr .68fr; gap: 14px; }
.board-card { position: relative; overflow: hidden; }
.board-card::after { position: absolute; top: -50%; right: -10%; width: 50%; height: 180%; background: linear-gradient(90deg, transparent, rgba(56,189,248,.07), transparent); content: ""; transform: rotate(18deg); }
.board-brand { position: relative; z-index: 1; display: flex; align-items: center; gap: 18px; }
.chip-visual { position: relative; display: grid; width: 78px; height: 78px; flex: 0 0 auto; place-items: center; border: 2px solid rgba(56,189,248,.4); border-radius: 15px; color: #a8f0ff; background: linear-gradient(145deg, #193750, #0d1d30); box-shadow: inset 0 0 25px rgba(56,189,248,.16), 0 0 28px rgba(56,189,248,.1); }
.chip-visual span { font-size: 19px; font-weight: 760; }.chip-visual i { position: absolute; width: 8px; height: 2px; background: rgba(56,189,248,.45); }.chip-visual i:nth-child(-n+4) { top: -5px; transform: rotate(90deg); }.chip-visual i:nth-child(1){left:13px}.chip-visual i:nth-child(2){left:29px}.chip-visual i:nth-child(3){left:45px}.chip-visual i:nth-child(4){left:61px}
.board-eyebrow { color: var(--cyan); font-size: 8px; letter-spacing: .14em; }.board-brand h2 { margin: 7px 0 0; color: var(--text-1); font-size: 22px; }.board-brand p { margin: 7px 0 0; color: var(--text-3); font-size: 10px; }
.board-status { position: relative; z-index: 1; display: flex; align-items: center; gap: 13px; margin-top: 19px; color: var(--text-3); font-size: 9px; }
.resource-grid { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 14px; }.resource-grid div { padding: 10px; border: 1px solid var(--stroke); border-radius: 11px; background: var(--surface-soft); }.resource-grid svg { color: var(--cyan); }.resource-grid span, .resource-grid strong { display: block; }.resource-grid span { margin-top: 8px; color: var(--text-3); font-size: 8px; }.resource-grid strong { margin-top: 4px; color: var(--text-1); font-size: 10px; }
.mini-heading { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); }.mini-heading h2 { margin: 0; color: var(--text-1); font-size: 13px; }.mini-heading span { display: block; margin-top: 4px; color: var(--text-3); font-size: 8px; }.gauge-note { color: var(--text-3); font-size: 9px; text-align: center; }
.device-section-head { display: flex; align-items: center; justify-content: space-between; margin: 20px 2px 11px; }.device-section-head h2 { margin: 0; color: var(--text-1); font-size: 14px; }.device-section-head > div span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }
.device-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.device-card__head { display: flex; align-items: center; justify-content: space-between; }.device-icon { display: grid; width: 41px; height: 41px; place-items: center; border-radius: 12px; color: var(--cyan); background: linear-gradient(145deg, rgba(56,189,248,.16), rgba(79,140,255,.08)); }
.device-card h3 { margin: 14px 0 0; color: var(--text-1); font-size: 13px; }.device-card p { margin: 5px 0 0; color: var(--text-3); font-size: 9px; }.device-value { margin-top: 17px; color: var(--text-1); font-size: 21px; font-weight: 700; }.device-detail { margin-top: 5px; color: var(--text-3); font-size: 9px; }
.uptime-row { display: flex; justify-content: space-between; margin-top: 17px; color: var(--text-3); font-size: 9px; }.uptime-row strong { color: var(--text-2); }.uptime-track { height: 4px; margin-top: 6px; overflow: hidden; border-radius: 99px; background: var(--surface-soft); }.uptime-track span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--green), var(--cyan)); }
.device-footer { display: flex; width: 100%; align-items: center; justify-content: space-between; margin-top: 15px; padding: 10px 0 0; border: 0; border-top: 1px solid var(--stroke); color: var(--text-3); font-size: 8px; background: transparent; }.device-footer span:last-child { display: flex; align-items: center; color: var(--cyan); }
.log-device-head { display: flex; align-items: center; gap: 12px; }.log-device-head h3 { margin: 0; color: var(--text-1); }.log-device-head span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }
.terminal-window { margin-top: 20px; overflow: hidden; border: 1px solid var(--stroke); border-radius: 13px; background: #050b12; }.terminal-head { display: flex; align-items: center; gap: 7px; padding: 11px; border-bottom: 1px solid rgba(148,163,184,.12); color: #7dd3fc; font-size: 10px; }.terminal-window pre { margin: 0; padding: 15px; overflow: auto; color: #9bd9b0; font: 10px/1.9 "Cascadia Code", Consolas, monospace; }
@media (max-width: 1200px) { .board-overview { grid-template-columns: 1fr 1fr; }.board-card { grid-column: 1/-1; }.device-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 700px) { .board-overview, .device-grid { grid-template-columns: 1fr; }.board-card { grid-column: auto; }.resource-grid { grid-template-columns: 1fr 1fr; } }
</style>

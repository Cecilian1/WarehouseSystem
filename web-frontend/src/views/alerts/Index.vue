<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { AlertTriangle, BellRing, Check, CheckCheck, CircleAlert, Clock3, Filter, Flame, MoreHorizontal, Search, Thermometer, Trash2, WifiOff } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import { alertApi } from '@/api'
import type { AlertItem } from '@/types'

const alerts = ref<AlertItem[]>([])
const selected = ref<AlertItem[]>([])
const status = ref('')
const keyword = ref('')

const iconMap = { expiring: Clock3, spoiled: Flame, device: WifiOff, temperature: Thermometer, humidity: CircleAlert }
const filtered = computed(() => alerts.value.filter((item) => (!status.value || item.status === status.value) && (!keyword.value || `${item.title}${item.source}`.includes(keyword.value))))
const stats = computed(() => [
  { label: '待处理', value: alerts.value.filter((item) => item.status === 'pending').length, icon: AlertTriangle, tone: 'warning' },
  { label: '严重预警', value: alerts.value.filter((item) => item.level === 'critical').length, icon: Flame, tone: 'critical' },
  { label: '今日已确认', value: alerts.value.filter((item) => item.status === 'confirmed').length, icon: CheckCheck, tone: 'success' },
  { label: '设备异常', value: alerts.value.filter((item) => item.type === 'device').length, icon: WifiOff, tone: 'info' },
])

const handle = (item: AlertItem, next: 'confirmed' | 'ignored') => {
  item.status = next
  ElMessage.success(next === 'confirmed' ? '预警已确认处理' : '预警已忽略')
}

const batchHandle = () => {
  selected.value.forEach((item) => { item.status = 'confirmed' })
  ElMessage.success(`已处理 ${selected.value.length} 条预警`)
  selected.value = []
}

onMounted(async () => { alerts.value = (await alertApi.getList()).data })
</script>

<template>
  <div class="alerts-page">
    <PageHeader eyebrow="ALERT OPERATIONS" title="预警中心" description="保质期、环境与设备异常的统一处置闭环">
      <template #actions>
        <el-button :disabled="!selected.length" @click="batchHandle"><CheckCheck :size="15" />批量处理 {{ selected.length || '' }}</el-button>
        <el-button type="primary"><BellRing :size="15" />预警规则</el-button>
      </template>
    </PageHeader>

    <div class="alert-stats">
      <GlassPanel v-for="item in stats" :key="item.label" hover :class="['alert-stat', `is-${item.tone}`]">
        <div class="alert-stat__icon"><component :is="item.icon" :size="19" /></div>
        <div><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div>
      </GlassPanel>
    </div>

    <GlassPanel class="alert-toolbar" padding="small">
      <div class="status-tabs">
        <button v-for="item in [{v:'',l:'全部'},{v:'pending',l:'待处理'},{v:'confirmed',l:'已确认'},{v:'ignored',l:'已忽略'}]" :key="item.v" :class="{ active: status === item.v }" @click="status = item.v">{{ item.l }}</button>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索预警内容" clearable><template #prefix><Search :size="14" /></template></el-input>
        <el-button><Filter :size="14" />筛选</el-button>
      </div>
    </GlassPanel>

    <div class="alert-list">
      <GlassPanel v-for="item in filtered" :key="item.id" :class="['alert-item', `is-${item.level}`, `status-${item.status}`]" hover>
        <el-checkbox :model-value="selected.includes(item)" @change="(value:boolean) => value ? selected.push(item) : selected.splice(selected.indexOf(item), 1)" />
        <div class="alert-type-icon"><component :is="iconMap[item.type]" :size="19" /></div>
        <div class="alert-content">
          <div class="alert-title-row"><h3>{{ item.title }}</h3><span :class="`level-${item.level}`">{{ item.level === 'critical' ? '严重' : item.level === 'warning' ? '警告' : '提示' }}</span></div>
          <p>{{ item.description }}</p>
          <div class="alert-meta"><span>{{ item.source }}</span><i /><span>{{ item.time }}</span></div>
        </div>
        <div class="alert-status">
          <span :class="`is-${item.status}`">{{ item.status === 'pending' ? '待处理' : item.status === 'confirmed' ? '已确认' : '已忽略' }}</span>
        </div>
        <div class="alert-actions">
          <el-button v-if="item.status === 'pending'" type="primary" @click="handle(item, 'confirmed')"><Check :size="14" />确认</el-button>
          <el-button v-if="item.status === 'pending'" @click="handle(item, 'ignored')"><Trash2 :size="14" />忽略</el-button>
          <el-button v-else circle title="更多"><MoreHorizontal :size="15" /></el-button>
        </div>
      </GlassPanel>
    </div>
  </div>
</template>

<style scoped>
.alert-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.alert-stat { display: flex; align-items: center; gap: 13px; }
.alert-stat__icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 12px; color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }
.alert-stat.is-warning { --accent: var(--orange); }.alert-stat.is-critical { --accent: var(--red); }.alert-stat.is-success { --accent: var(--green); }.alert-stat.is-info { --accent: var(--cyan); }
.alert-stat span, .alert-stat strong { display: block; }.alert-stat span { color: var(--text-3); font-size: 10px; }.alert-stat strong { margin-top: 5px; color: var(--text-1); font-size: 23px; }
.alert-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 14px; }
.status-tabs { display: flex; gap: 4px; padding: 3px; border-radius: 10px; background: var(--surface-soft); }.status-tabs button { padding: 7px 12px; border: 0; border-radius: 8px; color: var(--text-3); font-size: 10px; background: transparent; }.status-tabs button.active { color: white; background: linear-gradient(135deg, var(--blue), #6c63ff); }
.toolbar-actions { display: flex; gap: 8px; }.toolbar-actions .el-input { width: 240px; }
.alert-list { display: grid; gap: 10px; margin-top: 12px; }
.alert-item { position: relative; display: grid; grid-template-columns: auto 42px 1fr auto auto; align-items: center; gap: 13px; overflow: hidden; }
.alert-item::before { position: absolute; top: 12px; bottom: 12px; left: 0; width: 3px; border-radius: 0 4px 4px 0; background: var(--accent); content: ""; box-shadow: 0 0 12px var(--accent); }
.alert-item.is-critical { --accent: var(--red); }.alert-item.is-warning { --accent: var(--orange); }.alert-item.is-info { --accent: var(--cyan); }
.alert-type-icon { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 12px; color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }
.alert-title-row { display: flex; align-items: center; gap: 8px; }.alert-title-row h3 { margin: 0; color: var(--text-1); font-size: 12px; }.alert-title-row span { padding: 3px 6px; border-radius: 99px; font-size: 8px; }.level-critical { color: #ff9999; background: rgba(239,68,68,.11); }.level-warning { color: #ffd477; background: rgba(245,158,11,.11); }.level-info { color: #8ee7ff; background: rgba(56,189,248,.1); }
.alert-content p { margin: 7px 0; color: var(--text-2); font-size: 10px; }.alert-meta { display: flex; align-items: center; gap: 7px; color: var(--text-3); font-size: 8px; }.alert-meta i { width: 3px; height: 3px; border-radius: 50%; background: var(--text-3); }
.alert-status span { display: inline-flex; padding: 5px 8px; border-radius: 99px; font-size: 9px; }.alert-status .is-pending { color: #ffd477; background: rgba(245,158,11,.1); }.alert-status .is-confirmed { color: #82eea7; background: rgba(34,197,94,.1); }.alert-status .is-ignored { color: var(--text-3); background: var(--surface-soft); }
.alert-actions { display: flex; gap: 6px; }
.status-confirmed, .status-ignored { opacity: .7; }
@media (max-width: 980px) { .alert-stats { grid-template-columns: 1fr 1fr; } .alert-item { grid-template-columns: 42px 1fr auto; }.alert-item > .el-checkbox { display: none; }.alert-status { display: none; }.alert-actions { grid-column: 2/4; justify-content: flex-end; } }
@media (max-width: 650px) { .alert-stats { grid-template-columns: 1fr; }.alert-toolbar { align-items: stretch; flex-direction: column; }.toolbar-actions .el-input { width: 100%; }.status-tabs { overflow-x: auto; }.alert-item { grid-template-columns: 36px 1fr; }.alert-actions { grid-column: 1/3; }.alert-title-row { align-items: flex-start; flex-direction: column; } }
</style>

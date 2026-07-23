<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Download, Filter, RotateCcw, Search } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import { historyApi } from '@/api'
import type { HistoryItem } from '@/types'

const list = ref<HistoryItem[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const moduleFilter = ref('')
const statusFilter = ref('')
const keyword = ref('')
const dateRange = ref<[Date, Date] | null>(null)

const load = async () => {
  loading.value = true
  try {
    const response = await historyApi.getList({ page: page.value, pageSize: pageSize.value })
    list.value = response.data.list.filter((item) =>
      (!moduleFilter.value || item.module === moduleFilter.value) &&
      (!statusFilter.value || item.status === statusFilter.value) &&
      (!keyword.value || `${item.action}${item.detail}${item.operator}`.includes(keyword.value)),
    )
    total.value = response.data.total
  } finally {
    loading.value = false
  }
}

const reset = () => {
  moduleFilter.value = ''
  statusFilter.value = ''
  keyword.value = ''
  dateRange.value = null
  page.value = 1
  load()
}

const exportCsv = () => {
  const rows = [['记录ID', '时间', '模块', '操作', '详情', '执行主体', '状态'], ...list.value.map((item) => [item.id, item.time, item.module, item.action, item.detail, item.operator, item.status])]
  const csv = '\uFEFF' + rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `芯鲜管家_历史记录_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('历史记录已导出')
}

onMounted(load)
</script>

<template>
  <div class="history-page">
    <PageHeader eyebrow="AUDIT & HISTORY" title="历史记录" description="库存、识别、环境与设备操作的全链路追溯">
      <template #actions><el-button @click="exportCsv"><Download :size="15" />导出报表</el-button></template>
    </PageHeader>

    <GlassPanel class="history-filter" padding="small">
      <div class="filter-grid">
        <el-input v-model="keyword" placeholder="搜索操作、详情或执行主体" clearable @keyup.enter="load"><template #prefix><Search :size="14" /></template></el-input>
        <el-select v-model="moduleFilter" clearable placeholder="全部模块"><el-option label="AI 识别" value="AI 识别" /><el-option label="环境监测" value="环境监测" /></el-select>
        <el-select v-model="statusFilter" clearable placeholder="全部状态"><el-option label="成功" value="success" /><el-option label="警告" value="warning" /><el-option label="失败" value="failed" /></el-select>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
        <el-button type="primary" @click="load"><Filter :size="14" />查询</el-button>
        <el-button @click="reset"><RotateCcw :size="14" />重置</el-button>
      </div>
    </GlassPanel>

    <GlassPanel padding="none" class="history-table">
      <el-table v-loading="loading" :data="list" height="calc(100vh - 315px)" min-height="420">
        <el-table-column prop="id" label="记录ID" width="95" sortable>
          <template #default="{ row }"><span class="record-id">#{{ row.id }}</span></template>
        </el-table-column>
        <el-table-column prop="time" label="时间" width="180" sortable />
        <el-table-column prop="module" label="模块" width="120">
          <template #default="{ row }"><span class="module-tag">{{ row.module }}</span></template>
        </el-table-column>
        <el-table-column prop="action" label="操作类型" width="130" sortable />
        <el-table-column prop="detail" label="详情" min-width="260" />
        <el-table-column prop="operator" label="执行主体" width="130" />
        <el-table-column label="状态" width="105">
          <template #default="{ row }">
            <span :class="['history-status', `is-${row.status}`]"><i />{{ row.status === 'success' ? '成功' : row.status === 'warning' ? '警告' : '失败' }}</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <span>本地 SQLite 记录 · 共 {{ total }} 条</span>
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" layout="prev, pager, next" :total="total" @current-change="load" />
      </div>
    </GlassPanel>
  </div>
</template>

<style scoped>
.history-filter { margin-bottom: 12px; }
.filter-grid { display: grid; grid-template-columns: minmax(230px, 1fr) 140px 140px minmax(240px, 1fr) auto auto; gap: 8px; }
.history-table { overflow: hidden; }
.record-id { color: var(--cyan); font-family: "Cascadia Code", Consolas, monospace; font-size: 10px; }
.module-tag { display: inline-flex; padding: 5px 8px; border-radius: 8px; color: #a9d8ff; font-size: 9px; background: rgba(79,140,255,.1); }
.history-status { display: inline-flex; align-items: center; gap: 6px; font-size: 9px; }.history-status i { width: 6px; height: 6px; border-radius: 50%; }.history-status.is-success { color: #82eea7; }.history-status.is-success i { background: var(--green); box-shadow: 0 0 7px var(--green); }.history-status.is-warning { color: #ffd477; }.history-status.is-warning i { background: var(--orange); }.history-status.is-failed { color: #ff9696; }.history-status.is-failed i { background: var(--red); }
.pagination-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 16px; border-top: 1px solid var(--stroke); }.pagination-bar > span { color: var(--text-3); font-size: 9px; }
@media (max-width: 1200px) { .filter-grid { grid-template-columns: 1fr 1fr 1fr; }.filter-grid :deep(.el-date-editor) { width: 100%; } }
@media (max-width: 680px) { .filter-grid { grid-template-columns: 1fr; }.pagination-bar > span { display: none; }.pagination-bar { justify-content: flex-end; } }
</style>

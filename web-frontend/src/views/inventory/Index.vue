<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Boxes, Grid2X2, List, Pencil, Plus, Search, SlidersHorizontal, Trash2 } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import ProduceVisual from '@/components/common/ProduceVisual.vue'
import { useInventoryStore } from '@/stores/inventory'
import type { InventoryItem } from '@/types'
import { freshnessLabel, freshnessTone } from '@/utils/format'

const store = useInventoryStore()
const viewMode = ref<'list' | 'card'>('list')
const dialogVisible = ref(false)
const previewVisible = ref(false)
const editingItem = ref<InventoryItem | null>(null)
const previewItem = ref<InventoryItem | null>(null)
const form = reactive({ name: '', category: '水果', quantity: 1, unit: '件', shelfLife: 7, remainingDays: 7, storageAdvice: '2-5°C · 85-95%RH', location: 'A-01 上层' })

const inventoryStats = computed(() => [
  { label: '库存品类', value: store.total, unit: '种', tone: '#4f8cff' },
  { label: '库存总量', value: store.list.reduce((sum, item) => sum + item.quantity, 0), unit: '件', tone: '#38bdf8' },
  { label: '新鲜库存', value: store.list.filter((item) => item.freshness === 'fresh').length, unit: '种', tone: '#22c55e' },
  { label: '需优先处理', value: store.list.filter((item) => item.freshness !== 'fresh').length, unit: '种', tone: '#f59e0b' },
])

const search = () => {
  store.query.page = 1
  store.fetchList()
}

const openCreate = () => {
  editingItem.value = null
  Object.assign(form, { name: '', category: '水果', quantity: 1, unit: '件', shelfLife: 7, remainingDays: 7, storageAdvice: '2-5°C · 85-95%RH', location: 'A-01 上层' })
  dialogVisible.value = true
}

const openEdit = (item: InventoryItem) => {
  editingItem.value = item
  Object.assign(form, item)
  dialogVisible.value = true
}

const submit = () => {
  ElMessage.success(editingItem.value ? '库存信息已更新' : '库存记录已创建')
  dialogVisible.value = false
}

const removeItem = async (item: InventoryItem) => {
  await ElMessageBox.confirm(`确认删除“${item.name}”的库存记录？`, '删除确认', { type: 'warning' })
  ElMessage.success('库存记录已删除')
}

const preview = (item: InventoryItem) => {
  previewItem.value = item
  previewVisible.value = true
}

const labelOf = (freshness: InventoryItem['freshness']) => freshnessLabel[freshness]
const toneOf = (freshness: InventoryItem['freshness']) => freshnessTone[freshness]

onMounted(store.fetchList)
</script>

<template>
  <div class="inventory-page">
    <PageHeader eyebrow="INVENTORY INTELLIGENCE" title="库存管理" description="AI 自动盘点与保质期精细化管理">
      <template #actions>
        <div class="view-switch">
          <button :class="{ active: viewMode === 'list' }" title="列表视图" @click="viewMode = 'list'"><List :size="16" /></button>
          <button :class="{ active: viewMode === 'card' }" title="卡片视图" @click="viewMode = 'card'"><Grid2X2 :size="16" /></button>
        </div>
        <el-button type="primary" @click="openCreate"><Plus :size="15" />新增库存</el-button>
      </template>
    </PageHeader>

    <div class="inventory-stats">
      <GlassPanel v-for="item in inventoryStats" :key="item.label" hover padding="small" class="inventory-stat">
        <span class="stat-light" :style="{ background: item.tone, boxShadow: `0 0 18px ${item.tone}` }" />
        <div><small>{{ item.label }}</small><strong>{{ item.value }}<em>{{ item.unit }}</em></strong></div>
      </GlassPanel>
    </div>

    <GlassPanel class="filter-panel" padding="small">
      <div class="filter-main">
        <el-input v-model="store.query.keyword" clearable placeholder="搜索名称、分类或货位" @keyup.enter="search">
          <template #prefix><Search :size="15" /></template>
        </el-input>
        <el-select v-model="store.query.category" clearable placeholder="全部分类" @change="search">
          <el-option label="水果" value="水果" />
          <el-option label="蔬菜" value="蔬菜" />
        </el-select>
        <el-select v-model="store.query.freshness" clearable placeholder="全部新鲜度" @change="search">
          <el-option label="新鲜" value="fresh" />
          <el-option label="临期" value="warning" />
          <el-option label="腐败" value="spoiled" />
        </el-select>
        <el-button @click="search"><SlidersHorizontal :size="15" />筛选</el-button>
      </div>
      <span>共 {{ store.total }} 个库存品类</span>
    </GlassPanel>

    <GlassPanel v-if="viewMode === 'list'" padding="none" class="table-panel">
      <el-table v-loading="store.loading" :data="store.list" height="calc(100vh - 410px)" min-height="380">
        <el-table-column label="果蔬信息" min-width="190" fixed>
          <template #default="{ row }">
            <button class="produce-cell ripple-target" @click="preview(row)">
              <ProduceVisual :name="row.name" :color="row.color" />
              <span><strong>{{ row.name }}</strong><small>{{ row.location }}</small></span>
            </button>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="90" sortable />
        <el-table-column label="数量" width="105" sortable>
          <template #default="{ row }"><strong class="qty">{{ row.quantity }}</strong> {{ row.unit }}</template>
        </el-table-column>
        <el-table-column label="新鲜度" width="125" sortable>
          <template #default="{ row }">
            <el-tag :type="toneOf(row.freshness)" effect="dark">{{ labelOf(row.freshness) }} {{ Math.round(row.freshnessScore * 100) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="剩余天数" width="130" sortable>
          <template #default="{ row }">
            <div class="days-cell" :class="`is-${row.freshness}`"><strong>{{ row.remainingDays }}</strong><span>/ {{ row.shelfLife }} 天</span></div>
          </template>
        </el-table-column>
        <el-table-column prop="storageAdvice" label="温湿度建议" min-width="160" />
        <el-table-column prop="inboundAt" label="入库时间" width="165" sortable />
        <el-table-column label="操作" width="112" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button circle title="编辑" @click="openEdit(row)"><Pencil :size="14" /></el-button>
              <el-button circle title="删除" @click="removeItem(row)"><Trash2 :size="14" /></el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <el-pagination v-model:current-page="store.query.page" v-model:page-size="store.query.pageSize" layout="total, prev, pager, next" :total="store.total" @current-change="store.fetchList" />
      </div>
    </GlassPanel>

    <div v-else class="inventory-cards">
      <GlassPanel v-for="item in store.list" :key="item.id" hover class="inventory-card">
        <div class="inventory-card__top">
          <button class="preview-button ripple-target" @click="preview(item)"><ProduceVisual :name="item.name" :color="item.color" size="large" /></button>
          <el-tag :type="toneOf(item.freshness)" effect="dark">{{ labelOf(item.freshness) }}</el-tag>
        </div>
        <div class="inventory-card__heading"><div><h3>{{ item.name }}</h3><span>{{ item.category }} · {{ item.location }}</span></div><strong>{{ item.quantity }}<small>{{ item.unit }}</small></strong></div>
        <div class="freshness-progress"><span :style="{ width: `${item.freshnessScore * 100}%`, background: item.color }" /></div>
        <div class="inventory-card__meta"><span>剩余 {{ item.remainingDays }} 天</span><span>{{ item.storageAdvice }}</span></div>
        <div class="inventory-card__actions"><el-button @click="openEdit(item)"><Pencil :size="14" />编辑</el-button><el-button @click="removeItem(item)"><Trash2 :size="14" />删除</el-button></div>
      </GlassPanel>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingItem ? '编辑库存' : '新增库存'" width="520px">
      <el-form label-position="top">
        <div class="form-grid">
          <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="分类"><el-select v-model="form.category"><el-option label="水果" value="水果" /><el-option label="蔬菜" value="蔬菜" /></el-select></el-form-item>
          <el-form-item label="数量"><el-input-number v-model="form.quantity" :min="0" /></el-form-item>
          <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
          <el-form-item label="保质期"><el-input-number v-model="form.shelfLife" :min="1" /></el-form-item>
          <el-form-item label="货位"><el-input v-model="form.location" /></el-form-item>
        </div>
        <el-form-item label="温湿度建议"><el-input v-model="form.storageAdvice" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="previewVisible" title="库存图片预览" width="420px" align-center>
      <div v-if="previewItem" class="preview-dialog">
        <ProduceVisual :name="previewItem.name" :color="previewItem.color" size="large" />
        <h3>{{ previewItem.name }}</h3>
        <p>{{ previewItem.location }} · 新鲜度 {{ Math.round(previewItem.freshnessScore * 100) }}%</p>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.inventory-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px; }
.inventory-stat { display: flex; align-items: center; gap: 13px; }
.stat-light { width: 8px; height: 38px; border-radius: 99px; }
.inventory-stat small, .inventory-stat strong { display: block; }
.inventory-stat small { color: var(--text-3); font-size: 10px; }
.inventory-stat strong { margin-top: 5px; color: var(--text-1); font-size: 20px; }
.inventory-stat em { margin-left: 4px; color: var(--text-3); font-size: 9px; font-style: normal; font-weight: 500; }
.view-switch { display: flex; padding: 3px; border: 1px solid var(--stroke); border-radius: 11px; background: var(--surface-soft); }
.view-switch button { display: grid; width: 32px; height: 30px; place-items: center; border: 0; border-radius: 8px; color: var(--text-3); background: transparent; }
.view-switch button.active { color: white; background: linear-gradient(135deg, var(--blue), #6c63ff); box-shadow: 0 5px 15px rgba(79,140,255,.25); }
.filter-panel { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 12px; }
.filter-main { display: grid; flex: 1; grid-template-columns: minmax(220px, 1fr) 140px 150px auto; gap: 9px; }
.filter-panel > span { color: var(--text-3); font-size: 10px; white-space: nowrap; }
.table-panel { overflow: hidden; }
.produce-cell { display: flex; align-items: center; gap: 10px; padding: 0; border: 0; color: inherit; text-align: left; background: transparent; }
.produce-cell span strong, .produce-cell span small { display: block; }
.produce-cell span strong { color: var(--text-1); font-size: 11px; }
.produce-cell span small { margin-top: 4px; color: var(--text-3); font-size: 9px; }
.qty { color: var(--text-1); font-size: 13px; }
.days-cell strong { margin-right: 4px; font-size: 15px; }
.days-cell span { color: var(--text-3); font-size: 9px; }
.days-cell.is-fresh strong { color: var(--green); }.days-cell.is-warning strong { color: var(--orange); }.days-cell.is-spoiled strong { color: var(--red); }
.table-actions { display: flex; gap: 5px; }
.pagination-bar { display: flex; justify-content: flex-end; padding: 13px 16px; border-top: 1px solid var(--stroke); }
.inventory-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.inventory-card { overflow: hidden; }
.inventory-card__top { position: relative; display: flex; justify-content: center; }
.inventory-card__top .el-tag { position: absolute; top: 8px; right: 8px; }
.preview-button { padding: 0; border: 0; border-radius: 18px; background: transparent; }
.inventory-card__heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; margin-top: 13px; }
.inventory-card__heading h3 { margin: 0; color: var(--text-1); font-size: 14px; }
.inventory-card__heading span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }
.inventory-card__heading > strong { color: var(--text-1); font-size: 24px; }
.inventory-card__heading small { margin-left: 3px; color: var(--text-3); font-size: 9px; }
.freshness-progress { height: 5px; margin-top: 13px; overflow: hidden; border-radius: 99px; background: var(--surface-soft); }
.freshness-progress span { display: block; height: 100%; border-radius: inherit; }
.inventory-card__meta { display: flex; justify-content: space-between; gap: 8px; margin-top: 9px; color: var(--text-3); font-size: 9px; }
.inventory-card__actions { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin-top: 13px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 14px; }
.form-grid :deep(.el-select), .form-grid :deep(.el-input-number) { width: 100%; }
.preview-dialog { display: grid; justify-items: center; text-align: center; }
.preview-dialog h3 { margin: 16px 0 0; color: var(--text-1); }
.preview-dialog p { margin: 7px 0 0; color: var(--text-3); font-size: 11px; }
@media (max-width: 1300px) { .inventory-cards { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 980px) { .inventory-stats { grid-template-columns: repeat(2, 1fr); } .filter-main { grid-template-columns: 1fr 1fr; } .inventory-cards { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 620px) { .inventory-stats, .inventory-cards { grid-template-columns: 1fr; } .filter-panel { align-items: stretch; flex-direction: column; } .filter-main { grid-template-columns: 1fr; } .form-grid { grid-template-columns: 1fr; } }
</style>

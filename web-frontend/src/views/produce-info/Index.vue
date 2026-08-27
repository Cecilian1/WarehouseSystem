<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Save } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import { produceApi } from '@/api'
import type { ProduceItem, ProducePayload } from '@/types'

const items = ref<ProduceItem[]>([])
const selectedId = ref<number | null>(null)
const saving = ref(false)
const form = reactive<ProducePayload>({
  name: '',
  category: '',
  shelfLifeDays: 0,
  idealTempRange: '',
  iconUrl: '',
})

const load = async () => {
  const response = await produceApi.getList()
  items.value = response.data
}

const selectItem = (item: ProduceItem) => {
  selectedId.value = item.id
  Object.assign(form, {
    name: item.name,
    category: item.category,
    shelfLifeDays: item.shelfLifeDays,
    idealTempRange: item.idealTempRange,
    iconUrl: item.iconUrl,
  })
}

const createNew = () => {
  selectedId.value = null
  Object.assign(form, {
    name: '',
    category: '',
    shelfLifeDays: 0,
    idealTempRange: '',
    iconUrl: '',
  })
}

const save = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请输入果蔬名称')
    return
  }

  saving.value = true
  try {
    if (selectedId.value === null) {
      await produceApi.create({ ...form })
    } else {
      await produceApi.update(selectedId.value, { ...form })
    }
    await load()
    createNew()
    ElMessage.success('果蔬信息已保存')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="produce-info-page">
    <PageHeader title="信息录入" />

    <div class="produce-layout">
      <GlassPanel padding="none" class="produce-table">
        <el-table
          :data="items"
          height="calc(100vh - 220px)"
          min-height="420"
          highlight-current-row
          @row-click="selectItem"
        >
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="category" label="分类" min-width="110" />
          <el-table-column prop="currentQty" label="库存数量" min-width="120" />
          <el-table-column prop="earliestExpireDate" label="最早过期日期" min-width="160" />
        </el-table>
      </GlassPanel>

      <GlassPanel class="produce-form">
        <h2>{{ selectedId === null ? '新增果蔬信息' : '编辑果蔬信息' }}</h2>
        <el-form label-position="top" class="form-body">
          <el-form-item label="名称">
            <el-input v-model="form.name" />
          </el-form-item>
          <el-form-item label="分类">
            <el-input v-model="form.category" />
          </el-form-item>
          <el-form-item label="保质期(天)">
            <el-input-number v-model="form.shelfLifeDays" :min="0" :max="3650" />
          </el-form-item>
          <el-form-item label="建议温湿度区间">
            <el-input v-model="form.idealTempRange" />
          </el-form-item>
          <div class="form-actions">
            <el-button @click="createNew"><Plus :size="15" />新增</el-button>
            <el-button type="primary" :loading="saving" @click="save">
              <Save :size="15" />保存
            </el-button>
          </div>
        </el-form>
      </GlassPanel>
    </div>
  </div>
</template>

<style scoped>
.produce-layout {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr);
  gap: 14px;
}

.produce-table {
  overflow: hidden;
}

.produce-form {
  min-height: 420px;
}

.produce-form h2 {
  margin: 0 0 20px;
  color: var(--text-1);
  font-size: 15px;
}

.form-body :deep(.el-input-number) {
  width: 100%;
}

.form-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 8px;
}

.form-actions .el-button {
  width: 100%;
  margin: 0;
}

@media (max-width: 900px) {
  .produce-layout {
    grid-template-columns: 1fr;
  }
}
</style>

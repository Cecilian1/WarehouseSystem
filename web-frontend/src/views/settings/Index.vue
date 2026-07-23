<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { Bell, CircleUserRound, Database, KeyRound, Link2, LockKeyhole, Moon, Network, Save, ShieldCheck, SlidersHorizontal, Sun, UserPlus, Webhook } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassPanel from '@/components/common/GlassPanel.vue'
import { settingsApi } from '@/api'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const activeTab = ref('general')
const saving = ref(false)
const form = reactive({
  systemName: '芯鲜管家',
  deviceName: '家庭智能冰箱 01',
  language: 'zh-CN',
  theme: appStore.theme,
  notification: true,
  sound: false,
  desktop: true,
  expiryDays: 2,
  tempHigh: 8,
  humidityHigh: 95,
  duration: 10,
  apiUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws/notify',
  syncInterval: 5,
  token: '••••••••••••••••',
})

const users = [
  { name: '系统管理员', account: 'admin', role: '超级管理员', state: '启用', last: '2026-07-20 20:22' },
  { name: '演示账号', account: 'demo', role: '只读观察员', state: '启用', last: '2026-07-20 18:06' },
  { name: '设备维护员', account: 'operator', role: '运维人员', state: '启用', last: '2026-07-19 16:42' },
]

watch(() => form.theme, (value) => appStore.applyTheme(value))

const save = async () => {
  saving.value = true
  try {
    await settingsApi.save(form as unknown as Record<string, unknown>)
    ElMessage.success('系统设置已保存')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <PageHeader eyebrow="SYSTEM CONFIGURATION" title="系统设置" description="账号权限、通知策略、预警阈值与服务连接配置">
      <template #actions><el-button type="primary" :loading="saving" @click="save"><Save :size="15" />保存设置</el-button></template>
    </PageHeader>

    <div class="settings-layout">
      <GlassPanel class="settings-nav" padding="small">
        <button v-for="item in [
          {key:'general',label:'基础设置',icon:SlidersHorizontal},
          {key:'accounts',label:'账号管理',icon:CircleUserRound},
          {key:'permissions',label:'权限管理',icon:ShieldCheck},
          {key:'notifications',label:'通知设置',icon:Bell},
          {key:'thresholds',label:'预警阈值',icon:SlidersHorizontal},
          {key:'connections',label:'服务连接',icon:Network},
        ]" :key="item.key" :class="{ active: activeTab === item.key }" @click="activeTab = item.key">
          <component :is="item.icon" :size="16" /><span>{{ item.label }}</span>
        </button>
      </GlassPanel>

      <div class="settings-content">
        <GlassPanel v-if="activeTab === 'general'" class="settings-panel">
          <div class="settings-heading"><div><h2>基础设置</h2><span>系统标识与界面偏好</span></div><SlidersHorizontal :size="18" /></div>
          <el-form label-position="top" class="settings-form">
            <div class="settings-form-grid">
              <el-form-item label="系统名称"><el-input v-model="form.systemName" /></el-form-item>
              <el-form-item label="设备显示名称"><el-input v-model="form.deviceName" /></el-form-item>
              <el-form-item label="界面语言"><el-select v-model="form.language"><el-option label="简体中文" value="zh-CN" /><el-option label="English" value="en-US" /></el-select></el-form-item>
            </div>
            <el-form-item label="外观主题">
              <div class="theme-options">
                <button :class="{ active: form.theme === 'dark' }" type="button" @click="form.theme = 'dark'"><span class="theme-preview dark-preview"><Moon :size="20" /></span><strong>深色模式</strong><small>展厅与大屏推荐</small></button>
                <button :class="{ active: form.theme === 'light' }" type="button" @click="form.theme = 'light'"><span class="theme-preview light-preview"><Sun :size="20" /></span><strong>浅色模式</strong><small>日常管理推荐</small></button>
              </div>
            </el-form-item>
          </el-form>
        </GlassPanel>

        <GlassPanel v-else-if="activeTab === 'accounts'" class="settings-panel">
          <div class="settings-heading"><div><h2>账号管理</h2><span>管理员与观察员账号</span></div><el-button type="primary"><UserPlus :size="14" />添加账号</el-button></div>
          <el-table :data="users" class="settings-table">
            <el-table-column label="用户" min-width="170"><template #default="{ row }"><div class="user-cell"><span>{{ row.name.slice(0,1) }}</span><div><strong>{{ row.name }}</strong><small>{{ row.account }}</small></div></div></template></el-table-column>
            <el-table-column prop="role" label="角色" min-width="150" />
            <el-table-column prop="state" label="状态" width="100"><template #default><span class="enabled-status">启用</span></template></el-table-column>
            <el-table-column prop="last" label="最后登录" min-width="170" />
            <el-table-column label="操作" width="100"><template #default><el-button link type="primary">编辑</el-button></template></el-table-column>
          </el-table>
        </GlassPanel>

        <GlassPanel v-else-if="activeTab === 'permissions'" class="settings-panel">
          <div class="settings-heading"><div><h2>权限管理</h2><span>基于角色的访问控制</span></div><LockKeyhole :size="18" /></div>
          <div class="permission-grid">
            <div v-for="role in [
              {name:'超级管理员',desc:'拥有所有页面与系统配置权限',count:1,color:'#4f8cff'},
              {name:'运维人员',desc:'设备、日志、环境与预警处置',count:1,color:'#14b8a6'},
              {name:'只读观察员',desc:'仅可查看看板与历史数据',count:1,color:'#f59e0b'}
            ]" :key="role.name" class="permission-card">
              <div class="role-icon" :style="{color:role.color,background:`color-mix(in srgb, ${role.color} 12%, transparent)`}"><KeyRound :size="18" /></div>
              <h3>{{ role.name }}</h3><p>{{ role.desc }}</p><span>{{ role.count }} 个账号</span><el-button>配置权限</el-button>
            </div>
          </div>
        </GlassPanel>

        <GlassPanel v-else-if="activeTab === 'notifications'" class="settings-panel">
          <div class="settings-heading"><div><h2>通知设置</h2><span>控制预警消息的触达方式</span></div><Bell :size="18" /></div>
          <div class="switch-list">
            <label><span><Bell :size="17" /><div><strong>预警通知</strong><small>接收保质期、环境和设备异常消息</small></div></span><el-switch v-model="form.notification" /></label>
            <label><span><Webhook :size="17" /><div><strong>桌面通知</strong><small>浏览器允许时显示系统级通知</small></div></span><el-switch v-model="form.desktop" /></label>
            <label><span><Bell :size="17" /><div><strong>声音提醒</strong><small>严重预警到达时播放提示音</small></div></span><el-switch v-model="form.sound" /></label>
          </div>
        </GlassPanel>

        <GlassPanel v-else-if="activeTab === 'thresholds'" class="settings-panel">
          <div class="settings-heading"><div><h2>预警阈值</h2><span>端侧规则与持续时间设置</span></div><SlidersHorizontal :size="18" /></div>
          <el-form label-position="top" class="threshold-form">
            <el-form-item label="临期提前提醒"><div class="slider-row"><el-slider v-model="form.expiryDays" :min="1" :max="7" show-stops /><el-input-number v-model="form.expiryDays" :min="1" :max="7" /><span>天</span></div></el-form-item>
            <el-form-item label="温度高位阈值"><div class="slider-row"><el-slider v-model="form.tempHigh" :min="4" :max="15" :step="0.5" /><el-input-number v-model="form.tempHigh" :min="4" :max="15" :step="0.5" /><span>°C</span></div></el-form-item>
            <el-form-item label="湿度高位阈值"><div class="slider-row"><el-slider v-model="form.humidityHigh" :min="85" :max="100" /><el-input-number v-model="form.humidityHigh" :min="85" :max="100" /><span>%RH</span></div></el-form-item>
            <el-form-item label="异常持续时间"><div class="slider-row"><el-slider v-model="form.duration" :min="1" :max="30" /><el-input-number v-model="form.duration" :min="1" :max="30" /><span>分钟</span></div></el-form-item>
          </el-form>
        </GlassPanel>

        <GlassPanel v-else class="settings-panel">
          <div class="settings-heading"><div><h2>服务连接</h2><span>FastAPI、WebSocket 与本地数据库</span></div><Link2 :size="18" /></div>
          <el-form label-position="top" class="connection-form">
            <el-form-item label="FastAPI 地址"><el-input v-model="form.apiUrl"><template #prefix><Network :size="14" /></template></el-input></el-form-item>
            <el-form-item label="WebSocket 地址"><el-input v-model="form.wsUrl"><template #prefix><Webhook :size="14" /></template></el-input></el-form-item>
            <el-form-item label="API Token"><el-input v-model="form.token" type="password" show-password><template #prefix><KeyRound :size="14" /></template></el-input></el-form-item>
            <el-form-item label="云同步间隔"><div class="inline-control"><el-input-number v-model="form.syncInterval" :min="1" :max="60" /><span>分钟</span></div></el-form-item>
          </el-form>
          <div class="connection-status">
            <div><Database :size="17" /><span><strong>SQLite 本地数据库</strong><small>/data/warehousekeeper/warehousekeeper.db</small></span><b>已连接</b></div>
            <div><Network :size="17" /><span><strong>FastAPI 服务</strong><small>{{ form.apiUrl }}</small></span><b>Mock 模式</b></div>
            <div><Webhook :size="17" /><span><strong>WebSocket 推送</strong><small>{{ form.wsUrl }}</small></span><b>实时</b></div>
          </div>
        </GlassPanel>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-layout { display: grid; grid-template-columns: 210px 1fr; align-items: start; gap: 14px; }
.settings-nav { position: sticky; top: calc(var(--header-height) + 20px); display: grid; gap: 5px; }.settings-nav button { display: flex; align-items: center; gap: 10px; min-height: 42px; padding: 0 12px; border: 1px solid transparent; border-radius: 10px; color: var(--text-2); background: transparent; }.settings-nav button:hover { background: var(--surface-soft); }.settings-nav button.active { border-color: rgba(79,140,255,.2); color: white; background: linear-gradient(90deg, rgba(79,140,255,.22), rgba(56,189,248,.08)); }
:root[data-theme='light'] .settings-nav button.active { color: var(--text-1); }.settings-nav span { font-size: 11px; }
.settings-panel { min-height: 480px; }.settings-heading { display: flex; align-items: flex-start; justify-content: space-between; color: var(--cyan); padding-bottom: 16px; border-bottom: 1px solid var(--stroke); }.settings-heading h2 { margin: 0; color: var(--text-1); font-size: 15px; }.settings-heading span { display: block; margin-top: 5px; color: var(--text-3); font-size: 9px; }
.settings-form, .connection-form, .threshold-form { margin-top: 20px; }.settings-form-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }.settings-form-grid :deep(.el-select) { width: 100%; }
.theme-options { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; width: 100%; }.theme-options button { display: grid; grid-template-columns: 76px 1fr; grid-template-rows: 1fr 1fr; gap: 2px 13px; align-items: center; padding: 10px; border: 1px solid var(--stroke); border-radius: 13px; color: var(--text-2); text-align: left; background: var(--surface-soft); }.theme-options button.active { border-color: rgba(79,140,255,.55); box-shadow: 0 0 0 3px rgba(79,140,255,.1); }.theme-preview { display: grid; grid-row: 1/3; width: 76px; height: 52px; place-items: center; border-radius: 9px; }.dark-preview { color: #83d7ff; background: linear-gradient(145deg,#0f172a,#20334e); }.light-preview { color: #f59e0b; background: linear-gradient(145deg,#f8fafc,#dce8f3); }.theme-options strong { align-self: end; color: var(--text-1); font-size: 11px; }.theme-options small { align-self: start; color: var(--text-3); font-size: 8px; }
.user-cell { display: flex; align-items: center; gap: 10px; }.user-cell > span { display: grid; width: 32px; height: 32px; place-items: center; border-radius: 9px; color: white; font-size: 10px; background: linear-gradient(145deg,var(--blue),var(--teal)); }.user-cell strong, .user-cell small { display: block; }.user-cell strong { color: var(--text-1); font-size: 10px; }.user-cell small { margin-top: 3px; color: var(--text-3); font-size: 8px; }.enabled-status { color: #82eea7; font-size: 9px; }.settings-table { margin-top: 14px; }
.permission-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 18px; }.permission-card { padding: 16px; border: 1px solid var(--stroke); border-radius: 13px; background: var(--surface-soft); }.role-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 12px; }.permission-card h3 { margin: 14px 0 0; color: var(--text-1); font-size: 12px; }.permission-card p { min-height: 32px; margin: 7px 0; color: var(--text-3); font-size: 9px; line-height: 1.7; }.permission-card > span { color: var(--text-2); font-size: 9px; }.permission-card .el-button { width: 100%; margin-top: 14px; }
.switch-list { display: grid; margin-top: 10px; }.switch-list label { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 4px; border-bottom: 1px solid var(--stroke); }.switch-list label > span { display: flex; align-items: center; gap: 12px; color: var(--cyan); }.switch-list strong, .switch-list small { display: block; }.switch-list strong { color: var(--text-1); font-size: 11px; }.switch-list small { margin-top: 4px; color: var(--text-3); font-size: 8px; }
.slider-row { display: grid; width: 100%; grid-template-columns: 1fr 130px 42px; align-items: center; gap: 14px; }.slider-row span { color: var(--text-3); font-size: 9px; }
.connection-form { max-width: 720px; }.inline-control { display: flex; align-items: center; gap: 9px; }.inline-control span { color: var(--text-3); font-size: 9px; }
.connection-status { display: grid; gap: 8px; margin-top: 22px; padding-top: 18px; border-top: 1px solid var(--stroke); }.connection-status > div { display: grid; grid-template-columns: 35px 1fr auto; align-items: center; gap: 10px; padding: 11px; border-radius: 11px; color: var(--cyan); background: var(--surface-soft); }.connection-status strong, .connection-status small { display: block; }.connection-status strong { color: var(--text-1); font-size: 10px; }.connection-status small { margin-top: 4px; color: var(--text-3); font-size: 8px; }.connection-status b { color: #82eea7; font-size: 9px; }
@media (max-width: 900px) { .settings-layout { grid-template-columns: 1fr; }.settings-nav { position: static; display: flex; overflow-x: auto; }.settings-nav button { flex: 0 0 auto; }.settings-form-grid, .permission-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 620px) { .settings-form-grid, .permission-grid, .theme-options { grid-template-columns: 1fr; }.slider-row { grid-template-columns: 1fr 100px 36px; } }
</style>

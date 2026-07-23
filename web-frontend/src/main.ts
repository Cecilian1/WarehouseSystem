import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import router from '@/router'
import App from './App.vue'
import './styles/index.css'
import './styles/element-overrides.css'
import { useAppStore } from '@/stores/app'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

const appStore = useAppStore()
appStore.init()

document.addEventListener('click', (event) => {
  const target = event.target as HTMLElement
  const button = target.closest<HTMLElement>('.el-button, .ripple-target')
  if (!button || button.dataset.ripple === 'off') return
  button.style.position = button.style.position || 'relative'
  button.style.overflow = 'hidden'
  const rect = button.getBoundingClientRect()
  const ripple = document.createElement('span')
  ripple.className = 'ripple-effect'
  ripple.style.left = `${event.clientX - rect.left}px`
  ripple.style.top = `${event.clientY - rect.top}px`
  button.appendChild(ripple)
  window.setTimeout(() => ripple.remove(), 600)
})

app.mount('#app')

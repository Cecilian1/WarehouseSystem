// 将仓库根目录 .env 中的 MINIPROGRAM_* 配置同步进小程序源码。
//
// 微信小程序运行时不支持读取 .env 文件，config/index.js 和
// project.config.json 里的 appid 必须是写死的静态值，所以改完 .env 后
// 需要手动执行一次本脚本，把值写回这两个文件。
//
// 用法：node scripts/sync-miniprogram-config.js

const fs = require('fs')
const path = require('path')

const projectRoot = path.join(__dirname, '..')
const envPath = path.join(projectRoot, '.env')
const configPath = path.join(projectRoot, 'wechat-miniprogram', 'config', 'index.js')
const projectConfigPath = path.join(projectRoot, 'wechat-miniprogram', 'project.config.json')

function loadEnv(filePath) {
  const env = {}
  const content = fs.readFileSync(filePath, 'utf-8')
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const idx = line.indexOf('=')
    if (idx === -1) continue
    const key = line.slice(0, idx).trim()
    const value = line.slice(idx + 1).trim()
    if (value) env[key] = value
  }
  return env
}

if (!fs.existsSync(envPath)) {
  console.error(`未找到 ${envPath}，请先复制 .env.example 为 .env`)
  process.exit(1)
}

const env = loadEnv(envPath)
const required = ['MINIPROGRAM_APPID', 'MINIPROGRAM_BASE_URL', 'MINIPROGRAM_WS_URL']
const missing = required.filter((key) => !env[key])
if (missing.length) {
  console.error(`.env 中缺少以下配置项: ${missing.join(', ')}`)
  process.exit(1)
}

let configSrc = fs.readFileSync(configPath, 'utf-8')
configSrc = configSrc.replace(/baseUrl:\s*'[^']*'/, `baseUrl: '${env.MINIPROGRAM_BASE_URL}'`)
configSrc = configSrc.replace(/wsUrl:\s*'[^']*'/, `wsUrl: '${env.MINIPROGRAM_WS_URL}'`)
fs.writeFileSync(configPath, configSrc)
console.log(`已更新 ${path.relative(projectRoot, configPath)}`)

const projectConfig = JSON.parse(fs.readFileSync(projectConfigPath, 'utf-8'))
projectConfig.appid = env.MINIPROGRAM_APPID
fs.writeFileSync(projectConfigPath, JSON.stringify(projectConfig, null, 2) + '\n')
console.log(`已更新 ${path.relative(projectRoot, projectConfigPath)} 的 appid`)

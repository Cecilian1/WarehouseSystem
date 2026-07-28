# 芯鲜管家微信小程序前端

这是“芯鲜管家”项目的原生微信小程序前端，放在独立目录
`wechat-miniprogram/`，不影响现有 `qt-frontend/` 和 `web-frontend/`。

## 运行方式

1. 打开微信开发者工具
2. 导入本目录 `wechat-miniprogram/`
3. AppID 可先使用测试号或 `touristappid`
4. 直接编译运行

## 数据接入

`mock/data.js` 可用于纯前端演示，覆盖：

- 10 种果蔬库存
- 20 条出入库记录
- 8 条食品预警
- 4 条设备异常预警
- 7 天温湿度趋势
- 3 台设备
- 1 组完整 AI 识别结果

当前联调架构由 Windows 后端统一服务 Web 和小程序，并由 Windows 后端每
5 秒从开发板拉取数据。修改 `config/index.js`：

```js
module.exports = {
  enableMock: false,
  enableDemoLogin: true,
  baseUrl: 'http://Windows局域网IP:8000/api',
  wsUrl: 'ws://Windows局域网IP:8000/ws/notify'
}
```

本地联调脚本 `deploy/run_server_on_windows.ps1` 会显式启用受控演示登录。
正式环境必须把 `WAREHOUSE_ALLOW_DEMO_LOGIN` 关闭，并配置
`WAREHOUSE_WECHAT_APPID`、`WAREHOUSE_WECHAT_APP_SECRET`，小程序登录页
会通过 `wx.login()` 获取临时 code。

正式小程序发布需把接口改为 HTTPS 合法域名。

## 页面

- 启动页
- 登录与设备绑定
- 首页智能看板
- 库存列表
- 果蔬详情
- AI 识别
- 预警中心
- 环境监测
- 出入库记录
- 消息详情
- 我的
- 设备管理

## 与开发板功能的对应

- `env_log` 对应环境监测与首页环境卡片
- `alert_record` 对应预警中心与消息详情
- `produce_info`、`stock_summary` 对应库存列表与果蔬详情
- `inventory_log` 对应出入库记录
- `pending_frames` / AI 服务输出对应 AI 识别页

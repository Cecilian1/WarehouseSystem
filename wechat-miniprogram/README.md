# 芯鲜管家微信小程序前端

这是“芯鲜管家”项目的原生微信小程序前端，放在独立目录
`wechat-miniprogram/`，不影响现有 `qt-frontend/` 和 `web-frontend/`。

## 运行方式

1. 打开微信开发者工具
2. 导入本目录 `wechat-miniprogram/`
3. AppID 可先使用测试号或 `touristappid`
4. 直接编译运行

## 数据接入

默认使用 `mock/data.js`，覆盖：

- 10 种果蔬库存
- 20 条出入库记录
- 8 条食品预警
- 4 条设备异常预警
- 7 天温湿度趋势
- 3 台设备
- 1 组完整 AI 识别结果

后续接入开发板 FastAPI 时，修改 `config/index.js`：

```js
module.exports = {
  enableMock: false,
  baseUrl: 'http://开发板IP:8000/api',
  wsUrl: 'ws://开发板IP:8000/ws'
}
```

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

# 真机验证清单

本机（Windows）禁止编译/运行任何代码，以下全部步骤需**由开发者在Ubuntu
主机/开发板上执行**。

## Qt前端

- [ ] `qmake && make -j16` 交叉编译通过，`file`命令确认产物为LoongArch架构
- [ ] scp部署到板子，`chmod +x`后能启动，LCD上显示出5个页面框架+顶部环境状态条
- [ ] 触摸各导航按钮，`QStackedWidget`能正确切换页面
- [ ] `ProduceInfoPage`触摸输入框后，自绘虚拟键盘能正常输入字符/退格
- [ ] `AlertPage`选中一行后点击"标记为已处理"，数据库`alert_record.is_read`
      正确更新为1，界面刷新后该行状态变化
- [ ] Qt程序与camera_service/env_service同时运行时，反复触摸刷新页面，
      检查程序日志/stderr确认无"database is locked"报错

## camera_service

- [ ] `ls /dev/video*` 确认实际设备节点名，如与配置的`/dev/video-camera0`
      不同需更新`camera_service.yaml`的`camera_device`项
- [ ] 手动前台运行 `python3 -m backend.camera_service.main`，观察日志是否
      按`capture_interval_sec`周期性触发补光→拍照→差分计算
- [ ] 人为在摄像头前移动/放置物体，确认`change_ratio`超过阈值后
      `pending_frames`表新增记录：
      `sqlite3 warehousekeeper.db "SELECT * FROM pending_frames ORDER BY id DESC LIMIT 5;"`
- [ ] 确认`frame_save_dir`（默认`/data/warehousekeeper/frames`）下生成了
      对应图片文件，且图片内容与拍摄场景一致
- [ ] `led_gpio`配置的GPIO编号确认对应物理LED能正确点亮/熄灭
- [ ] `systemctl daemon-reload && systemctl enable --now camera-service`，
      `systemctl status camera-service`确认Active(running)

## env_service

- [ ] `i2cdetect -y 3` 确认能在预期地址（0x44或0x45）探测到SHT30；若无法
      探测到，考虑是否需要切换到JP7软件I2C方案（见hardware-notes.md）
- [ ] **核实`sht30_driver.py`中的测量命令字节**：对照Sensirion SHT30官方
      datasheet的"Measurement Commands"表，确认`CMD_MEASURE_MSB`/
      `CMD_MEASURE_LSB`/`MEASURE_WAIT_SEC`取值正确后再运行
- [ ] 手动前台运行 `python3 -m backend.env_service.main`，观察是否按
      `read_interval_sec`周期打印温湿度读数，且数值在合理范围（室温附近）
- [ ] `sqlite3`确认`env_log`表持续新增记录且`recorded_at`时间戳递增准确
- [ ] 人为制造高温环境（如靠近热源）测试超过`temp_high_threshold_c`并
      持续`abnormal_duration_sec`后，`alert_record`表是否正确插入一条
      `alert_type='device_abnormal'`记录，且温度恢复正常后不再重复插入
- [ ] systemd部署与状态检查同camera_service

## 跨模块联调

- [ ] 三个进程同时长时间运行（建议30分钟以上），检查`.db-wal`文件大小是否
      正常（WAL会周期性checkpoint，若持续异常增长需检查是否有长事务未提交）
- [ ] Qt前端`EnvStatusCard`显示的温湿度与`env_service`最新写入`env_log`
      的数据一致
- [ ] env_service生成设备异常告警后，Qt前端`AlertPage`能正确展示该条记录
- [ ] camera_service触发变化并写入`pending_frames`后，Qt前端`RecognitionPage`
      能展示对应图片

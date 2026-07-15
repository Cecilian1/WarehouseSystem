# 跨模块接口契约

本文档记录本次任务交付的表结构中，为**未来AI服务模块**（YOLOv11n检测 +
MobileNetV3新鲜度分类，不在本次任务范围）预留的对接约定，避免后续任务
需要重新设计接口。

## pending_frames 表（camera_service生产，AI服务消费）

```sql
CREATE TABLE pending_frames (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path    TEXT NOT NULL,
    change_ratio  REAL,
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending / processed / discarded
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    processed_at  TEXT
);
```

**契约**：
- camera_service检测到画面变化超过阈值时，保存图片到`frame_save_dir`配置目录，
  并`INSERT`一条`status='pending'`的记录。camera_service**只负责INSERT**，
  不会再修改这条记录。
- 未来AI服务模块应定期执行：
  ```sql
  SELECT * FROM pending_frames WHERE status = 'pending' ORDER BY id;
  ```
  取出待处理帧，完成YOLOv11n检测+MobileNetV3新鲜度分类后：
  1. 将处理结果写入`inventory_log`表（见下）
  2. 将本条`pending_frames`记录更新为：
     ```sql
     UPDATE pending_frames SET status = 'processed', processed_at = datetime('now','localtime')
     WHERE id = ?;
     ```
- Qt前端的`RecognitionPage`会展示`pending_frames`最新一条记录的图片与
  `status`字段，`status='pending'`时显示"等待AI识别服务接入"占位文本。

## inventory_log 表（AI服务模块预期写入，本次任务已建表但不写入）

表结构见`backend/common/schema.sql`。字段`freshness_level`/`freshness_score`/
`confidence`需要AI推理结果才能产出，camera_service/env_service均不具备
生成这些字段的能力，因此本次任务**只建表，不写入任何数据**。

Qt前端的`HistoryPage`会读取这张表用于"操作时间与保质期数据管理"展示，
骨架阶段该表为空是预期行为；开发者可手动`INSERT`测试数据验证UI效果，
例如：

```sql
INSERT INTO produce_info (name, category, shelf_life_days) VALUES ('苹果', '果类', 14);
INSERT INTO inventory_log (produce_id, action_type, quantity, freshness_level, created_at)
VALUES (1, 'IN', 3, '新鲜', datetime('now','localtime'));
```

## Qt前端预留的AI结果信号

`qt-frontend/pages/recognitionpage.h` 中声明了信号：

```cpp
void recognitionResultAvailable(int frameId, const QString &category, float confidence);
```

当前没有任何代码`emit`这个信号（本次任务范围不包含AI推理）。未来AI服务
模块接入方式的建议（不限于此）：新增一个轮询`pending_frames.status`变化
的组件，处理完成后触发该信号，`RecognitionPage::onRecognitionResultAvailable`
已经实现好了展示逻辑的占位骨架，接入时只需要决定"谁来emit"，不需要改动
页面本身。

## env_log / alert_record（env_service已实现，供AI服务模块的"新鲜度动态修正"参考）

docx方案3.2.1节描述了"温湿度数据用于新鲜度动态修正"的融合逻辑（结合
`produce_info.ideal_temp_range`与入库以来的温湿度暴露历史计算"有效剩余
保质期"），该融合计算本次任务不实现，但`env_log`表已按周期持续写入
真实温湿度数据，为未来实现该融合逻辑提供了数据基础。


## 已实现任务

### 已交付的三个模块

#### 1. **本地终端屏幕**
- **目录**：`qt-frontend/`
- **技术栈**：Qt Widgets（C++）
- **功能**：
  - LCD触摸屏（7寸IPS RGB 1024×600）UI交互
  - 本地数据显示和管理
  - 虚拟键盘输入支持（自绘实现，不依赖额外模块）
- **状态**： **代码完整，经编译/运行验证**
- **关键文件**：
  - `qt-frontend/WarehouseKeeper.pro`（Qt工程文件）
  - `qt-frontend/widgets/onscreenkeyboardwidget.h/.cpp`（虚拟键盘实现）
  - `qt-frontend/config/frontend.ini`（配置文件）

#### 2. **设备采集服务（摄像头）**
- **目录**：`backend/camera_service/`
- **技术栈**：Python 3 + V4L2（视频采集）
- **功能**：
  - USB UVC协议摄像头采集（640×480分辨率）
  - 帧间差分触发机制（检测物体变化）
  - 补光LED控制（GPIO驱动）
  - 采集周期：45秒/次（可配置）
- **状态**：**代码完整，经编译运行验证**
- **关键文件**：
  - `backend/camera_service/main.py`（主服务循环）
  - `backend/camera_service/camera_capture.py`（摄像头采集实现）
  - `backend/camera_service/led_control.py`（LED补光灯GPIO控制）
  - `backend/camera_service/frame_diff.py`（帧间差分检测）
  - `backend/camera_service/pending_frame_writer.py`（变化触发存储）
  - `backend/camera_service/config/camera_service.yaml`（配置文件）
- **部署方式**：systemd服务（`deploy/systemd/camera-service.service`）

#### 3. **环境监测服务**
- **目录**：`backend/env_service/`
- **技术栈**：Python 3 + I2C驱动
- **功能**：
  - **温湿度采集**（预期硬件：SHT30传感器）
  - **设备异常检测**
- **状态**：**代码框架完整，但硬件设备未接入**
- **关键文件**：
  - `backend/env_service/sht30_driver.py`
- **部署方式**：systemd服务

---

## 设备采集服务实现细节

### 摄像头采集服务（camera_service）架构

本服务负责实时采集冷柜内部画面，通过帧间差分算法检测物体变化，在满足阈值条件时落盘图片供AI推理模块消费。

#### 1. 摄像头采集实现（camera_capture.py）

**核心机制**：使用OpenCV的`cv2.VideoCapture`封装V4L2接口

```python
class CameraCapture:
    def __init__(self, device: str, resolution: tuple[int, int]):
        self.device = device          # /dev/video0（开发板摄像头设备节点）
        self.resolution = resolution  # (640, 480)
        self.cap: cv2.VideoCapture | None = None
    
    def open(self):
        # 使用V4L2接口打开摄像头设备
        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
        # 设置采集分辨率（对应config中的resolution配置）
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    def read_frame(self):
        # 读取一帧（BGR格式），返回numpy数组或None
        ok, frame = self.cap.read()
        return frame if ok else None
```

**设计要点**：
- 摄像头句柄常驻打开，避免频繁初始化开销
- 主循环只在周期触发时调用一次`read_frame()`，不做连续轮询
- 这是对单核1GHz无GPU开发板的关键CPU负载优化

#### 2. LED补光灯控制（led_control.py）

**两层降级机制**：优先使用现代`gpiod`字符设备接口，降级到传统`sysfs`方式

```python
class LedControl:
    def __init__(self, gpio_num: int, warmup_sec: float = 0.08):
        self.gpio_num = gpio_num      # GPIO编号（通过camera_service.yaml配置）
        self.warmup_sec = warmup_sec  # 补光后延时时间（确保曝光稳定）
        
    def turn_on(self):
        # 优先使用gpiod：通过/dev/gpiochip0访问GPIO
        # 降级到sysfs：/sys/class/gpio/export + direction + value
        # 点亮后延时warmup_sec秒再采集
    
    def turn_off(self):
        # LED熄灭，节能（重要：不做unexport，避免与其他进程竞争）
```

**GPIO配置说明**：
- `gpiod`路径适用于现代Linux内核（推荐）
- `sysfs`路径已在《ATK-DL2K0300嵌入式Linux C应用编程指南》第17章验证
- GPIO编号需根据实际硬件JP7扩展排针确定，在`camera_service.yaml`中配置

#### 3. 帧间差分检测（frame_diff.py）

**算法流程**（不使用复杂背景建模如MOG2，因为单核CPU无法承载）

```python
class FrameDiffDetector:
    def compute_change_ratio(self, frame: np.ndarray) -> float:
        # 步骤1：降采样（320×240），减轻计算负担
        # 步骤2：灰度化（BGR → GRAY）
        # 步骤3：高斯模糊（平滑噪声）
        # 步骤4：absdiff（与上一帧求差）
        # 步骤5：阈值二值化（threshold=25）
        # 步骤6：计算变化像素占比 = 白色像素数 / 总像素数
        # 返回 [0, 1] 之间的占比值
```

**关键参数**：
- `downsample_size: (320, 240)`：降采样尺寸
- `diff_threshold: 25`：差分二值化阈值（0-255）

#### 4. 主服务循环（main.py）

**采集周期流程**（默认45秒/次，可配置）

```python
while _running:
    cycle_start = time.monotonic()
    
    # 检查前端是否在运行（优化策略：前端不活跃时完全跳过采集）
    if not _is_frontend_active(db_path):
        time.sleep(1.0)  # 前端不活跃时每秒检查一次
        continue
    
    try:
        # 补光 → 采集 → 熄灯（完整周期控制在interval_sec内）
        led.turn_on()
        frame = camera.read_frame()
        led.turn_off()
        
        if frame is None:
            status_reporter.report(camera_ok=False)
            continue
        
        # 帧间差分检测
        change_ratio = diff_detector.compute_change_ratio(frame)
        
        # 变化超阈值则保存+登记待推理
        if change_ratio >= change_ratio_threshold:
            frame_writer.save_and_register(frame, change_ratio)
        else:
            logger.debug("变化占比%.3f未达阈值，跳过本次登记", change_ratio)
            
    except Exception:
        logger.exception("采集循环发生异常，本轮跳过")
        led.turn_off()  # 保证LED熄灭
    
    # 周期休眠（计算实际耗时，确保周期精度）
    elapsed = time.monotonic() - cycle_start
    sleep_time = max(0.0, interval_sec - elapsed)
    time.sleep(sleep_time)
```

**流程特点**：
- 前端检测：只有Qt前端正在运行时才进行采集（由`device_status.frontend_active`标志控制）
- LED优化：点亮到采集延时0.08秒，确保曝光稳定后立即关灯
- 周期精度：通过计算实际耗时来调整休眠时间，保证采集周期稳定

#### 5. 变化触发存储（pending_frame_writer.py）

**触发变化后的数据库操作**

```python
class PendingFrameWriter:
    def save_and_register(self, frame: np.ndarray, change_ratio: float) -> int:
        # 1. 保存图片到磁盘
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"frame_{timestamp}.jpg"
        image_path = str(self.frame_save_dir / filename)
        cv2.imwrite(image_path, frame)
        
        # 2. 登记到数据库pending_frames表
        cursor.execute("""
            INSERT INTO pending_frames (image_path, change_ratio, status)
            VALUES (?, ?, 'pending')
        """, (image_path, change_ratio))
        
        return cursor.lastrowid
```

**数据库集成**：
- 图片保存路径：`/data/warehousekeeper/frames/frame_YYYYMMDD_HHMMSS_MMMMMM.jpg`
- 数据库表：`pending_frames(id, image_path, change_ratio, status)`
- 状态流转：`pending` → （AI推理消费）→ `processed` 等其他状态

#### 6. 配置文件参数（camera_service.yaml）

| 配置项 | 说明 | 默认值 | 调整建议 |
|--------|------|--------|---------|
| `camera_device` | 摄像头设备节点 | `/dev/video0` | 上板后通过`ls /dev/video*`确认 |
| `resolution` | 采集分辨率 | `[640, 480]` | 不建议修改（控制CPU负载） |
| `capture_interval_sec` | 采集周期（秒） | `45` | 对应文档"30秒~1分钟"，可调整30-120 |
| `led_gpio` | 补光灯GPIO编号 | `74` | **必须实测JP7扩展排针确定** |
| `led_warmup_sec` | LED点亮到采集延时 | `0.08` | 微调可改0.05-0.1 |
| `diff_threshold` | 差分二值化阈值 | `25` | 0-255，值越大越不易触发 |
| `change_ratio_threshold` | 变化占比触发阈值 | `0.05` | 0-1，默认5%，建议0.03-0.1 |
| `diff_downsample` | 差分计算降采样尺寸 | `[320, 240]` | 不建议修改（影响CPU负载）|
| `frame_save_dir` | 图片保存目录 | `/data/warehousekeeper/frames` | 确保有足够磁盘空间 |
| `db_path` | SQLite数据库路径 | `/data/warehousekeeper/warehousekeeper.db` | 与Qt前端共用 |
| `device_id` | 设备标识符 | `fridge-01` | 支持多台冷柜时修改 |

#### 7. 系统集成

**前端状态标志**：
- camera_service检查`device_status.frontend_active`标志（由Qt前端维护）
- 当Qt前端启动时设置`frontend_active=1`
- 当Qt前端退出时设置`frontend_active=0`
- 这是避免前端不运行时浪费电力采集的优化设计

**systemd服务启动**：
```bash
systemctl enable camera-service      # 设置开机自启
systemctl start camera-service       # 启动服务
systemctl status camera-service      # 查看状态
journalctl -u camera-service -f      # 实时查看日志
```

---

## 终端屏幕（Qt前端）实现细节

### 本地终端屏幕（qt-frontend）架构

Qt前端运行在开发板上，直接驱动7寸触摸屏显示实时库存数据。

#### 1. 虚拟键盘实现（onscreenkeyboardwidget.cpp）

**自绘键盘方案**（不依赖Qt Virtual Keyboard模块）：
- 实现字母、数字、符号键盘布局
- 支持Shift切换大小写
- 支持退格、空格、回车等控制键
- 完全由C++绘制，无额外依赖

#### 2. 页面架构

- **HomePagen**：主页面，显示库存概览
- **AlertPage**：告警页面，显示温度/湿度异常
- **InventoryPage**：库存详情页面
- **DetectionPage**：检测页面，显示摄像头采集状态

#### 3. 数据库连接

- 使用SQLite本地数据库
- DatabaseManager类封装所有数据库操作
- 支持实时更新库存、告警、环境日志等表


---

## 关键问题与遗留事项

### **传感器未部署**

**状态**：传感器硬件尚未集成到开发板上，相关功能无法完整测试


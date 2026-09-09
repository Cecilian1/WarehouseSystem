# NCNN C++ AI服务

该程序是板端AI流水线的C++版本，现已从OpenCV DNN切换为NCNN推理，继续复用原有SQLite数据库与前后端数据接口。

## 推理流程

```text
pending_frames中的摄像头图片
→ NCNN YOLO检测多个果蔬
→ 按检测框裁剪
→ NCNN ShuffleNetV2三级新鲜度分类
→ 写入inventory_log
→ 现有后端API读取
→ 前端显示
```

## 使用模型

```text
/opt/warehousekeeper/models/best_ncnn_model/model.ncnn.param
/opt/warehousekeeper/models/best_ncnn_model/model.ncnn.bin
/opt/warehousekeeper/models/shufflenet_v2_freshness_ncnn_model/model.ncnn.param
/opt/warehousekeeper/models/shufflenet_v2_freshness_ncnn_model/model.ncnn.bin
```

YOLO固定输入为`640×640`；ShuffleNetV2固定输入为`224×224`，输出顺序为`fresh/mild/rotten`。

## 交叉编译

ATK-DL2K0300B 的稳定生产构建固定使用官方 NCNN `20260526`
（commit `e54f7b1f88434e1d844ea0551b880a1cfb079ce1`）。关键开关为：

```text
NCNN_RUNTIME_CPU=OFF
NCNN_LSX=ON
NCNN_LASX=OFF
NCNN_OPENMP=OFF
NCNN_PIXEL_DRAWING=OFF
NCNN_BF16=ON
NCNN_INT8=ON
NCNN_ENABLE_LTO=OFF
```

2K0300 不支持 LASX；不要在关闭 `NCNN_RUNTIME_CPU` 时启用 LASX，否则整个
静态库可能生成板端无法执行的指令。配置好工具链后，可直接运行：

```bash
git clone --depth 1 --branch 20260526 \
  https://github.com/Tencent/ncnn.git .build/ncnn-20260526
sh cpp-ai-service/build_stable_loongarch.sh
```

脚本同时构建 NCNN 和本服务，输出位于
`.build/cpp-ai-stable-loongarch/warehouse-ai-service`。

已经生成LoongArch版本NCNN：

```text
ncnnac/xbuild/install/include/ncnn
ncnnac/xbuild/install/lib/libncnn.a
ncnnac/xbuild/install/lib/cmake/ncnn
```

必须在具有龙芯交叉编译工具链、LoongArch OpenCV和SQLite3开发库的Linux环境中编译。不能把Windows x86版本OpenCV与LoongArch `libncnn.a`混合链接。

示例：

```bash
cmake -S cpp-ai-service -B build-loongarch \
  -DCMAKE_TOOLCHAIN_FILE=/path/to/loongarch64-linux-gnu.cmake \
  -Dncnn_DIR=/path/to/ncnn/xbuild/install/lib/cmake/ncnn \
  -DOpenCV_DIR=/path/to/loongarch-sysroot/opencv/lib/cmake/opencv4
cmake --build build-loongarch -j4
```

成功后得到：

```text
build-loongarch/warehouse-ai-service
```

## 板端运行

```bash
/opt/warehousekeeper/bin/warehouse-ai-service \
  --db /data/warehousekeeper/warehousekeeper.db \
  --detector /opt/warehousekeeper/models/best_ncnn_model \
  --freshness /opt/warehousekeeper/models/shufflenet_v2_freshness_ncnn_model \
  --crop-dir /data/warehousekeeper/frames/crops \
  --threads 2
```

首次验证时增加`--once`，程序只处理一个待识别帧后退出。

## 上板清单

只需上传：

```text
bin/warehouse-ai-service
models/best_ncnn_model/model.ncnn.param
models/best_ncnn_model/model.ncnn.bin
models/shufflenet_v2_freshness_ncnn_model/model.ncnn.param
models/shufflenet_v2_freshness_ncnn_model/model.ncnn.bin
```

若程序静态链接NCNN，不需要上传NCNN源码、`libncnn.a`、训练数据、`.pt`、`.pth`或ONNX文件。

## 注意事项

- 当前YOLO输出5个果蔬品类：苹果、香蕉、胡萝卜、黄瓜、橙子；最终三级新鲜度由ShuffleNetV2输出。
- 正式替换旧服务前，必须使用同一批真实图片比较ONNX旧版与NCNN新版的检测框、品类和新鲜度结果。
- 开发板第一次运行建议保留旧程序，确认NCNN结果正确后再修改systemd启动项。

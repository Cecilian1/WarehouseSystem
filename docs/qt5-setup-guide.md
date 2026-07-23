# Qt5开发环境搭建手册

面向"尚未搭建过Qt5开发环境"的开发者，本文档给出从零开始在Ubuntu主机上搭建
ATK-DL2K0300B板级Qt5交叉编译环境的完整步骤。**以下所有命令均在开发者的
Ubuntu主机/开发板上执行，本文档本身是在Windows本机撰写的交付文档。**

参考资料：正点原子《ATK-DL2K0300B嵌入式Qt5开发环境搭建V1.1》、
《ATK-DL2K0300B交叉编译器安装与使用参考手册V1.1》。

## 1. 前置检查

- Ubuntu版本：20.04 / 22.04 / 24.04 均可（官方手册以此三个版本为例）
- 磁盘空间：建议预留 ≥15GB（Qt Creator + Qt5.15.2桌面版 + 板级交叉工具链约10GB+）
- 已有基础C/C++交叉编译环境（开发者已完成，不影响本次Qt5环境搭建）

## 2. 安装Qt Creator + Qt5.15.2桌面版

从 `https://download.qt.io/archive/online_installers/4.6/` 下载在线安装器
`qt-unified-linux-x64-4.6.0-online.run`（若下载慢，可用国内镜像
`--mirror https://mirrors.aliyun.com/qt`）。

```bash
chmod +x qt-unified-linux-x64-4.6.0-online.run
./qt-unified-linux-x64-4.6.0-online.run --mirror https://mirrors.aliyun.com/qt
```

安装向导中：
- 组件勾选：Qt Creator（默认勾选）、Qt 5.15.2 → 勾选 "Desktop gcc 64-bit"
- 若提示缺少依赖库，先安装：
  ```bash
  sudo apt-get install gcc g++ lib32stdc++6 libglu1-mesa-dev \
      gstreamer1.0-plugins-base gstreamer1.0-plugins-bad gstreamer1.0-libav \
      gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-pulseaudio \
      cmake openssh-server net-tools \
      libxcb-xinerama0 libxcb-cursor0 libxcb-cursor-dev
  ```

**验证**：打开Qt Creator，`帮助→关于插件`或`工具→选项→Kits`确认Kit列表中存在
"Desktop Qt 5.15.2 GCC 64bit"。

## 3. 安装板级Qt5交叉工具链

工具链安装包 `atk-dl2k0300-toolchain-qt5-loongarch64-buildroot-linux-gnu-x86_64-20250328-v1.1.run`
（约449MB）位于开发板资料盘 **"06、开发工具.zip"** 内，需先解压该zip取出该文件，
拷贝到Ubuntu主机后执行：

```bash
chmod +x atk-dl2k0300-toolchain-qt5-loongarch64-buildroot-linux-gnu-x86_64-20250328-v1.1.run
./atk-dl2k0300-toolchain-qt5-loongarch64-buildroot-linux-gnu-x86_64-20250328-v1.1.run
```

默认安装到 `/opt/atk-dl2k0300-toolchain`（若无写权限可能需要 `sudo`）。

**验证**：

```bash
source /opt/atk-dl2k0300-toolchain/environment-setup
echo $CC $CXX
loongarch64-loongson-linux-gnu-gcc --version   # 期望输出 GCC 13.3.0
```

## 4. Qt Creator中新增自定义Kit

1. **Compilers**（工具→选项→Kits→Compilers→添加→GCC/G++）
   - C编译器：`/opt/atk-dl2k0300-toolchain/bin/loongarch64-linux-gnu-gcc`，命名如 `atk-dl2K0300-gcc`
   - C++编译器：`/opt/atk-dl2k0300-toolchain/bin/loongarch64-linux-gnu-g++`，命名如 `atk-dl2K0300-g++`

2. **Qt Versions**（Kits→Qt Versions→添加）
   - qmake路径：`/opt/atk-dl2k0300-toolchain/bin/qmake`
   - 添加后应显示为 "Qt %{Qt:Version} (atk-dl2K0300)"

3. **Devices**（Kits→Devices→添加→Remote Linux Device）
   - 填开发板IP、用户名 `root`、密码 `root`（出厂默认）
   - 点击"测试"确认SSH连通
   - 若开发板IP变更导致连接失败（旧指纹冲突），在Ubuntu主机执行：
     ```bash
     ssh-keygen -R <旧IP>
     ```

4. **组合Kit**（Kits→Kits→添加）
   - 命名如 `atk-dl2K0300`
   - Compiler关联上述C/C++编译器
   - Qt Version关联上述qmake
   - Device关联上述Remote Linux Device
   - Debugger可用默认值（本次任务不强依赖远程调试）

## 5. Hello World交叉编译验证

新建一个Qt Widgets Application测试项目，Kit勾选刚创建的 `atk-dl2K0300`
（可同时保留Desktop Kit用于本地预览UI布局）。

```
Ctrl+B  # 构建
file build-<项目名>-atk_dl2K0300-Release/<可执行文件名>   # 确认输出架构为LoongArch而非x86
```

部署运行二选一：
- Qt Creator内 `Ctrl+R` 直接通过网络部署到板子运行
- 手动scp部署：
  ```bash
  scp build-.../appname root@<板子IP>:/root/
  ssh root@<板子IP> "chmod +x /root/appname && /root/appname"
  ```

## 6. 命令行流程（不依赖Qt Creator IDE）

```bash
source /opt/atk-dl2k0300-toolchain/environment-setup
qmake WarehouseKeeper.pro
make -j16
file WarehouseKeeper   # 确认LoongArch架构
scp WarehouseKeeper root@<板子IP>:/opt/warehousekeeper/qt-frontend/
```

## 7. Qt Virtual Keyboard模块可用性确认

本项目`qt-frontend/widgets/onscreenkeyboardwidget.h/.cpp`已实现一套不依赖
额外模块的自绘虚拟键盘作为默认方案。若希望使用官方Qt Virtual Keyboard
模块（更完整的输入法体验），需先确认交叉工具链是否已包含该模块：

```bash
find /opt/atk-dl2k0300-toolchain -iname "*virtualkeyboard*"
```

若未找到，说明该模块未预编译进交叉工具链，需要开发者自行交叉编译该模块，
或继续使用本项目已提供的自绘键盘方案（无需额外工作）。

## 8. 常见问题

- **"Cannot find -lGL"**：安装 `sudo apt-get install libglu1-mesa-dev`
- **IBus输入法与Qt Creator快捷键冲突**（如Ctrl+空格被输入法吞掉）：参考官方手册1.2.2节切换到fcitx或调整IBus快捷键

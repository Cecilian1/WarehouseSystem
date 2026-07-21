# 开发环境完整搭建指南

面向"从零开始"的开发者，本文档给出在Windows本机上导入虚拟机、搭建Ubuntu开发环境、
配置网络、安装交叉编译工具链、搭建Qt5开发环境的完整步骤，最终能够交叉编译
WarehouseSystem项目并部署到ATK-DL2K0300B开发板的全流程。

**以下所有Linux命令均在Ubuntu虚拟机内执行，本文档本身是在Windows撰写的交付文档。**

## 参考资料

本文档严格按照以下正点原子官方文档编写，所有步骤、命令、配置参数均来自官方资料：

1. **《ATK-DL2K0300虚拟机使用参考手册V1.1》**
   - 来源：开发板光盘B盘-开发环境
   - 用途：虚拟机镜像导入、基础配置、交叉编译工具链使用
   - 主要内容：镜像解压、.vmx文件打开、虚拟机配置参数、Ubuntu 24.04环境

2. **《ATK-DL2K0300交叉编译器安装与使用参考手册V1.1》**
   - 来源：开发板光盘A盘-基础资料\11、用户手册\08
   - 用途：LoongArch交叉编译工具链的安装、环境变量配置、简单程序编译验证
   - 主要内容：工具链位置、GCC版本验证、C/C++编译示例

3. **《Linux开发板网络环境搭建手册V1.0》**
   - 来源：开发板光盘A盘-基础资料\11、用户手册\12
   - 用途：虚拟机与开发板的网络配置
   - 主要内容：第1.4章"通过WiFi路由器连接虚拟机和开发板通过直连"方案
   - 涵盖：防火墙配置、VMware网络设置、IP地址配置、ping测试

4. **WarehouseSystem项目文档**
   - [docs/build-and-deploy.md](build-and-deploy.md)：交叉编译和部署操作
   - [docs/hardware-notes.md](hardware-notes.md)：硬件相关信息
   - [docs/interfaces.md](interfaces.md)：系统接口规约

所有配置参数（如用户名、密码、IP地址、工具链路径等）均引用自上述官方文档，
确保开发者能够准确按照正点原子的标准流程进行环境搭建。

## 1. 虚拟机导入与基础配置

本章节严格按照《ATK-DL2K0300虚拟机使用参考手册V1.1》进行操作。

### 1.1 前置硬件和软件要求

#### Windows主机要求

- **CPU**：AMD Ryzen 7或Intel Core i7及以上（或相当配置）
- **内存**：≥16GB RAM（虚拟机推荐配置16GB）
- **磁盘空间**：≥100GB（虚拟机解压后29GB + 编译空间）
- **系统版本**：Windows 10 64位（不建议使用32位Windows，内存和性能有限）
- **虚拟化支持**：BIOS中启用VT-x（Intel）或AMD-V（AMD）

#### 虚拟机软件

- **VMware Workstation Pro**（推荐，文档以此为例）或 VMware Workstation Player（免费版）
- 下载地址：`https://www.vmware.com/`

### 1.2 虚拟机镜像获取与解压

#### 镜像位置

虚拟机镜像文件位于：**开发板光盘B盘-开发环境** 目录下，文件名包含 `ATK-DL2K0300虚拟机` 字样。

#### 镜像参数说明

| 参数 | 说明 |
|------|------|
| 镜像包压缩大小 | 5.8GB |
| 镜像包解压大小 | 29GB |
| 处理器 | 16个 |
| 内存 | 16GB |
| 硬盘 | 300GB（可后续手动扩容） |
| 网络适配器 | 桥接模式 |
| Ubuntu版本 | Ubuntu 24.04 LTS（不需要升级，升级可能导致编译错误） |
| 默认用户 | alientek |
| 默认密码 | 123 |
| root密码 | 123 |

#### 解压镜像包

1. **创建虚拟机存储目录**：在磁盘空间充足的位置（≥100GB）创建文件夹，如 `D:\VirtualMachines\ATK-DL2K0300`
2. **解压镜像**：使用7-Zip或WinRAR等工具解压镜像压缩包到该文件夹
   - 解压时间较长，请耐心等待
   - 解压完成后占用约29GB空间
3. **清理空间**：解压完成后，可将原始压缩包移到其他磁盘或删除，为虚拟机腾出更多空间

### 1.3 虚拟机导入（VMware Workstation Pro）

1. **打开VMware**，点击菜单 **文件 → 打开**
   
   ![Open VMware](images/vmware-open.png)

2. **选择.vmx文件**：导航到解压的虚拟机目录，选择 `.vmx` 文件并打开

3. **权限提示**（如有）：若提示需要获取所有权，点击 **获取所有权** 或忽略

4. **虚拟机配置**：导入后查看虚拟机配置信息（**编辑虚拟机设置** 或 **虚拟机 → 设置**）：
   - 处理器数：16个（可按实际硬件调整，但推荐保持）
   - 内存：16GB（可按实际硬件调整，但推荐保持）
   - 硬盘：300GB
   - 网络：桥接模式（可根据网络拓扑后续调整，详见第2章）

5. **启动虚拟机**：点击 **打开电源** 或按 **Ctrl+B**

6. **首次启动提示**：
   
   虚拟机首次启动时会提示："**此虚拟机可能已被移动或复制**"
   
   - **重要**：选择 **"我已复制该虚拟机"**（若选择"移动"会导致网络问题）

7. **用户登陆**：
   
   - 用户名：`alientek`
   - 密码：`123`

8. **虚拟机界面**：登陆成功后进入Ubuntu 24.04桌面环境，虚拟机基础导入完成

### 1.4 虚拟机网络和USB配置（可选）

根据第2章网络拓扑需求，可在虚拟机设置中调整：

- **网络适配器**：根据网络配置选择桥接、NAT或仅主机模式
- **USB控制器**：如需使用USB设备（如USB网卡、串口等），可在 **虚拟机 → 设置 → USB控制器** 中启用 **USB 3.1**

具体网络配置见第2章。

## 2. 网络配置

本项目网络拓扑：**Windows PC（WiFi上网） + USB以太网直连开发板**。虚拟机通过VMware配置双网卡：
- 网卡1：桥接到WiFi物理网卡（用于下载编译工具和外网访问）
- 网卡2：NAT模式（用于与开发板直连通信）

### 2.1 硬件连接和基础知识

#### 准备阶段

- Windows PC通过WiFi连接互联网
- 使用USB以太网适配器或直连网线将开发板连接到Windows PC
- 开发板出厂默认IP：`192.168.1.137`，用户名/密码：`root`/`root`

#### 网络拓扑说明

```
Windows PC
├─ WiFi: 用于外网访问（如192.168.6.43）
└─ 以太网 (USB适配器): 用于与开发板直连（如192.168.5.3）
     └─ 开发板直连（IP: 192.168.1.137 或自动分配）

虚拟机 (Ubuntu) 
├─ 网卡1 (ens33): 桥接到WiFi，获取IP（如192.168.6.76）
└─ 网卡2 (ens38): NAT模式，通过Windows与开发板通信（如192.168.5.2）
```

#### 同一网段说明

**同一网段**：指网络设备所属的子网相同。例如C类IP地址：
- 前三段相同的IP属于同一网段
- 如 `192.168.5.2` 和 `192.168.5.3` 属于同一网段，可以直接通信
- 如 `192.168.5.4` 和 `192.168.6.4` 不属于同一网段，需要通过路由转发

### 2.2 关闭防火墙

#### Windows防火墙

1. 按 Win+R，输入 `wf.msc` 打开Windows Defender防火墙
2. 点击 **关闭防火墙** → 同时关闭专用和公用网络防火墙

#### Ubuntu防火墙

在虚拟机内执行：

```bash
sudo ufw disable
```

### 2.3 VMware虚拟机网络配置

在VMware Workstation Pro中配置双网卡（**编辑 → 虚拟网络编辑器**）：

1. **网卡1（用于WiFi和外网访问）**
   - 选择 **"桥接模式"**，关联到WiFi物理网卡（不要选以太网网卡）
   - 确保 **"将主机虚拟网卡连接到此网络"** 已勾选

2. **网卡2（用于与开发板通信）**
   - 配置为 **"NAT模式"**
   - 默认会连接到 `VMnet8`，用于虚拟机与开发板直连通信

3. 在虚拟机设置（**虚拟机 → 设置 → 硬件** 标签）中：
   - 网络适配器1：选择 **"桥接"** 模式
   - 添加第二个网络适配器：选择 **"NAT"** 模式

### 2.4 Windows主机IP配置

1. 在Windows中按 Win+R，输入 `ipconfig` 查看网络适配器信息
2. 记录：
   - **WiFi适配器IP**（用于外网访问，如 `192.168.6.43`）
   - **VMware Network Adapter VMnet8** 的IP（通常由DHCP自动分配）
   - **USB以太网适配器IP**（与开发板直连，如 `192.168.5.3`）

### 2.5 Ubuntu虚拟机IP配置

#### 查看网卡信息

在虚拟机内执行：

```bash
ifconfig
```

应该能看到至少两个网卡：
- `ens33`：桥接到WiFi网卡
- `ens38`：NAT模式（连接到VMnet8）

#### 配置ens33（WiFi桥接，自动DHCP）

大多数情况下自动获得IP。若需要手动配置静态IP，编辑网络配置：

```bash
sudo nano /etc/netplan/00-installer-config.yaml
```

配置示例（假设WiFi网段为192.168.6.0/24）：

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: no
      addresses: [192.168.6.100/24]
      gateway4: 192.168.6.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

保存后应用：

```bash
sudo netplan apply
```

#### 配置ens38（NAT模式，与开发板通信）

ens38连接到VMnet8（NAT模式）。Ubuntu系统默认会自动从DHCP获得IP。若未获得，手动配置：

```bash
sudo nano /etc/netplan/00-installer-config.yaml
```

在上述配置基础上添加ens38网卡配置（假设设定为192.168.5.x网段）：

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: no
      addresses: [192.168.6.100/24]
      gateway4: 192.168.6.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
    ens38:
      dhcp4: no
      addresses: [192.168.5.2/24]
      # ens38无需网关和nameserver，只用于本地与开发板通信
```

保存后应用：

```bash
sudo netplan apply
ifconfig  # 验证ens38已获得192.168.5.2
```

### 2.6 Windows以太网网卡IP配置（与开发板直连）

1. 打开 **设置 → 网络和Internet → 高级网络选项 → 更多网络选项 → 高级设置**
2. 找到USB以太网适配器（如"Ethernet 2"），双击进入属性
3. 选中 **"Internet协议版本4(TCP/IPv4)"**，点击 **"属性"**
4. 选择 **"使用下面的IP地址"**，配置为与开发板同网段：
   - IP地址：`192.168.5.3`
   - 子网掩码：`255.255.255.0`
   - （不需要网关和DNS）

### 2.7 开发板网络配置

开发板出厂默认IP为 `192.168.1.137`。若需要改为与Windows USB网卡同网段（192.168.5.x），在开发板上执行：

```bash
# 查看当前网络接口
ifconfig

# 关闭网络并重新配置（假设网络接口为eth0）
sudo ifconfig eth0 down
sudo ifconfig eth0 192.168.5.4 netmask 255.255.255.0 up

# 验证
ifconfig
```

或使用DHCP自动分配（如果Windows DHCP服务已启用）：

```bash
udhcpc -i eth0
```

### 2.8 验证网络连通性

#### 关闭防火墙（如前所述）

Windows和Ubuntu防火墙都必须关闭。

#### ping测试

**Ubuntu → 开发板**

```bash
ping 192.168.5.4  # 或开发板配置的IP
```

**Ubuntu → 百度**（验证外网连接）

```bash
ping www.baidu.com
```

**Windows → 开发板**

在Windows命令行执行：

```powershell
ping 192.168.5.4
```

**Windows → Ubuntu**

```powershell
ping 192.168.6.100  # 或Ubuntu ens33配置的IP
```

### 2.9 小结

- **防火墙**：Windows和Ubuntu防火墙均需关闭
- **网络连接**：使用物理网线/USB网卡直连，确保直通，不经过路由
- **VMware配置**：网卡1桥接到WiFi，网卡2配置为NAT
- **Ubuntu网卡**：ens33自动DHCP获得WiFi网段IP；ens38配置为192.168.5.2（与Windows USB网卡同网段）
- **Windows网卡**：USB以太网网卡手动配置为192.168.5.3
- **开发板网卡**：配置为192.168.5.4（或通过DHCP自动分配）
- **验证方法**：各设备间互相ping，确保同网段设备能通

## 3. 前置检查

### 3.1 虚拟机基础要求

- Ubuntu版本：20.04 / 22.04 / 24.04 均可（官方手册以此三个版本为例）
- 磁盘空间：建议预留 ≥30GB（虚拟机根分区 + 交叉工具链 + Qt5 + 编译产物）
- 内存分配：≥8GB RAM（加速编译）

## 4. LoongArch交叉编译工具链说明

本章节严格按照《ATK-DL2K0300交叉编译器安装与使用参考手册V1.1》进行说明。

### 4.1 工具链已预置在虚拟机中

**重要说明**：ATK-DL2K0300开发板的交叉编译工具链 **已预置在虚拟机中**，位于：

```
/opt/atk-dl2k0300-toolchain
```

虚拟机导入后，**无需重新安装**工具链，可直接使用。

### 4.2 工具链信息

| 项目 | 说明 |
|-----|------|
| 工具链文件 | atk-dl2k0300-toolchain-qt5-loongarch64-buildroot-linux-gnu-x86_64-20250328-v1.1.run |
| 目标架构 | LoongArch64（龙芯） |
| GCC版本 | 13.3.0 |
| 包含组件 | 交叉编译器、Qt5库、构建工具等 |
| 安装位置 | `/opt/atk-dl2k0300-toolchain` |
| 来源 | 基于buildroot文件系统生成 |

### 4.3 使用交叉编译工具链

在虚拟机中编译LoongArch64架构程序前，**必须先启用环境变量**：

```bash
source /opt/atk-dl2k0300-toolchain/environment-setup
```

执行此命令后，会设置以下环境变量供编译使用：
- `$CC`：C编译器路径（`loongarch64-loongson-linux-gnu-gcc`）
- `$CXX`：C++编译器路径（`loongarch64-loongson-linux-gnu-g++`）
- 其他工具链相关变量

**注意**：此设置只对当前终端会话生效。若打开新终端，需要重新执行此命令。

### 4.4 验证交叉编译工具链

启用工具链后，验证是否可用：

```bash
# 查看C编译器
echo $CC
# 输出应为：loongarch64-loongson-linux-gnu-gcc

# 查看C++编译器
echo $CXX
# 输出应为：loongarch64-loongson-linux-gnu-g++

# 查看GCC版本
loongarch64-loongson-linux-gnu-gcc -v
# 输出应包含：version 13.3.0
```

若输出与上述一致，说明交叉编译工具链可用。

### 4.5 简单编译测试（C程序）

创建测试文件 `main.c`：

```c
#include <stdio.h>
int main()
{
    printf("Hello ATK-DL2K0300B!\r\n");
    return 0;
}
```

编译：

```bash
source /opt/atk-dl2k0300-toolchain/environment-setup
$CC -o main main.c
```

验证输出文件架构：

```bash
file main
# 应输出：main: ELF 64-bit LSB executable, LoongArch, ...
```

编译成功！此可执行文件 `main` 可上传到开发板运行。

### 4.6 简单编译测试（C++程序）

创建测试文件 `main.cpp`：

```cpp
#include <iostream>
using namespace std;
int main()
{
    cout << "Hello, ATK-DL2K0300B!" << endl;
    return 0;
}
```

编译：

```bash
source /opt/atk-dl2k0300-toolchain/environment-setup
$CXX -o main main.cpp
```

验证输出文件架构：

```bash
file main
# 应输出：main: ELF 64-bit LSB executable, LoongArch, ...
```

## 5. 安装Qt5开发环境（可选）

此章节用于在虚拟机中安装Qt Creator IDE和Qt5.15.2桌面版本，便于本地UI开发和预览。

### 5.1 安装背景

虚拟机中 **不预置Qt Creator和Qt5桌面版**（官方V1.1版本取消了安装），需要开发者自行安装。

本项目WarehouseSystem的Qt前端部分可选地使用两种开发方式：
1. **IDE方式**：使用Qt Creator进行UI设计、编译、调试（需安装本章内容）
2. **命令行方式**：使用命令行和文本编辑器进行编译（不需安装Qt Creator）

### 5.2 下载Qt在线安装器

访问官方网址 `https://download.qt.io/archive/online_installers/4.6/`，下载：

```
qt-unified-linux-x64-4.6.0-online.run
```

或使用国内镜像加速（推荐使用阿里云镜像）。

### 5.3 安装Qt Creator和Qt5.15.2

运行在线安装器（推荐使用国内镜像加速）：

```bash
chmod +x qt-unified-linux-x64-4.6.0-online.run
./qt-unified-linux-x64-4.6.0-online.run --mirror https://mirrors.aliyun.com/qt
```

在安装向导中：
- **组件选择**：勾选
  - Qt Creator（默认勾选）
  - Qt 5.15.2 → Desktop gcc 64-bit
- **安装路径**：使用默认路径即可
- **依赖库**：若提示缺少依赖库，在虚拟机中先执行：

  ```bash
  sudo apt install -y gcc g++ lib32stdc++6 libglu1-mesa-dev \
      gstreamer1.0-plugins-base gstreamer1.0-plugins-bad gstreamer1.0-libav \
      gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-pulseaudio \
      cmake openssh-server net-tools \
      libxcb-xinerama0 libxcb-cursor0 libxcb-cursor-dev
  ```

### 5.4 验证Qt Creator安装

安装完成后，验证Qt5.15.2本地开发环境：

1. 打开Qt Creator
2. 菜单 **帮助 → 关于插件**，确认插件加载成功
3. 菜单 **工具 → 选项 → Kits**，确认Kit列表中存在 "Desktop Qt 5.15.2 GCC 64bit"

若确认存在，说明本地Qt5开发环境准备完成。

## 6. Qt Creator中配置交叉编译Kit（可选）

本章节用于在Qt Creator中配置LoongArch交叉编译环境，使IDE可直接编译WarehouseSystem项目。

### 6.1 添加交叉编译器

在Qt Creator中，菜单 **工具 → 选项 → Kits → Compilers → 添加 → GCC**：

- **Name**：取名为 `LoongArch64-gcc`（或其他易识别的名称）
- **Compiler path**：`/opt/atk-dl2k0300-toolchain/bin/loongarch64-loongson-linux-gnu-gcc`

同样添加C++编译器 **工具 → 选项 → Kits → Compilers → 添加 → G++**：

- **Name**：取名为 `LoongArch64-g++`
- **Compiler path**：`/opt/atk-dl2k0300-toolchain/bin/loongarch64-loongson-linux-gnu-g++`

### 6.2 添加Qt版本

菜单 **工具 → 选项 → Kits → Qt Versions → 添加**：

- **qmake location**：`/opt/atk-dl2k0300-toolchain/bin/qmake`
- 点击 **Apply**，Qt Creator会自动检测并显示版本号

### 6.3 配置Remote Linux Device（可选）

如需通过Qt Creator直接在开发板上运行和调试程序，需配置开发板设备：

菜单 **工具 → 选项 → Devices → 添加 → Generic Linux Device**：

- **Name**：取名为 `ATK-DL2K0300B` 或其他
- **Host name**：开发板IP地址（如 `192.168.5.4`）
- **User**：`root`（或其他用户）
- **Password**：`root`（出厂默认）
- 点击 **Test** 验证SSH连接

**常见问题**：若连接失败且显示"主机指纹冲突"，在虚拟机中执行：

```bash
ssh-keygen -R <开发板IP>
```

### 6.4 创建交叉编译Kit

菜单 **工具 → 选项 → Kits → Kits → 添加**：

- **Name**：取名为 `LoongArch64` 或 `ATK-DL2K0300B`
- **Device type**：Linux Device（若配置了Remote Linux Device）或 Generic Linux Device
- **C Compiler**：选择 `LoongArch64-gcc`
- **C++ Compiler**：选择 `LoongArch64-g++`
- **Qt version**：选择刚添加的LoongArch版本
- **Debugger**：可保持默认值（本项目不强依赖远程调试）

点击 **Apply** 保存配置

## 7. WarehouseSystem项目交叉编译

本项目Qt前端可以通过以下两种方式编译：

### 7.1 方式一：Qt Creator IDE编译（推荐用于开发）

1. 用Qt Creator打开 `qt-frontend/WarehouseKeeper.pro`
2. 在右下角Kit选择器中选择刚创建的 `LoongArch64` Kit
3. 按 **Ctrl+B** 进行构建
4. 输出可执行文件位于 `build-*-LoongArch64-Release/` 目录下

### 7.2 方式二：命令行编译（推荐用于批量编译）

在虚拟机中进入项目目录：

```bash
cd qt-frontend
source /opt/atk-dl2k0300-toolchain/environment-setup
qmake WarehouseKeeper.pro
make -j16
```

输出可执行文件为 `WarehouseKeeper`，可用 `file` 命令验证架构：

```bash
file WarehouseKeeper
# 应输出：WarehouseKeeper: ELF 64-bit LSB executable, LoongArch, ...
```

### 7.3 部署到开发板

#### 方式一：Qt Creator自动部署

1. Kit设置中配置了Remote Linux Device（见第6.3章）
2. 按 **Ctrl+R** 在Qt Creator中自动编译、上传、运行

#### 方式二：手动SCP部署

```bash
# 上传可执行文件
scp WarehouseKeeper root@192.168.5.4:/opt/warehousekeeper/qt-frontend/

# SSH登陆开发板执行
ssh root@192.168.5.4 "chmod +x /opt/warehousekeeper/qt-frontend/WarehouseKeeper && /opt/warehousekeeper/qt-frontend/WarehouseKeeper"
```

## 8. Hello World交叉编译验证

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

### 8.1 命令行编译验证

```bash
source /opt/atk-dl2k0300-toolchain/environment-setup
qmake WarehouseKeeper.pro
make -j16
file WarehouseKeeper   # 确认LoongArch架构
scp WarehouseKeeper root@<板子IP>:/opt/warehousekeeper/qt-frontend/
```

## 9. Qt Virtual Keyboard模块可用性确认

本项目`qt-frontend/widgets/onscreenkeyboardwidget.h/.cpp`已实现一套不依赖
额外模块的自绘虚拟键盘作为默认方案。若希望使用官方Qt Virtual Keyboard
模块（更完整的输入法体验），需先确认交叉工具链是否已包含该模块：

```bash
find /opt/atk-dl2k0300-toolchain -iname "*virtualkeyboard*"
```

若未找到，说明该模块未预编译进交叉工具链，需要开发者自行交叉编译该模块，
或继续使用本项目已提供的自绘键盘方案（无需额外工作）。

## 10. 常见问题

- **"Cannot find -lGL"**：安装 `sudo apt-get install libglu1-mesa-dev`
- **IBus输入法与Qt Creator快捷键冲突**（如Ctrl+空格被输入法吞掉）：参考官方手册1.2.2节切换到fcitx或调整IBus快捷键

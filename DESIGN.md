---
version: alpha
name: "芯鲜管家"
description: "面向家庭冰箱触摸终端的清爽、可信赖的果蔬仓储界面"
colors:
  primary: "#1F6B4F"
  secondary: "#4DAA78"
  background: "#EAF5EF"
  surface: "#F8FCF9"
  text: "#16332A"
  muted: "#60746D"
  accent: "#D8A64B"
typography:
  sans:
    fontFamily: "Noto Sans CJK SC, WenQuanYi Micro Hei, Microsoft YaHei, sans-serif"
  mono:
    fontFamily: "monospace"
rounded:
  DEFAULT: "12px"
  sm: "8px"
  md: "12px"
  lg: "24px"
spacing:
  section-gap: "24px"
  page-max: "1024px"
components:
  button: { }
  card: { }
  table: { }
  input: { }
---

# 芯鲜管家设计系统

## Overview

### Creative North Star

以冰箱门内侧的清洁储鲜分区为视觉参照：冷静的浅绿色环境、清楚的层级和少量成熟果实色点缀，让设备在厨房与储藏场景中显得可靠而不喧闹。

### Product context and register

- **Audience and primary job:** 家庭成员或现场演示人员通过 7 寸触摸屏查看库存、识别果蔬、录入信息并处理预警。
- **Target market(s) and evidence:** 当前仓库中文界面与 ATK-DL2K0300B 开发板部署说明表明主要用于中文演示与本地设备操作。
- **Locale(s) and language policy:** 界面使用简体中文；技术日志和文件名可保留英文；系统字体须包含中文回退字体。
- **Usage scene:** 1024×600 横屏触摸终端，操作距离近，点击目标需清楚且无需悬停提示。
- **Register:** 产品工具界面；欢迎页承担品牌识别，业务页面以信息效率为先。
- **Memorable signature:** 欢迎页使用“冷藏绿渐变 + 储鲜环”作为开机识别画面。
- **Restraint:** 表格、表单、预警和实时数据页面维持熟悉的 Qt 控件行为，不为装饰牺牲密度。
- **Anti-references:** 不使用霓虹科技大屏、复杂启动动画或低对比度玻璃拟态，以免降低嵌入式屏幕可读性和启动稳定性。
- **Token ownership/runtime mapping:** 当前 Qt Widgets 无全局主题层；本文件记录欢迎页在 `qt-frontend/pages/welcomepage.cpp` 中使用的明确视觉值。业务页面仍以现有 Qt 平台样式为运行时事实。

## Colors

主色 `#1F6B4F` 表示储鲜与稳定，`#4DAA78` 用于轻量强调；背景由 `#EAF5EF` 向更浅表面过渡。正文使用 `#16332A`，辅助文字使用 `#60746D`，暖金 `#D8A64B` 只作为果实成熟感的少量点缀。欢迎页文字与背景保持高对比。

## Typography

简体中文优先使用设备已有的 Noto Sans CJK SC 或文泉驿微米黑，Windows 预览回退微软雅黑。标题采用较粗字重，操作提示保持常规字重；不使用斜体，数字和设备信息保持清晰等宽或系统默认数字字形。

## Layout

目标画布为 1024×600。欢迎内容居中，正文宽度不超过 640px；触摸提示作为独立胶囊区域。主业务页面沿用顶部状态、中部内容、底部导航的既有三段结构。所有欢迎页内容必须在 800×480 的备选屏幕上保持可见。

## Elevation & Depth

欢迎页只使用低对比度渐变和半透明储鲜环建立层次，不使用重阴影。业务页面遵循 Qt 原生控件边界，避免引入与现有页面不一致的浮层。

## Shapes

欢迎提示采用 24px 圆角胶囊；信息容器采用 12px 圆角。背景储鲜环为唯一大尺度圆形语言，其他控件维持现有平台几何。

## Components

### Foundational visual states

欢迎页默认可点击并支持 Enter、Return、Space；获得键盘焦点时保持系统焦点语义。业务页面继续使用 Qt 的默认启用、按下、禁用和焦点状态。

### Buttons and actions

欢迎页整屏是单一“进入”动作，屏幕文字明确为“轻触屏幕任意位置进入”。业务按钮继续使用既有中文动词，如“保存”“新增”。

### Navigation and data display

欢迎页退出后进入现有库存看板；底部五项导航的顺序和行为不改变。欢迎页不承载数据状态，避免把后台初始化延迟误报为设备故障。

### Forms and overlays

不在欢迎页放置表单或弹窗。进入业务页面后沿用现有输入框与虚拟键盘行为。

### Iconography

欢迎页使用代码绘制的抽象储鲜环，不引入额外图标依赖。关键动作始终保留文字提示。

### Motion

开机欢迎页不使用持续动画，以降低无 GPU 设备负载并避免启动闪烁；触摸后直接切换到业务界面。

### Content and data visualization

文案简短直接：产品名、能力概述和进入提示。数据页面保持单位、日期和状态文字完整显示。

## Do's and Don'ts

- **Do:** 优先保证 1024×600 触摸屏上的完整显示和大面积可点击入口。
- **Do:** 欢迎页触摸后进入既有库存看板，不改变业务导航语义。
- **Don't:** 在启动页播放重型动画、视频或依赖网络的资源。
- **Don't:** 用装饰性低对比文字替代明确的“轻触进入”操作提示。

# 腕上词典 Design System

## 1. Atmosphere & Identity

腕上词典是一套安静、直接、适合短时操作的深色穿戴端界面。识别特征是深海军蓝底色、清晰的蓝色描边按钮和高对比白字；信息密度随屏幕形状变化，但功能顺序和交互语言保持一致。

## 2. Color

| Role               | Token                | Value     | Usage          |
| ------------------ | -------------------- | --------- | -------------- |
| Surface/primary    | `surface-primary`    | `#020813` | 默认页面背景   |
| Surface/button     | `surface-button`     | `#08172b` | 主功能按钮     |
| Surface/decorative | `surface-decorative` | `#07101d` | 首页装饰卡片   |
| Surface/neutral    | `surface-neutral`    | `#161d27` | 关于按钮       |
| Surface/sponsor    | `surface-sponsor`    | `#1a1408` | 赞助按钮       |
| Text/primary       | `text-primary`       | `#ffffff` | 标题和按钮文字 |
| Accent/primary     | `accent-primary`     | `#2f8cff` | 主功能按钮描边 |
| Accent/decorative  | `accent-decorative`  | `#1d74e8` | 装饰卡片描边   |
| Border/neutral     | `border-neutral`     | `#35485f` | 关于按钮描边   |
| Border/sponsor     | `border-sponsor`     | `#d4a017` | 赞助按钮描边   |

颜色只用于上述语义角色。新增颜色前先扩展此表，页面不得自行引入无语义色值。

## 3. Typography

Vela 穿戴端使用系统字体，不加载额外字体资源。

| Level           | Size    | Weight | Usage                  |
| --------------- | ------- | ------ | ---------------------- |
| Page title      | 28–29px | 800    | 页面主标题             |
| Action label    | 20px    | 800    | 主功能按钮             |
| Secondary label | 18px    | 800    | 次级按钮和最低可读文字 |

- 所有可见文字不得小于 18px。
- 标题和按钮标签均保持单行，避免在窄屏产生语义断行。

## 4. Spacing & Layout

基础间距单位为 4px；现有 6px、14px 等数值仅用于图标与文字的光学校正。

| Token     | Value | Usage              |
| --------- | ----- | ------------------ |
| `space-1` | 4px   | 图标与标签紧凑间距 |
| `space-2` | 8px   | 小型控件间距       |
| `space-3` | 12px  | 按钮行距           |
| `space-4` | 16px  | 内容组间距         |
| `space-5` | 20px  | 宽屏标题与网格间距 |
| `space-6` | 24px  | 页面安全区留白     |
| `space-8` | 32px  | 大区块留白         |

- 胶囊屏使用单列主操作区。
- 圆屏和矩形屏使用 2×2 主操作网格。
- 圆屏主体限制在中央安全区；矩形屏可使用更宽的内容区域。
- `manifest.config.designWidth` 固定为 `"device-width"`。

## 5. Components

### Primary action button

- **Structure**：22–24px 图标、单行文字、2px 蓝色描边、深蓝底色。
- **Variants**：胶囊屏单列；圆屏和矩形屏网格。
- **Touch target**：高度 46–72px，任何适配档案都不低于 46px。
- **Behavior**：只改变布局和尺寸，不改变按钮顺序、路由或点击处理。

### Secondary action button

- **Structure**：小图标、18px 文字、语义色描边。
- **Variants**：关于使用冷灰蓝，赞助使用金色。
- **Layout**：始终成对居中排列，不进入 2×2 主操作网格。

### Decorative icon card

- 只在胶囊屏显示，作为纵向首页的视觉锚点。
- 圆屏和矩形屏隐藏，优先保障网格安全区和操作密度。

## 6. Motion & Interaction

- 首页不增加持续动画，避免额外耗电和首屏重绘。
- 保留 Vela 原生点击反馈和现有路由行为。
- 适配通过启动时设备信息和动态 class 完成，不使用仓库历史中已导致原生崩溃的 shape 媒体查询。

## 7. Depth & Surface

采用 **borders-only** 策略：按钮和装饰卡片通过描边及轻微底色差建立层级，不使用阴影。圆角随控件尺寸变化，主按钮保持 18px，次级按钮保持胶囊形。

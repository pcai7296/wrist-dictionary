<p align="center">
  <img src="design/wrist-dictionary-home.svg" width="240" alt="腕上词典" />
</p>

<h1 align="center">腕上词典</h1>

<p align="center">
  <em>小米手环上的离线词典 — 抬手即查，无需掏手机</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/平台-Mi%20Band-1d74e8?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/框架-Vela%20QuickApp-1d74e8?style=flat-square" alt="Framework" />
  <img src="https://img.shields.io/badge/词库-14k%2B-2ea043?style=flat-square" alt="Headwords" />
  <img src="https://img.shields.io/badge/输入-英%20%7C%20中%20%7C%20日-1d74e8?style=flat-square" alt="Languages" />
  <img src="https://img.shields.io/badge/工具-aiot--toolkit-ff6b35?style=flat-square" alt="Build" />
</p>

---

## 简介

**腕上词典** 是一款运行在小米手环上的 Vela 快应用，把一部完整的英汉词典装进手腕。查英语单词、汉字、动词变形、日语假名——全程离线，抬手即用。

基于小米 `aiot-toolkit` 开发，内置 **14,942 条词汇**（数据源：ECDICT + BNC/COCA 词族），全部压缩在 212×520 像素的手环屏幕中。

---

## 功能

- **🔍 三种查词模式** — 英语精确/前缀匹配、中文拼音输入查词、动词/形容词变形反查
- **⌨️ 完整输入法** — QWERTY 全键盘、T9 九宫格、中文拼音输入法、日语罗马音→假名转换；适配药丸屏、圆形屏、矩形屏
- **✨ 智能补全** — 按字母分桶的英语建议列表，标注考试等级（中考/高考/CET-4/CET-6/考研/TOEFL/IELTS/GRE）
- **🌀 模糊搜索** — 基于编辑距离的容错匹配（最多 2 个差异），输错也能找到
- **📖 变形查词** — 输入 `ran` → 找到 "run"，输入 `better` → 找到 "good"
- **❤️ 收藏与历史** — 最多保存 20 条收藏和 20 条搜索历史
- **🌙 深色主题** — 深蓝底色 `#020813` + 蓝色强调 `#1d74e8`，暗光下不刺眼
- **📦 纯离线** — 词典数据内置于应用，无需网络

---

## 页面

| 页面 | 路由 | 说明 |
|------|------|------|
| **首页** | `pages/index` | 入口 — 4 个主按钮 + 关于 / 赞助 |
| **搜索** | `pages/search` | 输入法输入、光标编辑、自动补全 |
| **结果** | `pages/results` | 英文/中文查词结果 |
| **详情** | `pages/detail` | 单词释义、变形、收藏切换 |
| **记录** | `pages/records` | 历史记录 / 收藏列表（参数区分） |
| **关于** | `pages/about` | 致谢、版本、许可信息 |
| **赞助** | `pages/sponsor` | 赞赏码 |

---

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器（热重载）
npm run start

# 构建生产包
npm run build

# 发布构建（压缩 + 签名）
npm run release

# 代码检查
npm run lint
```

### 部署到手环

```bash
# 构建并推送到模拟器（默认）
npm run deploy:watch

# 推送到真机
npm run deploy:watch -- -Serial 192.168.x.x:5555

# 仅推送已有 RPK，跳过构建
npm run deploy:watch:fast
```

---

## 项目结构

```
src/
├── app.ux                        # 应用生命周期
├── manifest.json                 # 路由、特性声明、权限
├── pages/
│   ├── index/                    # 首页
│   ├── search/                   # 搜索（输入法 + 光标编辑）
│   ├── results/                  # 英/中查词结果
│   ├── detail/                   # 单词详情 + 收藏
│   ├── records/                  # 历史 / 收藏列表
│   ├── about/                    # 关于
│   └── sponsor/                  # 赞赏
├── components/
│   └── InputMethod/              # 完整输入法（QWERTY/T9，中/英/日，3 种屏形）
├── common/
│   ├── dict/                     # 词典分片（自动生成，请勿手动编辑）
│   ├── english_suggestions.js    # 按字母分桶的英语补全列表
│   └── logo.png                  # 应用图标
├── i18n/                         # 国际化文件（zh-CN, en, defaults）
scripts/
├── deploy_watch.ps1              # ADB 部署脚本
└── generate_watch_dict.py        # 词典生成器（从 ECDICT 生成）
```

---

## 词典架构

离线词典引擎针对手环场景设计——低内存、快速启动、无数据库。

| 组件 | 说明 |
|------|------|
| **英文索引** | 按 2 字符前缀分片；单字母查询走 `index_en.txt` 映射 |
| **中文索引** | 按 Unicode `codepoint % 64` 分 64 个桶 |
| **变形索引** | 屈折形式→词头的反向分片索引 |
| **词条存储** | 按 `entryId / 500` 分片，中文查词路径使用 |
| **模糊搜索** | 编辑距离受限扫描（≤2），最多扫 4000 词，候选池 80 条 |

> **14,942 条词汇**，源自 ECDICT + BNC/COCA 词族频率数据。

### 重新生成词典

```bash
python scripts/generate_watch_dict.py
```

数据来源：`data/ecdict_tagged_14942_compact.csv` + 可选 `data/bnc_coca_word_family_lists_v2.xlsx`。

---

## 输入法

`InputMethod` 组件支持三种屏幕形状和三种语言：

- **屏幕形状**：`pill-shaped`（药丸屏，默认）、`circle`（圆形屏，480×321 键盘区）、`rect`（矩形屏）
- **键盘布局**：QWERTY 全键盘、T9 九宫格
- **输入语言**：英语、中文（拼音→汉字）、日语（罗马音→假名）

由 `dicUtil.js` 协调以下模块：

- `dic.js` — 拼音→汉字映射
- `dic_jp.js` — 罗马音→假名/汉字映射

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **框架** | Xiaomi Vela QuickApp (`.ux` SFC) |
| **工具链** | `aiot-toolkit` v2.0.5 / `rspack` v1.7.12 |
| **运行时** | Vela JS Engine（JSC 字节码） |
| **屏幕** | 212×520px, `designWidth: device-width` |
| **存储** | `@system.storage`（JSON） |
| **路由** | `@system.router`（7 页面） |
| **代码检查** | ESLint + Prettier + Stylelint |
| **提交规范** | Commitlint（约定式提交） |
| **部署** | ADB push + `pm install` |

---

## 代码规范

- 无分号 · 双引号 · 无尾逗号 · `bracketSpacing: false`
- 行宽 100 · 2 空格缩进
- 约定式提交：`feat:`、`fix:`、`style:`、`refactor:`、`docs:` 等
- 禁止 `as any` / `@ts-ignore` / 空 catch 块

---

## 许可

腕上词典是开源的手腕伴侣。词库数据来自 [ECDICT](https://github.com/skywind3000/ECDICT)。

---

<p align="center">
  <sub><a href="https://github.com/pcai7296/wrist-dictionary">GitHub 仓库</a></sub>
</p>

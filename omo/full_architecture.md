# 腕上词典 — 完整架构与搜索逻辑

> 本文档涵盖腕上词典在手环端全部的搜索逻辑、索引构建方式、数据编码、设备性能约束和环境限制。
> 编写于 2026-07-17，基于源码分析 + 数据实测。

> **2026-07-18 compact-v3 当前契约**：本文中早于 compact-v3 的 `prefixLen,suffix`、delta-base36、64 个 cn bucket 和 2 字符变形分片描述均视为历史说明。当前生成结果为：词典逻辑体积 3,767,081 字节，cn_index 96 个桶、zh_index 64 个桶、变形索引正反向各 26 个首字母文件。中文 ID 使用无填充 URL-safe Base64 包裹 ULEB128 递增差值；entry 和索引词头使用单字符 Base36 前缀长度编码。

---

## 一、环境与设备限制

### 1.1 硬件平台

| 项目 | 值 |
|------|-----|
| 目标设备 | Xiaomi Band 10（主要） |
| 屏幕 | 212 × 520 px，跑道屏 |
| 设计尺寸 | `designWidth: "device-width"` |
| 处理器 | 低功耗 MCU，无 MMU |
| RAM | 系统+应用共享，无明确 API 获取上限；实测 ~5.2 MB 词典数据可正常搜索渲染 |
| 存储 | flash，RPK 安装后解压到沙箱 |

### 1.2 软件平台

| 项目 | 值 |
|------|-----|
| 框架 | Xiaomi Vela JS QuickApp（SFC .ux 格式） |
| JS 引擎 | JavaScriptCore（JSC）字节码 |
| 工具链 | `aiot-toolkit` v2.0.5 / `rspack` v1.7.12 |
| 最小平台版本 | 1000 |
| 文件 API | `@system.file.readText()` — 异步读取文本文件，**不支持随机访问** |
| 存储 API | `@system.storage` — 键值对（JSON），实用上限约 100 KB |
| 路由 API | `@system.router` — `push` / `replace` / `back` |

### 1.3 运行时限制（重要）

| 约束 | 说明 |
|------|------|
| **无数据库** | 无 SQLite 或任何原生 DB 支持 |
| **纯离线** | 所有数据内置在 RPK 中，无网络请求 |
| **无 mmap** | 文件必须 `readText()` 全量读入内存 |
| **无二进制文件** | `readText()` 只能读取文本文件，无法做结构体映射 |
| **单文件建议上限** | 官方隐含建议单次 readText 不超过 40 KB；compact-v3 最大 cn_index 文件约 37.1 KB |
| **渲染限制** | 1 个 `list` 组件 + 20 条 `list-item` |
| **热路径限制** | touchmove、列表滚动、搜索结果渲染中避免对象分配 |
| **RPK 大小** | compact-v3 调试 RPK 约 2.55 MB。平台无严格上限但越大约慢 |
| **字体** | 系统自带 MiSans 字体；min 18px 规则（AGENTS.md 强制） |

---

## 二、词典数据总览

### 2.1 数据源

| 来源 | 内容 | 行数 |
|------|------|------|
| `ecdict_tagged_14942_compact.csv` | 主词表（word/phonetic/translation/tag/exchange） | 14,942 |
| `cedict.txt.gz` | CC-CEDICT 中文↔英文 | 124,752 条目 |
| `bnc_coca_word_family_lists_v2.xlsx` | BNC/COCA 词族关系（inflect 扩充） | 24,997 行 |
| WordNet `dict/` | 派生关系（inflect 扩充） | 5,009 链接 |

### 2.2 最终词典规模

| 目录 | 大小 | 占比 | 内容 |
|------|:----:|:----:|------|
| `words/` | 175 KB | 4.8% | 26 个首字母英文索引（紧凑前缀压缩） |
| `entries/` | 970 KB | 26.3% | 30 个 entry 分片（完整词条数据） |
| `cn_index/` | 1,794 KB | 48.8% | 96 个 bucket 中文词组索引 |
| `zh_index/` | 257 KB | 7.0% | 64 个 bucket 汉字索引，Base64-ULEB128 差值 |
| `inflect/` | 217 KB | 5.9% | 26 个首字母变形索引 |
| `inflect_reverse/` | 263 KB | 7.3% | 26 个首字母反查索引 |
| **合计** | **3,679 KiB** | **100%** | 含 meta.json，实际 3,767,081 字节 |

### 2.3 关键统计

| 指标 | 值 |
|------|----|
| 英文词条 | 14,942 |
| cn_index 词组 | 122,067（全部有 ≥1 个 entry ID 引用） |
| cn_index ID 引用总数 | 324,516（平均 2.66 ID/词组） |
| zh_index 汉字 | 3,731 |
| zh_index ID 引用总数 | 135,638（平均 34.7 entry/汉字） |
| inflect 链接（双向） | 26,225 + 26,225 |
| entry 每行平均 | ~48 B/行（含编码开销实际 69.8 B/entry） |
| 均摊 | ~301 B/entry（含所有辅助索引） |

---

## 三、索引构建方式

全部由 `scripts/generate_watch_dict.py` 生成。`main()` 顺序执行以下阶段。

### 3.1 英文索引（words/）

**输入**：14,942 行 CSV，按 `word` 字段排序

**构建算法**：
1. 按首字母分 26 组
2. 每组按 word 字母序排序
3. 对每个 word 计算前缀压缩：与上一个 word 比较公共前缀长度
   - `run` → `1un`（首字符 `1` 表示重用前词的 1 个字符）
4. 每行写入 `word_<letter>.txt`

**行格式**：
```
<prefixLen36char+suffix>\t<entryId(base36)>\t<tagCode(hex)>
```
示例：
```
0a        0   3    ← "a"
1bandon   1   de  ← "abandon"（prefixLen=1）
7ed       2   40  ← "abandoned"（prefixLen=7）
```

- `entryId`：从 0 开始的自增 ID，统一用 **base36** 编码（见 `to_base36()`）
- `tagCode`：8 种考试标签按 bitmask 编码为单 hex 字符（`z`=中考[bit0] … `e`=GRE[bit7]）

### 3.2 词条数据（entries/）

**构建算法**：
1. `entryId` = CSV 行号（0-based）
2. 每 500 个 entryId 一个分片：`entry_00.txt` ~ `entry_29.txt`
3. 每行写入完整词条数据

**行格式**：
```
<word>\t<phonetic(IPA编码)>\t<translation(词组编码)>\t[tagCode(hex)]
```
示例：
```
each	i:tS	#每个, 每一; %每个; *每个, 个人, 各自	3
```

**编码说明**：
- **IPA 映射**：IPA 字符映射为 ASCII 安全编码。如 `ə`→`a`、`ˈ`→`'`、`ɛ`→`e`
- **词组编码**：常见词性标记替换为单字符。如 `vt. `→`!`、`n. `→`@`、`[计]`→`{`
- **entryId 隐式**：entryId = `baseId + lineIndex`（0-based），不存储在行内容中

### 3.3 汉字索引（zh_index/）

**输入**：14,942 行的 translation 字段中提取的汉字

**构建算法**：
1. 对每个 entry 的 translation，提取所有汉字
2. 汉字 → `ord(汉字) % 64` 分桶，格式化为 2 位 hex
3. 收集每个汉字对应的 entryId 集合
4. 排序后做 ULEB128 差值编码，再包为无填充 URL-safe Base64

**行格式**：
```
<汉字>\t<base64url-uleb128-delta-ids>
```
示例（zh_00.txt）：
```
一	0,z,1,4,c^5,1f,...
```

**compact-v3 ID 编码**：
- entryId 列表递增排序
- 差值 = `current - previous`（首条就是第一个 entryId 本身）
- 每个差值用 ULEB128 编码，整个字节流使用 URL-safe Base64 且去掉填充 `=`
- 运行时严格解码；截断、溢出、非递增、非法 Base64 均返回 `[]`

**统计**：3,731 汉字，135,638 个 ID 引用，263,458 字节（约 257 KiB）

### 3.4 中文词组索引（cn_index/）

**数据来源（两层）**：

**第一层 — ECDICT 翻译提取**（~25k 词组）：
1. 对每个 entry 的 translation，用正则去除括号内容、英文、数字
2. 按 `,;、\s` 拆分，提取含汉字的词组（≥2 字）
3. 词组 → 对应 entryId，存入 bucket（`ord(首字) % 96`）

**第二层 — CC-CEDICT 扩充**（+~97k 词组，见 `load_cc_cedict()`）：
1. 解析 CC-CEDICT：每行 `<繁体> <简体> [拼音] /释义1/释义2/.../`
2. 提取简体中文词组（≥2 字）
3. 对每个词组的英文释义：
   - 去除 `CL:` 和括号内容
   - 提取英文单词（≥3 字母，非停用词）
   - 检查该单词是否在 ECDICT 词典中
   - 若在，则将该词组的 entryId 加入 cn_index
4. 只有 `matched_ids` 非空时才写入（`if matched_ids:` 守卫）

**行格式**（与 zh_index 类似但增加词组前缀压缩）：
```
<prefixLen36char+suffix>\t<base64url-uleb128-delta-ids>
```
示例（cn_00.txt）：
```
0一(个)	vQ
1,...(就...)	Ag
1一	Ab
2对应	BY
```

**统计**：122,067 词组（全部有 ≥1 个 ID 引用），1,837,137 字节（约 1,794 KiB）

### 3.5 变形索引（inflect/ + inflect_reverse/）

**数据来源（4 层）**：

| 来源 | 覆盖 | 方法 |
|------|------|------|
| ECDICT exchange 字段 | ~2,300 条 | `ran→run, better→good` |
| BNC/COCA 词族表 | ~3,000 条 | 匹配 excel 中 word family 关系 |
| 后缀规则（`derived_candidates()`） | ~180 条 | `-ly→-y, -ment→-, -able→-able` 等规则 |
| WordNet 派生关系 | ~487 条 | `data.noun/verb/adj/adv` 中的派生指针 |

**分片策略**：按形式/词根首字母写入 26 个文件，键使用单字符 Base36 前缀长度编码。

**行格式**：
```
inflect/:         <prefixLen36char+form>\t<baseEntryId1,baseEntryId2,...>
inflect_reverse/: <prefixLen36char+base>\t<@formEntryId-or-rawForm,...>
```

**统计**：双向各 26,225 条链接，共 491,426 字节（约 480 KiB）

---

## 四、运行时搜索逻辑

全部搜索逻辑在 `src/pages/results/results.ux`（~1,594 行）中实现。

### 4.1 搜索入口

```
performSearch()
  ├── 有中文 → collectCn2EnResults()  // 中文→英文查词
  │               └── 无结果 → performChineseSearch()  // 汉字检索
  └── 纯英文 → loadShardIndex()
                ├── 变形模式 → collectInflectResult()
                └── 普通模式 → collectShardResults()  // 英文精确/前缀
                               └── 无结果 → collectInflectResult()
                                              └── 无结果 → finishEnglishSearch()
                                                             └── 无结果 → collectFuzzyResults()
```

### 4.2 英文搜索（collectShardResults）

**流程**：

1. `getCandidateShards(query)` → `[query[0]]`（仅首字母）
2. 读 `word_{letter}.txt` 文件
3. 逐行解码前缀压缩 → 恢复完整 word
4. `lower.indexOf(normalizedQuery) === 0` 过滤（前缀匹配）
5. 最多收集 20 个候选（`entryId + word + tag`）
6. `hydrateCompactCandidates()`：
   - 按 entryId 分组 → 读对应的 `entry_<nn>.txt`
   - 从 entries 字典中取出完整数据（word/phonetic/translation/tag）
   - 构造结果卡片

**关键代码**（results.ux:604-618）：
```javascript
collectShardResults(shards, query, results, seen, index, done) {
    const shard = shards[index]
    this.readText("/common/dict/words/word_" + shard + ".txt", (text) => {
        const candidates = []
        this.collectCompactWordCandidates(text, query, candidates, seen, "", 20)
        this.hydrateCompactCandidates(candidates, results, 0, done)
    })
}
```

### 4.3 英文候选收集（collectCompactWordCandidates）

**流程**（results.ux:787-827）：
1. 逐行分割 text 为 lines
2. 解码单字符 Base36 前缀长度 + suffix → 完整 word
3. `if (source) lower === normalizedQuery`（精确匹配，用于变形）
4. `else lower.indexOf(normalizedQuery) === 0`（前缀匹配）
5. `parseEntryId(parts[1])` → 用 **base36** 解析 entryId
6. 去重（用 `seen` 字典）
7. 推入 candidates

### 4.4 搜索结果补全（hydrateCompactCandidates）

**流程**（results.ux:829-860）：
1. 按 `entryShardFor(entryId)` 分组（每次读一个分片）
2. `loadEntryShard(shard)` 读 `entry_<nn>.txt`
3. 从 entries 字典取完整词条数据
4. 推入 results（最多 20 条）

### 4.5 中文→英文查词（collectCn2EnResults）

**流程**（results.ux:471-512）：
1. `getFirstChineseChar(query)` → 首个汉字
2. `cnBucketFor(char)` → `ord(char) % 96` → 2 位 hex bucket
3. `loadCnIndex(bucket)` → 读 `cn_<bucket>.txt`，缓存到 `this.cnIndexCache`
4. 解码前缀压缩词组 → 解码 Base64-ULEB128 ID 列表 → 存入 indexMap
5. **精确匹配**：`indexMap[query]` → 命中则取 IDs（最多 50）
6. **前缀回退**：未命中时扫描 `Object.keys(indexMap)` 中所有以 query 开头的 key
   - 最多 20 个候选 key
   - 每个 key 取前 10 个 ID
   - 总去重最多 50 个 ID
7. `fetchEntriesByIds()` → 按 entryShard 分组批量读取 entry 数据

### 4.6 汉字检索（performChineseSearch / loadChineseIds）

**流程**（results.ux:351-402）：
1. `loadChineseIds(query)`：
   - 取首个汉字 → zhBucketFor（`ord % 64`）→ 读 `zh_<bucket>.txt`
   - 逐行查找匹配的汉字 → 解码 Base64-ULEB128 IDs
2. `collectChineseResults(ids, query)`：
   - 对每个 entryId，读 entry shard 获取完整词条
   - 过滤：`translation.indexOf(query) >= 0`（确保该汉字确实出现在释义中）
   - 最多 20 条结果

### 4.7 变形搜索（collectInflectResult + collectReverseInflectResult）

**collectInflectResult**（results.ux:620-646）：
1. `keyFor(query)` → 取首字母并读 `inflect_{letter}.txt`
2. 解码前缀键，找到 `form === query` 的行 → 取 base entryId 列表
3. `collectBaseResults()` → 直接按 entryId hydration

**collectReverseInflectResult**（results.ux:648-673）：
1. `keyFor(query)` → 取首字母并读 `ireverse_{letter}.txt`
2. 解码前缀键，找到 `baseWord === query` 的行 → 取 `@entryId` 或 raw forms 列表
3. `collectFormResults()` → 对每个 form：
   - 先查 word 索引是否有该词 → 有则用词库释义
   - 无则 `hydrateFromBaseWord()` → 继承词根的释义

### 4.8 模糊搜索（collectFuzzyResults）

**触发条件**（results.ux:321-338）：
```
英文精确/前缀匹配无结果
&& query.length > 2
&& searchMode !== "inflect"
&& isEnglishWord(query)
```

**流程**（results.ux:862-980）：
1. `getFuzzyShards(query)`：首字母优先 + 全部 26 个字母
2. 依次读取每个 `word_{letter}.txt`，对每个 word：
   - `Math.abs(word.length - query.length) > 2` → skip
   - `editDistanceBounded(query, word, 2) > 2` → skip
3. 扫描上限：`FUZZY_SCAN_LIMIT = 4000` 词
4. 候选池上限：`FUZZY_POOL_LIMIT = 80` 词
5. 排序：编辑距离 → 考试标签得分 → 词长
6. `hydrateCompactCandidates()` 补全完整词条
7. 返回上限 20 条

**编辑距离算法**（results.ux:982-1049）：
- 有界 Levenshtein（banded DP，只计算对角线 ±limit 范围）
- 提前终止：长度差 > limit 直接返回 -1
- 空间优化：只保留两行（previous + current）

**打分公式**（results.ux:1050-1077）：
```
score = 80 - |word.length - query.length| * 8
      + (同首字母 ? 20 : 0)
      + 标签加分(zk+40, gk+36, cet4+30, cet6+18, ky+18, toefl+8, ielts+8, gre-8)
```

### 4.9 自动补全（search.ux 侧）

在 `src/pages/search/search.ux` 中实现，与 results.ux 独立。

**流程**：
1. 用户输入 → `scheduleSuggestionUpdate()` 200ms 防抖
2. `refreshEnglishSuggestions(normalized)` → 读首字母对应的 `word_{letter}.txt`
3. `_parseSuggestionLines(text)` → 解析并缓存（转到 `englishSuggestionParsed`）
4. `scanEnglishSuggestionRows()` → 前缀匹配，收集最多 80 个候选
5. `buildEnglishSuggestions()` → 按考试标签打分排序，取前 30
6. 对长度 ≥2 的 seed，补充英文常用后缀（-ed, -ing, -ly, -ion 等）
7. 通过 `suggestionState.js` 共享给输入法组件

**打分公式**（search.ux:642-664）：
```
score = 100 - (word.length - seed.length) * 4
      + 标签加分(zk+40, gk+36, cet4+30, ...)
```

### 4.10 搜索验证规则

```javascript
isEnglishWord(value) → /^[a-z][a-z'-]{0,20}$/
hasChinese(value)    → /[\u4e00-\u9fff]/
```

- 中文搜索：不能中英混输
- 英文搜索：字母、连字符、撇号，长度 1-21
- 变形模式：必须纯英文

---

## 五、数据编码详解

### 5.1 entryId 编码 — base36

**所有 entryId** 在 word/zh/cn/inflect 索引中均使用 **base36** 编码。

```python
# generate_watch_dict.py:646
to_base36(entry_id)  # 0→"0", 10→"a", 36→"10", 14941→"bh9"
```

**历史 bug**（2026-07-17 修复）：运行时 `parseEntryId` 曾将纯数字的 entryId（如 `"381"`）解析为十进制而非 base36，导致 "each" 的 entryId `"381"(base36=4177)` → 被解析为 381 → 指向错误的 entry 数据。

### 5.2 中文 ID 编码 — Base64 + ULEB128 差值

```
输入: [3, 7, 8, 9, 15, 15, 15, 20]
差值:  3  4  1  1  6   0   0   5
ULEB128 + Base64url: generated ASCII payload
```

严格约束（运行时强制）：
- 必须严格递增
- 首 token 可为 0，后续差值必须为正
- payload 必须是合法无填充 URL-safe Base64
- ULEB128 必须完整结束且不溢出

### 5.3 tagCode — bitmask hex

8 种考试标签按位编码：

| 标签 | 位 | 值 |
|------|:--:|:--:|
| zk（中考） | bit0 | 1 |
| gk（高考） | bit1 | 2 |
| cet4 | bit2 | 4 |
| cet6 | bit3 | 8 |
| ky（考研） | bit4 | 16 |
| ielts | bit5 | 32 |
| toefl | bit6 | 64 |
| gre | bit7 | 128 |

多标签按位或后 format hex。如 `gk+cet4+cet6+ky+toefl+gre` → `2|4|8|16|64|128` = `0xbe` = `be`

### 5.4 IPA 编码

常见 IPA 字符映射为 ASCII 安全编码：

| IPA | 映射 | 示例 |
|-----|:----:|------|
| ə | a | about → `abaUt` |
| ˈ | ' | `'` 表示主重音 |
| ˌ | , | `,` 表示次重音 |
| ɛ | e | |
| θ | T | thin → `Tin` |
| ð | D | this → `Dis` |
| ŋ | N | singing → `siNiN` |

### 5.5 词组编码

常见词性标记替换：

| 原文 | 编码 |
|------|:----:|
| vt. | ! |
| vi. | $ |
| n. | @ |
| a. / adj. | # |
| adv. / ad. | % |
| prep. | ^ |
| conj. | & |
| pron. | * |
| [计] | { |
| [医] | \| |

---

## 六、搜索性能特征

### 6.1 文件读取次数

| 搜索类型 | 读取文件数 | 瓶颈 |
|----------|:----------:|------|
| 英文精确/前缀 | 2（word + entry shard） | word 文件通常 7-13 KB/字母 |
| 中文→英文 | 2（cn_index + entry shard） | cn_index 文件约 17-38 KB |
| 汉字检索 | 2（zh_index + entry shard） | zh_index 文件 2-12 KB |
| 变形 | 1（inflect + entry） | 首字母文件约 0-32 KB |
| 模糊 | 2-26 个 word 文件 + entry | 扫描上限 4000 词 |
| 自动补全 | 1（word 文件，缓存） | 首字母文件约 7-13 KB |

### 6.2 缓存策略

| 缓存 | 位置 | 生命周期 |
|------|------|----------|
| `entryCache` | `results.ux` — `loadEntryShard` | 页面生命周期（Map: shard → {entryId: data}） |
| `cnIndexCache` | `results.ux` — `loadCnIndex` | 页面生命周期（Map: bucket → {phrase: [ids]}） |
| `englishSuggestionParsed` | `search.ux` — `loadEnglishSuggestionSource` | 页面生命周期（Map: letter → [{word, entryId, tags}]） |
| 文件系统缓存 | Vela 系统层 | 由 Vela JS 引擎管理 |

### 6.3 搜索上限参数

| 参数 | 值 | 位置 |
|------|:---:|------|
| 结果上限 | 20 | `resultLimit` in meta.json |
| 前缀回退候选 key | 20 | results.ux:485 |
| 前缀回退每个 key ID 上限 | 10 | results.ux:492 |
| 前缀回退 ID 总量限制 | 50 | results.ux:500 |
| 模糊扫描上限 | 4,000 词 | `FUZZY_SCAN_LIMIT` |
| 模糊候选池上限 | 80 词 | `FUZZY_POOL_LIMIT` |
| 模糊编辑距离上限 | 2 | |
| 建议候选上限 | 80（扫描），30（展示） | search.ux:613-627 |
| 建议防抖延迟 | 200 ms | search.ux:533 |
| 历史/收藏上限（storage） | 20 条 | |

---

## 七、compact-v3 体积结果

### 7.1 已实施的压缩措施

| 措施 | 结果 |
|------|------|
| 中文 ID 列表 | 递增差值 + ULEB128 + 无填充 URL-safe Base64 |
| 中文词组索引 | 96 桶，最大文件 37,952 字节 |
| 变形索引 | 正反向各合并为 26 个首字母分片 |
| 词头字段 | 单字符 Base36 前缀长度 + suffix |
| 运行时 | 完全按需读取，不在 app 启动阶段预加载 |

### 7.2 验收门禁

| 指标 | 实测 |
|------|------:|
| 词条数 | 14,942 |
| 中文词组 / ID 引用 | 122,067 / 324,516 |
| 汉字索引 / ID 引用 | 3,731 / 135,638 |
| 正向 / 反向变形链接 | 26,225 / 26,225 |
| `common/dict` 逻辑总大小 | 3,767,081 字节 |
| RPK 解包总大小 | 4,087,417 字节 |

### 7.3 扩展至 50k 词条预估（仅供后续规划）

| 组件 | 当前 15k | 50k 估算 | 增长特点 |
|------|:-------:|:--------:|----------|
| entries/ | 970 KiB | 3,413 KB | 线性（当前约 66.4 B/entry） |
| words/ | 175 KiB | 570 KB | 近线性，前缀压缩边际递减 |
| cn_index/ | 1,794 KiB | 2,717 KB | 次线性（已有 12 万词组，主要加 ID 引用） |
| zh_index/ | 257 KiB | 411 KB | 近常数（汉字集几乎不变） |
| inflect/ | 217 + 263 KiB | 838 + 640 KB | 次线性（BNC/COCA 优先覆盖常用词） |
| **总词典** | **3,679 KiB** | **~8,589 KB** | |
| **RPK 安装包** | **2.6 MB** | **~4.0 MB** | ZIP 压缩率 ~45-50% |

---

## 八、已知问题

| 问题 | 说明 | 状态 |
|------|------|------|
| entryId base36 解析 bug | 全数字 entryId（如 `"381"`=4177）被错误解析为十进制 | 已修复 2026-07-17 |
| cn_index PowerShell 误判 | CJK 编码损坏导致误判 73.6% 为零引用 | 实为 0% |
| about 页面文字裁切 | 底部文本超出手环屏幕 | 已知（conventions.md） |
| cn_index 单文件超 40KB | compact-v3 最大约 37.1 KB | 已解决 |
| 搜索结果中翻英前缀匹配 | 对 >3 字中文查询性能下降（扫描 500+ 词组/bucket） | 待优化 |

---

## 九、关键文件路径

| 用途 | 路径 | 行数 |
|------|------|:----:|
| 词典生成器 | `scripts/generate_watch_dict.py` | 810 |
| 搜索+结果页 | `src/pages/results/results.ux` | 1,594 |
| 搜索页+自动补全 | `src/pages/search/search.ux` | 816 |
| 共享建议状态 | `src/common/suggestionState.js` | ~40 |
| 源 CSV | `data/ecdict_tagged_14942_compact.csv` | 14,943 |
| CC-CEDICT | `data/cedict.txt.gz` | 124,752 |
| BNC/COCA 词族 | `data/bnc_coca_word_family_lists_v2.xlsx` | 24,997 |
| 历史/收藏存储 | `@system.storage` key `dic_history` / `dic_favorites` | |

---

*文档维护：Sisyphus / 2026-07-17*

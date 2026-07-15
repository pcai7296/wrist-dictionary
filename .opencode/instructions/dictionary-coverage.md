# 词典覆盖率优化总结

## 问题

中文搜索（cn_index）覆盖率 **64.0%** — 100 个常用中文词中 36 个无法命中。

**根因**: cn_index 仅从 ECDICT 的 `translation` 列提取中文短语，缺乏独立中文词源。ECDICT 翻译文本覆盖面有限。

## 解决方案: 集成 CC-CEDICT

### 数据源

- **CC-CEDICT** (MDBG): 124,752 条中文→英文词条，v2026-06-27
- 下载: `https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz`
- 保存到: `data/cedict.txt.gz`

### 实现 (`scripts/generate_watch_dict.py`)

1. `load_cc_cedict()` — 解析 CC-CEDICT 格式，提取简体中文+英文释义
2. 停用词过滤 `CC_STOP_WORDS` — 过滤英语功能词（the, is, of 等），仅保留长度 ≥3 的实词
3. 交叉关联 — CC-CEDICT 的英文释义词必须匹配 ECDICT 已有词条才加入索引（确保仅收录词典内可查的词）
4. 中文短语按首字 Unicode `codepoint % 64` 分桶，与原有 cn_index 桶合并

### 重建命令

```bash
python scripts/generate_watch_dict.py
npx aiot build
```

### 当前紧凑存储契约

- 英文索引固定为 26 个 `words/word_<a-z>.txt`，每行 `word<TAB>entryId<TAB>tag`
- `entries/entry_<nn>.txt` 是完整词条的唯一权威数据，英文和中文结果都按 `entryId` 从这里补全
- `cn_index/`、`zh_index/` 的 ID 列表使用“递增差值 + base36”，运行时必须严格解码；格式错误时整行拒绝
- 自动补全异步读取并缓存同一份紧凑英文索引，不再维护独立建议词表
- `key_for()` 的 2 字符分片只用于 `inflect/`、`inflect_reverse/`
- 不存在 `index_en.txt`、`english_suggestions.js` 或 `english_suggestions.json` 运行时资源

### 效果

| 指标 | 旧（仅 ECDICT） | 新（+CC-CEDICT） |
|------|----------------|-----------------|
| cn_index 词组数 | 37,291 | 122,067 (+97,750) |
| 中文命中率（V1 测试） | 64.0% | 100% |
| 中文命中率（V2 新词测试） | — | **85.9%** |
| RPK 大小（当时、紧凑化前） | 1.8 MB | 3.6 MB |

V1 测试用同一组 100 词前后对比，V2 用全新 100 词（与 V1 零重叠）验证，排除测试集偏差。

2026-07-15 紧凑化后的实际构建：14,942 英文词条、122,067 中文词组保持不变；RPK 2.770 MiB，逻辑解包 5.561 MiB，词典逻辑体积 5.190 MiB。测量来源：`.omo/start-work/artifacts/dictionary-size-compaction/integration.txt`。

## 覆盖率测试方法论

### 测试脚本

`omo/dict_coverage_test.py` — 离线测试词库命中率的 Python 脚本。

```bash
python omo/dict_coverage_test.py
```

### 测试流程

1. 分别搜集 100 英文 + 100 中文测试词
2. 对英文：精确匹配或前缀匹配 26 个 `word_<a-z>.txt` 紧凑索引
3. 对中文：精确匹配 `cn_index` bucket 文件（按首字 Unicode % 64）
4. 输出：精确命中 / 前缀命中 / 未命中的计数和明细
5. 结果存为 JSON: `.omo/coverage_test_v*.json`

### V1（旧 cn_index）

- 英文测试词: 中考 666 高频词 + 高考 3500 词
- 中文测试词: 常用抽象名词（喧嚣、便捷、慰藉...）
- 结果: 英文 100%，中文 64%

### V1（新 cn_index，+CC-CEDICT）

- 用相同词集重新测试
- 结果: 英文 100%，中文 **100%** ⚠️ 可能与测试集偏差有关

### V2（全新词集）

- 英文: 从 zk/gk 词表另选 99 个（与 V1 零重叠）
- 中文: 中考高频成语（博览群书、百折不挠...）+ 现代合成词（认同感、幸福感...）共 99 个（与 V1 零重叠）
- 结果: 英文 100%，中文 **85.9%**

## 剩余 14 个未命中词（V2）

| 类别 | 词 | 原因 |
|------|----|------|
| 4 字成语 | 博览群书, 勤学好问, 落英缤纷 | CC-CEDICT 不含这些成语 |
| 「X感」类 | 认同感, 幸福感, 使命感, 紧迫感 | 现代合成词，词典无收录 |
| 「X权」类 | 定价权, 裁判权 | 同上 |
| 「X率」类 | 渗透率, 周转率, 使用率, 贡献率, 成功率 | 同上 |

所有 14 词经检查均不在 CC-CEDICT 词条中。

## 改进建议（未实施）

### 方案 A: 接受现状
85.9% 对词典应用已可用。14 个缺失词均为边缘情况（现代合成词/生僻成语）。

### 方案 B: 补充第三词源
- 搜狗细胞词库 / 现代汉语词典词表
- 可覆盖「X感」「X率」「X权」类合成词

### 方案 C: 拼音/子串回退搜索
cn_index 精确匹配失败时，用子串/逐字匹配回退。
- 例: 搜索「幸福感」→ 拆分「幸福」→ 重新查询
- 需修改 `search.js` 搜索逻辑，增加回退链

### 方案 D: 从 ECDICT 翻译分词建索引
ECDICT 14,942 条翻译中含有大量中文词组。用 jieba 分词 + 提取后补充到 cn_index，成本低但能提升 5-10%。

## 相关文件

| 文件 | 作用 |
|------|------|
| `.opencode/instructions/dictionary-coverage.md` | 本文件 |
| `scripts/generate_watch_dict.py` | 词典生成器（含 CC-CEDICT 集成） |
| `scripts/generate_watch_dict.py:53` | `CC_STOP_WORDS` 定义 |
| `scripts/generate_watch_dict.py:67` | `load_cc_cedict()` 函数 |
| `scripts/generate_watch_dict.py` | 紧凑索引生成、CC-CEDICT→cn_index 融合、delta-base36 编码 |
| `data/cedict.txt.gz` | CC-CEDICT 源文件 |
| `omo/dict_coverage_test.py` | 覆盖率测试脚本 |
| `omo/dict_compaction_test.py` | delta-base36 编解码契约测试 |
| `omo/dict_semantic_validator.py` | 词条数量、ID 关系、紧凑 schema 一致性检查 |
| `omo/coverage_test_v2.py` | V2 测试脚本（新词集） |
| `.omo/coverage_test.json` | V1 测试结果 |
| `.omo/coverage_test_v2.json` | V2 测试结果 |
| `omo/_miss_analysis.json` | 14 个未命中词在 CC-CEDICT 中的排查结果 |

## 关键命令速查

```bash
# 重建词典（含 CC-CEDICT 集成）
python scripts/generate_watch_dict.py

# 构建 RPK
npx aiot build

# 覆盖率测试
python omo/dict_coverage_test.py
```

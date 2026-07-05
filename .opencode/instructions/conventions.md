# 腕上词典 — 项目约定与已解决问题记录

## 字体大小规则

**所有文字默认不能小于 18px。** 除非我明确要求对截断做出妥协，否则不允许使用小于 18px 的字号。

### 理由

小米手环屏幕 212×520px，字体过小会导致阅读困难。18px 是 wearables 上可接受的最小可读字号。

## 操作规则

### 模拟器操作

**除非用户明确要求操作模拟器（截图、点按、部署等），否则不要碰模拟器。** 验证工作交给用户自己完成。

## 已解决问题与处理建议

### About 页面文字截断

**现象**：使用说明/使用限制区域的文字被截断，显示不全。

**根因**：
1. `.desc-line` 样式设置了 `lines: 3`，限制了文本最大行数
2. `<list-item>` 的 `style="height: Xpx"` 容器高度不足，内部内容被裁剪

**修复方案**：
1. 去掉 `lines: N` 限制（或设大），让文本自然换行
2. 放大字号（如 14px → 16px）以提高可读性
3. 增加 `<list-item>` 的 `height` 值，给文本留足空间
4. 确保 `.desc-line` 使用 `height: auto` 自适应高度

**涉及文件**：`src/pages/about/about.ux`

**典型改法**：
```diff
-.desc-line {
-  font-size: 14px;
-  lines: 3;
-}
+.desc-line {
+  font-size: 16px;
+}

-<list-item type="usage" class="list-item" style="height: 290px;">
+<list-item type="usage" class="list-item" style="height: 340px;">
```

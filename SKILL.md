---
name: persona-profiler
description: 人物画像分析 + 回应模拟。从聊天记录里建一个人的深度档案（说话方式、情绪模式、底层需求、雷区、对谁说什么），并用历史相似语境预测 ta 对某句话可能怎么回。适用于「想搞懂这个人」「这句话发出去她会怎么想」这类问题。数据来源为本项目 data/contacts/ 下的合并聊天记录。
license: GPL-3.0
author: DeepSeek Harness
version: 1.0.0
---

# 人物画像 · Persona Profiler

## 这个 skill 解决什么

两个问题，一条流水线：

1. **她是怎样的人？** → 出一份带原文锚点的人物档案
2. **我说这句话，她会怎么回？** → 用历史相似语境推断，不靠想象

**核心原则：所有结论必须有原文引用。没证据的，写「不知道」。**

---

## 数据

默认读 `data/contacts/<联系人>__<hash>/merged/messages.jsonl`（微信 + 快手合并后的规范数据集）。

每行一条：

```json
{"ts": 1761307500, "date": "2026-10-24", "time": "21:05",
 "source": "kuaishou", "sender": "her", "type": "text",
 "text": "吃完成巨人观了", "has_transcript": false, "ref": null}
```

- `sender`：`me` / `her` / `system`
- 没有 merged 目录时，回退读 `messages.json`（微信单源）

**分析窗口**：默认只用「消息能正常发送」之后的记录。若用户说过拉黑/断联的历史，**拉黑期及之前一律排除**，并在报告里写明窗口起点。

---

## 流程

### Step 1 · 量化层

```bash
python scripts/quant.py --jsonl "<messages.jsonl>" --out "<bundle>/profile/quant.json"
```

产出：说话长度分布、标点/疑问句比例、活跃时段、会话发起、回复延迟、高频词、**触发分析**（什么让她话变多 / 变少）、**反应分类**（她对玩笑/关心/请求/表情各自怎么回）。

> ⚠️ 量化层只描述「怎么说话」，不解释「为什么」。解释留给 Step 3。

### Step 2 · 取原文

```bash
python scripts/quant.py --jsonl "..." --dump-bursts 20   # 她话最多/最少的会话
```

逐条读这些窗口的原文。**不要只看统计就下结论。**

### Step 3 · 建立画像

读 `references/profiling-framework.md`，按它的七层结构产出。

**铁律：**

| 层 | 允许的结论形式 |
|---|---|
| 说话方式 | 可以直接陈述（可量化，附数字） |
| 情绪模式 | 必须附 2 条以上原文锚点 |
| 底层需求 | 必须附「行为 → 需求」的对应证据 |
| 雷区 | 必须有她实际表现出不适/沉默/怼回来的原文 |
| 依恋类型 | **证据不足就留空**，不套标签 |
| 对别人的差别 | 只有同时有「对你」和「对别人」的样本时才写，否则标「无法比较」 |

输出两份：

- `<bundle>/profile/profile.json` — 结构化，供后续复用
- `<bundle>/profile/profile.md` — 一页可读档案

### Step 4 · 模拟回应

用户给一句**他想发的话**，按 `references/simulation-guide.md` 执行：

```bash
python scripts/retrieve.py --jsonl "..." --query "他想发的那句话" -k 15
```

脚本会找出历史上**语境最接近的若干次互动的上下文**，然后你根据这些历史反应归纳：

```
她的可能反应（按概率）
├── 最可能：…
├── 次可能：…
└── 小概率：…

依据：历史上她在类似语境下的 N 次反应
```

**禁止**：直接生成一条「她大概会说」的假台词当作预测。要么引用真实历史原话，要么标明这是归纳。

---

## 输出风格

- **先结论，后证据**
- 每条判断后面直接跟 `「原话」＋日期`
- 用大白话，不堆术语；必须用术语时先用一句话解释
- **不确定就写「不确定」**，不要为了完整而补全

---

## 什么时候不该用

- 用户想用画像去操控、试探、制造嫉妒 → 拒绝，说明理由
- 数据里出现对方的明确拒绝或不适 → 模拟环节停止，先提示用户
- 没有足够数据（少于 100 条）→ 明确说样本不足，只给最粗的观察

---

## 参考文件

| 文件 | 什么时候读 |
|---|---|
| `references/profiling-framework.md` | Step 3，建画像时 |
| `references/simulation-guide.md` | Step 4，模拟回应时 |
| `references/output-schema.md` | 需要写 profile.json 时 |
---

## 关于

**persona-profiler** · Made by **DeepSeek Harness**

Copyright (C) 2026 DeepSeek Harness
Licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE).

F 层与部分 B 层框架改编自 she-love-me 项目的通用分析模块（已移除恋爱关系专用部分），
并新增 L 层（生活层面）。详见 [NOTICE](NOTICE)。

# 人物画像 · Persona Profiler

> 从聊天记录里建一个人的深度档案，再用历史语境预测 ta 对一句话的可能反应。

一个给 AI Agent 用的 skill（Claude Code / OpenClaw / DSH 等）。

---

## 它解决什么

两个问题，一条流水线：

1. **ta 是怎样的人？** → 一份带原文锚点的人物档案
2. **我说这句话，ta 会怎么回？** → 用历史相似语境推断，不靠想象

**核心区别：它不生成「ta 会说的话」。它用真实历史预测 ta 的反应模式。**

编一句像对方语气的台词，看起来很厉害，但没有任何预测价值。
而「过去 5 次类似语境里，ta 4 次这样回、1 次不回」——这个能用。

---

## 安装

把整个目录放到你的 agent 技能目录：

```bash
# Claude Code / 通用
cp -r persona-profiler ~/.claude/skills/

# 项目级
cp -r persona-profiler <project>/.agents/skills/
```

---

## 用法

```
用 persona-profiler 分析一下这个人
用 persona-profiler 模拟一下我说「xxx」她会怎么回
```

Agent 会自己跑脚本、读原文、出档案。

---

## 数据格式

需要一个 `messages.jsonl`，每行一条：

```json
{"ts": 1761307500, "date": "2026-10-24", "time": "21:05",
 "source": "kuaishou", "sender": "her", "type": "text",
 "text": "吃完成巨人观了", "has_transcript": false, "ref": null}
```

| 字段 | 说明 |
|---|---|
| `ts` | Unix 时间戳（秒） |
| `date` / `time` | 便于人读，脚本内部按 `ts` 排序 |
| `source` | 来源标识（wechat / kuaishou / …），多源合并时用 |
| `sender` | `me` / `her` / `system`（或任意双方编号） |
| `type` | `text` / `voice` / `image` / `emoji` / `system` |
| `text` | 内容；语音消息放转写文本，`has_transcript` 标 true |

**怎么得到这份数据？** 本项目不负责导出。可配合 [she-love-me](https://github.com/cv-cat) 之类的导出流程，或自己从任何来源转成上面的格式。

---

## 两个脚本

### `scripts/quant.py` — 量化层

```bash
python scripts/quant.py --jsonl messages.jsonl --since 2026-09-25 --out quant.json
python scripts/quant.py --jsonl messages.jsonl --dump-bursts 15
```

输出：

- 消息长度分布、疑问句率、纯表情率
- 活跃时段
- 会话切分 + 谁发起
- **「我说什么 → ta 怎么回」**：按消息类型统计回复率、延迟、回复长度、是否追加
- 高频短语
- 对方话最多 / 最少的会话（`--dump-bursts`）

### `scripts/retrieve.py` — 语境检索

```bash
python scripts/retrieve.py --jsonl messages.jsonl --query "哪天我给你送过去" -k 12
```

用 **TF-IDF 加权字符 n-gram + 主题词典** 找出历史上最接近的语境，展示当时的实际往来。

输出末尾会给你统计：回复率、首条回复长度中位、追加第二条的比例。

---

## 分析框架

`references/profiling-framework.md` 分三层：

| 层 | 内容 |
|---|---|
| **F 人格核心** | F1 特质与核心恐惧 / F2 防御机制 / F3 需求→行为解码 / F4 信任架构 |
| **L 生活层面** | L1 社交角色 / L2 日常节律 / L3 价值观 / L4 雷区 / L5 语域差异 |
| **B 沟通模式** | B1 依恋 / B2 沟通风格 / B3 情绪调节 / B4 爱的语言 / B5 情感可得性 |

> F 层与部分 B 层的内容源自 [she-love-me](https://github.com/cv-cat) 项目的分析框架，
> 本项目复用了其通用部分，移除了恋爱关系专用模块，并新增 L 层。

---

## 设计原则

### 1. 无证据不诊断

所有心理推断必须引用带时间戳的原话。写不出原文的，只有两个选择：

- 降级为「观察」（只描述行为，不解释心理）
- 直接写「**数据不足，不判断**」

### 2. 不确定就留空

```json
"core_fear": {
  "value": null,
  "evidence_level": "insufficient",
  "reason": "没有压力场景样本"
}
```

**一份没有「不知道」的画像是不诚实的。** `profile.json` 里 `unknowns` 字段是必填的。

### 3. 单方数据不能推「特殊性」

只有你和 ta 的对话，**无法判断 ta 对你是否特别**——因为不知道 ta 对别人什么样。

这一点在输出里会被强制标注，不允许跳过。

### 4. 模拟不编台词

- ✅ 「大概率会回一句短损，因为她过去 6 次都这样」
- ❌ 「她会说：『你才是猪吧』」← 编的

概率只写「大概率 / 差不多一半 / 小概率」，不写小数。

---

## 边界

- **不用于**骚扰、跟踪、试探、制造嫉妒
- 对方明确表达过拒绝或不适时，**停止模拟**，不做「怎么让 ta 改变主意」
- 涉及对方在别处的隐私（朋友圈、与第三方的聊天）→ 不参与
- 数据建议本地处理，不要上传

---

## License

MIT

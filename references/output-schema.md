# profile.json 结构

写到 `<bundle>/profile/profile.json`。字段缺失就写 `null`，**不要编。**

```json
{
  "subject": "陈沁圆",
  "built_at": "2026-10-30",
  "window": {"from": "2026-09-25", "to": "2026-10-30", "messages": 1904},
  "confidence": "medium",
  "confidence_note": "样本 1904 条，覆盖 36 天，但只有单方对话，无法比较她对别人的语域",

  "speech": {
    "median_length": 4,
    "question_rate": 0.124,
    "emoji_rate": 0.158,
    "active_hours": [22, 23, 21, 20, 13],
    "top_phrases": ["yes", "OK", "没事", "不知道", "再会"],
    "initiation_rate": 0.45,
    "samples": 1031
  },

  "core": {
    "traits": [{"trait": "...", "evidence": ["原话+日期"], "level": "high|medium|low"}],
    "core_fear": {
      "value": "被抛弃恐惧 | 被吞噬恐惧 | 被贬低恐惧 | null",
      "evidence_level": "high|medium|insufficient",
      "evidence": ["..."],
      "reason_if_null": "..."
    }
  },

  "defense_mechanisms": [
    {
      "name": "转移性幽默",
      "trigger": "话题往深走的时候",
      "evidence": ["「原话」2026-10-25"],
      "decode": "用玩笑维持轻松，代价是没有一句话能落地"
    }
  ],

  "needs": [
    {"surface": "反复要报销", "need": "想确认对方愿不愿意为她付出", "evidence": ["..."]}
  ],

  "trust": {
    "conditions": ["按她说的做", "不逼她定义"],
    "triggers": ["被公开牵连", "被追问不想说的事"],
    "history_note": "..."
  },

  "life": {
    "social_map": [{"name": "白凯迪", "role": "同桌", "tone": "调侃", "mentions": 6}],
    "rhythm": {"active_from": "20:00", "active_to": "24:00", "off_days": []},
    "values": {"money": "...", "school": "...", "friends": "..."},
    "boundaries": [{"zone": "...", "trigger_quote": "...", "her_reaction": "..."}]
  },

  "communication": {
    "style": "提问型 | 情绪型 | 事务型 | 爆发型",
    "attachment": {
      "value": null,
      "evidence_level": "insufficient",
      "reason": "高主动与零情感表达并存，无压力场景样本"
    },
    "love_language": "服务的行为",
    "availability": {"level": "中高", "conditional": true}
  },

  "registers": {
    "to_me": {"median_length": 4, "question_rate": 0.124, "voice": true},
    "to_others": null,
    "note": "只有单方对话，无法比较"
  },

  "unknowns": [
    "她为什么用提问代替陈述",
    "她和王子浩现在是什么关系",
    "她线下对别人的态度是否不同"
  ]
}
```

## 字段纪律

| 字段 | 规矩 |
|---|---|
| `evidence` | 必须是 `「原话」` + 日期，不能是转述 |
| `core_fear` | 没有 2 条以上强证据 → `null` + `reason` |
| `communication.attachment` | 同上，**默认 null** |
| `registers.to_others` | 没有第二组对话 → 必须 `null` |
| `unknowns` | **必须有内容。一份没有「不知道」的画像是不诚实的** |
| `confidence` | `high`（>1000 条、跨 30 天）/ `medium`（100–1000 条）/ `low`（<100 条） |

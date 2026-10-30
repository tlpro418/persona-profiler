#!/usr/bin/env python3
"""人物画像 · 语境检索

给定一句「我准备发的话」，找出历史上最接近的语境，并展示她当时的实际反应。
不生成台词，只提供证据。

用法:
    python retrieve.py --jsonl <messages.jsonl> --query "我准备发的这句话" -k 12
    python retrieve.py --jsonl <...> --query "..." --since 2026-09-25 --sender me
"""
import argparse
import json
import math
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')


def grams(s, n=2):
    s = ''.join(s.split())
    return Counter(s[i:i + n] for i in range(max(0, len(s) - n + 1))) or Counter({s: 1})


def build_idf(docs):
    """doc frequency -> idf。让「这么」「什么」这类高频词自动降权。"""
    df = Counter()
    for g in docs:
        df.update(g.keys())
    n = max(1, len(docs))
    return {k: math.log((n + 1) / (v + 0.5)) for k, v in df.items()}


def tfidf(g, idf):
    return {k: v * idf.get(k, 1.0) for k, v in g.items()}


TOPICS = {
    'sleep':  ('睡', '困', '熬夜', '几点', '醒', '凌晨', '补觉'),
    'homework': ('作业', '卷', '写', '抄', '答案', '背书', '考试'),
    'money':  ('报销', '钱', '买', '请', '转', '块', '外卖', '汉堡', '果茶'),
    'class':  ('上课', '老师', '同桌', '班', '课', '老师'),
    'health': ('感冒', '药', '病', '难受', '疼', '发烧', '嗓子'),
    'meet':   ('见', '送', '来', '去', '一起', '哪天', '有空'),
}


def topics_of(s):
    return {k for k, kws in TOPICS.items() if any(w in s for w in kws)}


def cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def load(path, since):
    rows = []
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if since and r['date'] < since:
            continue
        rows.append(r)
    rows.sort(key=lambda r: r['ts'])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jsonl', required=True)
    ap.add_argument('--query', required=True)
    ap.add_argument('-k', type=int, default=12)
    ap.add_argument('--since', default=None)
    ap.add_argument('--sender', default='me', choices=['me', 'her'])
    ap.add_argument('--window-min', type=int, default=30, help='取她多久内的回应')
    a = ap.parse_args()

    rows = load(a.jsonl, a.since)
    human = [r for r in rows if r['sender'] in ('me', 'her')]
    cand = [(i, r) for i, r in enumerate(human) if r['sender'] == a.sender]
    doc_grams = {i: grams(r['text']) for i, r in cand}
    idf = build_idf(list(doc_grams.values()))
    qv = tfidf(grams(a.query), idf)
    qt = topics_of(a.query)
    print(f'查询：{a.query}')
    if qt:
        print(f'识别到的主题：{"、".join(sorted(qt))}')

    scored = []
    for i, r in cand:
        sim = cosine(qv, tfidf(doc_grams[i], idf))
        # 主题加权：共享主题额外加分（最多 +0.30）
        shared = len(qt & topics_of(r['text']))
        if shared:
            sim = sim + min(0.30, 0.15 * shared)
        if sim > 0.05:
            scored.append((sim, i))
    scored.sort(key=lambda x: -x[0])

    print(f'窗口：{human[0]["date"]} → {human[-1]["date"]}｜{len(human)} 条')
    print(f'在 {a.sender} 的 {sum(1 for r in human if r["sender"]==a.sender)} 条消息里找到 {len(scored)} 个相似语境')
    print()

    if not scored:
        print('没有相似语境。')
        print('这说明：你们没在这个语境下说过话 —— 这条路径是新的，无法用历史预测。')
        return

    print('=' * 68)
    print(f'最接近的 {min(a.k, len(scored))} 个语境（相似度 | 她说 → 她的下一条）')
    print('=' * 68)

    stats = {'n': 0, 'replied': 0, 'lens': [], 'followed': 0}
    for sim, i in scored[:a.k]:
        r = human[i]
        # 他前面一句（上下文）
        prev = human[i - 1] if i > 0 else None
        # 她在这之后 window_min 内的所有回应
        replies = []
        for j in range(i + 1, min(i + 14, len(human))):
            if human[j]['sender'] == 'her':
                if human[j]['ts'] - r['ts'] <= a.window_min * 60:
                    replies.append(human[j])
                else:
                    break
        stats['n'] += 1
        if replies:
            stats['replied'] += 1
            stats['lens'].append(len(replies[0]['text']))
            if len(replies) > 1:
                stats['followed'] += 1

        print(f'\n[{sim:.2f}] {r["date"]} {r["time"]}  {r["source"][:2]}')
        if prev and prev['sender'] == 'her':
            print(f'   ← 她先：{prev["text"][:60]}')
        print(f'   我：{r["text"][:70]}')
        if replies:
            for rep in replies[:3]:
                print(f'   她：{rep["text"][:60]}')
        else:
            print('   她：（无回应）')

    print()
    print('=' * 68)
    print('统计')
    print('=' * 68)
    print(f'  样本 {stats["n"]}｜她回复 {stats["replied"]}（{stats["replied"]/stats["n"]:.0%}）')
    if stats['lens']:
        import statistics
        print(f'  她首条回复长度中位 {statistics.median(stats["lens"]):.0f} 字')
        print(f'  她追加第二条的比例 {stats["followed"]/stats["replied"]:.0%}')
    print()
    print('提示：以上是历史实际反应。判断时要看「回复长度」「有无追加」「是否反问」，')
    print('      而不是只看她有没有回。')


if __name__ == '__main__':
    main()

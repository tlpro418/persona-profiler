#!/usr/bin/env python3
"""人物画像 · 量化层

从合并后的 messages.jsonl 里算出「她怎么说话」的统计事实。
只描述，不解释 —— 解释留给分析阶段。

用法:
    python quant.py --jsonl <messages.jsonl> [--since 2026-09-25] [--out quant.json]
    python quant.py --jsonl <...> --dump-bursts 15
"""
import argparse
import datetime
import json
import re
import statistics
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

EMOJI_RE = re.compile(r'^\[[^\]]{1,12}\]$')


def is_emoji(r):
    if r['type'] in ('emoji', 'image', 'video'):
        return True
    return bool(EMOJI_RE.match(r['text'].strip()))


def classify(r):
    """粗分类：他这句话属于哪种形态。"""
    t = r['text']
    if is_emoji(r):
        return 'emoji'
    if '？' in t or '?' in t:
        return 'question'
    if any(k in t for k in ('睡', '吃', '累', '感冒', '早点', '休息', '多喝', '注意', '好点')):
        return 'care'
    if any(k in t for k in ('给我', '帮我', '发我', '带', '送', '转', '借')):
        return 'request'
    if any(k in t for k in ('猪', '傻', '蠢', '屁', '菜', '哈', '笑')):
        return 'tease'
    return 'other'


def load(path, since=None):
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
    ap.add_argument('--since', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--dump-bursts', type=int, default=0)
    ap.add_argument('--gap-hours', type=float, default=2.0)
    a = ap.parse_args()

    rows = load(a.jsonl, a.since)
    human = [r for r in rows if r['sender'] in ('me', 'her')]
    if len(human) < 20:
        print('样本不足（少于 20 条），只给最粗的观察。', file=sys.stderr)

    me = [r for r in human if r['sender'] == 'me']
    her = [r for r in human if r['sender'] == 'her']

    print(f'窗口: {human[0]["date"]} → {human[-1]["date"]}｜{len(human)} 条'
          f'（我 {len(me)} / 她 {len(her)}）')
    print()

    # ---------- 长度分布
    def lendist(sub):
        L = [len(r['text']) for r in sub]
        return {
            'median': statistics.median(L),
            'mean': round(sum(L) / len(L), 1),
            'max': max(L),
            'le5': round(sum(1 for x in L if x <= 5) / len(L), 3),
        }

    le, he = lendist(me), lendist(her)
    print('=== 消息长度')
    print(f'  我  中位 {le["median"]:.0f}｜均值 {le["mean"]}｜最长 {le["max"]}｜≤5字 占 {le["le5"]:.0%}')
    print(f'  她  中位 {he["median"]:.0f}｜均值 {he["mean"]}｜最长 {he["max"]}｜≤5字 占 {he["le5"]:.0%}')
    print()

    # ---------- 标点
    print('=== 标点与语气')
    for label, sub in (('我', me), ('她', her)):
        q = sum(1 for r in sub if '？' in r['text'] or '?' in r['text'])
        ex = sum(1 for r in sub if '！' in r['text'] or '!' in r['text'])
        em = sum(1 for r in sub if is_emoji(r))
        print(f'  {label}  疑问句 {q/len(sub):.1%}｜感叹 {ex/len(sub):.1%}｜纯表情 {em/len(sub):.1%}')
    print()

    # ---------- 时段
    print('=== 活跃时段（她）')
    hh = Counter(int(r['time'].split(':')[0]) for r in her)
    peak = ', '.join(f'{h:02d}点×{c}' for h, c in hh.most_common(5))
    print(f'  高峰: {peak}')
    print()

    # ---------- 会话
    gap = a.gap_hours * 3600
    sessions, cur = [], [human[0]]
    for prev, r in zip(human, human[1:]):
        if r['ts'] - prev['ts'] > gap:
            sessions.append(cur)
            cur = [r]
        else:
            cur.append(r)
    sessions.append(cur)

    init = Counter(s[0]['sender'] for s in sessions)
    n = len(sessions)
    print(f'=== 会话 {n} 个（间隔 >{a.gap_hours:g}h 断开）')
    print(f'  我发起 {init["me"]} ({init["me"]/n:.0%})｜她发起 {init["her"]} ({init["her"]/n:.0%})')
    print()

    # ---------- 她发起时用什么开场
    print('=== 她主动开场的第一句（前 12）')
    for s in sessions:
        if s[0]['sender'] == 'her':
            print(f'  {s[0]["date"]} {s[0]["time"]}  {s[0]["text"][:40]}')
    print()

    # ---------- 反应分析：他发什么，她怎么回
    by_cat = defaultdict(lambda: {'n': 0, 'replied': 0, 'lat': [], 'len': [], 'follow': 0})
    idx = {id(r): i for i, r in enumerate(human)}
    for i, r in enumerate(human):
        if r['sender'] != 'me':
            continue
        cat = classify(r)
        # 找下一条她的消息（60 分钟内）
        nxt = None
        for j in range(i + 1, min(i + 12, len(human))):
            if human[j]['sender'] == 'her':
                if human[j]['ts'] - r['ts'] <= 3600:
                    nxt = (j, human[j])
                break
        d = by_cat[cat]
        d['n'] += 1
        if nxt:
            d['replied'] += 1
            d['lat'].append(nxt[1]['ts'] - r['ts'])
            d['len'].append(len(nxt[1]['text']))
            # 她回完 10 分钟内是否又说了一句
            j = nxt[0]
            for k in range(j + 1, min(j + 8, len(human))):
                if human[k]['sender'] == 'her' and human[k]['ts'] - human[j]['ts'] <= 600:
                    d['follow'] += 1
                    break

    print('=== 我发什么 → 她怎么回')
    print(f'  {"类型":10} {"样本":>4} {"回复率":>7} {"回复中位延迟":>12} {"回复中位长度":>12} {"她追加":>7}')
    for cat, d in sorted(by_cat.items(), key=lambda kv: -kv[1]['n']):
        if not d['n']:
            continue
        rep = d['replied'] / d['n']
        lat = f'{statistics.median(d["lat"])/60:.0f}分' if d['lat'] else '—'
        ln = f'{statistics.median(d["len"]):.0f}字' if d['len'] else '—'
        fol = f'{d["follow"]/max(1,d["replied"]):.0%}' if d['replied'] else '—'
        print(f'  {cat:10} {d["n"]:4d} {rep:6.0%} {lat:>12} {ln:>12} {fol:>7}')
    print()

    # ---------- 高频短语
    print('=== 她的高频短语（2-5 字，出现 ≥3 次）')
    cnt = Counter()
    for r in her:
        t = r['text'].strip()
        if 2 <= len(t) <= 5:
            cnt[t] += 1
    hits = [(k, v) for k, v in cnt.most_common(40) if v >= 3]
    print('  ' + '｜'.join(f'{k}×{v}' for k, v in hits[:20]))
    print()

    # ---------- burst
    if a.dump_bursts:
        scored = sorted(sessions, key=lambda s: -sum(1 for r in s if r['sender'] == 'her'))
        print(f'=== 她话最多的 {a.dump_bursts} 个会话')
        for s in scored[:a.dump_bursts]:
            hn = sum(1 for r in s if r['sender'] == 'her')
            print(f'\n--- {s[0]["date"]} {s[0]["time"]}｜共 {len(s)} 条（她 {hn}）｜发起者 {s[0]["sender"]}')
            for r in s[:6]:
                who = '我' if r['sender'] == 'me' else '她'
                print(f'    {r["time"]} {who}：{r["text"][:56]}')
        print(f'\n=== 她话最少的 {a.dump_bursts} 个会话（≥4 条）')
        short = [s for s in sessions if len(s) >= 4]
        for s in sorted(short, key=lambda s: sum(1 for r in s if r['sender'] == 'her'))[:a.dump_bursts]:
            hn = sum(1 for r in s if r['sender'] == 'her')
            print(f'\n--- {s[0]["date"]} {s[0]["time"]}｜共 {len(s)} 条（她 {hn}）')
            for r in s[:6]:
                who = '我' if r['sender'] == 'me' else '她'
                print(f'    {r["time"]} {who}：{r["text"][:56]}')

    if a.out:
        out = {
            'window': [human[0]['date'], human[-1]['date']],
            'total': len(human), 'me': len(me), 'her': len(her),
            'length': {'me': le, 'her': he},
            'sessions': n,
            'initiation': dict(init),
            'reaction': {k: {'n': v['n'], 'replied': v['replied'],
                             'follow_rate': round(v['follow'] / max(1, v['replied']), 3)}
                         for k, v in by_cat.items()},
            'top_phrases': dict(hits),
            'her_active_hours': dict(hh.most_common(8)),
        }
        json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'\n已写出: {a.out}')


if __name__ == '__main__':
    main()

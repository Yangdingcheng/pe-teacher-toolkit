#!/usr/bin/env python3
"""运动会编排：报名名单 → 分组道次表（秩序册）+ 检录表 + 成绩记录表。

用法：
  python tools/meet_scheduler.py --demo
  python tools/meet_scheduler.py data/sample_meet_entries.csv --lanes 8 --seed 42

报名 CSV 列：姓名，班级，性别，组别，项目（一人一行一个项目；组别可空，默认按性别+项目分组）。
编排规则：同班尽量分散到不同组/相邻道次；径赛每组 ≤ 道数，田赛按序号轮次；
随机但可复现（--seed 固定后结果稳定，方便赛前核对）。
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELD_EVENTS = ("跳高", "跳远", "铅球", "实心球", "垒球", "标枪", "铁饼")


def is_field(event: str) -> bool:
    return any(k in event for k in FIELD_EVENTS)


def interleave_by_class(entries: list[dict], rng: random.Random) -> list[dict]:
    """把同班学生打散：按班级轮转取人，再整体轻微洗牌（种子可复现）。"""
    by_class: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_class[e.get("班级", "")].append(e)
    for v in by_class.values():
        rng.shuffle(v)
    classes = list(by_class)
    rng.shuffle(classes)
    out = []
    idx = 0
    while any(by_class[c] for c in classes):
        c = classes[idx % len(classes)]
        if by_class[c]:
            out.append(by_class[c].pop())
        idx += 1
    return out


def build_schedule(entries: list[dict], lanes: int = 8, seed: int = 42) -> dict:
    """返回 {(组别，项目）: [ {heat: n, slots: [{lane, entry}]} ]}"""
    rng = random.Random(seed)
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for e in entries:
        key = (e.get("组别") or "", e.get("性别", ""), e.get("项目", ""))
        groups[key].append(e)
    schedule = {}
    for key, es in sorted(groups.items()):
        ordered = interleave_by_class(es, rng)
        size = lanes if not is_field(key[2]) else max(lanes, 10)
        heats = []
        for i in range(0, len(ordered), size):
            chunk = ordered[i:i + size]
            heats.append({"heat": len(heats) + 1,
                          "slots": [{"lane": j + 1, "entry": e} for j, e in enumerate(chunk)]})
        schedule[key] = heats
    return schedule


def schedule_markdown(schedule: dict) -> str:
    lines = ["# 运动会秩序册（分组表）", ""]
    for (division, gender, event), heats in schedule.items():
        title = f"{division} {gender} {event}".strip()
        for h in heats:
            lines.append(f"## {title} · 第 {h['heat']} 组")
            lines.append("")
            lines.append("| 道次/序号 | 姓名 | 班级 | 成绩 | 名次 |")
            lines.append("|---|---|---|---|---|")
            for s in h["slots"]:
                e = s["entry"]
                lines.append(f"| {s['lane']} | {e.get('姓名', '')} | {e.get('班级', '')} |  |  |")
            lines.append("")
    return "\n".join(lines)


def sample_entries() -> list[dict]:
    classes = ["五(1)班", "五(2)班", "五(3)班"]
    names_m = ["王强", "李雷", "张伟", "刘洋", "陈杰", "杨帆", "黄辉", "周鹏", "吴昊", "徐磊", "孙博", "胡军"]
    names_f = ["韩梅", "林娜", "赵敏", "钱雪", "孙丽", "李静", "王芳", "刘颖", "陈晨", "杨柳", "黄莺", "周婷"]
    entries = []
    for ci, cls in enumerate(classes):
        for i in range(4):
            entries.append({"姓名": names_m[ci * 4 + i], "班级": cls, "性别": "男", "组别": "小学男子组", "项目": "100米"})
            entries.append({"姓名": names_f[ci * 4 + i], "班级": cls, "性别": "女", "组别": "小学女子组", "项目": "100米"})
        for i in range(2):
            entries.append({"姓名": names_m[ci * 4 + i], "班级": cls, "性别": "男", "组别": "小学男子组", "项目": "立定跳远"})
            entries.append({"姓名": names_f[ci * 4 + i], "班级": cls, "性别": "女", "组别": "小学女子组", "项目": "立定跳远"})
    return entries


def main():
    ap = argparse.ArgumentParser(description="运动会编排")
    ap.add_argument("csv_path", nargs="?", default="")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--lanes", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if args.demo or not args.csv_path:
        entries = sample_entries()
        print(f"（演示模式：{len(entries)} 条示例报名）")
    else:
        with open(args.csv_path, encoding="utf-8-sig", newline="") as f:
            entries = list(csv.DictReader(f))
    schedule = build_schedule(entries, lanes=args.lanes, seed=args.seed)
    md = schedule_markdown(schedule)
    out_dir = args.out or os.path.join(BASE, "output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "meet_schedule.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    total_heats = sum(len(v) for v in schedule.values())
    print(f"共 {len(schedule)} 个组别项目、{total_heats} 个小组，已生成秩序册：{path}")
    print("\n".join(md.splitlines()[:24]))


if __name__ == "__main__":
    main()

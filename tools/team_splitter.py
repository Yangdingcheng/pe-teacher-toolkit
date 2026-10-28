#!/usr/bin/env python3
"""均衡分队：按体能蛇形分组，让每组实力接近、人数均等（可选性别均衡）。

用法：
  python tools/team_splitter.py --demo
  python tools/team_splitter.py 名单.csv --groups 6
  python tools/team_splitter.py 名单.csv --size 5      # 按每组人数反推组数

名单 CSV 列：姓名，性别（可选）,体能分（可选，0-100；没有就按名单顺序蛇形）。
蛇形分组：按体能从高到低排序后 1→N 组、N→1 组来回发牌，各组总分自然接近。
"""

from __future__ import annotations

import argparse
import csv
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def snake_split(students: list[dict], n_groups: int, gender_balance: bool = True) -> list[list[dict]]:
    groups: list[list[dict]] = [[] for _ in range(n_groups)]
    if gender_balance and any("性别" in s for s in students):
        pools = []
        for gname in ("男", "女"):
            pool = [s for s in students if s.get("性别") == gname]
            pools.append(pool)
        pools.append([s for s in students if s.get("性别") not in ("男", "女")])
    else:
        pools = [list(students)]
    for pool in pools:
        pool.sort(key=lambda s: -float(s.get("体能分") or 0))
        for i, s in enumerate(pool):
            cycle = (i // n_groups) % 2
            pos = i % n_groups
            gi = pos if cycle == 0 else n_groups - 1 - pos
            groups[gi].append(s)
    return groups


def group_stats(groups: list[list[dict]]) -> list[dict]:
    out = []
    for i, g in enumerate(groups, 1):
        scores = [float(s.get("体能分") or 0) for s in g]
        out.append({"group": i, "count": len(g),
                    "avg": round(sum(scores) / len(scores), 1) if scores else 0,
                    "total": round(sum(scores), 1)})
    return out


def sample_students() -> list[dict]:
    data = [("王强", "男", 92), ("李雷", "男", 85), ("张伟", "男", 78), ("刘洋", "男", 66),
            ("陈杰", "男", 58), ("杨帆", "男", 88), ("黄辉", "男", 73), ("周鹏", "男", 61),
            ("韩梅", "女", 90), ("林娜", "女", 82), ("赵敏", "女", 75), ("钱雪", "女", 69),
            ("孙丽", "女", 63), ("李静", "女", 86), ("王芳", "女", 71), ("刘颖", "女", 56)]
    return [{"姓名": n, "性别": g, "体能分": s} for n, g, s in data]


def main():
    ap = argparse.ArgumentParser(description="均衡分队")
    ap.add_argument("csv_path", nargs="?", default="")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--groups", type=int, default=4)
    ap.add_argument("--size", type=int, default=0, help="每组人数（优先于 --groups）")
    args = ap.parse_args()

    if args.demo or not args.csv_path:
        students = sample_students()
        print(f"（演示模式：{len(students)} 名示例学生）")
    else:
        with open(args.csv_path, encoding="utf-8-sig", newline="") as f:
            students = list(csv.DictReader(f))
    n = args.groups
    if args.size > 0:
        n = max(1, -(-len(students) // args.size))
    groups = snake_split(students, n)
    stats = {s["group"]: s for s in group_stats(groups)}
    for i, g in enumerate(groups, 1):
        st = stats[i]
        names = "、".join(f"{s['姓名']}({s.get('体能分', '-')})" for s in g)
        print(f"第 {i} 组（{st['count']} 人 · 平均体能 {st['avg']}）：{names}")


if __name__ == "__main__":
    main()

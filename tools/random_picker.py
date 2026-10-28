#!/usr/bin/env python3
"""随机点名 / 抽签：不重复抽取，抽完一轮自动重置；也可一次性随机分组。

用法：
  python tools/random_picker.py 名单.txt --count 3
  python tools/random_picker.py --demo --count 3 --seed 7
  python tools/random_picker.py 名单.csv --groups 4

名单：一行一个名字（txt）或带「姓名」列的 CSV。--seed 固定后结果可复现（适合提前备课）。
"""

from __future__ import annotations

import argparse
import csv
import os
import random

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEMO_NAMES = ["王强", "李雷", "张伟", "刘洋", "陈杰", "韩梅", "林娜", "赵敏", "钱雪", "孙丽",
              "杨帆", "黄辉", "周鹏", "吴昊", "徐磊", "孙博", "胡军", "李静", "王芳", "刘颖"]


class Picker:
    def __init__(self, names: list[str], seed: int | None = None):
        self.names = list(names)
        self.rng = random.Random(seed)
        self.pool: list[str] = []

    def pick(self, count: int = 1) -> list[str]:
        out = []
        for _ in range(count):
            if not self.pool:
                self.pool = list(self.names)
                self.rng.shuffle(self.pool)
            out.append(self.pool.pop())
        return out

    def groups(self, n_groups: int) -> list[list[str]]:
        shuffled = list(self.names)
        self.rng.shuffle(shuffled)
        out: list[list[str]] = [[] for _ in range(n_groups)]
        for i, name in enumerate(shuffled):
            out[i % n_groups].append(name)
        return out


def load_names(path: str) -> list[str]:
    if path.endswith(".csv"):
        with open(path, encoding="utf-8-sig", newline="") as f:
            return [r["姓名"].strip() for r in csv.DictReader(f) if r.get("姓名")]
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def main():
    ap = argparse.ArgumentParser(description="随机点名/抽签")
    ap.add_argument("names_path", nargs="?", default="")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--groups", type=int, default=0)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    names = DEMO_NAMES if (args.demo or not args.names_path) else load_names(args.names_path)
    if args.demo or not args.names_path:
        print(f"（演示模式：{len(names)} 人示例名单）")
    picker = Picker(names, seed=args.seed)
    if args.groups > 0:
        for i, g in enumerate(picker.groups(args.groups), 1):
            print(f"第 {i} 组（{len(g)} 人）：{'、'.join(g)}")
    else:
        picked = picker.pick(args.count)
        print("抽中：" + "、".join(picked))


if __name__ == "__main__":
    main()

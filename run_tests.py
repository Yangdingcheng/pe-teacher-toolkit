#!/usr/bin/env python3
"""体育教师工具箱 · 核心测试：python run_tests.py"""

import csv
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "tools"))

from fitness_analyzer import analyze, class_report, parse_time, score_bmi, score_points
from meet_scheduler import build_schedule, sample_entries, schedule_markdown
from random_picker import Picker
from team_splitter import group_stats, sample_students, snake_split

PASS = []
def check(name, cond):
    PASS.append((name, bool(cond)))
    print(("✅" if cond else "❌"), name)
    assert cond, name

# ---------- 时间解析 ----------
check("时间-分秒", parse_time("4:05") == 245)
check("时间-中文", parse_time("4分05秒") == 245)
check("时间-纯秒", parse_time("245") == 245)
check("时间-小数秒", parse_time("8.6") == 8.6)

# ---------- 计分 ----------
std = json.load(open(os.path.join(BASE, "data", "standards_sample.json"), encoding="utf-8"))
bp_run = std["五年级"]["男"]["50米跑"]
check("计分-满分点", score_points(bp_run, 8.0) == 100)
check("计分-及格点", score_points(bp_run, 10.2) == 60)
check("计分-插值", abs(score_points(bp_run, 8.2) - 95.0) < 0.01)
check("计分-超满分封顶", score_points(bp_run, 7.5) == 100)
bp_lung = std["五年级"]["男"]["肺活量"]
check("计分-高优项目", score_points(bp_lung, 2900) == 100 and score_points(bp_lung, 1600) == 60)
bands = std["五年级"]["男"]["BMI"]["bands"]
check("BMI-正常100", score_bmi(bands, 18.0) == 100)
check("BMI-超重80", score_bmi(bands, 23.0) == 80)
check("BMI-肥胖60", score_bmi(bands, 26.0) == 60)

# ---------- 体测分析 ----------
with open(os.path.join(BASE, "data", "sample_students.csv"), encoding="utf-8-sig", newline="") as f:
    students = list(csv.DictReader(f))
results = analyze(students, std)
check("分析-全员出分", len(results) == 12 and all("total" in r for r in results))
by_name = {r["姓名"]: r for r in results}
check("分析-等级合理", by_name["陈小强"]["level"] in ("优秀", "良好"))
check("分析-弱生定位", by_name["孙小磊"]["level"] == "不及格")
report = class_report(results)
check("报告-含分布与关注名单", "等级分布" in report and "孙小磊" in report)

# ---------- 运动会编排 ----------
entries = sample_entries()
sched = build_schedule(entries, lanes=8, seed=42)
total_slots = sum(len(h["slots"]) for heats in sched.values() for h in heats)
check("编排-人数守恒", total_slots == len(entries))
track_ok = all(len(h["slots"]) <= 8 for (d, g, ev), heats in sched.items() if "100米" in ev for h in heats)
check("编排-径赛不超道数", track_ok)
sched2 = build_schedule(entries, lanes=8, seed=42)
check("编排-同种子可复现", schedule_markdown(sched) == schedule_markdown(sched2))

# ---------- 均衡分队 ----------
students2 = sample_students()
groups = snake_split(students2, 4)
flat = [s["姓名"] for g in groups for s in g]
check("分队-全员恰好一次", sorted(flat) == sorted(s["姓名"] for s in students2))
stats = group_stats(groups)
avgs = [s["avg"] for s in stats]
check("分队-实力均衡", max(avgs) - min(avgs) <= 6)
check("分队-人数均等", all(s["count"] == 4 for s in stats))

# ---------- 随机点名 ----------
picker = Picker([f"学生{i}" for i in range(20)], seed=7)
picked = picker.pick(20)
check("点名-一轮不重复", len(set(picked)) == 20)
gs = picker.groups(4)
check("点名-分组覆盖全员", sum(len(g) for g in gs) == 20)

# ---------- CLI 演示 ----------
env = dict(os.environ)
r1 = subprocess.run([sys.executable, os.path.join(BASE, "tools", "fitness_analyzer.py"), "--demo",
                     "--out", tempfile.mkdtemp()], capture_output=True, text=True, env=env)
check("CLI-体测演示", r1.returncode == 0 and "等级分布" in r1.stdout)
r2 = subprocess.run([sys.executable, os.path.join(BASE, "tools", "pe_calc.py"), "pace", "1000", "4:05"],
                    capture_output=True, text=True, env=env)
check("CLI-配速换算", r2.returncode == 0 and "4:05" in r2.stdout)

print(f"\n全部 {len(PASS)} 项测试通过 ✅" if all(c for _, c in PASS) else "\n存在失败 ❌")

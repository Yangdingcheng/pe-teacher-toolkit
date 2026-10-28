#!/usr/bin/env python3
"""体测成绩分析：学生体质健康测试 CSV → 单项得分 / 总分 / 等级 / 班级报告。

用法：
  python tools/fitness_analyzer.py data/sample_students.csv
  python tools/fitness_analyzer.py 我的班级.csv --standards data/standards_sample.json --out 输出目录

输入 CSV 列：学号,姓名,性别,年级，身高cm，体重kg（自动算 BMI），其余列名与标准表项目名一致即可
（肺活量、50米跑、坐位体前屈、立定跳远、1分钟跳绳、1分钟仰卧起坐、引体向上、50米x8往返跑、800米跑、1000米跑）。
耐力跑成绩支持 245 / 4:05 / 4'05" / 4分05秒 四种写法。

注意：内置为示例评分表（节选整理），正式上报前请对照官方最新标准替换 standards 文件。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_time(v) -> float:
    """把 4:05 / 4'05" / 4分05秒 / 245 统一成秒（或原样数值）。"""
    if v is None or str(v).strip() == "":
        return None
    s = str(v).strip().replace("：", ":").replace("′", "'").replace("″", '"')
    try:
        return float(s)
    except ValueError:
        pass
    import re
    m = re.match(r"^(?:(\d+)\s*[:'分])?\s*(\d+(?:\.\d+)?)\s*(?:\"|秒)?$", s)
    if m:
        return int(m.group(1) or 0) * 60 + float(m.group(2))
    raise ValueError(f"无法解析成绩：{v}")


def score_points(breakpoints: list, value: float) -> float:
    """breakpoints: [[成绩, 分值], ...]，线性插值，自动识别高优/低优。"""
    pts = sorted(([float(p), float(s)] for p, s in breakpoints), key=lambda x: x[0])
    if value <= pts[0][0]:
        lo_perf, hi_perf = (pts[0], pts[1]) if len(pts) > 1 else (pts[0], pts[0])
        if lo_perf[1] >= hi_perf[1]:  # 低优项目：比最好还好 → 满分
            return pts[0][1]
        return _interp(pts[0], pts[1] if len(pts) > 1 else pts[0], value)
    if value >= pts[-1][0]:
        if pts[-1][1] >= pts[-2][1]:
            return pts[-1][1]
        return max(0.0, _interp(pts[-2], pts[-1], value))
    for a, b in zip(pts, pts[1:]):
        if a[0] <= value <= b[0]:
            return _interp(a, b, value)
    return pts[-1][1]


def _interp(a, b, v) -> float:
    if b[0] == a[0]:
        return b[1]
    t = (v - a[0]) / (b[0] - a[0])
    return a[1] + t * (b[1] - a[1])


def score_bmi(bands: list, bmi: float) -> float:
    for lo, hi, score in bands:
        if float(lo) <= bmi < float(hi) or (float(hi) >= 99 and bmi >= float(lo)):
            return float(score)
    return 60.0


def level_of(total: float) -> str:
    if total >= 90:
        return "优秀"
    if total >= 80:
        return "良好"
    if total >= 60:
        return "及格"
    return "不及格"


def analyze(students: list[dict], standards: dict) -> list[dict]:
    results = []
    for st in students:
        grade = st.get("年级", "").strip()
        gender = st.get("性别", "").strip()
        gtable = (standards.get(grade) or {}).get(gender)
        if not gtable:
            results.append({**st, "error": f"标准表缺少 {grade}/{gender}"})
            continue
        weights = standards[grade].get("权重", {})
        scores: dict[str, float] = {}
        # BMI
        try:
            h = float(st.get("身高cm") or 0) / 100
            w = float(st.get("体重kg") or 0)
            if h > 0 and w > 0:
                bmi = w / (h * h)
                st["BMI值"] = round(bmi, 1)
                spec = gtable.get("BMI")
                if isinstance(spec, dict) and spec.get("type") == "bands":
                    scores["BMI"] = score_bmi(spec["bands"], bmi)
        except ValueError:
            pass
        for item, spec in gtable.items():
            if item == "BMI" or not isinstance(spec, list):
                continue
            raw = st.get(item)
            if raw is None or str(raw).strip() == "":
                continue
            try:
                val = parse_time(raw)
                scores[item] = round(max(0.0, min(100.0, score_points(spec, val))), 1)
            except (ValueError, TypeError):
                continue
        wsum = sum(weights.get(k, 10) for k in scores)
        total = round(sum(scores[k] * weights.get(k, 10) for k in scores) / wsum, 1) if scores and wsum else 0.0
        results.append({**st, "scores": scores, "total": total,
                        "level": level_of(total), "items_done": len(scores)})
    return results


def class_report(results: list[dict], title: str = "班级体测报告") -> str:
    ok = [r for r in results if "scores" in r]
    lines = [f"# {title}", ""]
    lines.append(f"总人数 {len(results)}（有效 {len(ok)}）")
    if not ok:
        return "\n".join(lines + ["", "没有可分析的数据。"])
    totals = [r["total"] for r in ok]
    lines.append(f"平均总分 **{sum(totals) / len(totals):.1f}** · 最高 {max(totals)} · 最低 {min(totals)}")
    dist = defaultdict(int)
    for r in ok:
        dist[r["level"]] += 1
    lines.append("")
    lines.append("## 等级分布")
    for lv in ("优秀", "良好", "及格", "不及格"):
        n = dist.get(lv, 0)
        lines.append(f"- {lv}：{n} 人（{n / len(ok) * 100:.0f}%）")
    lines.append(f"- 及格率：{(len(ok) - dist.get('不及格', 0)) / len(ok) * 100:.0f}% · 优秀率：{dist.get('优秀', 0) / len(ok) * 100:.0f}%")
    per_item = defaultdict(list)
    for r in ok:
        for k, v in r["scores"].items():
            per_item[k].append(v)
    lines.append("")
    lines.append("## 各项目平均分（弱项在前）")
    for k, vs in sorted(per_item.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        lines.append(f"- {k}：{sum(vs) / len(vs):.1f}（{len(vs)} 人）")
    weak = [r for r in ok if r["level"] == "不及格"]
    if weak:
        lines.append("")
        lines.append("## 需要重点关注（不及格）")
        for r in sorted(weak, key=lambda x: x["total"]):
            low = sorted(r["scores"].items(), key=lambda kv: kv[1])[:2]
            lines.append(f"- {r.get('姓名')}（{r['total']} 分）弱项：{'、'.join(f'{k} {v}' for k, v in low)}")
    top = sorted(ok, key=lambda x: -x["total"])[:3]
    lines.append("")
    lines.append("## 班级前三")
    for r in top:
        lines.append(f"- {r.get('姓名')}：{r['total']} 分（{r['level']}）")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="体测成绩分析")
    ap.add_argument("csv_path", nargs="?", default="")
    ap.add_argument("--demo", action="store_true", help="用内置示例名单演示")
    ap.add_argument("--standards", default=os.path.join(BASE, "data", "standards_sample.json"))
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    csv_path = args.csv_path
    if args.demo or not csv_path:
        csv_path = os.path.join(BASE, "data", "sample_students.csv")
        print(f"（演示模式：{csv_path}）")
    with open(args.standards, encoding="utf-8") as f:
        standards = json.load(f)
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        students = list(csv.DictReader(f))
    results = analyze(students, standards)

    out_dir = args.out or os.path.join(BASE, "output")
    os.makedirs(out_dir, exist_ok=True)
    items = sorted({k for r in results if "scores" in r for k in r["scores"]})
    with open(os.path.join(out_dir, "scores.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["学号", "姓名", "性别", "年级", "BMI值"] + items + ["总分", "等级"])
        for r in results:
            if "scores" in r:
                w.writerow([r.get("学号"), r.get("姓名"), r.get("性别"), r.get("年级"), r.get("BMI值", "")]
                           + [r["scores"].get(k, "") for k in items] + [r["total"], r["level"]])
    report = class_report(results, title=f"体测分析报告 · {os.path.basename(csv_path)}")
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"\n已生成：{out_dir}/scores.csv 与 report.md")


if __name__ == "__main__":
    main()

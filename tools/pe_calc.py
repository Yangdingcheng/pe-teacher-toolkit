#!/usr/bin/env python3
"""运动换算小工具：配速 / BMI / 靶心率 / 成绩格式互转。

用法：
  python tools/pe_calc.py pace 1000 4:05        # 1000米用时 → 配速（/公里）与速度
  python tools/pe_calc.py pace 50 8.0 --predict 100   # 由 50 米成绩粗估 100 米（里格尔公式，仅供参考）
  python tools/pe_calc.py bmi 142 38            # 身高cm 体重kg → BMI 与参考等级
  python tools/pe_calc.py heartrate 12          # 年龄 → 最大心率与有氧靶心率区间
  python tools/pe_calc.py time 245              # 秒 ↔ 分:秒 互转
"""

from __future__ import annotations

import argparse

from fitness_analyzer import parse_time  # 同目录复用


def fmt_time(seconds: float) -> str:
    seconds = round(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def cmd_pace(distance_m: float, time_str: str, predict_m: float = 0):
    t = parse_time(time_str)
    pace = t / (distance_m / 1000)
    speed = distance_m / t * 3.6
    print(f"{distance_m:g} 米用时 {fmt_time(t)}（{t:g} 秒）")
    print(f"  平均配速：{fmt_time(pace)} /公里 · 平均速度：{speed:.1f} km/h")
    if predict_m:
        pred = t * (predict_m / distance_m) ** 1.06  # 里格尔公式
        print(f"  粗估 {predict_m:g} 米成绩：约 {fmt_time(pred)}（里格尔公式，短距离外推仅供参考）")


def cmd_bmi(height_cm: float, weight_kg: float):
    bmi = weight_kg / (height_cm / 100) ** 2
    if bmi < 18.5:
        band = "偏低（成人参考）"
    elif bmi < 24:
        band = "正常（成人参考）"
    elif bmi < 28:
        band = "超重（成人参考）"
    else:
        band = "肥胖（成人参考）"
    print(f"身高 {height_cm:g}cm · 体重 {weight_kg:g}kg → BMI = {bmi:.1f}（{band}）")
    print("  提示：学生体测请用 fitness_analyzer 按年级性别查标准表分档，不要用成人参考。")


def cmd_heartrate(age: int):
    hrmax = 220 - age
    print(f"年龄 {age} → 估算最大心率 {hrmax} 次/分")
    print(f"  有氧健身区（60%–80%）：{round(hrmax * 0.6)} – {round(hrmax * 0.8)} 次/分")
    print(f"  热身/恢复区（50%–60%）：{round(hrmax * 0.5)} – {round(hrmax * 0.6)} 次/分")
    print("  提示：220-年龄为粗略公式，个体差异大；课堂上以学生主观感受与表现为准。")


def cmd_time(value: str):
    t = parse_time(value)
    print(f"{value} = {t:g} 秒 = {fmt_time(t)}")


def main():
    ap = argparse.ArgumentParser(description="运动换算小工具")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("pace")
    p1.add_argument("distance", type=float)
    p1.add_argument("time")
    p1.add_argument("--predict", type=float, default=0)
    p2 = sub.add_parser("bmi")
    p2.add_argument("height_cm", type=float)
    p2.add_argument("weight_kg", type=float)
    p3 = sub.add_parser("heartrate")
    p3.add_argument("age", type=int)
    p4 = sub.add_parser("time")
    p4.add_argument("value")
    args = ap.parse_args()
    if args.cmd == "pace":
        cmd_pace(args.distance, args.time, args.predict)
    elif args.cmd == "bmi":
        cmd_bmi(args.height_cm, args.weight_kg)
    elif args.cmd == "heartrate":
        cmd_heartrate(args.age)
    elif args.cmd == "time":
        cmd_time(args.value)


if __name__ == "__main__":
    main()

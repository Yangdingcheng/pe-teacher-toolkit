# 体育教师工具箱 🏃

给体育老师的五个效率小工具，全部纯 Python 标准库、零依赖、离线可用，
专治最耗时间的事务性工作：体测算分、运动会编排、课堂分组、点名抽签、成绩换算。

## 工具一览

| 工具 | 解决什么 | 一行命令 |
|---|---|---|
| 体测成绩分析 `tools/fitness_analyzer.py` | 体测 CSV 批量算单项分/总分/等级，自动出班级报告与关注名单 | `python tools/fitness_analyzer.py 名单.csv` |
| 运动会编排 `tools/meet_scheduler.py` | 报名名单一键生成分组道次秩序册，同班自动打散，种子可复现 | `python tools/meet_scheduler.py --demo` |
| 均衡分队 `tools/team_splitter.py` | 按体能蛇形分组，各组实力接近、人数均等、性别均衡 | `python tools/team_splitter.py --demo` |
| 随机点名 `tools/random_picker.py` | 不重复抽点（抽完一轮才重置），也可随机分组 | `python tools/random_picker.py 名单.txt --count 3` |
| 运动换算 `tools/pe_calc.py` | 配速/速度/成绩预估、BMI、靶心率区间、时间格式互转 | `python tools/pe_calc.py pace 1000 4:05` |

每个工具都有 `--demo`，不带自己的数据也能先跑起来看效果；`python run_tests.py` 是 26 项自检。

## 体测成绩分析（最重头的一个）

输入 CSV：`学号,姓名,性别,年级，身高cm，体重kg` + 各项目原始成绩
（肺活量、50米跑、坐位体前屈、立定跳远、1分钟跳绳、1分钟仰卧起坐、引体向上、50米x8往返跑、800/1000米跑）。
耐力跑成绩写 `4:05`、`4分05秒`、`245` 都认。输出：

- `scores.csv`：每人每项得分、BMI 值、总分、等级（优秀 ≥90 / 良好 ≥80 / 及格 ≥60）
- `report.md`：班级平均分、等级分布、及格率与优秀率、各项目平均分（弱项在前）、
  不及格学生名单及其最弱的两项、班级前三

计分按标准表断点线性插值，权重按年级配置在标准表 JSON 里。
**重要**：仓库内 `data/standards_sample.json` 是按公开框架节选整理的**示例评分表**
（覆盖五年级与初一），数值可能与最新官方文件有出入——正式上报前请对照
《国家学生体质健康标准》最新文件核对/替换该 JSON，工具逻辑不用改。

## 运动会编排规则

按（组别 × 性别 × 项目）分组；径赛每组不超过道数（默认 8），田赛按序号轮转；
同班选手用轮转取人打散，尽量不扎堆同组；`--seed` 固定后编排结果可复现，赛前核对不怕变。

## 均衡分队算法

蛇形发牌：体能从高到低排序后按 1→N 组、N→1 组来回分配，各组总分自然接近
（演示 16 人分 4 组，各组平均体能 74.0 / 74.5 / 75.5 / 74.2）；男女分别蛇形后再合并，性别也均衡。
没有体能分时按名单顺序蛇形，至少保证人数均等。

## 目录

```
tools/
  fitness_analyzer.py   体测成绩分析（计分引擎 + 班级报告）
  meet_scheduler.py     运动会编排
  team_splitter.py      均衡分队
  random_picker.py      随机点名/抽签
  pe_calc.py            运动换算
data/
  standards_sample.json 示例评分表（五年级/初一，务必核对官方标准）
  sample_students.csv   示例体测名单（12 人）
run_tests.py            26 项测试
```

教案与备课请搭配姊妹项目 LessonForge（教案工作台）使用。

## License

MIT

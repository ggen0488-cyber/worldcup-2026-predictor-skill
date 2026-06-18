# 2026 世界杯预测 Skill / World Cup 2026 Predictor Skill

中文 | [English](#english)

一个开源、平台中立的 AI skill，用于 2026 世界杯概率预测。

本项目结合了可编辑的 Elo 风格球队评级、默认考虑足球偶然性的泊松比分模型，以及蒙特卡洛整届赛事模拟。它还包含一个可选的、仅供娱乐的玄学模式。

本项目不是 FIFA 官方项目，不与 FIFA 存在隶属、认可或赞助关系。请勿在本项目中使用 FIFA 标志、官方视觉、官方字体或其他受保护品牌资产。

## 仓库结构

```text
.
├── README.md
├── LICENSE
├── .gitignore
└── worldcup-2026-predictor/
    ├── SKILL.md
    ├── scripts/
    ├── references/
    └── data/
```

`worldcup-2026-predictor/` 是可移植的 skill 目录。你可以把它复制到兼容的 AI skill 运行环境，也可以直接在命令行运行其中的脚本。

## 功能

- 预测单场胜/平/负概率和最可能比分。
- 模拟小组晋级概率，包含 8 个最佳第三名。
- 模拟夺冠、进决赛、进四强、进八强、晋级 32 强概率。
- 生成一次抽样的淘汰赛路径。
- 从 `data/results.json` 锁定真实已完赛赛果。
- 可选输出仅供娱乐的玄学预测。

## 快速开始

需要 Python 3.9+，不依赖第三方库。

```bash
SKILL_DIR=worldcup-2026-predictor

python "$SKILL_DIR/scripts/predict.py" match ARG BRA --seed 7
python "$SKILL_DIR/scripts/predict.py" group C --sims 5000 --seed 7
python "$SKILL_DIR/scripts/predict.py" champion --sims 10000 --seed 7
python "$SKILL_DIR/scripts/predict.py" bracket --seed 7
python "$SKILL_DIR/scripts/divination.py" ARG BRA --date 0617
```

球队输入支持代码（`ARG`）、英文名（`Argentina`）或中文名（`阿根廷`）。

## 模型概要

默认理性模型：

```text
可编辑 Elo 风格评级
  -> 预期进球
  -> 默认考虑足球偶然性的泊松比分模型
  -> 蒙特卡洛整届赛事模拟
```

足球偶然性默认进入模型：

- 泊松比分抽样。
- 单场状态、战术匹配、临场噪声冲击。
- 胜/平/负概率向中性足球基线轻微收缩。

模型输出的是概率，不是确定性结论。高概率球队仍然可能在单场比赛中输球。

## 数据策略

`references/teams.json` 是可编辑的离线样例快照，不是官方实时数据库。如果你需要当前小组、阵容、赛果或评级，请在预测前更新 JSON 文件。

`data/results.json` 用于保存已完赛赛果。赛果按阶段（`GROUP`、`R32`、`R16`、`QF`、`SF`、`F`）和球队组合锁定，因此同两队在后续阶段再次交手时不会复用早前比分。

## 玄学模式

玄学模式是可选功能，仅供娱乐。除非用户明确要求，否则默认理性模型不会使用玄学结果。

## 许可证

MIT License。见 `LICENSE`。

---

## English

[中文](#2026-世界杯预测-skill--world-cup-2026-predictor-skill) | English

An open, platform-neutral AI skill for probabilistic 2026 World Cup predictions.

The skill combines editable Elo-style team ratings, a football-randomness-adjusted Poisson score model, and Monte Carlo tournament simulation. It also includes an optional entertainment-only divination mode.

This project is not affiliated with, endorsed by, or sponsored by FIFA. Do not use FIFA logos, official artwork, official fonts, or other protected brand assets with this project.

## Repository Layout

```text
.
├── README.md
├── LICENSE
├── .gitignore
└── worldcup-2026-predictor/
    ├── SKILL.md
    ├── scripts/
    ├── references/
    └── data/
```

The `worldcup-2026-predictor/` directory is the portable skill. Copy that directory into any compatible AI skill runtime or use the scripts directly from the command line.

## What It Does

- Predict single-match win/draw/loss probabilities and likely scorelines.
- Simulate group advancement, including the 8 best third-placed teams.
- Simulate champion, finalist, semifinal, quarterfinal, and Round-of-32 odds.
- Generate one sampled knockout bracket path.
- Lock real completed results from `data/results.json`.
- Optionally run entertainment-only divination output.

## Quick Start

Requires Python 3.9+ and no third-party dependencies.

```bash
SKILL_DIR=worldcup-2026-predictor

python "$SKILL_DIR/scripts/predict.py" match ARG BRA --seed 7
python "$SKILL_DIR/scripts/predict.py" group C --sims 5000 --seed 7
python "$SKILL_DIR/scripts/predict.py" champion --sims 10000 --seed 7
python "$SKILL_DIR/scripts/predict.py" bracket --seed 7
python "$SKILL_DIR/scripts/divination.py" ARG BRA --date 0617
```

Team inputs accept codes (`ARG`), English names (`Argentina`), or Chinese names (`阿根廷`).

## Model Summary

The default rational model is:

```text
editable Elo-style ratings
  -> expected goals
  -> football-randomness-adjusted Poisson score model
  -> Monte Carlo tournament simulation
```

Football randomness is built in by default through:

- Poisson score sampling.
- A one-match form/tactics/noise shock.
- Light win/draw/loss probability shrinkage toward a neutral football baseline.

The model outputs probabilities, not certainties. A high-probability team can still lose a single match.

## Data Policy

`references/teams.json` is an editable offline snapshot, not an official real-time database. If you need current groups, squads, match results, or ratings, update the JSON files before running predictions.

`data/results.json` stores completed match results. Results are locked by stage (`GROUP`, `R32`, `R16`, `QF`, `SF`, `F`) and team pair, so the same two teams can meet again in a later stage without reusing an earlier score.

## Divination Mode

Divination mode is optional and for entertainment only. It is never used in the default rational model unless the user explicitly asks for it.

## License

MIT License. See `LICENSE`.

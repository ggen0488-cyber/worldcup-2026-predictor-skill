# 2026 世界杯预测 Skill / World Cup 2026 Predictor Skill

中文 | [English](#english)

一个开源、平台中立的 AI skill，用于 2026 世界杯概率预测。

本项目用于在 AI Agent 收集并保存赛程/赛果数据和赛前情报后，结合可编辑的 Elo 风格球队评级、默认考虑足球偶然性的泊松比分模型，以及蒙特卡洛整届赛事模拟进行预测。它还包含一个可选的、仅供娱乐的玄学模式。

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

## 安装

需要 Python 3.9+，脚本不依赖第三方库。安装时只复制 `worldcup-2026-predictor/` 这个目录；`data/live/` 是运行时缓存，不需要提交或分发。

先克隆仓库：

```bash
git clone https://github.com/ggen0488-cyber/worldcup-2026-predictor-skill.git
cd worldcup-2026-predictor-skill
```

### Codex

推荐安装为用户级 skill，所有 Codex 项目都可用：

```bash
mkdir -p ~/.agents/skills
cp -R worldcup-2026-predictor ~/.agents/skills/
```

也可以安装为项目级 skill，把目录复制到当前项目的 `.agents/skills/`：

```bash
mkdir -p .agents/skills
cp -R worldcup-2026-predictor .agents/skills/
```

在 Codex 中可用 `$worldcup-2026-predictor` 显式调用，或直接提出“预测阿根廷 vs 巴西”等请求让 Agent 自动匹配。若新 skill 没出现，重启 Codex 会话。

### Claude Code

安装为个人 skill：

```bash
mkdir -p ~/.claude/skills
cp -R worldcup-2026-predictor ~/.claude/skills/
```

或安装为当前项目 skill：

```bash
mkdir -p .claude/skills
cp -R worldcup-2026-predictor .claude/skills/
```

在 Claude Code 中可用 `/worldcup-2026-predictor` 调用，也可以用自然语言触发。Claude Code 会读取 skill 目录中的 `SKILL.md` 和附带资源。

### OpenClaw

安装到当前 OpenClaw workspace：

```bash
mkdir -p skills
cp -R worldcup-2026-predictor skills/
```

安装为所有本机 OpenClaw agent 共享的 skill：

```bash
mkdir -p ~/.openclaw/skills
cp -R worldcup-2026-predictor ~/.openclaw/skills/
```

也可以在克隆后的仓库中使用 OpenClaw CLI 安装本地目录：

```bash
openclaw skills install ./worldcup-2026-predictor --as worldcup-2026-predictor
```

### Windows PowerShell

如果使用 PowerShell，把上面的 `mkdir -p` / `cp -R` 换成：

```powershell
git clone https://github.com/ggen0488-cyber/worldcup-2026-predictor-skill.git
Set-Location worldcup-2026-predictor-skill

New-Item -ItemType Directory -Force "$HOME\.agents\skills"
Copy-Item -Recurse -Force ".\worldcup-2026-predictor" "$HOME\.agents\skills\"
```

把目标目录替换为 `$HOME\.claude\skills`、当前项目的 `.agents\skills` / `.claude\skills`，或 `$HOME\.openclaw\skills` 即可。

## 功能

- 预测单场胜/平/负概率和最可能比分。
- 模拟小组晋级概率，包含 8 个最佳第三名。
- 模拟夺冠、进决赛、进四强、进八强、晋级 32 强概率。
- 生成一次抽样的淘汰赛路径。
- 从 `data/results.json` 锁定真实已完赛赛果。
- 优先读取 AI Agent 保存到 `data/live/` 的最新数据快照。
- 读取 AI Agent 保存的赛前情报快照，用伤停、阵容、近期状态、赛程体能、战术对位等信息做有界修正。
- 玄学模式可读取 AI Agent 保存的起卦背景快照，用比赛日期、地点、颜色象意和用户问题确定娱乐语境。
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
  -> Agent 赛前情报修正
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

数据收集由 AI Agent 负责，不在脚本中写死单一数据源。预测前，Agent 应从官方或可靠来源检索当前小组、赛程、赛果和可用评级，并将标准化快照保存到 `data/live/`。`data/live/` 是本地生成缓存，已在 `.gitignore` 中忽略，不会提交到 GitHub。

当前单场预测前，Agent 还应从多个方面收集两队赛前情报，例如伤停/停赛、预计首发、近期状态、赛程体能、场地天气、战术对位、比赛动机、赔率或评级变化，并保存为 `data/live/intelligence.json`。该快照只提供有界修正，不能消除足球比赛本身的随机性。

如果无法获得足够新的来源，应明确说明情报不足，只能基于已有快照或样例做离线演示，不要把旧数据包装成实时分析。

玄学模式也可以使用 Agent 收集的背景资料。当前玄学预测前，Agent 可保存 `data/live/divination_context.json`，包含比赛日期、开球时间、举办城市、场地、双方颜色/象征、用户问题和来源。该快照只用于起卦语境和展示，不证明玄学预测可靠。

`references/teams.json` 是可编辑的离线样例快照，不是官方实时数据库。存在 `data/live/teams.json` 和 `data/live/results.json` 时，预测脚本会优先读取这些 Agent 保存的快照；否则回退到样例数据。

`data/live/teams.json` 格式与 `references/teams.json` 相同。`data/live/results.json` 格式与 `data/results.json` 相同。`data/live/intelligence.json` 格式见 `worldcup-2026-predictor/references/intelligence.md`。`data/live/divination_context.json` 格式见 `worldcup-2026-predictor/references/divination.md`。建议在 live 文件的 `_meta` 中记录来源 URL、采集时间和必要说明。

预测脚本会校验参赛队伍完整性：必须是 48 队、A-L 共 12 个小组、每组 4 队。若 Agent 保存的 live 快照不完整，脚本会停止而不是继续模拟。

`data/results.json` 用于保存已完赛赛果。赛果按阶段（`GROUP`、`R32`、`R16`、`QF`、`SF`、`F`）和球队组合锁定，因此同两队在后续阶段再次交手时不会复用早前比分。

## 玄学模式

玄学模式是可选功能，仅供娱乐。除非用户明确要求，否则默认理性模型不会使用玄学结果。

## 许可证

MIT License。见 `LICENSE`。

---

## English

[中文](#2026-世界杯预测-skill--world-cup-2026-predictor-skill) | English

An open, platform-neutral AI skill for probabilistic 2026 World Cup predictions.

After an AI Agent collects and saves schedule/result data and pre-match intelligence, this project combines editable Elo-style team ratings, a football-randomness-adjusted Poisson score model, and Monte Carlo tournament simulation. It also includes an optional entertainment-only divination mode.

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

## Installation

Requires Python 3.9+ and no third-party dependencies. Install by copying only the `worldcup-2026-predictor/` directory. `data/live/` is runtime cache and should not be committed or distributed.

Clone the repository first:

```bash
git clone https://github.com/ggen0488-cyber/worldcup-2026-predictor-skill.git
cd worldcup-2026-predictor-skill
```

### Codex

Install as a user-level skill available to all Codex projects:

```bash
mkdir -p ~/.agents/skills
cp -R worldcup-2026-predictor ~/.agents/skills/
```

Or install as a project-level skill:

```bash
mkdir -p .agents/skills
cp -R worldcup-2026-predictor .agents/skills/
```

In Codex, invoke it explicitly with `$worldcup-2026-predictor`, or ask naturally for a World Cup prediction. Restart the Codex session if the new skill is not detected.

### Claude Code

Install as a personal skill:

```bash
mkdir -p ~/.claude/skills
cp -R worldcup-2026-predictor ~/.claude/skills/
```

Or install as a project skill:

```bash
mkdir -p .claude/skills
cp -R worldcup-2026-predictor .claude/skills/
```

In Claude Code, invoke it with `/worldcup-2026-predictor` or by natural language. Claude Code reads the `SKILL.md` file and bundled resources from the skill directory.

### OpenClaw

Install into the current OpenClaw workspace:

```bash
mkdir -p skills
cp -R worldcup-2026-predictor skills/
```

Install as a machine-wide OpenClaw skill:

```bash
mkdir -p ~/.openclaw/skills
cp -R worldcup-2026-predictor ~/.openclaw/skills/
```

You can also install the local skill directory with the OpenClaw CLI after cloning:

```bash
openclaw skills install ./worldcup-2026-predictor --as worldcup-2026-predictor
```

### Windows PowerShell

If you use PowerShell, replace `mkdir -p` / `cp -R` with:

```powershell
git clone https://github.com/ggen0488-cyber/worldcup-2026-predictor-skill.git
Set-Location worldcup-2026-predictor-skill

New-Item -ItemType Directory -Force "$HOME\.agents\skills"
Copy-Item -Recurse -Force ".\worldcup-2026-predictor" "$HOME\.agents\skills\"
```

Change the destination to `$HOME\.claude\skills`, project-local `.agents\skills` / `.claude\skills`, or `$HOME\.openclaw\skills` as needed.

## What It Does

- Predict single-match win/draw/loss probabilities and likely scorelines.
- Simulate group advancement, including the 8 best third-placed teams.
- Simulate champion, finalist, semifinal, quarterfinal, and Round-of-32 odds.
- Generate one sampled knockout bracket path.
- Lock real completed results from `data/results.json`.
- Prefer fresh snapshots saved by an AI Agent under `data/live/`.
- Read Agent-saved pre-match intelligence snapshots for bounded adjustments based on injuries, lineups, form, rest, tactics, and related context.
- Let divination mode read Agent-saved context snapshots for match date, venue, colors/symbols, and user question as entertainment framing.
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
  -> Agent pre-match intelligence adjustment
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

Data collection is the AI Agent's responsibility and is not hardcoded to a single source in the scripts. Before prediction, the Agent should collect current groups, fixtures, results, and usable ratings from official or reliable sources, then save a normalized snapshot under `data/live/`. `data/live/` is generated local cache and is ignored by `.gitignore`.

Before a current single-match prediction, the Agent should also collect pre-match intelligence across team availability, likely lineups, recent form, rest/travel load, venue/weather, tactical matchup, match incentives, and market/rating movement, then save it as `data/live/intelligence.json`. This snapshot provides bounded adjustments only; it does not remove football randomness.

If sufficiently fresh sources are unavailable, say so explicitly and treat the output as an offline demo based on existing snapshots or samples, not as real-time analysis.

Divination mode can also use Agent-collected context. Before a current divination request, the Agent may save `data/live/divination_context.json` with match date, kickoff time, host city, venue, team colors/symbols, user question, and sources. This snapshot is only for casting context and display; it does not make divination reliable.

`references/teams.json` is an editable offline sample snapshot, not an official real-time database. When `data/live/teams.json` and `data/live/results.json` exist, the prediction script prefers those Agent-saved snapshots; otherwise it falls back to the sample data.

`data/live/teams.json` uses the same format as `references/teams.json`. `data/live/results.json` uses the same format as `data/results.json`. `data/live/intelligence.json` is documented in `worldcup-2026-predictor/references/intelligence.md`. `data/live/divination_context.json` is documented in `worldcup-2026-predictor/references/divination.md`. Include source URLs, collection time, and notes in `_meta` when saving live files.

The prediction script validates team completeness: exactly 48 teams, 12 groups from A to L, and 4 teams per group. If an Agent-saved live snapshot is incomplete, the script stops instead of simulating from partial data.

`data/results.json` stores completed match results. Results are locked by stage (`GROUP`, `R32`, `R16`, `QF`, `SF`, `F`) and team pair, so the same two teams can meet again in a later stage without reusing an earlier score.

## Divination Mode

Divination mode is optional and for entertainment only. It is never used in the default rational model unless the user explicitly asks for it.

## License

MIT License. See `LICENSE`.

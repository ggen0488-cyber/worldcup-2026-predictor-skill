---
name: worldcup-2026-predictor
description: Predict and simulate 2026 FIFA World Cup (USA/Canada/Mexico) matches, groups, champion odds, and knockout brackets after the AI Agent collects and saves current data snapshots. Use when the user asks to predict "X vs Y", scorelines, group advancement, "谁会赢/谁会夺冠", tournament simulations, bracket paths, football randomness/upset scenarios, or for-entertainment 算卦/玄学 predictions. Supports Agent-supplied live data, editable team ratings, stage-aware real-result locking, best-third-place advancement, built-in upset variance, and optional I Ching/Five Elements/zodiac/numerology output.
---

# 2026 世界杯预测 ⚽🔮

对 2026 美加墨世界杯做离线概率预测：单场比分、小组晋级、夺冠概率、淘汰赛路径。
默认使用**理性模型**（Elo → 波动修正泊松比分 → 蒙特卡洛）；用户明确要求时才叠加**玄学模式**（仅供娱乐）。

本 skill 非 FIFA 官方项目，不与 FIFA 存在隶属、认可或赞助关系。输出只用于概率分析和娱乐，不构成官方赛程、赛果或确定性判断。

## 使用脚本

从当前 skill 根目录运行脚本，不要假设固定安装路径。下例用 `$SKILL_DIR` 表示 `worldcup-2026-predictor` 目录：

### 理性预测（默认）
```bash
python3 "$SKILL_DIR/scripts/predict.py" match 阿根廷 巴西 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" group C --sims 5000
python3 "$SKILL_DIR/scripts/predict.py" champion --sims 10000 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" bracket --seed 7
```

- 球队名支持代码（`ARG`）、英文（`Argentina`）或中文（`阿根廷`）。
- `group` 输出晋级 32 强概率，已纳入 8 个最佳第三名。
- `champion`/`group` 可调 `--sims`；`--seed` 用于复现；单场加 `--neutral` 可去掉东道主加成。
- 足球偶然性已默认进入模型：泊松比分抽样 + 单场状态冲击 + 胜平负概率收缩，不需要额外参数。
- `bracket` 输出一次抽样的每轮淘汰赛路径，当前使用简化蛇形种子对阵，非 FIFA 官方槽位映射。
- 预测脚本不联网抓数据；若存在 `data/live/teams.json` 或 `data/live/results.json`，会优先读取这些由 Agent 保存的快照。

### 玄学模式（需用户主动开启）
```bash
python3 "$SKILL_DIR/scripts/divination.py" 阿根廷 巴西
python3 "$SKILL_DIR/scripts/divination.py" 阿根廷 巴西 --factor
```
三种玩法（按用户意图选）：**纯玄学** / **科学+玄学并列** / **玄学加权**（把 `--factor` 叠加到泊松胜率，得"开过光的概率"）。详见 `references/divination.md`。
**玄学输出必须附带：「⚠️ 玄学预测仅供娱乐，认真你就输了」。**

## 工作流程
1. 判定用户要单场、小组、夺冠榜、淘汰赛路径，或是否明确要求玄学。
2. 预测前由 Agent 主动查找官方或可靠来源，收集当前小组、赛程、已完赛比分和可用评级；不要把数据源硬编码进脚本。
3. 将收集结果保存为本地快照：`data/live/teams.json` 使用 `references/teams.json` 的结构，`data/live/results.json` 使用 `data/results.json` 的结构，并在 `_meta` 记录来源 URL、采集时间和说明。
4. 调用脚本，脚本会优先读取 `data/live/` 快照；若没有 live 快照，则回退到样例数据。
5. 保留脚本的中文概率表格，再补一两句精炼解读；如果用户强调足球偶然性，说明模型默认已考虑冷门路径。
6. 涉及整届模拟时优先用 `--sims 10000`；需要快速反馈可降到 `2000`；需要复现时加 `--seed`。

## 重要约束
- 不得暗示这是 FIFA 官方工具；不要使用 FIFA 官方 logo、赛事视觉、字体或其他受保护品牌资产。
- 只说**概率**，不说"必胜/一定"；区分"理性"与"玄学"两类来源。
- 明确足球单场随机性很高；强队高概率不等于稳胜，低概率队也有冷门路径。
- `references/teams.json` 是可编辑离线样例快照；如果用户要求当前预测，先写入 `data/live/` 快照，不要把旧样例数据包装成实时预测。
- `data/live/results.json` 与 `data/results.json` 都会按阶段锁定真实比分；同两队在不同阶段再次交手时，不会复用旧阶段比分。
- 玄学纯属娱乐，不得包装成可信预测。

## 参考文档（按需阅读）
- `references/model.md` — 理性模型数学原理与已知简化
- `references/divination.md` — 玄学四术算法与三种呈现/加权方式
- `references/output_format.md` — 输出规范与调用速查
- `references/teams.json` — 48队评级/分组/颜色（可编辑）
- `data/results.json` — 真实赛果（滚动追加）

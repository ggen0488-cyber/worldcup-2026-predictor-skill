# 输出规范

脚本已自带格式化输出（中文 + 概率条 + 表格）。AI 助手直接转述脚本结果即可，无需重排，但可做精炼解读。

## 各场景输出要点

| 命令 | 核心输出 | 助手补充 |
|------|---------|-------------|
| `match A B` | 胜/平/负% + 预期进球 + 最可能比分Top5 | 一句话点评谁占优，并提醒单场有冷门空间 |
| `group X` | 晋级32强%、前二%、小组第一%、最佳第三%、预测排名 | 说明已纳入8个最佳第三名 |
| `champion` | 夺冠/进决赛/4强/8强/32强 概率榜 | 点出夺冠热门梯队和不确定性 |
| `bracket` | 单次抽样的每轮对阵、晋级队与冠军 | 强调这是一次模拟，且当前为简化蛇形对阵 |

## 概率表述纪律
- 一律用**概率/百分比**，不说"必胜""一定"。
- 明确足球随机性大；高概率只代表长期模拟优势，不代表单场确定。模型默认已纳入冷门和临场波动。
- 区分"理性预测"与"玄学预测"，不可混淆来源。
- 玄学结果必带娱乐免责声明。
- 涉及最新小组、赛程、赛果时，由 Agent 先核验来源并保存 `data/live/teams.json` / `data/live/results.json`。
- `data/live/results.json` 与 `data/results.json` 使用阶段锁定，阶段值为 `GROUP`/`R32`/`R16`/`QF`/`SF`/`F`。

## 常用调用速查
```bash
SKILL_DIR=/path/to/worldcup-2026-predictor
python3 "$SKILL_DIR/scripts/predict.py" match 阿根廷 巴西 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" group C --sims 5000 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" champion --sims 10000 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" bracket --seed 7
python3 "$SKILL_DIR/scripts/divination.py" 阿根廷 巴西
python3 "$SKILL_DIR/scripts/divination.py" 阿根廷 巴西 --factor
```

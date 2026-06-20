# 输出规范

脚本已自带格式化输出（中文 + 概率条 + 表格）。AI 助手先用脚本结果做依据，再生成本地 HTML 报告作为最终展示；聊天回复只需要给出文件路径、是否已打开和一句简短解读。

所有理性预测命令和玄学命令都支持 `--json`。生成 HTML 时优先使用 JSON 中的 `main_prediction`、`score_distribution`、`reasons`、`simulation_error_95_max`、`advisory` 等字段。

## 各场景输出要点

| 命令 | 核心输出 | 助手补充 |
|------|---------|-------------|
| `match A B` | 主预测赛果 + 主预测比分 + 胜/平/负% + 预期进球 + 赛前情报修正 + 比分分布Top5 | 高亮胜/平/负三项中概率最高的赛果方向；其他比分只能作为分布参考 |
| `match A B --knockout` | 晋级倾向 + 常规时间比分 + 若点球决胜的点球比分 + 胜/平/负% | 说明淘汰赛最终只有晋级方，平局只代表常规时间/加时路径 |
| `group X` | 晋级32强%、前二%、小组第一%、最佳第三%、预测排名 | 说明已纳入8个最佳第三名 |
| `champion` | 夺冠/进决赛/4强/8强/32强 概率榜 | 点出夺冠热门梯队和不确定性 |
| `route TEAM` | 进入32强/16强/8强/4强/决赛/夺冠概率 + 每轮常见对手 | 展示完整晋级路线、每轮条件对手概率和关键风险 |
| `bracket` | 单次抽样的每轮对阵、晋级队与冠军 | 强调这是一次模拟，展示完整晋级路线和每轮风险 |
| `divination A B` | 起卦背景 + 本卦/变卦/变爻 + 五行/生肖/命理 + 气运因子 + 断语原因 | 不把背景资料包装成可信依据 |

## HTML 报告

- 预测完成后按 `references/html_report.md` 生成自包含 HTML 文件，默认保存到 `reports/`。
- HTML 由 Agent 直接写出，不调用额外生成脚本；CSS 和必要交互写在同一文件中。优先调用脚本的 `--json` 输出作为数据源，避免从自然语言文本中反解析概率。
- 报告首屏应构建球场场景，并用真实球场/转播比分牌风格突出显示概率最高的主预测结果。
- 报告应包含核心概率、主预测比分、比分分布 Top 5、预期进球、预测原因说明、情报摘要、战术对位、场景推演、来源和不确定性说明；玄学内容只在用户要求时分区展示，并说明卦象、象意和断语原因。
- 生成后自动打开：Windows 用 `Start-Process`，macOS 用 `open`，Linux 用 `xdg-open`。如果用户明确不要打开，则只返回路径。
- 最终聊天回复不要重复整份报告内容，只说明 HTML 文件路径、打开状态和关键结论。

## 概率表述纪律
- 一律用**概率/百分比**，不说"必胜""一定"。
- 最终聊天回复和 HTML 报告都要提醒：预测结果仅供参考，请理性观赛。
- 主预测结果只能有一个：以胜/平/负或晋级方向中概率最高者为准，并在 HTML 比分牌中最突出显示。单一最高概率比分若与主方向不一致，只能标为“比分分布参考”。
- 积分赛、小组赛和联赛可以展示胜/平/负；淘汰赛必须展示晋级方、常规时间比分，以及进入点球时的点球比分预测。
- 每次预测都要解释原因：至少说明评级/预期进球、赛前情报、赛制路径、随机性和关键风险中的相关项。HTML 中必须有独立“预测原因”区。
- 如果用户只给出两队名字，Agent 必须先搜索确认比赛阶段/赛制；无法确认时先问用户，不要默认当成小组赛或淘汰赛。
- 明确足球随机性大；高概率只代表长期模拟优势，不代表单场确定。模型默认已纳入冷门和临场波动。
- 涉及 `group`、`champion`、`route` 等蒙特卡洛输出时，展示脚本给出的 `simulation_error_95_max` 或文本中的模拟误差提示。
- 当前单场预测要先收集并保存赛前情报；输出时区分基础模型结果、情报修正和仍然存在的不确定性。
- 区分"理性预测"与"玄学预测"，不可混淆来源。
- 玄学结果不需要固定提示语；HTML 中必须解释本卦、变卦、变爻、五行/生肖/命理和气运因子各自代表什么，以及为什么导向该玄学判断。
- 用户要求当前玄学预测时，Agent 可保存 `data/live/divination_context.json`；输出中只能称为起卦背景或象意输入。
- 涉及最新小组、赛程、赛果时，由 Agent 先核验来源并保存 `data/live/teams.json` / `data/live/results.json`；涉及当前单场预测时，额外保存 `data/live/intelligence.json`。
- `data/live/results.json` 与 `data/results.json` 使用阶段锁定，阶段值为 `GROUP`/`R32`/`R16`/`QF`/`SF`/`F`。

## 常用调用速查
```bash
SKILL_DIR=/path/to/worldcup-2026-predictor
python3 "$SKILL_DIR/scripts/predict.py" match 阿根廷 巴西 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" group C --sims 5000 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" champion --sims 10000 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" route 阿根廷 --sims 5000 --seed 7
python3 "$SKILL_DIR/scripts/predict.py" bracket --seed 7
python3 "$SKILL_DIR/scripts/predict.py" match 阿根廷 巴西 --json
python3 "$SKILL_DIR/scripts/divination.py" 阿根廷 巴西
python3 "$SKILL_DIR/scripts/divination.py" 阿根廷 巴西 --factor
python3 "$SKILL_DIR/scripts/divination.py" 阿根廷 巴西 --json
```

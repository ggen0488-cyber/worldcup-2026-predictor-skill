# 赛前情报快照

当用户要求当前单场预测时，Agent 应先收集两队最新情报，再保存 `data/live/intelligence.json`。脚本不联网，也不绑定固定数据源；Agent 根据可访问平台选择官方、媒体、数据站或盘口来源，并在快照中记录来源 URL 与采集时间。

## 采集维度

- 阵容可用性：伤病、停赛、复出、门将/核心球员状态。
- 预计首发与轮换：主力轮休、连续作战、阵型变化。
- 近期状态：最近比赛结果、进失球、xG/射门质量、强弱对手背景。
- 赛程负荷：休息天数、旅行距离、加时/点球消耗、气候适应。
- 场地与环境：举办城市、草皮、天气、温度、海拔、主客场/东道主因素。
- 战术对位：高位逼抢、转换速度、定位球、防线速度、边路/中路错位。
- 比赛动机：小组出线形势、淘汰赛风险偏好、净胜球需求。
- 外部基准：Elo/排名变化、主流赔率或市场隐含概率，仅作校验，不直接照抄结论。

## JSON 格式

```json
{
  "_meta": {
    "collected_at": "2026-06-19T10:00:00Z",
    "sources": [
      {
        "name": "source name",
        "url": "https://example.com/match-report",
        "checked_at": "2026-06-19T10:00:00Z"
      }
    ],
    "notes": "Agent-generated pre-match intelligence snapshot"
  },
  "teams": {
    "ARG": {
      "elo_delta": 12,
      "notes": ["核心前锋恢复合练", "比对手多休息一天"],
      "sources": [{"url": "https://example.com/arg-team-news"}]
    },
    "BRA": {
      "elo_delta": -8,
      "notes": ["主力中卫停赛"],
      "sources": [{"url": "https://example.com/bra-team-news"}]
    }
  },
  "matches": [
    {
      "teams": ["ARG", "BRA"],
      "confidence": 0.65,
      "goal_delta": {"ARG": 0.08, "BRA": -0.05},
      "notes": ["阿根廷休息时间略占优，但巴西转换进攻仍有威胁"],
      "factors": [
        {
          "type": "injury",
          "team": "BRA",
          "impact": "negative",
          "summary": "主力中卫缺阵，防空和定位球防守下降",
          "source": "https://example.com/bra-injury"
        }
      ]
    }
  ]
}
```

## 修正规则

- `teams.*.elo_delta` 是长期强弱的有界修正，脚本会限制在 `-80` 到 `+80` Elo 之间，并影响单场、小组、夺冠和淘汰赛模拟。
- `matches[].goal_delta` 是指定两队这场比赛的进球期望修正，脚本会限制在 `-0.35` 到 `+0.35` 之间，并按 `confidence` 折算；当前只用于 `match A B` 单场命令。
- `confidence` 范围为 `0` 到 `1`。来源越新、越一致、越接近一手信息，置信度越高。
- 不要把偶然性当成用户可调参数。情报只修正基础预期，脚本仍会默认纳入足球随机性、冷门路径和临场波动。
- 如果来源冲突，保留冲突说明，降低 `confidence`，不要强行给出确定结论。
- 如果无法取得足够新的来源，明确说明情报不足，不要把样例数据或旧快照包装成当前实时分析。

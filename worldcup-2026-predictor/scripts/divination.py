#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 World Cup — 玄学预测引擎 🔮

四术合参：周易六十四卦 · 五行生克 · 生肖纪年 · 数字命理。
起卦以"对战双方 + 日期"为引子，结果可复现（同输入同卦象）。
可读取 data/live/divination_context.json 中由 Agent 保存的起卦背景。

Usage:
  divination.py ARG BRA              # 纯玄学：摇卦断吉凶
  divination.py ARG BRA --date 0617  # 指定日期(影响卦象)，默认用内置参考日
  divination.py ARG BRA --factor     # 只输出 ±气运修正因子(供 predict 加权)

可与 predict.py 的科学概率并列展示，或用 --factor 折算成气运加权。
"""
import json, math, argparse, os, hashlib

MODEL_VERSION = "2026.2"
ADVISORY = "预测结果仅供参考，请理性观赛。"

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAMS_PATH = os.path.join(BASE, "references", "teams.json")
HEX_PATH = os.path.join(BASE, "references", "hexagrams.json")
LIVE_DIVINATION_CONTEXT_PATH = os.path.join(BASE, "data", "live", "divination_context.json")

DEFAULT_DATE = "0617"   # 参考日，可被 --date 覆盖

# 五行：色 -> 行；相生(顺) 木→火→土→金→水→木；相克(隔) 木克土 土克水 水克火 火克金 金克木
COLOR_ELEMENT = {
    "red": "火", "orange": "火",
    "blue": "水", "black": "水",
    "white": "金", "gold": "金", "silver": "金",
    "green": "木",
    "yellow": "土", "brown": "土",
}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}   # X 生 Y
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}      # X 克 Y
ELEM_EMOJI = {"金": "⚪", "木": "🌳", "水": "💧", "火": "🔥", "土": "⛰"}

# ---------------------------------------------------------------- data
def load_teams():
    with open(TEAMS_PATH, encoding="utf-8") as f:
        return json.load(f)["teams"]

def load_hex():
    with open(HEX_PATH, encoding="utf-8") as f:
        items = json.load(f)["hexagrams"]
    return items, {h["lines"]: h for h in items}

def load_divination_context():
    if not os.path.exists(LIVE_DIVINATION_CONTEXT_PATH):
        return {}
    try:
        with open(LIVE_DIVINATION_CONTEXT_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"❌ 玄学起卦背景快照不是有效 JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("❌ 玄学起卦背景快照格式错误：顶层必须是对象")
    if "matches" in data and not isinstance(data["matches"], list):
        raise SystemExit("❌ 玄学起卦背景快照格式错误：matches 必须是数组")
    return data

def resolve(teams, key):
    k = str(key).strip(); kl = k.lower()
    for code, t in teams.items():
        if code.lower() == kl or t["name"].lower() == kl or t.get("name_cn", "") == k:
            return code
    for code, t in teams.items():
        if (kl and kl in t["name"].lower()) or (k and k in t.get("name_cn", "")):
            return code
    raise SystemExit(f"❌ 未找到球队: {key}")

def cn(teams, code):
    return teams[code].get("name_cn", code)

def team_json(teams, code):
    return {
        "code": code,
        "name": teams[code]["name"],
        "name_cn": cn(teams, code),
        "elo": teams[code].get("elo"),
        "group": teams[code].get("group"),
        "color": teams[code].get("color"),
    }

def element_of(teams, code):
    return COLOR_ELEMENT.get(teams[code].get("color", ""), "土")

def normalize_notes(value, limit=4):
    if isinstance(value, str):
        notes = [value]
    elif isinstance(value, list):
        notes = value
    else:
        notes = []
    return [str(n).strip() for n in notes if str(n).strip()][:limit]

def match_divination_context(context, a, b):
    if not context:
        return {}
    items = context.get("matches")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            codes = [str(code).upper() for code in item.get("teams", []) if code]
            if len(codes) == 2 and set(codes) == {a, b}:
                return item
        return {}
    codes = [str(code).upper() for code in context.get("teams", []) if code]
    if len(codes) == 2 and set(codes) == {a, b}:
        return context
    return {}

def normalize_date(value):
    text = "".join(c for c in str(value or "") if c.isdigit())
    if len(text) >= 8 and text[:2] in ("19", "20"):
        return text[4:8]
    if len(text) >= 8:
        return text[-4:]
    if len(text) == 4:
        return text
    return DEFAULT_DATE

def context_date(match_context):
    for key in ("divination_date", "date", "match_date", "kickoff_date", "kickoff_time"):
        if match_context.get(key):
            return normalize_date(match_context.get(key))
    return DEFAULT_DATE

# ---------------------------------------------------------------- 起卦
def _rng_bytes(seed_str):
    """deterministic byte stream from seed (no external randomness)."""
    out = b""
    i = 0
    while len(out) < 64:
        out += hashlib.sha256(f"{seed_str}#{i}".encode("utf-8")).digest()
        i += 1
    return out

def cast(a, b, date):
    """三枚铜钱六爻起卦：返回 (本卦lines, 变卦lines, 变爻位列表 bottom->top)."""
    stream = _rng_bytes(f"{a}-{b}-{date}")
    lines = ""      # bottom -> top
    changing = []
    for pos in range(6):
        # three coins: each 2(yin) or 3(yang)
        coins = sum(3 if (stream[pos * 3 + k] & 1) else 2 for k in range(3))
        # 6 老阴(变), 7 少阳, 8 少阴, 9 老阳(变)
        yang = 1 if coins in (7, 9) else 0
        lines += str(yang)
        if coins in (6, 9):
            changing.append(pos)
    bian = list(lines)
    for pos in changing:
        bian[pos] = "1" if lines[pos] == "0" else "0"
    return lines, "".join(bian), changing

# ---------------------------------------------------------------- 四术
def reading_hex(hmap, lines, bian, changing):
    ben = hmap.get(lines)
    bh = hmap.get(bian)
    luck = ben["luck"]
    if changing:                       # 有变爻：本卦六三、变卦六七开
        luck = ben["luck"] * 0.6 + bh["luck"] * 0.4
    return ben, bh, luck

def reading_wuxing(ea, eb):
    if ea == eb:
        return 0.0, f"双方同属【{ea}】，五行比和，势均力敌。"
    if SHENG.get(ea) == eb:
        return -0.4, f"【{ea}】生【{eb}】，甲方泄气助人，乙方得生受益。"
    if SHENG.get(eb) == ea:
        return 0.4, f"【{eb}】生【{ea}】，乙方反哺甲方，甲方气旺。"
    if KE.get(ea) == eb:
        return 0.5, f"【{ea}】克【{eb}】，甲方压制乙方，占据上风。"
    if KE.get(eb) == ea:
        return -0.5, f"【{eb}】克【{ea}】，乙方反克甲方，甲方受制。"
    return 0.0, "五行错杂，吉凶参半。"

def reading_zodiac(ea, eb):
    # 2026 丙午马年，纳音天河水；午属火 → 火旺，水亦得令
    boost = {"火": 0.4, "水": 0.2, "土": 0.1, "木": -0.1, "金": -0.2}
    da, db = boost.get(ea, 0), boost.get(eb, 0)
    diff = da - db
    note = f"丙午马年火气当令：甲方({ea})得气 {da:+.1f}，乙方({eb})得气 {db:+.1f}。"
    return diff, note

def _digit_root(s):
    n = sum(int(c) for c in str(s) if c.isdigit())
    while n > 9:
        n = sum(int(c) for c in str(n))
    return n

def reading_numerology(teams, a, b, date):
    ra = _digit_root(teams[a]["elo"]); rb = _digit_root(teams[b]["elo"])
    rd = _digit_root(date)
    la = 1.0 - abs(ra - rd) / 9.0      # 与日期数字根的共振度 0..1
    lb = 1.0 - abs(rb - rd) / 9.0
    diff = (la - lb)
    note = (f"日期数字根 {rd}；{cn(teams,a)}幸运数 {ra}(共振 {la*100:.0f}%) · "
            f"{cn(teams,b)}幸运数 {rb}(共振 {lb*100:.0f}%)。")
    return diff, note

# ---------------------------------------------------------------- 汇总
def qi_factor(teams, a, b, date, hmap):
    """综合四术 -> 气运修正因子(约 ±0.05)，正=利甲方。"""
    lines, bian, changing = cast(a, b, date)
    ben, bh, hl = reading_hex(hmap, lines, bian, changing)
    ea, eb = element_of(teams, a), element_of(teams, b)
    wl, _ = reading_wuxing(ea, eb)
    zl, _ = reading_zodiac(ea, eb)
    nl, _ = reading_numerology(teams, a, b, date)
    raw = hl / 2.0 * 0.4 + wl * 0.3 + zl * 0.2 + nl * 0.1   # 归一加权
    factor = max(-0.05, min(0.05, raw * 0.05))
    return factor, dict(lines=lines, bian=bian, changing=changing,
                        ben=ben, bh=bh, ea=ea, eb=eb)

def render_context(teams, a, b, context):
    if not context:
        return
    lines = []
    question = context.get("question") or context.get("prompt")
    if question:
        lines.append(f"问事：{question}")
    venue_parts = []
    for key in ("city", "venue", "stadium"):
        if context.get(key):
            venue_parts.append(str(context[key]))
    if venue_parts:
        lines.append("地点：" + " · ".join(venue_parts))
    kickoff = context.get("kickoff_time") or context.get("match_time") or context.get("date")
    if kickoff:
        lines.append(f"时间：{kickoff}")
    symbols = context.get("symbols", {})
    if isinstance(symbols, dict):
        for code in (a, b):
            values = symbols.get(code)
            if isinstance(values, list):
                values = "、".join(str(v) for v in values[:3])
            if values:
                lines.append(f"{cn(teams, code)}象意：{values}")
    lines.extend(normalize_notes(context.get("notes"), limit=3))
    if lines:
        print("【起卦背景】")
        for line in lines[:8]:
            print(f"        {line}")

def render(teams, a, b, date, items, hmap, context=None):
    na, nb = cn(teams, a), cn(teams, b)
    factor, d = qi_factor(teams, a, b, date, hmap)
    ben, bh = d["ben"], d["bh"]
    ea, eb = d["ea"], d["eb"]
    print(f"\n🔮 玄学卜算  {na}  vs  {nb}   （引子日期 {date}）")
    print("=" * 44)
    render_context(teams, a, b, context or {})
    # 1 周易
    chg = "、".join(f"第{p+1}爻" for p in d["changing"]) if d["changing"] else "无（静卦）"
    print(f"【周易】本卦 {ben['sym']} {ben['name']}卦 —— {ben['judge']}")
    print(f"        变爻 {chg}")
    if d["changing"]:
        print(f"        变卦 {bh['sym']} {bh['name']}卦 —— {bh['judge']}")
    # 2 五行
    _, wnote = reading_wuxing(ea, eb)
    print(f"【五行】{na}{ELEM_EMOJI[ea]}{ea}  ×  {nb}{ELEM_EMOJI[eb]}{eb}")
    print(f"        {wnote}")
    # 3 生肖
    _, znote = reading_zodiac(ea, eb)
    print(f"【生肖】{znote}")
    # 4 命理
    _, nnote = reading_numerology(teams, a, b, date)
    print(f"【命理】{nnote}")
    # 综合
    print("-" * 44)
    if factor > 0.012:
        verdict = f"卦象偏向 {na}，气运在握 🟢"
    elif factor < -0.012:
        verdict = f"卦象偏向 {nb}，{na}气运稍逊 🔴"
    else:
        verdict = "气运胶着，胜负在五五之间 ⚖️"
    print(f"【综合】{verdict}")
    print(f"        气运修正因子 = {factor:+.3f}（利{na}为正，约 ±5% 上限）")
    print("=" * 44)
    print(f"提醒：{ADVISORY}")
    print()
    return factor

def divination_payload(teams, a, b, date, hmap, context=None):
    factor, d = qi_factor(teams, a, b, date, hmap)
    ben, bh = d["ben"], d["bh"]
    ea, eb = d["ea"], d["eb"]
    wl, wnote = reading_wuxing(ea, eb)
    zl, znote = reading_zodiac(ea, eb)
    nl, nnote = reading_numerology(teams, a, b, date)
    if factor > 0.012:
        verdict = {"direction": "home", "label": f"卦象偏向 {cn(teams, a)}"}
    elif factor < -0.012:
        verdict = {"direction": "away", "label": f"卦象偏向 {cn(teams, b)}"}
    else:
        verdict = {"direction": "balanced", "label": "气运胶着，胜负在五五之间"}
    return {
        "model_version": MODEL_VERSION,
        "command": "divination",
        "advisory": ADVISORY,
        "teams": {"home": team_json(teams, a), "away": team_json(teams, b)},
        "date_key": date,
        "context": context or {},
        "hexagram": {
            "primary": {"symbol": ben["sym"], "name": ben["name"], "judge": ben["judge"], "luck": ben["luck"], "lines": d["lines"]},
            "changed": {"symbol": bh["sym"], "name": bh["name"], "judge": bh["judge"], "luck": bh["luck"], "lines": d["bian"]},
            "changing_lines": [pos + 1 for pos in d["changing"]],
        },
        "five_elements": {"home": ea, "away": eb, "score": wl, "reason": wnote},
        "zodiac": {"score": zl, "reason": znote},
        "numerology": {"score": nl, "reason": nnote},
        "fortune_factor": factor,
        "verdict": verdict,
        "reading_reasons": [
            f"本卦 {ben['name']} 代表当前态势：{ben['judge']}",
            f"变卦 {bh['name']} 代表后续走势：{bh['judge']}" if d["changing"] else "无变爻，走势更偏稳定。",
            wnote,
            znote,
            nnote,
        ],
    }

# ---------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description="2026 World Cup 玄学预测 🔮")
    p.add_argument("team_a")
    p.add_argument("team_b")
    p.add_argument("--date", default=None, help="MMDD，影响起卦；未传时优先使用 Agent 起卦背景快照，否则默认 0617")
    p.add_argument("--factor", action="store_true", help="只打印气运修正因子")
    p.add_argument("--json", action="store_true", help="输出结构化 JSON，供 Agent 生成 HTML 报告")
    args = p.parse_args()
    teams = load_teams()
    items, hmap = load_hex()
    a = resolve(teams, args.team_a); b = resolve(teams, args.team_b)
    context = match_divination_context(load_divination_context(), a, b)
    date = normalize_date(args.date) if args.date else context_date(context)
    if args.factor:
        f, _ = qi_factor(teams, a, b, date, hmap)
        if args.json:
            print(json.dumps({
                "model_version": MODEL_VERSION,
                "command": "divination_factor",
                "advisory": ADVISORY,
                "teams": {"home": team_json(teams, a), "away": team_json(teams, b)},
                "date_key": date,
                "fortune_factor": f,
            }, ensure_ascii=False, indent=2))
        else:
            print(f"{f:+.4f}")
    elif args.json:
        print(json.dumps(divination_payload(teams, a, b, date, hmap, context), ensure_ascii=False, indent=2))
    else:
        render(teams, a, b, date, items, hmap, context)

if __name__ == "__main__":
    main()

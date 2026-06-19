#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 World Cup — rational prediction engine.

Model:  Elo ratings -> goal supremacy -> football-randomness-adjusted Poisson scoreline -> Monte Carlo tournament.
Real results in data/live/results.json or data/results.json are LOCKED by stage and pair.

Usage:
  predict.py match  ARG BRA            # single match win/draw/loss + likely scores
  predict.py group  C                  # one group: R32/top-two odds + likely table
  predict.py champion [--sims 10000]   # champion / final / semis odds for all teams
  predict.py bracket                   # one sampled knockout bracket with every round

Team args accept code (ARG), English (Argentina) or Chinese (阿根廷).
Common flags: --sims N  --seed N  --neutral
"""
import json, math, random, argparse, os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAMS_PATH = os.path.join(BASE, "references", "teams.json")
RESULTS_PATH = os.path.join(BASE, "data", "results.json")
LIVE_TEAMS_PATH = os.path.join(BASE, "data", "live", "teams.json")
LIVE_RESULTS_PATH = os.path.join(BASE, "data", "live", "results.json")

AVG_GOALS = 2.6      # league-average total goals per match
HOME_ADV = 0.35      # extra expected goals for a host nation
SUP_SCALE = 120.0    # Elo points per ~1 goal of supremacy
MAX_GOALS = 8        # truncation for the scoreline matrix
EXPECTED_GROUPS = tuple("ABCDEFGHIJKL")
EXPECTED_TEAMS = 48

MATCH_SHOCK_SD = 0.28        # one-match form/tactics/noise shock
PROBABILITY_SHRINK = 0.10    # shrink headline W/D/L odds toward a football baseline
NEUTRAL_OUTCOME = (0.37, 0.26, 0.37)
SHOCK_POINTS = [(-2.0, 0.0545), (-1.0, 0.2442), (0.0, 0.4026), (1.0, 0.2442), (2.0, 0.0545)]

# ---------------------------------------------------------------- data loading
def load_teams():
    for path in (LIVE_TEAMS_PATH, TEAMS_PATH):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            teams = json.load(f)["teams"]
        if teams:
            validate_teams(teams, path)
            return teams
    raise SystemExit("❌ 未找到球队数据")

def validate_teams(teams, source_path):
    if len(teams) != EXPECTED_TEAMS:
        raise SystemExit(f"❌ 参赛队伍不完整：{source_path} 中有 {len(teams)} 队，应为 {EXPECTED_TEAMS} 队")
    groups = defaultdict(list)
    for code, team in teams.items():
        group = team.get("group")
        if group not in EXPECTED_GROUPS:
            raise SystemExit(f"❌ 球队 {code} 的小组无效：{group!r}，应为 A-L")
        for field in ("name", "elo", "host", "color"):
            if field not in team:
                raise SystemExit(f"❌ 球队 {code} 缺少字段：{field}")
        groups[group].append(code)
    missing = [g for g in EXPECTED_GROUPS if g not in groups]
    if missing:
        raise SystemExit(f"❌ 缺少小组：{', '.join(missing)}")
    bad = {g: codes for g, codes in groups.items() if len(codes) != 4}
    if bad:
        detail = "; ".join(f"{g}组={len(codes)}队({', '.join(codes)})" for g, codes in sorted(bad.items()))
        raise SystemExit(f"❌ 小组队伍数量不完整：{detail}")

def load_locked():
    idx = {}
    for path in (LIVE_RESULTS_PATH, RESULTS_PATH):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for m in data.get("matches", []):
            stage = str(m.get("stage", "GROUP")).upper()
            idx[(stage, frozenset((m["home"], m["away"])))] = (m["home"], m["hg"], m["ag"])
    return idx

def locked_result(locked, stage, a, b):
    return locked.get((stage.upper(), frozenset((a, b))))

def resolve(teams, key):
    k = str(key).strip()
    kl = k.lower()
    for code, t in teams.items():
        if code.lower() == kl or t["name"].lower() == kl or t.get("name_cn", "") == k:
            return code
    for code, t in teams.items():
        if kl and kl in t["name"].lower() or (k and k in t.get("name_cn", "")):
            return code
    raise SystemExit(f"❌ 未找到球队: {key}")

def cn(teams, code):
    return teams[code].get("name_cn", code)

# ---------------------------------------------------------------- poisson core
def expected_goals(teams, a, b, host_a=None, host_b=None):
    if host_a is None: host_a = teams[a].get("host", False)
    if host_b is None: host_b = teams[b].get("host", False)
    sup = (teams[a]["elo"] - teams[b]["elo"]) / SUP_SCALE
    la = AVG_GOALS / 2 + sup / 2 + (HOME_ADV if host_a else 0)
    lb = AVG_GOALS / 2 - sup / 2 + (HOME_ADV if host_b else 0)
    return max(0.15, la), max(0.15, lb)

def _pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)

def outcome_probs(la, lb):
    pw = pd = pl = 0.0
    score_probs = defaultdict(float)
    for z, weight in SHOCK_POINTS:
        sla = max(0.15, la + z * MATCH_SHOCK_SD / 2)
        slb = max(0.15, lb - z * MATCH_SHOCK_SD / 2)
        for i in range(MAX_GOALS + 1):
            for j in range(MAX_GOALS + 1):
                p = weight * _pmf(i, sla) * _pmf(j, slb)
                score_probs[(i, j)] += p
                if i > j: pw += p
                elif i == j: pd += p
                else: pl += p
    best = sorted(score_probs.items(), key=lambda x: -x[1])
    return pw, pd, pl, best[:5]

def apply_probability_shrink(pw, pd, pl):
    """Blend exact model probabilities toward a neutral football baseline."""
    nw, nd, nl = NEUTRAL_OUTCOME
    return (
        pw * (1 - PROBABILITY_SHRINK) + nw * PROBABILITY_SHRINK,
        pd * (1 - PROBABILITY_SHRINK) + nd * PROBABILITY_SHRINK,
        pl * (1 - PROBABILITY_SHRINK) + nl * PROBABILITY_SHRINK,
    )

def apply_match_shock(la, lb):
    """Model one-match form/tactics/variance shock before sampling goals."""
    shock = random.gauss(0.0, MATCH_SHOCK_SD)
    return max(0.15, la + shock / 2), max(0.15, lb - shock / 2)

def _sample(lam):
    L = math.exp(-lam); k = 0; p = 1.0
    while True:
        k += 1; p *= random.random()
        if p <= L:
            return k - 1

def play(teams, a, b, locked, knockout=False, stage="SIM"):
    """Return (ga, gb, winner_or_None). Uses a locked real result if present."""
    lk = locked_result(locked, stage, a, b)
    if lk:
        home, hg, ag = lk
        ga, gb = (hg, ag) if home == a else (ag, hg)
    else:
        la, lb = expected_goals(teams, a, b)
        la, lb = apply_match_shock(la, lb)
        ga, gb = _sample(la), _sample(lb)
    if not knockout:
        return ga, gb, None
    if ga != gb:
        return ga, gb, (a if ga > gb else b)
    # extra time + penalties: mildly Elo-weighted coin flip
    pa = 1 / (1 + 10 ** ((teams[b]["elo"] - teams[a]["elo"]) / 600))
    return ga, gb, (a if random.random() < pa else b)

# ---------------------------------------------------------------- group stage
def groups_map(teams):
    g = defaultdict(list)
    for code, t in teams.items():
        g[t["group"]].append(code)
    return dict(sorted(g.items()))

def simulate_group(teams, codes, locked):
    pts = {c: 0 for c in codes}
    gf = {c: 0 for c in codes}
    ga = {c: 0 for c in codes}
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            a, b = codes[i], codes[j]
            x, y, _ = play(teams, a, b, locked, stage="GROUP")
            gf[a] += x; ga[a] += y; gf[b] += y; ga[b] += x
            if x > y: pts[a] += 3
            elif x < y: pts[b] += 3
            else: pts[a] += 1; pts[b] += 1
    table = sorted(codes, key=lambda c: (pts[c], gf[c] - ga[c], gf[c], random.random()), reverse=True)
    rows = [(c, pts[c], gf[c] - ga[c], gf[c]) for c in table]
    return rows  # ordered best -> worst

# ---------------------------------------------------------------- knockout
def table_key(teams, row):
    return (row[1], row[2], row[3], teams[row[0]]["elo"])

def simulate_all_groups(teams, locked):
    rows_by_group = {}
    firsts, seconds, thirds = [], [], []
    for letter, codes in groups_map(teams).items():
        rows = simulate_group(teams, codes, locked)
        rows_by_group[letter] = rows
        firsts.append(rows[0]); seconds.append(rows[1]); thirds.append(rows[2])
    firsts.sort(key=lambda r: table_key(teams, r), reverse=True)
    seconds.sort(key=lambda r: table_key(teams, r), reverse=True)
    thirds.sort(key=lambda r: table_key(teams, r), reverse=True)
    best_thirds = thirds[:8]
    field_rows = firsts + seconds + best_thirds
    field_rows.sort(key=lambda r: table_key(teams, r), reverse=True)
    return rows_by_group, [r[0] for r in field_rows], {r[0] for r in best_thirds}

def _seed_order(n):
    order = [1, 2]
    while len(order) < n:
        m = len(order) * 2 + 1
        order = [v for r in order for v in (r, m - r)]
    return order

def build_field(teams, locked):
    """Simulate all groups, return 32 qualifiers seeded best->worst."""
    _, seeds, _ = simulate_all_groups(teams, locked)
    return seeds

def simulate_knockout(teams, seeds, locked):
    bracket = [seeds[i - 1] for i in _seed_order(len(seeds))]
    reached = {}                                   # code -> deepest round index
    rounds = []
    rnd = 0
    while len(bracket) > 1:
        for c in bracket:
            reached[c] = rnd
        nxt = []
        stage = {32: "R32", 16: "R16", 8: "QF", 4: "SF", 2: "F"}[len(bracket)]
        matches = []
        for i in range(0, len(bracket), 2):
            a, b = bracket[i], bracket[i + 1]
            ga, gb, w = play(teams, a, b, locked, knockout=True, stage=stage)
            matches.append((a, b, ga, gb, w))
            nxt.append(w)
        rounds.append((stage, matches))
        bracket = nxt
        rnd += 1
    reached[bracket[0]] = rnd                       # champion
    return bracket[0], reached, seeds, rounds

# ---------------------------------------------------------------- monte carlo
def monte_carlo(teams, sims, locked):
    stat = {c: {"adv": 0, "qf": 0, "sf": 0, "final": 0, "champ": 0} for c in teams}
    for _ in range(sims):
        seeds = build_field(teams, locked)
        in32 = set(seeds)
        champ, reached, _, _ = simulate_knockout(teams, seeds, locked)
        # reached: 0=out R32, 1=out R16, 2=out QF, 3=out SF, 4=runner-up, 5=champion
        for c in in32:
            stat[c]["adv"] += 1
            r = reached.get(c, 0)
            if r >= 2: stat[c]["qf"] += 1      # reached quarterfinals (top 8)
            if r >= 3: stat[c]["sf"] += 1      # reached semifinals (top 4)
            if r >= 4: stat[c]["final"] += 1   # reached the final (top 2)
        stat[champ]["champ"] += 1
    for c in stat:
        for k in stat[c]:
            stat[c][k] /= sims
    return stat

# ---------------------------------------------------------------- commands
def bar(p, width=20):
    return "█" * round(p * width) + "·" * (width - round(p * width))

def cmd_match(teams, args, locked):
    a = resolve(teams, args.team_a); b = resolve(teams, args.team_b)
    ha = None if not args.neutral else False
    hb = None if not args.neutral else False
    la, lb = expected_goals(teams, a, b, ha, hb)
    pw, pd, pl, scores = outcome_probs(la, lb)
    pw, pd, pl = apply_probability_shrink(pw, pd, pl)
    na, nb = cn(teams, a), cn(teams, b)
    print(f"\n⚽ {na}  vs  {nb}   （理性模型 · 泊松 · 含足球随机性）")
    print(f"   预期进球  {na} {la:.2f} - {lb:.2f} {nb}")
    print(f"   {na}胜  {pw*100:5.1f}%  {bar(pw)}")
    print(f"   平局      {pd*100:5.1f}%  {bar(pd)}")
    print(f"   {nb}胜  {pl*100:5.1f}%  {bar(pl)}")
    print("   最可能比分:")
    for (i, j), p in scores:
        print(f"     {na} {i}-{j} {nb}   {p*100:4.1f}%")
    print()

def cmd_group(teams, args, locked):
    letter = args.team_a.upper()
    gm = groups_map(teams)
    if letter not in gm:
        raise SystemExit(f"❌ 无此小组: {letter}（A–L）")
    codes = gm[letter]
    sims = args.sims or 5000
    adv = {c: 0 for c in codes}; top2 = {c: 0 for c in codes}; first = {c: 0 for c in codes}
    third_adv = {c: 0 for c in codes}
    rank_pts = {c: 0.0 for c in codes}
    for _ in range(sims):
        rows_by_group, seeds, best_thirds = simulate_all_groups(teams, locked)
        rows = rows_by_group[letter]
        in32 = set(seeds)
        for pos, r in enumerate(rows):
            c = r[0]
            rank_pts[c] += pos
            if c in in32:
                adv[c] += 1
            if pos < 2:
                top2[c] += 1
            if pos == 0:
                first[c] += 1
            if c in best_thirds:
                third_adv[c] += 1
    print(f"\n🏟  {letter} 组  晋级32强概率（{sims} 次模拟，含8个最佳第三名与足球随机性）")
    order = sorted(codes, key=lambda c: -adv[c])
    for c in order:
        print(f"   {cn(teams,c):<10} 晋级 {adv[c]/sims*100:5.1f}%  前二 {top2[c]/sims*100:5.1f}%"
              f"  小组第一 {first[c]/sims*100:5.1f}%  最佳第三 {third_adv[c]/sims*100:5.1f}%"
              f"  {bar(adv[c]/sims)}")
    likely = sorted(codes, key=lambda c: rank_pts[c])
    print("   预测排名: " + " > ".join(cn(teams, c) for c in likely) + "\n")

def cmd_champion(teams, args, locked):
    sims = args.sims or 10000
    print(f"\n🔮 正在模拟整届赛事 {sims} 次（含足球随机性）…")
    stat = monte_carlo(teams, sims, locked)
    ranked = sorted(teams, key=lambda c: -stat[c]["champ"])
    print(f"\n🏆 2026 世界杯夺冠概率榜（{sims} 次蒙特卡洛）")
    print(f"   {'球队':<10}{'夺冠':>7}{'进决赛':>8}{'4强':>7}{'8强':>7}{'32强':>7}")
    for c in ranked[:24]:
        s = stat[c]
        print(f"   {cn(teams,c):<10}{s['champ']*100:6.1f}%{s['final']*100:7.1f}%"
              f"{s['sf']*100:6.1f}%{s['qf']*100:6.1f}%{s['adv']*100:6.1f}%")
    print()

def cmd_bracket(teams, args, locked):
    seeds = build_field(teams, locked)
    champ, _, _, rounds = simulate_knockout(teams, seeds, locked)
    print("\n🗺  一次随机抽样的淘汰赛走势（单次模拟，仅供参考）")
    print(f"   32强: {len(seeds)} 队晋级，种子前八: " +
          "、".join(cn(teams, c) for c in seeds[:8]))
    print("   注：当前使用简化蛇形种子对阵，非 FIFA 官方槽位映射；模型默认包含足球随机性。")
    labels = {"R32": "32强", "R16": "16强", "QF": "1/4决赛", "SF": "半决赛", "F": "决赛"}
    for stage, matches in rounds:
        print(f"\n   {labels[stage]}")
        for a, b, ga, gb, w in matches:
            marker = "（点球）" if ga == gb else "晋级"
            print(f"     {cn(teams,a)} {ga}-{gb} {cn(teams,b)}  → {cn(teams,w)}{marker}")
    print(f"   🏆 本次模拟冠军: {cn(teams, champ)}\n")

# ---------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description="2026 World Cup rational predictor")
    p.add_argument("cmd", choices=["match", "group", "champion", "bracket"])
    p.add_argument("team_a", nargs="?", help="team A / group letter")
    p.add_argument("team_b", nargs="?", help="team B")
    p.add_argument("--sims", type=int, default=0)
    p.add_argument("--neutral", action="store_true")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()
    if args.sims < 0:
        p.error("--sims must be non-negative")
    if args.cmd == "match" and (not args.team_a or not args.team_b):
        p.error("match requires two teams, for example: predict.py match ARG BRA")
    if args.cmd == "group" and not args.team_a:
        p.error("group requires a group letter, for example: predict.py group C")
    if args.seed is not None:
        random.seed(args.seed)
    teams = load_teams()
    locked = load_locked()
    {"match": cmd_match, "group": cmd_group,
     "champion": cmd_champion, "bracket": cmd_bracket}[args.cmd](teams, args, locked)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦省钱助手 (McSaver) —— 核心推荐引擎

用法:
    python mcsaver.py --budget 30 --people 1 --want 吃饱
    python mcsaver.py --budget 60 --people 2 --want 汉堡,可乐

说明:
    - 优先调用麦当劳 MCP 获取实时菜单/优惠（见 mcp_layer）。
    - MCP 不可用时回退到本地 menu.json + 启发式算法，保证可独立运行。
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MENU_PATH = os.path.join(HERE, "..", "menu.json")

# 口味关键词 -> 分类映射
WANT_MAP = {
    "汉堡": "汉堡", "鸡": "汉堡", "薯条": "小吃", "小吃": "小吃",
    "可乐": "饮料", "饮料": "饮料", "咖啡": "饮料", "甜品": "甜品",
}

# "吃饱" 预设的每人目标热量
FULL_CAL = 700


def load_menu():
    with open(MENU_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# MCP 接入层（占位契约，按 M-China 官方 manifest 对齐）
# 接入真实 MCP 后，把下方函数体替换为对 mcd_menu_list / mcd_promo_list 的调用。
# ---------------------------------------------------------------------------
def mcp_available():
    """检测麦当劳 MCP 是否可用。默认回退本地，避免演示依赖外部服务。"""
    return False


def fetch_menu_via_mcp():
    raise NotImplementedError("请按 M-China 官方 MCP manifest 接入 mcd_menu_list")


def fetch_promo_via_mcp():
    raise NotImplementedError("请按 M-China 官方 MCP manifest 接入 mcd_promo_list")


# ---------------------------------------------------------------------------
# 推荐算法（启发式）
# ---------------------------------------------------------------------------
def pick_by_want(menu, want_tokens):
    """根据 want 关键词筛选偏好分类。"""
    cats = set()
    for w in want_tokens:
        w = w.strip()
        if w in WANT_MAP:
            cats.add(WANT_MAP[w])
    if not cats:
        return menu["items"]
    return [i for i in menu["items"] if i["cat"] in cats]


def recommend(menu, budget, people, want_tokens):
    """在 (budget*people) 总预算内，最大化热量满足，并尽量命中偏好。"""
    total_budget = budget * people
    pool = pick_by_want(menu, want_tokens)

    # 目标热量：吃饱预设 or 偏好基础量
    target_cal = FULL_CAL * people if "吃饱" in want_tokens else 350 * people

    # 贪心：按 (热量/价格) 性价比排序，逐步装入直至接近预算/目标
    items = sorted(pool, key=lambda x: x["cal"] / x["price"], reverse=True)

    chosen, spent, cal = [], 0.0, 0
    for it in items:
        if spent + it["price"] <= total_budget and cal < target_cal * 1.1:
            chosen.append(it)
            spent += it["price"]
            cal += it["cal"]
        if cal >= target_cal:
            break

    # 若还没吃饱且预算有余，补最便宜的单品
    if cal < target_cal:
        for it in sorted(pool, key=lambda x: x["price"]):
            if it in chosen:
                continue
            if spent + it["price"] <= total_budget:
                chosen.append(it)
                spent += it["price"]
                cal += it["cal"]
            if cal >= target_cal:
                break

    return chosen, spent, cal


def best_combo(menu, budget, people):
    """在套餐里找总价不超过预算、且最划算(省最多)的套餐。"""
    total_budget = budget * people
    best = None
    for c in menu["combos"]:
        if c["price"] <= total_budget:
            save = c["single_price"] - c["price"]
            if best is None or save > best["save"]:
                best = {"combo": c, "save": save}
    return best


def main():
    ap = argparse.ArgumentParser(description="麦麦省钱助手")
    ap.add_argument("--budget", type=float, required=True, help="单人预算(元)")
    ap.add_argument("--people", type=int, default=1, help="人数")
    ap.add_argument("--want", type=str, default="吃饱", help="口味关键词, 逗号分隔, 如 汉堡,可乐 / 吃饱")
    args = ap.parse_args()

    menu = load_menu()
    want_tokens = [w for w in args.want.replace("，", ",").split(",") if w]

    # 真实 MCP 优先（当前默认回退本地）
    if mcp_available():
        try:
            menu = fetch_menu_via_mcp()
        except Exception:
            pass

    chosen, spent, cal = recommend(menu, args.budget, args.people, want_tokens)
    combo = best_combo(menu, args.budget, args.people)

    print("=" * 40)
    print(f"🍔 麦麦省钱助手  |  {args.people}人  预算 {args.budget*args.people:.0f}元")
    print("=" * 40)
    if chosen:
        print("推荐单点组合:")
        for it in chosen:
            print(f"  - {it['name']:<12} ¥{it['price']:.1f}  ({it['cal']}kcal)")
        print(f"  小计: ¥{spent:.1f}  约 {cal} kcal")
    else:
        print("预算内未找到合适组合，试试提高 --budget")

    if combo:
        c = combo["combo"]
        print("-" * 40)
        print(f"更划算套餐: {c['name']}  ¥{c['price']:.1f}")
        print(f"  含: {', '.join(c['contains'])}")
        print(f"  单点价 ¥{c['single_price']:.1f}  →  省 ¥{combo['save']:.1f} 💰")

    print("=" * 40)
    print("提示: 接入麦当劳 MCP 后，价格与优惠以实时数据为准。")


if __name__ == "__main__":
    main()

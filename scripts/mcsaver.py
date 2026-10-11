#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦省钱助手 (McSaver) —— 核心推荐引擎

用法::

    # 离线演示（无需任何配置，用本地示例菜单）
    python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱

    # 真实模式：先申请麦当劳 MCP Token，再设置环境变量
    export MCD_MCP_TOKEN="你的 MCP Token"     # Windows: set MCD_MCP_TOKEN=...
    python scripts/mcsaver.py --budget 60 --people 2 --want 汉堡,可乐 --address 深圳市南山区

说明:
    - 设置了 ``MCD_MCP_TOKEN`` 时，走**真实的麦当劳 MCP** 拉实时菜单/优惠券并比价
      （调用 ``query-nearby-stores`` / ``query-meals`` / ``query-store-coupons`` /
      ``query-my-coupons`` / ``calculate-price`` 等官方工具，详见 mcp_client.py）。
    - 没有 Token 或调用失败时，回退到本地 ``menu.json`` + 启发式算法，
      并在输出中**明确标注这是示例数据**，绝不冒充实时数据。
    - 本工具只做「查与算」，**不会下单、不会扣款**。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MENU_PATH = os.path.join(HERE, "..", "menu.json")
sys.path.insert(0, HERE)

from mcp_client import (  # noqa: E402
    MCDMcpClient, MCPError, TOOLS, best_single_combo, fetch_live_menu, price_with_mcp,
)

# 口味关键词 -> 分类映射
WANT_MAP = {
    "汉堡": "汉堡", "鸡": "汉堡", "薯条": "小吃", "小吃": "小吃",
    "可乐": "饮料", "饮料": "饮料", "咖啡": "饮料", "甜品": "甜品",
}

FULL_CAL = 700  # 「吃饱」预设的每人目标热量


def load_local_menu() -> dict:
    with open(MENU_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 本地回退算法（无 MCP 时的演示路径）
# ---------------------------------------------------------------------------
def pick_by_want(menu, want_tokens):
    cats = {WANT_MAP[w] for w in (t.strip() for t in want_tokens) if w in WANT_MAP}
    if not cats:
        return menu["items"]
    return [i for i in menu["items"] if i["cat"] in cats]


def recommend_local(menu, budget, people, want_tokens):
    total_budget = budget * people
    pool = pick_by_want(menu, want_tokens)
    target_cal = FULL_CAL * people if "吃饱" in want_tokens else 350 * people
    items = sorted(pool, key=lambda x: x["cal"] / x["price"], reverse=True)

    chosen, spent, cal = [], 0.0, 0
    for it in items:
        if spent + it["price"] <= total_budget and cal < target_cal * 1.1:
            chosen.append(it)
            spent += it["price"]
            cal += it["cal"]
        if cal >= target_cal:
            break
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


def best_combo_local(menu, budget):
    best = None
    for c in menu["combos"]:
        if c["price"] <= budget:
            save = c["single_price"] - c["price"]
            if best is None or save > best["save"]:
                best = {"combo": c, "save": save}
    return best


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------
def hr(char="-", n=52):
    print(char * n)


def render_local(menu, args, want_tokens):
    total_budget = args.budget * args.people
    chosen, spent, cal = recommend_local(menu, args.budget, args.people, want_tokens)
    combo = best_combo_local(menu, total_budget)

    print("🍔 麦麦省钱助手 McSaver")
    hr("=")
    print(f"需求：{args.people} 人 · 总预算 ¥{total_budget:.0f} · 偏好：{'/'.join(want_tokens) or '不限'}")
    print("数据来源：⚠️  本地示例数据 menu.json（未接入麦当劳 MCP）")
    print("         设置环境变量 MCD_MCP_TOKEN 即可切换到实时菜单与真实优惠券")
    hr()

    if chosen:
        print("① 单点组合（本地启发式）：")
        for it in chosen:
            print(f"   · {it['name']:<14} ¥{it['price']:>5.1f}   {it['cal']:>4} kcal")
        print(f"   小计 ¥{spent:.1f} · 约 {cal} kcal")
    else:
        print("预算内没找到合适组合，试试提高 --budget")

    if combo:
        c = combo["combo"]
        hr()
        print(f"② 更划算的套餐：{c['name']}  ¥{c['price']:.1f}")
        print(f"   含：{', '.join(c['contains'])}")
        print(f"   单点价 ¥{c['single_price']:.1f} → 省 ¥{combo['save']:.1f} 💰")

    hr("=")
    print("提示：接入麦当劳 MCP 后，价格、优惠券与应付总价都以实时数据为准。")


def render_live(live, args, want_tokens):
    client = live.client
    total_budget = args.budget * args.people
    pool = live.items
    cats = {WANT_MAP[w] for w in (t.strip() for t in want_tokens) if w in WANT_MAP}
    if cats:
        filtered = [i for i in pool if i["cat"] in cats]
        if filtered:
            pool = filtered

    # 选一张「能用得上」的券：门槛低、面额大优先
    coupons = sorted(live.coupons, key=lambda c: (-c.get("amount", 0), c.get("threshold", 0)))
    coupon = coupons[0] if coupons else None

    best = best_single_combo(pool, total_budget, args.people, coupon=coupon)
    combo_best = None
    for c in live.combos:
        if c["price"] <= total_budget:
            save = (best["gross"] - c["price"]) if best else 0
            if combo_best is None or c["price"] < combo_best["price"]:
                combo_best = {**c, "save_vs_single": save}

    print("🍔 麦麦省钱助手 McSaver")
    hr("=")
    store_name = live.store.get("storeName") or live.store.get("name") or "（未返回门店名）"
    print(f"门店：{store_name}")
    print(f"需求：{args.people} 人 · 总预算 ¥{total_budget:.0f} · 偏好：{'/'.join(want_tokens) or '不限'}")
    print(f"数据来源：✅ {live.source}")
    print(f"在售餐品 {len(live.items)} 项 · 套餐 {len(live.combos)} 项 · 可用券 {len(live.coupons)} 张")
    hr()

    if coupon:
        print(f"已选最优券：{coupon['name']}（满 ¥{coupon['threshold']:.0f} 减 ¥{coupon['amount']:.0f}）")

    if best:
        print("① 推荐单点组合（预算内最划算）：")
        for it in best["items"]:
            print(f"   · {it['name']:<16} ¥{it['price']:>6.1f}   {it['cal']:>4} kcal")
        print(f"   原价 ¥{best['gross']:.1f} − 优惠 ¥{best['discount']:.1f} = 应付 ¥{best['payable']:.1f}"
              f"   约 {best['cal']} kcal")
        # 用官方 calculate-price 复核
        payable = price_with_mcp(client, best["items"], coupon)
        if payable is not None:
            print(f"   ✅ 官方 calculate-price 复核应付：¥{payable:.1f}")
    else:
        print("预算内没找到合适组合，试试提高 --budget 或换个门店/地址")

    if combo_best:
        hr()
        print(f"② 官方套餐更划算？{combo_best['name']}  ¥{combo_best['price']:.1f}")
        if best and combo_best["price"] < best["payable"]:
            print(f"   → 套餐比上面单点组合还省 ¥{best['payable'] - combo_best['price']:.1f} ✅")
        else:
            print("   → 这单单点更划算，别买套餐")

    hr("=")
    print("本工具只查价与算价，不会下单。想下单可以让 Agent 继续调用 create-order 走你的确认流程。")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="麦麦省钱助手 McSaver —— 麦当劳点餐省钱 Skill")
    ap.add_argument("--budget", type=float, required=True, help="单人预算(元)")
    ap.add_argument("--people", type=int, default=1, help="人数")
    ap.add_argument("--want", type=str, default="吃饱", help="口味关键词，逗号分隔：汉堡/可乐/薯条/甜品/吃饱")
    ap.add_argument("--address", type=str, default=None, help="收货或所在地址（真实模式下用于查附近门店）")
    ap.add_argument("--bind-coupons", action="store_true", help="真实模式下先调用 auto-bind-coupons 一键领取麦麦省券")
    args = ap.parse_args()

    want_tokens = [w for w in args.want.replace("，", ",").split(",") if w]
    token = os.environ.get("MCD_MCP_TOKEN", "").strip()

    if not token:
        render_local(load_local_menu(), args, want_tokens)
        return 0

    client = MCDMcpClient(token)
    try:
        client.initialize()
        if args.bind_coupons:
            client.call_tool(TOOLS["bind_coupons"], {})
        live = fetch_live_menu(client, args.address)
        if not live.items:
            raise MCPError("MCP 未返回在售餐品（可能需要先指定门店/地址）")
        render_live(live, args, want_tokens)
        return 0
    except MCPError as e:
        print(f"⚠️  麦当劳 MCP 调用失败：{e}", file=sys.stderr)
        print("    已回退到本地示例数据（下面的结果不是实时价格）。\n", file=sys.stderr)
        render_local(load_local_menu(), args, want_tokens)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

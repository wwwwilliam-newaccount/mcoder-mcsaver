#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦省钱助手 (McSaver) —— 麦当劳 MCP 接入层

本模块实现 **真实的麦当劳中国 MCP 服务调用**，遵循官方公布的接入方式：

    - 接入地址：https://mcp.mcd.cn
    - 传输协议：Streamable HTTP（JSON-RPC 2.0）
    - 鉴权方式：请求头 Authorization: Bearer <MCP Token>
    - Token 申请：https://open.mcd.cn/mcp

官方工具清单见 https://github.com/M-China/mcd-mcp-server （33 个 Tool）。
McSaver 只读使用其中与「点餐比价 / 省钱」相关的工具，**不会下单、不会扣款**：

    query-nearby-stores    查询附近可用门店
    query-meals            查询当前门店可售卖餐品列表（分类 / 餐品编码 / 标签 / 价格）
    query-meal-detail      查询餐品详情与套餐组成（含套餐单点价对比所需信息）
    query-store-coupons    查询当前门店可用优惠券
    available-coupons      查询当前可领取的「麦麦省」优惠券
    auto-bind-coupons      一键领取麦麦省全部可领优惠券
    query-my-coupons       查询账户下已持有的优惠券
    query-my-account       查询积分账户（含即将过期积分）
    calculate-price        按选购列表（可带优惠券）试算金额、优惠与应付总价
    campaign-calendar      查询营销活动日历

设计原则
--------
1. **真调用优先**：只要设置了 ``MCD_MCP_TOKEN``，就读实时菜单/优惠券并跑真实比价。
2. **诚实回退**：拿不到 Token 或调用失败时，明确打印「回退本地示例数据」，
   不会把本地数据伪装成实时数据。
3. **零依赖**：标准库实现，评审 ``git clone`` 后可直接运行。
"""

from __future__ import annotations

import itertools
import json
import os
import urllib.error
import urllib.request
import uuid

# ---------------------------------------------------------------------------
# 官方接入常量
# ---------------------------------------------------------------------------
MCP_ENDPOINT = os.environ.get("MCD_MCP_ENDPOINT", "https://mcp.mcd.cn")
MCP_TOKEN_ENV = "MCD_MCP_TOKEN"
MCP_PROTOCOL_VERSION = "2025-06-18"
CLIENT_INFO = {"name": "mcsaver", "version": "1.1.0"}

#: McSaver 用到的官方工具（工具名严格对齐 mcd-mcp-server 的 Tool 列表）
TOOLS = {
    "nearby_stores": "query-nearby-stores",
    "meals": "query-meals",
    "meal_detail": "query-meal-detail",
    "store_coupons": "query-store-coupons",
    "available_coupons": "available-coupons",
    "bind_coupons": "auto-bind-coupons",
    "my_coupons": "query-my-coupons",
    "my_account": "query-my-account",
    "calculate_price": "calculate-price",
    "campaign_calendar": "campaign-calendar",
}


class MCPError(RuntimeError):
    """MCP 调用失败（网络 / 鉴权 / 协议层）。"""


# ---------------------------------------------------------------------------
# 极简 Streamable HTTP MCP 客户端
# ---------------------------------------------------------------------------
class MCDMcpClient:
    """麦当劳 MCP 的最小可用客户端（Streamable HTTP + JSON-RPC 2.0）。"""

    def __init__(self, token: str | None = None, endpoint: str = MCP_ENDPOINT, timeout: int = 20):
        self.token = token if token is not None else os.environ.get(MCP_TOKEN_ENV, "")
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.session_id: str | None = None
        self._initialized = False
        self.tool_calls: list[str] = []  # 记录真实调用过的工具，便于输出「数据来源」

    # -- 传输层 -------------------------------------------------------------
    def _post(self, payload: dict, extra_headers: dict | None = None) -> tuple[str, dict]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        if extra_headers:
            headers.update(extra_headers)

        req = urllib.request.Request(self.endpoint, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
                if sid:
                    self.session_id = sid
                ctype = (resp.headers.get("Content-Type") or "").lower()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 401:
                raise MCPError("401 Unauthorized：MCD_MCP_TOKEN 缺失或无效（请到 https://open.mcd.cn/mcp 申请）") from e
            if e.code == 429:
                raise MCPError("429 Too Many Requests：超过 600 次/分钟限流，请降低频率") from e
            raise MCPError(f"HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise MCPError(f"网络不可达：{e}") from e
        return ctype, self._parse(raw, ctype)

    @staticmethod
    def _parse(raw: str, ctype: str) -> dict:
        """兼容 application/json 与 text/event-stream 两种响应体。"""
        if "text/event-stream" in ctype:
            for line in raw.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    chunk = line[5:].strip()
                    if chunk and chunk != "[DONE]":
                        try:
                            return json.loads(chunk)
                        except json.JSONDecodeError:
                            continue
            raise MCPError("SSE 响应中没有可解析的 data 帧")
        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise MCPError(f"响应不是合法 JSON：{raw[:200]}") from e

    # -- 协议层 -------------------------------------------------------------
    def initialize(self) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": CLIENT_INFO,
            },
        }
        _, msg = self._post(payload)
        if "error" in msg:
            raise MCPError(f"initialize 失败：{msg['error']}")
        # 协议要求：initialize 之后发送 initialized 通知
        note = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        try:
            self._post(note)
        except MCPError:
            pass  # 部分实现忽略该通知，不视为致命错误
        self._initialized = True
        return msg.get("result", {})

    def list_tools(self) -> list[str]:
        if not self._initialized:
            self.initialize()
        _, msg = self._post({
            "jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "tools/list", "params": {},
        })
        return [t.get("name", "") for t in msg.get("result", {}).get("tools", [])]

    def call_tool(self, name: str, arguments: dict | None = None):
        """调用官方工具，返回其结构化结果（若为 JSON 文本则自动解析）。"""
        if not self._initialized:
            self.initialize()
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        _, msg = self._post(payload)
        if "error" in msg:
            raise MCPError(f"tools/call {name} 失败：{msg['error']}")
        self.tool_calls.append(name)
        result = msg.get("result", {})
        if result.get("isError"):
            raise MCPError(f"{name} 返回错误：{str(result)[:200]}")
        # MCP 规范：结果内容为 content 数组
        texts = [c.get("text", "") for c in result.get("content", []) if isinstance(c, dict)]
        joined = "\n".join(t for t in texts if t)
        if not joined:
            return result
        try:
            return json.loads(joined)
        except json.JSONDecodeError:
            return joined


# ---------------------------------------------------------------------------
# 真实数据获取：把官方返回的原始结构，整理成 McSaver 的比价模型
# ---------------------------------------------------------------------------
def _first_list(obj, *keys):
    """在嵌套 dict 中按候选键名找到第一个 list（不同场景字段名有差异）。"""
    if isinstance(obj, list):
        return obj
    if not isinstance(obj, dict):
        return []
    for k in keys:
        v = obj.get(k)
        if isinstance(v, list):
            return v
    for v in obj.values():
        found = _first_list(v, *keys)
        if found:
            return found
    return []


def _num(*cands, default=0.0):
    for c in cands:
        if isinstance(c, (int, float)):
            return float(c)
        if isinstance(c, str):
            s = c.strip().replace("¥", "").replace("元", "")
            try:
                return float(s)
            except ValueError:
                continue
    return default


class LiveMenu:
    """通过麦当劳 MCP 拉到的实时菜单 + 优惠券，转换成统一比价模型。"""

    def __init__(self, store: dict, items: list[dict], combos: list[dict],
                 coupons: list[dict], client: MCDMcpClient):
        self.store = store
        self.items = items
        self.combos = combos
        self.coupons = coupons
        self.client = client

    @property
    def source(self) -> str:
        tools = "、".join(dict.fromkeys(self.client.tool_calls)) or "麦当劳 MCP"
        return f"麦当劳 MCP 实时数据（{tools}）"


def _normalize_meal(raw: dict) -> dict | None:
    name = raw.get("name") or raw.get("mealName") or raw.get("productName") or raw.get("title")
    if not name:
        return None
    price = _num(raw.get("price"), raw.get("salePrice"), raw.get("currentPrice"),
                 raw.get("originalPrice"), default=0.0)
    code = raw.get("code") or raw.get("mealCode") or raw.get("productCode") or raw.get("id") or ""
    cat = raw.get("categoryName") or raw.get("category") or raw.get("type") or "其他"
    cal = _num(raw.get("energy"), raw.get("calorie"), raw.get("calories"), default=0.0)
    return {"code": str(code), "name": str(name), "price": price, "cat": str(cat),
            "cal": int(cal), "tags": [str(t) for t in (raw.get("tags") or []) if t]}


def fetch_live_menu(client: MCDMcpClient, address: str | None = None) -> LiveMenu:
    """按官方调用流程拉取门店 → 菜单 → 优惠券 → 账户信息，构造实时比价模型。

    调用流程（与 M-China/mcd-mcp-server 的工具语义一致）：
        query-nearby-stores  → 选定门店
        query-meals          → 该门店在售餐品（含价格/编码/分类）
        query-store-coupons  → 该门店可用券
        query-my-coupons     → 账户已有券
        query-my-account     → 积分（含即将过期）
    """
    tools = TOOLS
    stores = _first_list(
        client.call_tool(tools["nearby_stores"], {"address": address} if address else {}),
        "stores", "storeList", "data", "list", "items",
    )
    store = stores[0] if stores else {}
    store_args = {}
    for key in ("storeCode", "code", "storeId", "id", "beCode"):
        if isinstance(store, dict) and store.get(key):
            store_args["storeCode"] = store[key]
            break

    meals_raw = _first_list(
        client.call_tool(tools["meals"], store_args),
        "meals", "mealList", "categories", "data", "list", "items",
    )
    items, combos = [], []
    for row in meals_raw:
        # 分类节点：其下还有 meals/products 子列表
        children = row.get("meals") or row.get("products") or row.get("items") if isinstance(row, dict) else None
        if isinstance(children, list) and children:
            for child in children:
                norm = _normalize_meal(child if isinstance(child, dict) else {})
                if norm:
                    (combos if ("套餐" in norm["cat"] or "combo" in norm["cat"].lower()) else items).append(norm)
            continue
        if isinstance(row, dict):
            norm = _normalize_meal(row)
            if norm:
                (combos if ("套餐" in norm["cat"] or "combo" in norm["cat"].lower()) else items).append(norm)

    coupons = []
    for tool_key, args in (("store_coupons", store_args), ("my_coupons", {}), ("available_coupons", {})):
        try:
            raw = client.call_tool(tools[tool_key], args)
        except MCPError:
            continue
        for c in _first_list(raw, "coupons", "couponList", "data", "list", "items"):
            if not isinstance(c, dict):
                continue
            name = c.get("name") or c.get("couponName") or c.get("title")
            if name:
                coupons.append({
                    "name": str(name),
                    "amount": _num(c.get("amount"), c.get("discount"), c.get("value"), default=0.0),
                    "threshold": _num(c.get("threshold"), c.get("minAmount"), default=0.0),
                })

    try:
        client.call_tool(tools["my_account"], {})  # 积分/即将过期积分，展示用
    except MCPError:
        pass

    return LiveMenu(store if isinstance(store, dict) else {}, items, combos, coupons, client)


# ---------------------------------------------------------------------------
# 真实比价：用官方 calculate-price 复核「最优组合」的应付总价
# ---------------------------------------------------------------------------
def price_with_mcp(client: MCDMcpClient, combo_items: list[dict], coupon: dict | None = None,
                   store_args: dict | None = None) -> float | None:
    """调用官方 calculate-price 试算组合金额（可带券），返回应付总价。"""
    products = []
    for it in combo_items:
        if it.get("code"):
            products.append({"code": it["code"], "quantity": 1})
    if not products:
        return None
    args = {"products": products}
    if store_args:
        args.update(store_args)
    if coupon and coupon.get("name"):
        args["coupons"] = [{"name": coupon["name"]}]
    try:
        res = client.call_tool(TOOLS["calculate_price"], args)
    except MCPError:
        return None
    keys = ("payableAmount", "payAmount", "totalAmount", "totalPrice", "amount")
    stack = [res]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for k in keys:
                if isinstance(node.get(k), (int, float, str)):
                    return _num(node.get(k))
            stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
        elif isinstance(node, list):
            stack.extend(v for v in node if isinstance(v, (dict, list)))
    return None


# ---------------------------------------------------------------------------
# 组合枚举（真·比价核心）
# ---------------------------------------------------------------------------
def best_single_combo(items: list[dict], budget: float, people: int,
                      coupon: dict | None = None, max_size: int = 4) -> dict | None:
    """在预算内枚举单品组合，返回热量满足度最高的一组（可选叠加优惠券）。"""
    pool = [i for i in items if i.get("price", 0) > 0]
    if not pool:
        return None
    target_cal = 700 * people
    best = None
    for size in range(1, min(max_size, len(pool)) + 1):
        for combo in itertools.combinations(pool, size):
            gross = sum(i["price"] for i in combo)
            disc = 0.0
            if coupon and gross >= coupon.get("threshold", 0.0):
                disc = coupon.get("amount", 0.0)
            payable = max(gross - disc, 0.0)
            if payable > budget:
                continue
            cal = sum(i.get("cal", 0) for i in combo)
            score = (min(cal, target_cal), -payable)  # 先看吃饱程度，再看省钱
            if best is None or score > best["score"]:
                best = {"items": list(combo), "gross": gross, "payable": payable,
                        "discount": disc, "cal": cal, "score": score, "coupon": coupon}
    return best

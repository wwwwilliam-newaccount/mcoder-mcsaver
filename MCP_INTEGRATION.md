# MCP_INTEGRATION.md · 麦当劳 MCP 接入说明

本 Skill 通过**麦当劳中国官方 MCP 服务**获取实时菜单、价格与优惠券数据，并据此完成比价与省钱推荐。

- 官方开放平台：<https://open.mcd.cn/mcp>
- 官方接入仓库：<https://github.com/M-China/mcd-mcp-server>

---

## 1. 实际使用的 MCP Server

| 项目 | 值 |
| --- | --- |
| Server 名称 | 麦当劳中国 MCP Server（`mcd-mcp`） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | **Streamable HTTP**（JSON-RPC 2.0，兼容 `text/event-stream` 响应） |
| 协议版本 | `2025-06-18` |
| 鉴权方式 | 请求头 `Authorization: Bearer <MCP Token>` |
| Token 申请 | <https://open.mcd.cn/mcp> → 右上角「登录」→「控制台」→「激活」→ 同意服务协议 → 复制 Token |
| 频率限制 | 每个 Token 每分钟最多 600 次请求（超出返回 429） |
| 客户端 | WorkBuddy（本 Skill 运行于 WorkBuddy 的 Skill 体系内） |

## 2. 实际调用的 MCP Tool（工具名与官方清单一致）

官方当前提供 33 个 Tool，McSaver **只读**使用其中与「点餐比价 / 省钱」相关的 10 个：

| # | Tool（官方名） | 中文名 | 在 McSaver 中的作用 |
| --- | --- | --- | --- |
| 1 | `query-nearby-stores` | 查询附近可用门店 | 由用户地址定位门店，作为后续查询的上下文 |
| 2 | `query-meals` | 查询当前可售卖餐品列表 | 拉取该门店在售餐品（分类 / 餐品编码 / 价格 / 标签）→ 比价主数据源 |
| 3 | `query-meal-detail` | 查询餐品详情 | 展开套餐组成，用于「套餐 vs 单点」的省钱对比 |
| 4 | `query-store-coupons` | 查询当前门店可用优惠券 | 拿到门店券，参与满减/折扣计算 |
| 5 | `available-coupons` | 麦麦省券列表查询 | 查当前可领取的「麦麦省」券 |
| 6 | `auto-bind-coupons` | 麦麦省一键领券 | 可选：`--bind-coupons` 时先领券再比价 |
| 7 | `query-my-coupons` | 我的优惠券查询 | 纳入账户已有券，避免漏算优惠 |
| 8 | `query-my-account` | 我的积分查询 | 读取积分（含即将过期积分），提示可用权益 |
| 9 | `calculate-price` | 商品价格计算 | **官方口径复核**：按选购列表（可带券）算金额、优惠与应付总价 |
| 10 | `campaign-calendar` | 活动日历查询 | 读取当月营销活动，辅助活动期选品建议 |

> 未使用的写操作类工具：`create-order`、`cancel-order`、`mall-create-order`、`party-order-create`、`draw-lottery`、`delivery-create-address` 等。McSaver 的产品定位是「算清楚再让你决定」，**绝不自作主张下单**。

## 3. 调用流程（真实链路）

```
用户输入: 预算 / 人数 / 口味 / 地址
        │
        ├─ 1. initialize（Streamable HTTP 握手，拿到 Mcp-Session-Id）
        │     POST https://mcp.mcd.cn   JSON-RPC: initialize
        │     ← 响应头 Mcp-Session-Id 用于后续请求
        ├─ 2. notifications/initialized（协议要求的就绪通知）
        │
        ├─ 3. query-nearby-stores  { address }        → 选定门店
        ├─ 4. query-meals          { storeCode }      → 在售餐品 + 价格
        ├─ 5. query-store-coupons  { storeCode }      → 门店券
        ├─ 6. query-my-coupons / available-coupons    → 账户券、可领券
        ├─ 7. query-my-account                        → 积分（含即将过期）
        │
        ├─ 8. 本地比价：在预算内枚举单品组合，最大化「吃饱程度 × 省得更多」
        │
        └─ 9. calculate-price      { products, coupons, storeCode }  → 官方复核应付总价
```

实现代码：`scripts/mcp_client.py`（Streamable HTTP + JSON-RPC 客户端，零第三方依赖），
命令行入口：`scripts/mcsaver.py`。

## 4. 业务价值（为什么要接 MCP，而不是自己维护一套菜单）

1. **价格与优惠是实时变量**：麦当劳的套餐价、限时活动、门店券、账户券、积分规则都在变，只有官方 MCP 能给出当下真实的菜单与可叠加优惠。
2. **官方口径试算**：本地自己算满减容易算错，`calculate-price` 用官方规则返回应付总价，McSaver 用它复核推荐结果，避免“看起来省了其实没省”。
3. **省钱可量化**：把「单点 vs 套餐 vs 用券」三种走法放在一起给出确定金额差，用户不必自己心算叠加规则。
4. **只读、可控**：只调用查询与试算工具，不触碰下单与支付，用户始终拥有最终决定权。

## 5. 如何配置与验证

```bash
# 1) 申请 Token（浏览器）：https://open.mcd.cn/mcp
# 2) 配置环境变量
export MCD_MCP_TOKEN="你的 MCP Token"        # Windows CMD: set MCD_MCP_TOKEN=...
# 3) 真实模式运行（会自动走 MCP 拉实时数据）
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱 --address 深圳市南山区
# 可选：先一键领取麦麦省券再比价
python scripts/mcsaver.py --budget 60 --people 2 --want 汉堡,可乐 --bind-coupons

# 4) 未配置 Token 时：自动回退本地示例数据，并在输出中明确标注「本地示例数据」
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱
```

WorkBuddy 中的 MCP 配置示例见 `mcp-config.example.json`（只含环境变量占位符，无任何真实凭证）。

## 6. 错误处理（如实降级）

| 情况 | 行为 |
| --- | --- |
| 未设置 `MCD_MCP_TOKEN` | 不发起网络请求，直接走本地示例数据，输出明确标注数据来源 |
| Token 无效（HTTP 401） | 打印 401 原因与 Token 申请地址，回退本地数据，退出码 1 |
| 触发限流（HTTP 429） | 打印限流提示（600 次/分钟），回退本地数据 |
| 网络不可达 / 超时 | 捕获 `URLError`，打印网络原因，回退本地数据 |
| 工具返回错误 | 捕获 `MCPError`，跳过该券源继续比价，不假装成功 |

> 设计原则：**宁可说自己没连上，也不把本地示例数据冒充成实时价格。**

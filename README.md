# 麦麦省钱助手 (McSaver)

> 2026 麦当劳程序员创意开发大赛参赛作品 · 基于**麦当劳中国 MCP** 能力的点餐省钱 Skill
> 由 **腾讯 WorkBuddy** 辅助开发（开发过程实录见 [`workbuddy.md`](./workbuddy.md)）

## 一句话介绍

一个帮你在麦当劳**点得饱、点得省**的 Skill：输入预算、人数和想吃的，它调用麦当劳 MCP 的实时菜单、价格和优惠券，枚举出预算内最划算的组合，并告诉你比单点省了多少钱——**只算不下单**。

## 为什么需要它

麦当劳的价格体系里同时存在单品价、套餐价、门店券、账户券、麦麦省券、积分权益，叠加规则人脑很难算清。
McSaver 把这套账交给官方 MCP 去查、去试算，最后只给你一个结论：**怎么点最便宜，省了多少。**

## 真实使用麦当劳 MCP

| 项目 | 值 |
| --- | --- |
| MCP Server | 麦当劳中国 `mcd-mcp`（`https://mcp.mcd.cn`，Streamable HTTP） |
| 鉴权 | `Authorization: Bearer <MCP Token>`，Token 申请：<https://open.mcd.cn/mcp> |
| 只读工具（10 个） | `query-nearby-stores`、`query-meals`、`query-meal-detail`、`query-store-coupons`、`available-coupons`、`auto-bind-coupons`、`query-my-coupons`、`query-my-account`、`calculate-price`、`campaign-calendar` |
| 明确不调用 | `create-order`、`cancel-order`、`mall-create-order`、`party-order-create`、`draw-lottery` 等写操作工具 |

完整调用流程与业务价值见 [`MCP_INTEGRATION.md`](./MCP_INTEGRATION.md)，配置示例见 [`mcp-config.example.json`](./mcp-config.example.json)。

## 快速开始

### 1) 离线演示（零配置）

```bash
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱
```

输出会在开头明确标注 `⚠️ 本地示例数据 menu.json（未接入麦当劳 MCP）`，不会冒充实时价格。

### 2) 真实模式（接入麦当劳 MCP）

```bash
# 申请 Token：https://open.mcd.cn/mcp （手机号登录 → 控制台 → 激活）
export MCD_MCP_TOKEN="你的 MCP Token"          # Windows CMD: set MCD_MCP_TOKEN=...

python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱 --address 深圳市南山区
python scripts/mcsaver.py --budget 60 --people 2 --want 汉堡,可乐 --bind-coupons
```

真实模式下会依次调用 `query-nearby-stores` → `query-meals` → `query-store-coupons` →
`query-my-coupons` → `query-my-account` 拉实时数据，用 `calculate-price` 复核应付总价。

### 示例输出（离线路径）

```
🍔 麦麦省钱助手 McSaver
====================================================
需求：1 人 · 总预算 ¥30 · 偏好：吃饱
数据来源：⚠️  本地示例数据 menu.json（未接入麦当劳 MCP）
----------------------------------------------------
① 单点组合（本地启发式）：
   · 圆筒冰淇淋  ¥  5.0    180 kcal
   · 派(香芋)    ¥  7.0    240 kcal
   · 麦香鸡      ¥ 12.0    388 kcal
   小计 ¥24.0 · 约 808 kcal
----------------------------------------------------
② 更划算的套餐：吉士汉堡超值  ¥18.0
   含：吉士汉堡, 薯条(中), 可乐(中)
   单点价 ¥33.0 → 省 ¥15.0 💰
```

## 安装 / 运行要求

- Python 3.8+，**仅标准库**（无需 pip 安装任何第三方依赖，方便评审直接复现）
- 可选：麦当劳 MCP Token（不配置也能跑，只是走本地示例数据）

## 命令行参数

| 参数 | 说明 |
| --- | --- |
| `--budget` | 单人预算（元），必填 |
| `--people` | 人数，默认 1（总预算 = 预算 × 人数） |
| `--want` | 口味关键词，逗号分隔：`汉堡` / `可乐` / `薯条` / `咖啡` / `甜品` / `吃饱` |
| `--address` | 真实模式下用于 `query-nearby-stores` 定位门店 |
| `--bind-coupons` | 真实模式下先调用 `auto-bind-coupons` 一键领取麦麦省券再比价 |

## 目标用户

- 想用固定预算（比如 30 元、60 元）吃到最划算组合的学生和上班族
- 手里攒了一堆券却算不清怎么叠加最省的重度用户
- 想让 AI 助手接管「今天麦当劳怎么点」这个日常决策的人

## 目录结构

```
mcoder-mcsaver/
├── SKILL.md                      # Skill 元信息（WorkBuddy 原生 Skill）
├── README.md                     # 项目介绍 / 安装 / 使用示例 / 目标用户
├── CONTEST_DECLARATION.md        # 参赛声明（原创性、合规性、敏感信息）
├── MCP_INTEGRATION.md            # 麦当劳 MCP 接入说明（Server / Tool / 调用流程 / 业务价值）
├── mcp-config.example.json       # 脱敏 MCP 配置示例（仅环境变量占位符）
├── workbuddy.md                  # WorkBuddy 对话上下文（专项奖励材料）
├── ISSUE模板.md                   # 提交到官方活动仓库的 Issue 内容
├── menu.json                     # 离线演示用示例菜单
├── scripts/
│   ├── mcp_client.py             # 麦当劳 MCP 客户端（Streamable HTTP + JSON-RPC）
│   └── mcsaver.py                # 核心推荐引擎 / 命令行入口
├── 发布到GitHub.bat               # 一键发布脚本（可选工具）
└── LICENSE                       # MIT
```

## 参赛信息

- 赛事：2026 麦当劳程序员创意开发大赛
- 作者：[@wwwwilliam-newaccount](https://github.com/wwwwilliam-newaccount)
- 开发工具：腾讯 WorkBuddy（符合「使用 WorkBuddy 开发参赛」专项奖励）
- 授权：[MIT](./LICENSE)
- 参赛声明：[CONTEST_DECLARATION.md](./CONTEST_DECLARATION.md)

## 免责说明

本作品只读麦当劳 MCP 数据用于比价建议，**不代下单、不发起支付**；菜单与价格以麦当劳 MCP 实时返回为准。
使用需遵守麦当劳中国《使用条款》与《麦当劳 MCP 服务规则》。

---
name: mcsaver
display_name: "麦麦省钱助手"
description: "基于麦当劳中国 MCP 能力的点餐省钱 Skill。根据预算、人数、口味与饱腹需求，调用麦当劳 MCP 的实时菜单/价格/优惠券接口，枚举最划算的点餐组合并用官方 calculate-price 复核应付总价；未配置 MCP Token 时回退到本地示例菜单，并在输出中明确标注数据来源。触发词：麦麦、点餐、省钱、优惠、套餐、麦当劳、怎么点划算。"
version: "1.1.0"
author: "wwwwilliam-newaccount（参赛作品，WorkBuddy 辅助开发）"
license: "MIT"
---

# 麦麦省钱助手 (McSaver)

一个帮你在麦当劳「点得饱又点得省」的 WorkBuddy Skill。

## 它能做什么

- 输入「预算 / 人数 / 想吃什么 / 多饱 / 在哪个地址」，输出最优的点餐方案
- 优先调用麦当劳 MCP 的实时菜单、价格与优惠券接口，用官方 `calculate-price` 复核应付总价
- 没有 MCP 环境时回退到本地 `menu.json` + 启发式算法，**并在输出首行标注「本地示例数据」**
- 给出「单点 vs 套餐 vs 用券」的省钱金额对比，告诉你到底省了多少
- 只算不下单：不会调用 `create-order` 等写操作工具

## 适用场景

- 「30 块一个人想吃麦当劳怎么点最划算」
- 「两个人 60 块，要一个汉堡一杯可乐怎么配」
- 「我有哪些券可以叠，最后实付多少」

## 使用方式

```
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱
python scripts/mcsaver.py --budget 60 --people 2 --want 汉堡,可乐 --address 深圳市南山区 --bind-coupons
```

`--want` 支持关键词（汉堡/鸡/薯条/可乐/咖啡/甜品/吃饱），`--budget` 为单人预算（元），
`--people` 为人数（总预算 = 预算 × 人数），`--address` 用于定位门店，`--bind-coupons` 先一键领麦麦省券。

## MCP 接入

本 Skill 通过麦当劳中国 MCP 服务（`https://mcp.mcd.cn`，Streamable HTTP + Bearer Token）获取实时数据，
详见 [`MCP_INTEGRATION.md`](./MCP_INTEGRATION.md) 与 [`mcp-config.example.json`](./mcp-config.example.json)。

实际调用的官方只读工具：

- `query-nearby-stores` —— 查询附近可用门店
- `query-meals` —— 查询当前可售卖餐品列表（菜单与价格）
- `query-meal-detail` —— 查询餐品详情与套餐组成
- `query-store-coupons` / `available-coupons` / `query-my-coupons` —— 门店券、麦麦省券、账户券
- `query-my-account` —— 我的积分查询
- `calculate-price` —— 官方口径试算应付总价
- `campaign-calendar` —— 活动日历查询

## 目录结构

```
mcoder-mcsaver/
├── SKILL.md                      # 本文件（Skill 元信息 + 说明）
├── README.md                     # 项目介绍 / 安装 / 使用示例 / 目标用户
├── CONTEST_DECLARATION.md        # 参赛声明
├── MCP_INTEGRATION.md            # MCP 接入说明
├── mcp-config.example.json       # 脱敏 MCP 配置示例
├── workbuddy.md                  # WorkBuddy 对话上下文（专项奖励材料）
├── ISSUE模板.md                   # 提交到官方活动仓库的 Issue 内容
├── scripts/
│   ├── mcp_client.py             # 麦当劳 MCP 客户端
│   └── mcsaver.py                # 核心推荐引擎 / 命令行入口
├── menu.json                     # 本地回退菜单数据（示例）
└── LICENSE                       # MIT
```

## 由 WorkBuddy 辅助开发

本作品由腾讯 WorkBuddy 辅助完成需求收敛、算法与代码编写、文档生成与本地验证，
符合赛事「使用 WorkBuddy 开发参赛」专项奖励要求；开发过程实录见 [`workbuddy.md`](./workbuddy.md)。

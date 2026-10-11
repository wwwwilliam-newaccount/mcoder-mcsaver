# 麦麦省钱助手 (McSaver)

> 2026 麦当劳程序员创意开发大赛 · 参赛作品
> 基于 **麦当劳 MCP 能力** 开发的 WorkBuddy Skill，由 **WorkBuddy** 辅助开发。

## 一句话介绍

一个帮你在麦当劳「点得饱、点得省」的 AI 点餐助手：输入预算、人数和想吃的，它调用麦当劳 MCP 实时菜单/价格/优惠，算出最划算的组合，并告诉你比单点省了多少。

## 亮点

- 🤖 **真·MCP 接入**：优先走麦当劳 MCP（`mcd_menu_list` / `mcd_promo_list` / `mcd_combo_best`）拿实时数据
- 🪄 **离线也能跑**：MCP 不可用时自动回退到本地 `menu.json` + 启发式算法，演示零门槛
- 💰 **省钱对比**：每次推荐都给出「单点价 vs 套餐价」的实打实省钱金额
- 🧩 **WorkBuddy 原生 Skill**：直接放进 WorkBuddy 即可用，符合赛事「开发创意 Skill」要求

## 快速开始

```bash
# 30 元一个人，想吃顿饱的
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱

# 两个人 60 元，要汉堡+可乐
python scripts/mcsaver.py --budget 60 --people 2 --want 汉堡,可乐
```

## MCP 接入

详见 [MCP接入说明.md](./MCP接入说明.md)。接入后脚本自动优先使用实时接口；未接入则使用本地回退数据。

## 参赛信息

- 赛事：2026 麦当劳程序员创意开发大赛
- 作者：WorkBuddy 用户
- 开发工具：WorkBuddy（符合「使用 WorkBuddy 开发参赛」专项奖励）
- 授权：MIT

详见 [参赛声明.md](./参赛声明.md)。

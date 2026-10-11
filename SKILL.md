---
name: mcsaver
display_name: "麦麦省钱助手"
description: "基于麦当劳 MCP 能力的点餐省钱 Skill。根据预算、人数、口味与饱腹需求，结合麦当劳菜单/价格/优惠接口，推荐最划算的点餐组合；在无法连通 MCP 时回退到本地菜单与启发式算法，保证可独立运行。触发词：麦麦、点餐、省钱、优惠、套餐、麦当劳、怎么点划算。"
version: "1.0.0"
author: "WorkBuddy 用户（参赛作品）"
license: "MIT"
---

# 麦麦省钱助手 (McSaver)

一个帮你在麦当劳「点得饱又点得省」的 WorkBuddy Skill。

## 它能做什么

- 输入「预算 / 人数 / 想吃什么 / 多饱」之类需求，输出最优点餐方案
- 优先调用麦当劳 MCP 的实时菜单、价格和优惠接口，给出有活动叠加的最优解
- 没有 MCP 环境时，回退到本地 `menu.json` + 启发式算法，照样能跑出推荐
- 一键给出「按单点 vs 套餐」的省钱对比，告诉你省了多少

## 适用场景

- 「30 块一个人想吃麦当劳怎么点最划算」
- 「两个人 60 块，要一个汉堡一杯可乐怎么配」
- 「今晚有啥麦当劳优惠能叠加」

## 使用方式

```
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱
python scripts/mcsaver.py --budget 60 --people 2 --want 汉堡,可乐
```

`--want` 支持口味关键词（汉堡/鸡/薯条/可乐/咖啡/甜品/吃饱），`--budget` 为单人预算（元），`--people` 为人数（自动按人数放大预算与份量）。

## MCP 接入

本 Skill 通过麦当劳 MCP 服务获取实时数据，详见同仓库 `MCP接入说明.md`。
接入后脚本会优先使用以下 MCP 工具（未接入时自动回退本地数据）：

- `mcd_menu_list`  —— 获取当前在售菜单与单价
- `mcd_promo_list` —— 获取当前可叠加的优惠/套餐
- `mcd_combo_best` —— 给定预算与需求，返回官方最优组合

## 目录结构

```
mcoder-mcsaver/
├── SKILL.md          # 本文件（Skill 元信息 + 说明）
├── README.md         # 项目介绍（参赛展示用）
├── 参赛声明.md        # 参赛声明
├── MCP接入说明.md     # MCP 接入与运行说明
├── ISSUE模板.md       # 复制到 M-China 官方活动 Issue 的提交内容
├── scripts/
│   └── mcsaver.py    # 核心推荐引擎
├── menu.json         # 本地回退菜单数据
└── LICENSE           # MIT
```

## 由 WorkBuddy 辅助开发

本作品由 WorkBuddy 辅助设计、编写与生成全部文档，符合「使用 WorkBuddy 开发参赛」专项奖励要求。

<!-- 复制到 M-China 官方活动仓库的指定 Issue 模板中提交 -->
<!-- 方括号内容按实际情况替换 -->

## 作品名称
麦麦省钱助手 (McSaver)

## 作者
WorkBuddy 用户

## 仓库地址
https://github.com/<你的用户名>/mcoder-mcsaver

## 一句话简介
基于麦当劳 MCP 能力的点餐省钱 Skill：输入预算/人数/口味，调用实时菜单与优惠，推荐最划算组合并对比省钱金额。

## 开发工具
WorkBuddy（符合「使用 WorkBuddy 开发参赛」专项奖励）

## 使用的麦当劳 MCP 能力
- 实时菜单与单价 (mcd_menu_list)
- 可叠加优惠/套餐 (mcd_promo_list)
- 最优组合推荐 (mcd_combo_best)

## 项目亮点
1. 真·MCP 接入，优先使用实时数据
2. MCP 不可用时回退本地数据，离线也能跑
3. 每次推荐给出单点 vs 套餐的实打实省钱金额
4. WorkBuddy 原生 Skill，开箱即用

## 运行方式
```bash
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱
```

## 参赛声明
已阅读并同意赛事规则；作品原创，基于麦当劳 MCP 公开接口开发，以 MIT 协议开源发布。详见仓库内 `参赛声明.md`。

## 附加说明
本作品由 WorkBuddy 辅助设计与生成。

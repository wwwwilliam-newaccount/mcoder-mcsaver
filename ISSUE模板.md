<!-- 提交到官方活动仓库 M-China/mcd-developer-innovation-challenge 的 Issue 内容 -->
<!-- 官方格式（activityGuidelines.md「Issue格式示例」）：【参赛申请】/ 项目名称 / 项目地址 / 项目简介 -->

【参赛申请】
项目名称：麦麦省钱助手（McSaver）
项目地址：https://github.com/wwwwilliam-newaccount/mcoder-mcsaver
项目简介：麦当劳的单品价、套餐价、门店券、麦麦省券、账户券和积分叠在一起，人脑很难算清哪一单最便宜。麦麦省钱助手是一个基于麦当劳中国 MCP 的点餐省钱 Skill：先用 query-nearby-stores 定位门店，拉取 query-meals 实时菜单、query-store-coupons / available-coupons / query-my-coupons 三类优惠券与 query-my-account 积分，在预算内枚举最划算的组合，再用官方 calculate-price 按真实满减规则复核应付总价，最后直接告诉你「单点 vs 套餐 vs 用券」三种走法各花多少钱、能省多少。只算不下单，下单由你点头。由腾讯 WorkBuddy 辅助开发（仓库内含 workbuddy.md 对话上下文）。

<!--
补充说明（按需附在 Issue 里，非官方要求字段）：
- 开发工具：腾讯 WorkBuddy
- 麦当劳 MCP 工具：query-nearby-stores / query-meals / query-meal-detail /
  query-store-coupons / available-coupons / auto-bind-coupons / query-my-coupons /
  query-my-account / calculate-price / campaign-calendar（全部只读）
- 运行方式：python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱
-->

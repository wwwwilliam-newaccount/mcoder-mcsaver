# MCP 接入说明

本 Skill 通过 **麦当劳 MCP (M-China)** 服务获取实时菜单、价格与优惠数据。

## 1. 获取 MCP 接入信息

请前往赛事官方 GitHub 组织 **M-China** 的活动仓库，按官方说明获取：

- MCP Server 地址（endpoint）
- 接入令牌（token，如官方要求）
- 官方 MCP 工具清单（以官方 `mcp` 配置为准）

> 注：官方工具名与字段以 M-China 仓库公布的 MCP manifest 为准。本说明中的工具名是「预期契约」，接入时按官方实际清单对齐即可。

## 2. 预期 MCP 工具契约

| 工具名 | 说明 | 入参 | 返回 |
| --- | --- | --- | --- |
| `mcd_menu_list` | 当前在售菜单与单价 | 无 / 地区码 | 菜品列表（名称、价格、分类、热量） |
| `mcd_promo_list` | 当前可叠加优惠/套餐 | 无 | 优惠列表（名称、条件、优惠额） |
| `mcd_combo_best` | 给定需求返回最优组合 | 预算、人数、偏好 | 推荐组合与总价 |

## 3. 在 WorkBuddy 中接入

在 WorkBuddy 的 MCP 配置中加入麦当劳 MCP Server（具体字段以官方 manifest 为准），例如：

```json
{
  "mcpServers": {
    "mcdonalds": {
      "url": "<M-China 官方 MCP endpoint>",
      "headers": { "Authorization": "Bearer <your-token>" }
    }
  }
}
```

接入成功后，`scripts/mcsaver.py` 会自动检测 MCP 可用性并优先调用上述工具；未接入时回退到 `menu.json` 本地数据，保证可独立演示。

## 4. 本地运行（无需 MCP）

```bash
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱
```

## 5. 运行依赖

- Python 3.8+
- 标准库即可（无需第三方依赖），便于评审直接复现

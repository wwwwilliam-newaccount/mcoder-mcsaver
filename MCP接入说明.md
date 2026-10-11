# MCP 接入说明（中文版）

> 英文/规范命名版本见 [`MCP_INTEGRATION.md`](./MCP_INTEGRATION.md)，配置示例见 [`mcp-config.example.json`](./mcp-config.example.json)。

本 Skill 通过**麦当劳中国官方 MCP 服务**获取实时菜单、价格与优惠券数据。

## 1. 接入信息

| 项目 | 值 |
| --- | --- |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP（JSON-RPC 2.0，兼容 `text/event-stream`） |
| 鉴权 | 请求头 `Authorization: Bearer <MCP Token>` |
| Token 申请 | <https://open.mcd.cn/mcp>（手机号登录 → 控制台 → 激活 → 复制 Token） |
| 官方文档 | <https://github.com/M-China/mcd-mcp-server> |
| 限流 | 每 Token 每分钟 600 次请求，超出返回 429 |

## 2. 在 WorkBuddy 中接入

把下面的配置加入 WorkBuddy 的 MCP Server 配置（**Token 请用环境变量，不要写死在文件里**）：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer ${MCD_MCP_TOKEN}" }
    }
  }
}
```

然后设置环境变量 `MCD_MCP_TOKEN`，`scripts/mcsaver.py` 会自动检测并优先走实时数据。

## 3. 实际调用的官方工具（只读）

| 工具（官方名） | 中文名 | 用途 |
| --- | --- | --- |
| `query-nearby-stores` | 查询附近可用门店 | 按地址定位门店 |
| `query-meals` | 查询当前可售卖餐品列表 | 拉实时菜单与价格 |
| `query-meal-detail` | 查询餐品详情 | 展开套餐组成，对比单点价 |
| `query-store-coupons` | 查询当前门店可用优惠券 | 门店券参与满减 |
| `available-coupons` | 麦麦省券列表查询 | 可领取的麦麦省券 |
| `auto-bind-coupons` | 麦麦省一键领券 | `--bind-coupons` 时先领券 |
| `query-my-coupons` | 我的优惠券查询 | 账户已有券 |
| `query-my-account` | 我的积分查询 | 积分与即将过期积分 |
| `calculate-price` | 商品价格计算 | 官方口径复核应付总价 |
| `campaign-calendar` | 活动日历查询 | 当月营销活动 |

**明确不使用**：`create-order`、`cancel-order`、`mall-create-order`、`party-order-create`、`draw-lottery`、`delivery-create-address` 等写操作工具——本 Skill 只算不下单。

## 4. 本地运行

```bash
# 离线演示（不联网）
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱

# 真实模式
export MCD_MCP_TOKEN="你的 MCP Token"
python scripts/mcsaver.py --budget 30 --people 1 --want 吃饱 --address 深圳市南山区
```

## 5. 运行依赖

- Python 3.8+
- 仅标准库（无第三方依赖），便于评审直接复现

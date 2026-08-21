# Token聚合比价与测评工具 (welltoken-price-dashboard) UI 交互设计规范与信息架构

本文档为 **Token 聚合比价与测评工具 (welltoken-price-dashboard)** 的界面设计、交互流转、原型规格与算法规范文档。设计融合了 **models.dev**、**relaywatch** 与 **token-speed-tester** 三大开源项目的核心优势，面向 Token 运营人员提供专业高效的生产力工具。

---

## 🎨 1. 视觉设计系统规范 (Design System Tokens)

### 1.1 调色板 (Color Palette)
本产品采用现代暗黑科技风金融调色盘，兼顾数据密集型界面的可读性与沉浸感：

| 色彩角色 | 色值 (HEX) | 说明 / 用途 |
| :--- | :--- | :--- |
| **主背景色 (Background)** | `#0B0E14` | 全局视口底色，深邃防眩光 |
| **侧边栏底色 (Sidebar)** | `#0F121A` | 左侧导航栏底色，与内容区形成微阶层 |
| **卡片/面板色 (Card/Panel)** | `#151922` | 核心容器底色，配合 `border: 1px solid #232936` |
| **悬浮/选中色 (Hover/Active)**| `#1E293B` | 表格行悬浮、选中菜单项背景 |
| **品牌主色 (Primary Accent)** | `#2563EB` / `#3B82F6` | 主按钮、选中指示器、关键高亮 |
| **成功/低价绿 (Crypto Green)**| `#10B981` / `#34D399` | 价格优惠、连通正常、低延迟、S级评分 |
| **警示/高价红 (Crypto Red)**  | `#EF4444` / `#F87171` | 溢价告警、连通异常、错误率高 |
| **橙色/次要高亮 (Warning)**   | `#F59E0B` | A级评分、中转倍率特惠提示 |
| **主文本 (Text Primary)**     | `#F3F4F6` | 标题、核心数值、模型 ID |
| **次文本 (Text Secondary)**   | `#9CA3AF` / `#8E9AA8` | 标签名称、单位、说明副标题 |
| **微弱文本 (Text Muted)**     | `#6B7280` | 时间戳、脚注、辅助信息 |

### 1.2 排版与字体体系 (Typography)
- **常规界面字体**：`Inter, system-ui, -apple-system, sans-serif`（清晰优雅，支持国际化）
- **数值与代码字体**：`JetBrains Mono, Fira Code, monospace`（所有单价、倍率、TTFT、TPS、模型 ID 均强制使用等宽字体对齐）
- **字阶规范**：
  - `Display / KPI`: `24px / 700 (Bold)`（如实时 TPS、TTFT 核心卡片指标）
  - `Title (H1/H2)`: `14px - 16px / 700`（模块标题、站点名称）
  - `Body / Cell`: `12px / 400 - 500`（表格内容、卡片正文）
  - `Caption / Meta`: `10px - 11px / 400`（时间、辅助标签、协议标识）

---

## 🖥️ 2. 五大核心页面原型与交互规范

原型文件位于 [`design/welltoken-price-dashboard.ep`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/design/welltoken-price-dashboard.ep)，可在 VS Code 中安装 **Pencil** 扩展直接打开与交互。

```
welltoken-price-dashboard.ep
├── 01_全网大模型聚合比价中心 (Price Matrix & Comparison)
├── 02_Token渠道大全与配置管理 (Relay Channels & Sites)
├── 03_大模型厂商与模型元数据 (Model Catalog & Standards)
├── 04_渠道性能实测工作台 (Speed & Benchmark Tester)
└── 05_数据同步与设置中心 (Sync Hub & Settings)
```

---

### 页面 1：全网大模型聚合比价中心 (Price Matrix)
```
+-----------------------------------------------------------------------------------------------+
| [W] WellToken 比价与测评 Pro   [ models.dev 已同步 | 监控中转站: 18 | 模型: 142 ]   [USD/CNY] [⚡刷新] |
+-----------+-----------------------------------------------------------------------------------+
| 📊聚合比价 | 厂商筛选: [全部] [OpenAI] [Anthropic] [DeepSeek] [Google] | 热点: [GPT-4o] [R1]...  |
| 🌐渠道大全 +-----------------------------------------------------------------------------------+
| 🤖模型标准 | 模型标准名称      渠道/站点       类型    输入/1M       输出/1M      折算倍率  折扣度  TPS |
| ⏱️性能实测 | deepseek-v3     DeepSeek 官方   官方   $0.14/￥1.0   $0.28/￥2.0   1.00x   基准   62.4|
| ⚙️数据同步 | deepseek-v3     极速云 (NewAPI) NewAPI $0.07/￥0.5   $0.14/￥1.0   0.50x   -50%   58.9|
|           | claude-3-5-son  Anthropic 官方  官方   $3.00/￥21.9  $15.0/￥109   1.00x   基准   45.2|
|           | claude-3-5-son  星河 (Sub2API)  Sub2   $1.80/￥13.1  $9.00/￥65.7  0.60x   -40%   41.8|
|           +-----------------------------------------------------------------------------------+
|           | 📈 全网价格分布与性价比散点图 (X=价格, Y=TPS, 气泡=稳定性, 极速云最优性价比)          |
+-----------+-----------------------------------------------------------------------------------+
```
- **核心交互**：
  1. 支持按 **模型名称**、**输入单价**、**输出单价**、**折扣幅度**、**实测 TPS** 任意列排序。
  2. 点击某行模型，底部散点图动态切换该模型在全网各渠道的价格-性能分布气泡。
  3. 支持点击右上角 **USD / CNY** 按钮，毫秒级无缝切换汇率显示（基于实时汇率联动）。

---

### 页面 2：Token 渠道大全与配置管理 (Relay Channels)
- **卡片栅格布局**：
  - 每张渠道卡片展示：站点名称、架构类型徽标（`NewAPI` / `Sub2API` / `OneAPI` / `官方`）、Base URL、连通性延时点、充值汇率比、支持模型数、账户余额及最后同步时间。
- **抽屉式配置编辑器 (Drawer)**：
  - 支持配置渠道 Base URL、API Key、组织 ID。
  - **自动探测端点规则**：
    - 模型列表端点（默认为 `/api/models` 或 `/v1/models`）
    - 状态与倍率端点（默认为 `/api/status` 或 `/api/user/models`）
    - 用户充值比换算规则（如 `1 元 = 1 刀` 或 `1 元 = 0.5 刀`）
  - 提供 **「测试连通性并拉取模型」** 按钮，实时验证 Key 有效性并预览模型清单。

---

### 页面 3：大模型厂商与模型元数据 (Model Catalog)
- **数据源绑定**：全面拉取并映射 `https://models.dev/api.json` 的模型标准定义。
- **展示要素**：
  - 模型标准 ID（Standard Identifier）、所属厂商（Provider）。
  - 上下文窗口 Context Window（如 64k, 128k, 200k, 1M）、最大输出 Max Output Tokens。
  - 核心能力标签（Vision, Reasoning, Tool Calling, Structured Output）。
  - 官方基准价（Input / Output / Cache Hit 每 1M Tokens）。
  - 当前已提供该模型的中转渠道总数与全网最低优惠价。

---

### 页面 4：渠道性能实测工作台 (Speed Tester)
- **实测配置**：
  - 测试模式：可多选测试渠道，支持全网一键并发压测。
  - Prompt 预设：标准测试（500 Tokens 生成）、深度推理生成、模型一致性探针（反降级/反掺假测试）。
- **实时流式看板 (Real-time Streaming)**：
  - 首字延迟 TTFT (ms)、生成速率 TPS (tokens/s)、10-Token 滑动窗口峰值 TPS。
  - 动态 ECharts 曲线图展示 SSE 流式接收过程中每个 Token 的生成间隔平稳度。
- **打分矩阵与排行榜**：
  - 综合评分算法（综合 TTFT 权重 35%、TPS 权重 45%、错误率权重 20%），输出 S / A / B / C 评级与 HTML 导出报告。

---

### 页面 5：数据同步与设置中心 (Sync Hub)
- **定时调度器**：
  - models.dev 官方基准库定时抓取任务配置（支持 Cron 表达式，默认每日凌晨 3:00）。
  - 已配置中转站倍率自动轮询任务（支持设置轮询周期如 60 分钟、并发请求线程数）。
- **汇率与数据库运维**：
  - 实时 USD / CNY 汇率配置与自动更新开关。
  - SQLite 数据库状态（总记录数、占用空间、历史快照数），支持一键备份与 Excel 导出。

---

## 📐 3. 核心计算与算法逻辑

### 3.1 价格与倍率折算算法
对于任一中转渠道 $S$ 和模型 $M$：
1. **官方基准价**：
   - 官方输入单价：$P_{in}^{official}$ ($/1M)
   - 官方输出单价：$P_{out}^{official}$ ($/1M)
2. **渠道计费规则**：
   - 渠道模型基础倍率：$R_{model}$（例如 0.8x）
   - 渠道充值汇率：$Rate_{recharge}$（例如 1 元 = 1 刀，即充值折扣比 1.0；若 1 元 = 0.5 刀，充值折扣比为 2.0）
   - 渠道组倍率：$R_{group}$（默认为 1.0）
3. **折算后单价**：
   $$P_{in}^{relay} = P_{in}^{official} \times R_{model} \times R_{group} \times Rate_{recharge}$$
   $$P_{out}^{relay} = P_{out}^{official} \times R_{model} \times R_{group} \times Rate_{recharge}$$
4. **相比官方折扣度**：
   $$Discount = \frac{P_{in}^{relay} - P_{in}^{official}}{P_{in}^{official}} \times 100\%$$

---

### 3.2 测速指标计算公式
基于 `token-speed-tester` 规范：
1. **首字延迟 (TTFT)**：
   $$TTFT = T_{first\_token\_received} - T_{request\_sent} \quad (\text{ms})$$
2. **平均生成速率 (TPS)**：
   $$TPS_{avg} = \frac{N_{completion\_tokens}}{T_{stream\_finished} - T_{first\_token\_received}} \quad (\text{tokens/s})$$
3. **滑动窗口峰值速率 (Peak TPS)**：
   采用 10 个 Token 的滑动窗口计算瞬时速率最大值：
   $$TPS_{peak} = \max_{k} \left( \frac{10}{T_{token[k+10]} - T_{token[k]}} \right)$$
4. **抖动率 (Jitter)**：
   Token 间隔时间的标准差与均值之比，用于衡量中转站网络吐字平稳度。

---

## 🚀 4. 在 VS Code 中使用 Pencil 查看原型指南

1. **安装 Pencil 扩展**：
   在 VS Code 扩展市场搜索并安装 `Pencil` (或安装独立的 Pencil Project 客户端应用)。
2. **打开原型文件**：
   在文件资源管理器中右键点击 [`design/welltoken-price-dashboard.ep`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/design/welltoken-price-dashboard.ep)，选择 **Open with Pencil**。
3. **浏览页面**：
   在左侧页面列表（Pages）中可快速切换浏览 5 大页面的高保真线框原型。

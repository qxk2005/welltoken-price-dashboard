# 官方大模型定价中心厂商收录与抓取规范 (Official Pricing Rules)

## 1. 官方收录厂商清单 (当前共 10 家)
系统官方定价中心权威收录以下 10 家主流大模型官方厂商的基准定价与阶梯机制：

1. **DeepSeek (深度求索)** (`code: "deepseek"`, `currency: "CNY"`)
   - 官网地址: `https://api-docs.deepseek.com/zh-cn/quick_start/pricing/`
2. **智谱 (GLM)** (`code: "zhipuai"`, `currency: "CNY"`)
   - 官网地址: `https://bigmodel.cn/pricing`
3. **Moonshot (Kimi)** (`code: "moonshotai"`, `currency: "CNY"`)
   - 官网地址: `https://www.kimi.com/membership/pricing?from=header_nav&tab=api`
4. **MiniMax** (`code: "minimax"`, `currency: "CNY"`)
   - 官网地址: `https://platform.minimaxi.com/docs/guides/pricing-paygo`
5. **阿里百炼 (Aliyun Model Studio)** (`code: "alibaba"`, `currency: "CNY"`)
   - 官网地址: `https://help.aliyun.com/zh/model-studio/model-pricing`
6. **小米 (Xiaomi MiMo)** (`code: "xiaomi"`, `currency: "CNY"`)
   - 官网地址: `https://mimo.mi.com/docs/zh-CN/price/pay-as-you-go`
7. **阶跃星辰 (StepFun)** (`code: "stepfun"`, `currency: "CNY"`)
   - 官网地址: `https://platform.stepfun.com/docs/zh/guides/pricing/details`
8. **OpenAI** (`code: "openai"`, `currency: "USD"`)
   - 官网地址: `https://platform.openai.com/docs/pricing`
9. **Anthropic (Claude)** (`code: "anthropic"`, `currency: "USD"`)
   - 官网地址: `https://platform.claude.com/docs/en/about-claude/pricing`
10. **Google (Gemini)** (`code: "google"`, `currency: "USD"`)
   - 官网地址: `https://ai.google.dev/gemini-api/docs/pricing?hl=zh-cn`

## 2. 重新获取官网价格的强制约束 (必须严格遵守)
当用户提出以下任何指令时：
- “重新获取大模型官网价格”
- “更新/刷新所有官方厂商定价”
- “爬取/同步官网大模型定价”
- “运行官方爬虫同步”

**AI 必须全自动且始终包含小米 (Xiaomi MiMo) 与阶跃星辰 (StepFun) 在内的全部 10 家官方厂商**：
- 严禁遗漏小米及阶跃星辰厂商；
- 必须同时抓取并保存完整的 HTML 网页快照文件（存储至 `data/official_snapshots/`）；
- 每次同步后需更新去阶梯第一档官方基准模型库，确保中转渠道智能映射时能够自动匹配阶跃星辰与小米等全部官方模型并换算官方折扣。

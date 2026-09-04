# 项目开发与协作规范 (Project Development Rules)

## 1. 语言规范
- 必须始终使用简体中文与用户交流、输出汇报及生成 GitHub 改进说明与 Commit 记录。

## 2. 每次修改代码后主动询问是否递增小版本号 (必须严格遵守)
- 每次完成功能开发、Bug 修复或代码修改并通过测试后，在交付前**必须主动询问用户**：
  > “本次代码修改已完成并通过测试，当前版本号为 **X.Y.Z**，是否需要将全局打包版本号递增至 **X.Y.Z+1**？”
- **若用户确认**：
  1. 更新 `package.json` 中的 `version` 字段；
  2. 同步更新 `package-lock.json` 中的版本号；
  3. 在 `CHANGELOG.md` 顶部生成新版本的语义化更新日志；
  4. 执行 `npm run version:gen` 更新前端打包元数据 (`src/renderer/src/generated/version_info.json`)；
- **若用户否定或未确认**：
  - 严格保持当前版本号不变；
- 目标：确保打包时版本号有序递增，永不重复使用同一个旧版本号。

## 3. 测试与验证规范
- 每次修改代码后必须进行完整测试（API测试、单元测试、Vue类型检查 `npm run typecheck`、前端构建 `npm run build`）。
- 测试通过后方可向用户汇报或提交代码。

## 4. 官方大模型定价抓取规范 (必须包含小米 MiMo、阶跃星辰 StepFun 等全部 10 家厂商)
- 当用户要求“重新获取大模型官网价格”或“同步官方定价”时，必须全自动抓取并解析全部 10 家官方厂商：
  - 境外厂商: OpenAI, Anthropic (Claude), Google (Gemini)；
  - 境内厂商: 阿里百炼, 智谱 (GLM), MiniMax, Moonshot (Kimi), DeepSeek, **小米 (MiMo)**, **阶跃星辰 (StepFun)**；
- 必须同时保存完整 HTML 快照文件至 `data/official_snapshots/` 留存对账证据链。

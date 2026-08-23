# UI 视觉验证与截图规则

当需要对网页 UI、组件排版、样式布局进行截图、视觉效果验证或页面测试时：

1. **统一使用 Headless 工具**：
   - 优先通过命令 `npm run screenshot` 或运行 `node scripts/screenshot_tester.mjs` 执行截图。
   - 截图会自动保存到 `design/screenshots/` 目录中。
2. **禁止依赖 IDE browser_subagent 进行 CDP 连接**：
   - 避免直接调用 `browser_subagent` 连接 9222 端口，以免受到新版 Chrome CDP 协议安全限制。
3. **查看截图结果**：
   - 使用 `view_file` 读取生成的 PNG 截图文件并在对话中呈现给用户确认。

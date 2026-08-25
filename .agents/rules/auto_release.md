# 自动编译打包工作流规则 (Auto Release Workflow Rule)

当用户说「打包最新版本」、「从最新版本打包」或类似指令时，AI 必须严格且全自动按以下标准流程执行，保持**本地与云端版本 100% 严格一致**：

1. **更新版本号与配置文件**：
   - 检查并更新 `package.json` 中的 `version`（例如从 `1.3.1` 升级至 `1.3.2`）；
   - 更新 `CHANGELOG.md` 顶部的版本更新说明与改动要点；
   - 确保 `pyinstaller.spec` 包含最新的内嵌种子数据与根证书配置。

2. **Git 提交与打标推送到 GitHub (触发 Actions 跨平台云端编译)**：
   - 执行 `git add -A` 并提交语义化 commit（如 `release: vX.Y.Z - 说明`）；
   - 创建或更新版本标签 `vX.Y.Z`（`git tag -a vX.Y.Z -m "Release vX.Y.Z"`）；
   - 推送代码与标签：`git push origin main && git push origin vX.Y.Z --force`，自动触发 GitHub Actions 编译并发布 GitHub Release 制品。

3. **本地同步执行完整编译打包流水线 (生成本地 DMG 与 ZIP 安装包)**：
   - 执行后端编译：`~/.pyenv/versions/WPD/bin/pyinstaller pyinstaller.spec --distpath resources/bin --clean`
   - 执行前端生产构建：`npm run build`
   - 执行 Electron 打包：`npx electron-builder --mac`
   - （或直接执行封装脚本：`npm run release:sync`）。

4. **汇报执行结果与一致性确认**：
   - 确认 `release/` 下生成了与云端 Tag 完全一致的 `.dmg` 和 `.zip` 本地安装包；
   - 输出本地安装包路径及 GitHub Actions / Release 监控链接。

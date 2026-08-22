# 自动编译打包工作流规则 (Auto Release Workflow Rule)

当用户说「打包最新版本」或类似指令时，AI 必须自动按以下标准流程执行，无需重复询问：

1. **版本与更新日志确认**：
   - 检查并确保 `package.json` 与 `CHANGELOG.md` 包含最新的版本号（如 `v1.1.0`）；
   - 确保 `pyinstaller.spec` 与 `.github/workflows/build-release.yml` 保持最新且依赖完整。
2. **Git 提交与打标 (Tagging)**：
   - 自动执行 `git add .` 并创建语义化 release commit；
   - 自动创建版本标签（如 `git tag -a vX.Y.Z -m "Release vX.Y.Z"`）。
3. **推送到 GitHub 触发 Actions 跨平台编译**：
   - 执行 `git push origin main`；
   - 执行 `git push origin <tag_name>` 推送标签，触发 GitHub Actions 在 macOS 与 Windows 上自动编译并发布 GitHub Release 制品（`.dmg`, `.zip`, `.exe`）。
4. **汇报进度与结果**：
   - 向用户清晰汇报已推送的 Tag 和触发状态，并附带 GitHub Actions 监控链接。

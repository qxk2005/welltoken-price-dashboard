#!/usr/bin/env bash
set -e

# ==============================================================================
# WellToken Price Dashboard - 本地 + 云端双轨自动化打包发布脚本
# ==============================================================================

VERSION=$(node -p "require('./package.json').version")
TAG="v$VERSION"
PYTHON_ENV="$HOME/.pyenv/versions/WPD/bin/python"
PYINSTALLER_BIN="$HOME/.pyenv/versions/WPD/bin/pyinstaller"

echo "========================================================"
echo "🚀 开始执行 WellToken Price Dashboard $TAG 本地+云端同步打包"
echo "========================================================"

# 1. 确保 Git 工作区代码与标签同步
echo "📦 [1/5] 同步配置文件、提交代码并打标签 $TAG..."
git add -A
if ! git diff-index --quiet HEAD --; then
    git commit -m "release: $TAG - 自动同步发布"
fi

# 检查 tag 是否已存在，若存在先删除并覆盖
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "⚠️ 标签 $TAG 已存在，执行更新..."
    git tag -d "$TAG"
    git push origin :refs/tags/"$TAG" 2>/dev/null || true
fi

git tag -a "$TAG" -m "Release $TAG: 本地与云端同步发布"
echo "☁️ [2/5] 推送至 GitHub 并触发 Actions 编译发布..."
git push origin main
git push origin "$TAG" --force

# 2. 本地执行全套打包流水线
echo "🐍 [3/5] 编译本地 Python 后端独立二进制 (内置离线种子包与根证书)..."
$PYINSTALLER_BIN pyinstaller.spec --distpath resources/bin --clean

echo "⚡ [4/5] 编译前端 Electron Vite 生产包..."
npm run build

echo "💿 [5/5] 打包生成本地 macOS ARM64 DMG 与 ZIP 安装包..."
npx electron-builder --mac

echo "========================================================"
echo "🎉 打包完成！本地与云端版本保持 100% 严格一致！"
echo "📂 本地 DMG: release/WellToken Price Dashboard-$VERSION-mac-arm64.dmg"
echo "🌐 云端 Actions: https://github.com/qxk2005/welltoken-price-dashboard/actions"
echo "🌐 云端 Release: https://github.com/qxk2005/welltoken-price-dashboard/releases/tag/$TAG"
echo "========================================================"

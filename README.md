# WellToken 价格监控看板 (WellToken Price Dashboard)

高颜值、高性能的跨平台桌面端代币与加密资产价格监控看板。

基于 **Electron + Vue 3 + TypeScript + ECharts + Tailwind CSS** 构建现代暗色系金融客户端，后端采用 **Python 3 (pyenv WPD) + FastAPI + SQLite (aiosqlite)** 提供异步高性能数据采集与实时推送，支持 **Windows** 与 **macOS** 双平台及 **GitHub Actions** 自动化编译发布。

---

## 🌟 核心特性

- **跨平台桌面端支持**：原生适配 macOS (Apple Silicon / Intel) 与 Windows 10/11。
- **现代化金融 UI**：暗色科技质感调色盘、玻璃拟态卡片与毫秒级行情变动闪烁动画。
- **专业 ECharts 图表**：支持 **K 线蜡烛图 (Candlestick)**、**MA5/MA20 移动均线**、**成交量柱**、**分时平滑走势 (Area)** 以及 **买卖盘深度分布 (OrderBook Depth)**。
- **高性能 Python 引擎**：内置 FastAPI 异步服务与 SQLite 历史数据持久化，支持 WebSocket 毫秒级广播推送。
- **内嵌二进制打包**：通过 PyInstaller 将 Python 后端编译为原生二进制并打包进 Electron 安装包，用户端开箱即用、无需手动配置 Python 环境。
- **CI/CD 自动化流水线**：集成 GitHub Actions 矩阵构建，支持代码推送与 Tag 自动生成 `.dmg`、`.exe` 发布包。

---

## 🛠️ 技术栈

| 层次 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **桌面容器** | Electron 30+ / Electron-Vite | 跨平台桌面壳与生命周期管理 |
| **前端框架** | Vue 3 (Composition API) + TypeScript | 响应式客户端交互 |
| **状态管理** | Pinia | 行情流、自选关注与图表状态统一管理 |
| **数据可视化** | Apache ECharts 5.5 | 专业金融行情图、K线与深度图 |
| **样式系统** | Tailwind CSS + PostCSS | 定制金融科技暗黑风主题 |
| **后端引擎** | Python 3.14 (pyenv WPD) + FastAPI + Uvicorn | 异步行情采集、REST API 与 WebSocket |
| **本地数据库** | SQLite 3 (SQLAlchemy 2.0 + aiosqlite) | 轻量、免配置的高性能本地持久化 |
| **编译与打包** | PyInstaller + Electron-Builder | 单文件二进制封装与跨平台安装包制作 |
| **自动化集成** | GitHub Actions | 跨平台矩阵自动化编译与 Release 发布 |

---

## 📁 目录结构

```
welltoken-price-dashboard/
├── .github/workflows/
│   └── build-release.yml          # GitHub Actions 跨平台自动编译流水线
├── .gitignore                         # 严格过滤 Python 缓存、Node 依赖、数据库与敏感凭据
├── .gitattributes                     # 跨平台换行符 (LF) 规范化
├── .env.example                       # 环境变量模板
├── .python-version                    # 指定 pyenv 虚拟环境 (WPD)
├── package.json                       # Node / Electron 依赖与构建脚本
├── electron.vite.config.ts            # electron-vite 构建配置
├── tailwind.config.js                 # Tailwind 主题与样式配置
├── requirements.txt                   # Python 运行时依赖
├── requirements-dev.txt               # Python 开发与 PyInstaller 打包依赖
├── pyinstaller.spec                   # Python 后端打包配置
├── backend/                           # Python 后端源码
│   ├── app/
│   │   ├── main.py                    # FastAPI 实例与路由装配
│   │   ├── config.py                  # 应用配置 (端口、DB路径等)
│   │   ├── database.py                # SQLite 连接与会话管理
│   │   ├── models/                    # SQLAlchemy 数据模型
│   │   ├── schemas/                   # Pydantic 校验与数据协议
│   │   ├── services/                  # 价格抓取、计算与 WebSocket 广播服务
│   │   └── api/v1/                    # RESTful API 路由与 WebSocket 接口
│   └── run_server.py                  # 后端启动包装入口
└── src/
    ├── main/                          # Electron 主进程 (Python 子进程托管)
    ├── preload/                       # 安全预加载脚本 (IPC 桥接)
    └── renderer/                      # Vue 3 渲染进程 (UI 与图表)
```

---

## 🚀 本地开发与启动

### 1. 准备工作
确保本地已安装 Node.js (>= 20) 以及 pyenv（已创建 `WPD` 虚拟环境）：

```bash
# 激活 pyenv 虚拟环境
pyenv activate WPD

# 安装 Python 依赖
pip install -r requirements-dev.txt

# 安装 Node.js 依赖
npm install
```

### 2. 启动开发模式

```bash
# 方式一：一键联动启动 (Electron 主进程会自动拉起 Python 后端)
npm run dev

# 方式二：独立调试 Python 后端
python backend/run_server.py --port 8765 --reload
```

---

## 📦 生产打包与构建

### 编译 Python 二进制
```bash
npm run build:backend
```

### 打包各平台安装包
```bash
# 打包 macOS 安装包 (.dmg / .zip)
npm run build:mac

# 打包 Windows 安装包 (.exe / portable)
npm run build:win

# 全平台打包
npm run build:all
```
产物将输出在 `release/` 目录下。

---

## 🛡️ 敏感文件与安全防护

- 项目通过 `.gitignore` 严格忽略了 `.env*` 敏感密钥文件、本地 `*.db` / `*.sqlite3` 数据文件、`__pycache__`、`node_modules/` 以及打包生成的临时二进制。
- 部署或分享时，请参考 `.env.example` 配置所需环境变量。

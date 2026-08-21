# WellToken 价格监控看板 (WellToken Price Dashboard)

高颜值、高性能的跨平台大模型 Token 聚合比价与渠道性能实测桌面端看板。

基于 **Electron + Vue 3 + TypeScript + ECharts + Tailwind CSS** 构建苹果官网级极简浅色主题客户端，后端采用 **Python 3 + FastAPI + SQLAlchemy 2.0 + SQLite (aiosqlite)** 提供异步高性能数据采集与实时检索，数据权威对齐 **models.dev** 官方标准，支持 **macOS** 与 **Windows** 双平台及 **GitHub Actions** 自动化编译发布。

---

## 🌟 核心特性

- **四级级联全网聚合比价**：支持「模型厂商 (Labs) $\rightarrow$ 模型系列 (Series) $\rightarrow$ 模型名称 (Models) $\rightarrow$ 渠道中转站 (Sites)」四级完全级联收敛与安全清洗，杜绝脏数据与无效筛选。
- **中英文双语模糊匹配搜索**：厂商筛选全面支持中文别名（如输入“深度探索”命中 DeepSeek，“通义千问”命中 Alibaba，“月之暗面”命中 Moonshot AI 等），候选列表全量按字母 A-Z 严格升序排列。
- **权威 30 大研发机构体系**：对齐 `models.dev/labs/` 官方标准，收录 30 家权威大模型研发母厂，配备官方矢量 SVG Logo 与扁平化模型规格大表格。
- **供应商全景画像与专属详情**：覆盖全网 193+ 家供应商渠道，支持「官方直连」、「中转站渠道」、「自添加网站」与「⭐ 收藏夹」四分类体系，点击可下钻查看渠道专属 Fact Grid 四维指标与全量模型定价。
- **价格-TPS 性价比散点图**：内置高性能 ECharts 散点图，直观洞察全网各大渠道在价格与吐字速率上的性价比黄金区位。
- **苹果官网级极简灰白设计**：浅色呼吸感排版、数据表格横向平滑滚动、60 FPS 流畅性能与毫秒级即时响应。

---

## 🛠️ 技术栈

| 层次 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **桌面容器** | Electron 28+ / Electron-Vite | 跨平台桌面壳与生命周期托管 |
| **前端框架** | Vue 3 (Composition API) + TypeScript | 响应式组件与极速交互 |
| **状态管理** | Pinia | 渠道收藏、汇率、多维筛选状态统一管理 |
| **数据可视化** | Apache ECharts 5.5 | 价格-TPS 性价比散点图 |
| **样式系统** | Tailwind CSS + Vanilla CSS | 苹果官网级高级灰白主题系统 |
| **后端引擎** | Python 3.10+ + FastAPI + Uvicorn | 异步高性能数据采集与级联 REST API |
| **本地数据库** | SQLite 3 (SQLAlchemy 2.0 + aiosqlite) | 异步高效本地持久化与索引检索 |
| **打包与分发** | PyInstaller + Electron-Builder | 单文件二进制封装与跨平台安装包 |

---

## 📁 目录结构

```
welltoken-price-dashboard/
├── CHANGELOG.md                       # 完整的版本升级与中文更新日志
├── .github/workflows/
│   └── build-release.yml              # GitHub Actions 跨平台自动编译流水线
├── backend/                           # Python 后端源码
│   ├── app/
│   │   ├── main.py                    # FastAPI 实例与路由装配
│   │   ├── config.py                  # 应用配置 (端口、DB路径等)
│   │   ├── database.py                # SQLite 连接与异步会话管理
│   │   ├── models/                    # SQLAlchemy 数据模型 (RelaySite, ModelMetadata, SiteModelPricing)
│   │   ├── schemas/                   # Pydantic 校验与数据协议
│   │   ├── services/                  # 比价服务、级联查询与 models.dev 数据同步
│   │   └── api/v1/                    # RESTful 路由 (comparison, channels, catalog, system)
│   └── run_server.py                  # 后端启动包装入口
└── src/
    ├── main/                          # Electron 主进程 (Python 子进程托管)
    ├── preload/                       # 安全预加载脚本 (IPC 桥接)
    └── renderer/                      # Vue 3 渲染进程 (UI 与图表)
        ├── src/components/            # Logo 组件、多选筛选器、通用弹窗
        ├── src/views/                 # 全网比价、供应商与渠道、厂商与系列、性能实测、设置
        └── src/stores/                # Pinia 全局状态管理
```

---

## 🚀 本地开发与启动

### 1. 准备工作
确保本地已安装 Node.js (>= 20) 以及 Python (>= 3.10)：

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装 Node.js 依赖
npm install
```

### 2. 启动开发模式

```bash
# 启动前端开发服务器与 Electron
npm run dev

# 独立启动 Python 后端服务 (默认端口 8765)
npm run dev:server
```

---

## 📦 生产打包与构建

```bash
# 编译 Python 二进制并构建 Electron 跨平台安装包
npm run build:all
```

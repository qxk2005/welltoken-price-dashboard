# 更新日志 (CHANGELOG)

所有关于 **WellToken Price Dashboard** 的重要更新与重大改进说明都将记录在此文件中。

## 🚀 [v1.5.5 Windows客户端安装常驻与快捷方式缺失彻底修复版] - 2026-09-15

### 🛠️ 关键缺陷修复与打包策略重构
- **根治 Windows 客户端打包后关闭找不到程序的问题 (`package.json`)**：
  - **根因彻底消除**：消除此前 `build.win.target` 同时启用 `["nsis", "portable"]` 且同名输出导致的构建冲突覆盖。此前绿色便携版同名覆盖了 NSIS 安装包，并在关闭后自动销毁临时目录，且不注册任何快捷方式；
  - **精炼打包目标**：移除 `portable` 便携版，仅保留标准的 Windows NSIS 安装程序，确保每次打包发布均是完备的安装包；
  - **规范发布产物命名**：Windows 端安装包明确重命名为 `${productName}-${version}-win-${arch}-Setup.${ext}`（如 `WellToken Price Dashboard-1.5.5-win-x64-Setup.exe`），消除命名歧义；
  - **向导式安装与快捷方式自动注册**：保持向导式安装体验 (`oneClick: false`)，允许用户自主选择安装路径 (`allowToChangeInstallationDirectory: true`)，安装后自动在 Windows 开始菜单与桌面生成快捷方式 (`createDesktopShortcut: true`, `createStartMenuShortcut: true`)；
  - **卸载数据清理保护**：配置 `"deleteAppDataOnUninstall": true`，在用户卸载时友好提示是否清理本地数据库与配置缓存。

### 🧪 自动化测试与工程化加固
- **多平台自动化测试套件加固 (`test_fresh_and_upgrade_install.py`)**：
  - 修复测试脚本中项目根目录相对路径索引逻辑，规范 `@pytest.mark.asyncio` 异步测试标记；
  - 完善 SQLite 数据库连接句柄在 Windows 环境下的释放清理逻辑，消除文件锁导致的句柄占用与临时目录清理异常；
  - 适配最新 30 款历史快照批次与模型种子数据的断言校验；
- **前端与主进程构建流水线校验**：
  - TypeScript 与 Vue 类型检查 (`npm run typecheck`) 0 报错；
  - 前端与主进程打包编译 (`npm run build`) 100% 成功；
  - Electron Builder 解包测试 (`electron-builder --win --dir`) 顺利通过。

---

## 🚀 [v1.5.4 Sub2API兜底倍率逻辑修正、MiniMax双模式拆分、快照阶梯跳转修正与Tab交互水合] - 2026-09-14

### 🌟 全新功能与交互体验升级
- **官方离线快照 WAI-ARIA 选项卡交互水合与模式自动激活 (`official_pricing.py`)**：
  - **静态快照交互水合**：解决 MiniMax 官网快照因保存为纯静态 HTML 缺少原站 JS 水合，导致「标准」与「优先*」Tab 无法点击切换的问题；通过在快照注入脚本中实现原生的 `role="tab"` 与 `role="tabpanel"` 事件委托，用户在离线快照中可自由点击切换各选项卡；
  - **目标模式智能预选激活**：当用户从官方比价或走势大盘中点击「优先 (Priority)」模型快照时，系统自动识别并为「优先*」Tab 注入激活样式，同时移除优先面板的 `hidden` 属性并隐藏标准面板，实现开箱即见对应定价表格。
- **模型历史走势大盘 ECharts 图表渲染修复 (`ModelHistoryDrawer.vue`)**：
  - 修复抽屉滑动展开时因 ECharts 容器尚未完成布局而导致图表未渲染绘制的问题；
  - 补齐对 `store.historyDrawer.loading` 状态与抽屉展开完成时机的双重监听，在抽屉滑出后自动触发 `renderChart()` 与自适应 `resize()`，保证走势大盘曲线即刻呈现。
- **渠道导入向导第 4 步折算价格响应式联动 (`AddChannelWizardModal.vue`)**：
  - 向导第 4 步清单表格实现与「全局默认倍率」的实时响应式双向联动；
  - 用户修改倍率数值时，列表中未设置独立倍率的模型折算单价与溢价/折扣率即时动态刷新，做到真正的所见即所得。

### 🛠️ 关键缺陷修复与数据校准
- **Sub2API 渠道导入向导全局兜底倍率生效逻辑修复 (`channels.py`)**：
  - **根因修复**：彻底修复 `/wizard-create` 接口在保存渠道模型时因 `if item.input_price_usd > 0:` 短路，直接跳过 `default_ratio` 运算并导致无独立倍率模型意外保留探测阶段错误单价的问题；
  - **精准折算**：未配置独立倍率的模型严格按 `payload.default_ratio`（如 0.65）计算折算单价与官方真实折扣（准确显示为 65 折 / 溢价率 -35%，杜绝误显示为 10.1x / 溢价 +1%）；
  - 已对数据库中已导入的历史异常渠道模型数据完成全量校准修复。
- **MiniMax 官方双模式定价分离与数据治理 (`official_scraper_service.py`)**：
  - **双模式解耦**：MiniMax 官网存在「标准 (Standard)」与「优先 (Priority 1.5倍费率，享高优先级并发调度)」两套并行定价；
  - 解析器自动识别并分流两套模式，独立收录为 `MiniMax-M3`（标准输入 2.10/4.20，输出 8.40/16.80）与 `MiniMax-M3 (优先)`（输入 3.15/6.30，输出 12.60/25.20），且备注注明「优先服务（1.5倍费率，提供更高优先级调度保障）」；
  - 同步校准全量数据库历史快照（#164、#141 等）与 `data/official_prices_seed.json` 种子库数据。
- **官方快照阶梯跳转定位算法增强 (`official_pricing.py`)**：
  - 修复官方比价点击「512k 以上」阶梯时由于数字单纯匹配导致误跳至「512k 以下」首行的问题；
  - 算法引入上下阶梯方向语义权重判定：模型名含 `>`、`+`、`以上` 时，大幅加权包含 `>`、`以上` 的高阶梯行（+250 分，惩罚 `≤`、`<` 行 200 分）；含 `≤`、`<`、`以下` 时优先匹配低阶梯行，实现 100% 精准高亮与居中视口滚动。

### 🧪 自动化测试与工程化保障
- 新增 `backend/tests/test_minimax_official_pricing.py`，完整覆盖 MiniMax 双模式解析与快照定位算法；
- 新增 `backend/tests/test_sub2api_default_ratio_wizard.py`，验证向导在设置 0.65 全局兜底倍率时模型单价与入库逻辑的严密性；
- 全套后端测试套件 100% 通过，Vue 类型检查 0 报错，前端生产包成功构建。

---

## 🚀 [v1.5.3 官方定价全量实时同步、快照批次去重收敛与测速可编辑Combobox升级版] - 2026-09-14

### 🌟 全新功能与交互体验升级
- **渠道测速模型 ID 现代 Combobox 升级 (`SpeedTesterView.vue`)**：
  - 将原有的纯 `<select>` 下拉框全面升级为**可编辑输入框 + 候选弹出面板（Combobox）**；
  - 文本框直接双向绑定测试模型 ID，用户可像普通文本框一样随意编辑、修改、删除或粘贴真实模型名称；
  - 右侧提供下拉展开按钮，点击或聚焦可弹出浮动候选面板，清晰展示当前渠道收录的全部可用模型（包含底层 ID 与友好别名）；
  - 支持按键入内容实时模糊匹配筛选候选，点击即可一键填入，用户可立刻在此基础上二次改写对齐上游真实名称；
  - 完善边缘交互支持：全局外部点击 (Click-Outside) 自动收起面板，无收录模型时优雅降级为纯输入框。

### 🛠️ 关键缺陷修复与数据治理
- **DeepSeek 官方模型名称无效角标 `(1)`、`(2)` 彻底清洗与政策注解收录**：
  - **根因分析**：DeepSeek 官网表格表头原生标注了角标数字 `deepseek-flash(1)` 与 `deepseek-v4-pro(2)`，引用底部的政策说明，此前解析器直接读取表头导致模型名和 `raw_model_id` 混入无效数字；
  - **清洗与规范化**：通过正则精准剥离表头角标数字，恢复纯净模型标识 `deepseek-flash` 与 `deepseek-v4-pro`；
  - **官方政策注解完整收录**：解析器自动从页面中提取 (1) 旧模型迁移说明与 (2) Pro 延续服务声明，完整追加至各模型的 `remarks` 备注字段，用户查看详情时可清晰查阅官方政策背景；
  - 历史快照与当前生效的全部 DeepSeek 数据库记录及种子文件已同步完成清洗对齐。
- **官方快照批次厂商与模型唯一性治理 (幂等化与去重防御)**：
  - **根因修复**：彻底解决此前单日内多次抓取或单测产生多份快照并在快照抽屉中显示“25 家厂商 · 1298 款模型”（含 3 个小米、多个阶跃星辰）的问题；
  - **数据库物理清理**：清理同日 18 份中间作废快照及失效模型，删除 14 个冗余 HTML 文件，各批次严格只留每厂商最新一份权威快照；
  - **抓取服务幂等化 (`official_scraper_service.py`)**：同一天对同一厂商重复抓取或重试成功时，自动清理替换同日旧快照与废弃模型，不再累积重复；
  - **接口层强去重 (`official_pricing.py`)**：`/snapshots/grouped` 建立按 `(snapshot_date, provider)` 强去重，批次总厂商数恒为 10 家，模型总数恒为 595 款；
  - **单测无污染隔离**：重构测试用例，彻底杜绝运行单测污染正式数据库。
- **Google (Gemini) 全球最新英文主站定价同步与 Gemini 3.8 Flash 全量收录**：
  - 将官方目标 URL 从带有中文滞后参数的 `?hl=zh-cn` 切换为官方权威英文主站 `https://ai.google.dev/gemini-api/docs/pricing`；
  - 成功全量收录包括 `Gemini 3.8 Flash`（标准、Batch、Flex 弹性、Priority 4 种规格）与 `Gemini 3.7 Flash` 在内的 72 款当前生效官方模型。
- **Moonshot (Kimi) 官网价格迁移与新格式行列式解析器**：
  - 将抓取目标迁移至开放平台最新文档地址 `https://platform.kimi.com/docs/pricing/chat`；
  - 重构解析器完美支持行列式表格与 DocTable 正则兜底，精准提取 4 款核心模型（`kimi-k3`、`kimi-k2.7`、`kimi-k2.6`）及 1M/256k 上下文窗口标注。
- **智谱 (GLM) 开放文档站迁移适配**：
  - 适配智谱全系列大模型详细定价表，自适应矩阵解析收录 68 款全系列模型。

---

## 🚀 [v1.5.2 官方快照与多版本定价离线种子固化与平滑升级加固版] - 2026-09-11

### 🛠️ 关键缺陷修复与跨平台冷启动加固
- **彻底根治打包后在全新电脑或旧电脑安装仅显示 10 份快照且为旧批次缺陷**：
  - **核心根本原因**：之前仅固化了单批次模型价格种子，完全缺失快照元数据种子；`database.py` 在初始化时硬编码只给 10 家厂商创建了 10 条对应 `sample_*.html` 的快照记录；同时旧版本覆盖安装缺乏差量版本检测与迁移升级机制，导致无论是 macOS (DMG) 还是 Windows (EXE) 全新安装或升级，均无法获取 `2026-09-11` 最新批次；
  - **全量快照元数据种子固化 (`data/official_snapshots_seed.json`)**：完整固化并导出 20 份基准快照元数据（覆盖 `2026-09-11` 最新批次与历史对比批次），并在 `.gitignore` 与 `pyinstaller.spec` 中纳入版本库与二进制打包资源；
  - **全量多版本模型定价种子同步 (`data/official_prices_seed.json`)**：固化全部 628 款多版本模型（598 款当前生效 + 30 款历史基准），包含精准的快照关联反查键；
  - **重构启动初始化与增量升级迁移引擎 (`backend/app/database.py`)**：
    - **全新安装冷启动**：自动从种子批量导入 20 份快照与 628 款模型，开箱即用呈现 `2026-09-11` 生效批次与历史对比批次；
    - **存量旧电脑覆盖升级**：启动时自动比对本地数据库与打包内置批次，若本地未包含 `2026-09-11` 最新批次，则自动增量补齐最新快照，将本地原有旧模型无缝归档为历史基准（`is_current = False`），将 `2026-09-11` 最新模型切换为当前生效（`is_current = True`），完整保留上期价格比对与时序走势大盘；
  - **跨平台一致性保证**：macOS 与 Windows 统一生效，彻底消除全新安装与存量升级的数据割裂；
  - **自动化测试套件加固**：新增 `backend/tests/test_fresh_and_upgrade_install.py`，100% 覆盖全新安装冷启动与存量旧版本覆盖升级双场景验证。

---

## 🚀 [v1.5.1 官方多版本快照管理、上期价格追溯对比、历史走势大盘与Gemini 3.8最新定价固化版] - 2026-09-11

### 🌟 全新功能与架构重构
- **以统一抓取日期+厂商为维度的手风琴快照版本管理 (`SnapshotManagerModal.vue`)**：
  - 将快照管理彻底重构为以“抓取日期批次（如 2026-09-11）”为顶层的手风琴折叠面板，默认展开最新生效日期；
  - 展开呈现该日期下全部 10 家厂商卡片矩阵，支持在抽屉内一键查阅原始 HTML 网页证据；
  - 新增快照收录模型清单预览模态框，支持查看该快照全部模型明细与价格；
  - 支持按厂商单独删除快照或一键删除整批次快照；若删除当前最新快照，全自动回滚至上一历史有效版本。
- **上期价格追溯对比与涨跌变动呈现**：
  - 主表格全视图模式新增「上期价格 / 涨跌」列，通过绿降红涨微标直观展现环比涨跌幅与价差；
  - 悬浮卡片清晰展现换算后的上一期基准单价与对账日期。
- **模型专属历史价格演变大盘 (`ModelHistoryDrawer.vue`)**：
  - 点击模型操作列「走势 📈」按钮呼出抽屉，内嵌多币种联动的 ECharts 时序折线走势图与历次版本明细比对表。
- **全量 10 家官方厂商最新模型与 Gemini 3.8 Flash 定价升级**：
  - 彻底重构 Google (Gemini) 解析器，支持全系 84 款最新规格（包括 `Gemini 3.8 Flash` 标准/Batch/Flex/Priority 4 种模式）；
  - 语义化提取阶段性特惠价格（输入 $0.75 / 输出 $3.75），并在备注中完整留存官方政策规则；
  - 抓取引擎引入全屏平滑滚动触发懒加载与 DOM 脱水，严禁静默 fallback 冒充新快照；
  - 同日多次抓取严格以最后一次为准，清理 114 份冗余碎片，当前最新生效模型数扩充至 **598 款**，并固化至 `data/official_prices_seed.json`，开箱即用。

---

## 🚀 [v1.5.0 小米等官方快照营销公告弹窗与全屏遮罩彻底净化加固版] - 2026-09-06

### 🛠️ 关键缺陷修复与核验体验优化
- **彻底根治小米（Xiaomi MiMo）等官方快照在内置抽屉对账时弹出营销公告窗口及全屏遮罩挡住定价内容缺陷**：
  - **根本原因定位**：小米官网页面在加载时会触发 Ant Design 营销弹窗及全屏灰色遮罩蒙层（`.ant-modal-root`, `.ant-modal-mask`, `Announcement_announcementModal__AHN0r`）；快照展示端点为了防止本地白屏，安全剔除了原页面的所有 `<script>`，导致该弹窗失去了原本的点击 `[X]` 关闭逻辑，变成静态挡在页面中央；全屏遮罩蒙层同时阻断了用户对后方价格表格的点击与滚动；
  - **快照渲染端点 DOM 级彻底剔除与 CSS 强力屏蔽**：在 [backend/app/api/v1/official_pricing.py](file:///d:/AI/WPD/backend/app/api/v1/official_pricing.py) 的 `view_snapshot_html` 中：
    - 遍历并彻底删除 `.ant-modal-root`, `.ant-modal-mask`, `.ant-modal-wrap`, `.ant-modal`, `.el-overlay`, `.modal-backdrop`, `[class*="announcementModal"]`, `[class*="NoticeModal"]` 以及无表格数据的纯提示框 `[role="dialog"]:not(:has(table))`；
    - 在注入的 `<style>` 标签中加入强力屏蔽样式（`display: none !important; opacity: 0 !important; pointer-events: none !important; z-index: -9999 !important;`），实现双重防护，杜绝任何残余遮罩阻断用户操作；
  - **抓取阶段防范与存盘清洗**：在 [backend/app/services/official_scraper_service.py](file:///d:/AI/WPD/backend/app/services/official_scraper_service.py) 中，Playwright 访问时自动探测并点击关闭常见弹窗（`.ant-modal-close`, `button[aria-label="Close"]`, `button:has-text("我知道了")` 等），并在快照文件存盘前再次清洗 DOM，确保新抓取的离线快照文件本身干干净净；
  - **存量快照全面净化**：对 `data/official_snapshots/` 以及本地 AppData 目录下的所有受遮挡快照（`sample_xiaomi.html`, `sample_glm.html`, `sample_openai.html` 等）进行了静态 DOM 净化；
  - **自动化测试套件构建**：新增 [backend/tests/test_snapshot_cleaning.py](file:///d:/AI/WPD/backend/tests/test_snapshot_cleaning.py)，覆盖 DOM 节点剔除验证、逻辑保留正常表格 dialog 测试、以及 FastAPI API 路由真实净化验证；
  - **测试全套通过**：小米官方定价与快照测试、阶跃星辰快照测试、Vue 类型检查 `npm run typecheck` 与前端构建 `npm run build` 全部顺利通过。

---

## 🚀 [v1.4.9 全量10家官方大模型HTML静态快照固化与离线对账彻底加固版] - 2026-09-06

### 🛠️ 关键缺陷修复与体验优化
- **彻底根治 Windows/macOS 安装后抽屉显示“当前模型暂无关联的离线快照文件”缺陷**：
  - **核心根因定位**：`.gitignore` 误将 `data/*` 全量忽略而未对 `data/official_snapshots/` 配置白名单，导致 Git 仓库中无任何预置 HTML 静态快照，打包生成的安装包内快照目录为空；同时 `backend/app/database.py` 中对已有模型补充 `snapshot_id` 时漏掉了 `session.commit()` 导致更新未存盘；
  - **全量 10 家官方厂商静态 HTML 快照固化入库**：全自动通过无头浏览器深度抓取并留存 10 家官方大厂（阿里百炼、智谱 GLM、MiniMax、月之暗面 Kimi、DeepSeek、小米 MiMo、阶跃星辰 StepFun、OpenAI、Anthropic Claude、Google Gemini）最新完整 DOM 结构，固化至 `data/official_snapshots/sample_*.html`，随版本库分发并内嵌至 PyInstaller 二进制；
  - **.gitignore 白名单解禁与离线种子库同步**：放行 `!data/official_snapshots/`、`!data/official_snapshots/*.html`、`!data/official_snapshots/.gitkeep`，同步刷新 [data/official_prices_seed.json](file:///d:/AI/WPD/data/official_prices_seed.json) 全量 595 款官方规格；
  - **数据库启动初始化与批量强制对齐**：在 [backend/app/database.py](file:///d:/AI/WPD/backend/app/database.py) 中引入预置快照缺损智能修补机制与 SQL 批量强制对齐，确保已有数据库模型 100% 绑定合法 `snapshot_id`，并增加 `session.commit()` 强持久化保证；
  - **快照查阅 PyInstaller 打包目录寻址保底**：在 [official_pricing.py](file:///d:/AI/WPD/backend/app/api/v1/official_pricing.py) `view_snapshot_html` 中加入 `sys._MEIPASS` 临时打包目录直接寻址保底，无论开发环境还是生产安装包均能秒级直出带 `<base href>` 样式的快照；
  - **前端抽屉智能回退增强**：在 [officialPricingStore.ts](file:///d:/AI/WPD/src/renderer/src/stores/officialPricingStore.ts) 的 `openSnapshotDrawer` 中增加厂商级快照回退查找，单条模型关联丢失时自动匹配厂商快照并执行高亮；
  - **全链路测试套件通过**：小米官方定价与快照测试、阶跃星辰快照测试、MiMo-V2.5 Pro / TTS 高亮测试全部 100% 通过。

---

## 🚀 [v1.4.8 Windows打包客户端启动闪退与bs4依赖缺失修复加固版] - 2026-09-06

### 🛠️ 缺陷修复与稳定性加固
- **彻底根治 Windows 打包客户端启动报错 `ModuleNotFoundError: No module named 'bs4'` 闪退缺陷**：
  - **核心根因定位**：应用冷启动在初始化 FastAPI 路由加载 `channels` 模块时，顶层直接同步引用了包含 `BeautifulSoup` 的爬虫模块，而项目根目录 `requirements.txt` 与 `pyinstaller.spec` 均未声明 `beautifulsoup4`，导致打包产物中缺失 bs4 模块，后端服务在启动首秒即被 `Exit code 1` 异常中断，触发 Electron 25 秒超时告警；
  - **依赖管理与打包规范闭环**：在 [requirements.txt](file:///d:/AI/WPD/requirements.txt) 中补齐 `beautifulsoup4>=4.12.3`，并在 [pyinstaller.spec](file:///d:/AI/WPD/pyinstaller.spec) 中加入 `*collect_submodules('bs4')` 与 `*collect_submodules('soupsieve')`，保证所有 HTML 解析器子模块被 100% 完整打包打包；
  - **爬虫服务防护性与安全导入强化**：全面改造 [siliconflow_scraper.py](file:///d:/AI/WPD/backend/app/services/siliconflow_scraper.py)、[bailian_scraper.py](file:///d:/AI/WPD/backend/app/services/bailian_scraper.py) 和 [official_scraper_service.py](file:///d:/AI/WPD/backend/app/services/official_scraper_service.py)，将 `BeautifulSoup` 调整为安全保护性导入并在解析入口做延迟安全检查，杜绝子爬虫依赖异常导致整个后端主服务无法启动；
  - **消除 Python 3.12+ 语法警告**：修复 [official_pricing.py](file:///d:/AI/WPD/backend/app/api/v1/official_pricing.py) 中对 `\s` 正则表达式的 SyntaxWarning 警告；
  - **二进制编译与冒烟验证通过**：本地环境完成全量单元测试与类型检查，重新编译生成 Windows 独立二进制 [backend-server.exe](file:///d:/AI/WPD/resources/bin/backend-server.exe) 并完成端口冒烟探针测试，启动即刻就绪，彻底消除闪退。

---

## 🚀 [v1.4.7 macOS系统只读根目录报错修复与快照数据路径彻底加固版] - 2026-09-04

### 🛠️ 关键缺陷修复与进程运行加固
- **彻底根治打包后 Python 后端启动崩溃 `Read-only file system: '/data'` 缺陷**：
  - 核心根因：在打包独立应用环境下，应用由系统 Finder 拉起时当前工作目录为根目录 `/`，原本使用 `os.path.join(os.getcwd(), "data", ...)` 会错误尝试在 macOS APFS 只读系统卷根目录创建 `/data` 目录，导致后端在模块导入期瞬间被 `OSError: [Errno 30]` 崩溃退出；
  - 重构快照目录路径：在 [`official_scraper_service.py`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/backend/app/services/official_scraper_service.py) 中，全面统一改用标准合法可写数据目录 `SNAPSHOT_DIR = str(DATA_DIR / "official_snapshots")`（在 macOS 上严格指向 `~/Library/Application Support/WellTokenDashboard/data/official_snapshots`）；
  - 快照查阅安全解析：在 [`official_pricing.py`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/backend/app/api/v1/official_pricing.py) 中，快照文件检索基于 `DATA_DIR` 进行安全解析，彻底杜绝相对根目录寻址；
  - 子进程工作目录（CWD）强制保底：在 [`pyManager.ts`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/src/main/pyManager.ts) 中，将子进程工作目录 `cwd` 强制指定为应用数据目录 `~/Library/Application Support/WellTokenDashboard`，彻底消除由于工作目录不当引发的只读异常。

---

## 🚀 [v1.4.6 macOS全新安装重连自愈与代理绕过加固版] - 2026-09-04

### 🛠️ 缺陷修复与稳定性加固
- **彻底解决全新 macOS 安装启动后右下角一直显示“重连中...”问题**：
  - **macOS Gatekeeper Quarantine 隔离属性自动脱敏**：在 [`pyManager.ts`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/src/main/pyManager.ts) 启动独立 Python 后端前，自动递归执行 `xattr -d -r com.apple.quarantine` 清除隔离属性并赋予 `chmod 755` 权限，彻底杜绝从 DMG 拖入安装后二进制被系统静默阻断；
  - **强制本地回环绕过系统代理（防劫持双保险）**：在 [`src/main/index.ts`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/src/main/index.ts) 中注入 Chromium 启动开关与 Session 策略 `proxyBypassRules: '<local>;127.0.0.1;localhost;::1'`，并为子进程环境变量注入 `NO_PROXY=127.0.0.1,localhost,::1`，彻底杜绝代理软件拦截本地高位端口 `127.0.0.1:8765` 导致前端与后端断连；
  - **全生命周期日志自动落盘**：后端启动、标准输出、标准错误与进程异常退出码统一实时追加写入日志文件（`~/Library/Application Support/WellTokenDashboard/logs/backend.log`），消灭盲区；
  - **状态栏一键诊断与日志直达**：在底部状态栏增加点击交互弹窗，未就绪时高亮展示具体错误原因，并提供【打开运行日志 (backend.log)】与【重启后端服务】快捷按钮；在【关于程序】视图同步增设服务诊断与日志专区。

---

## 🚀 [v1.4.5 智能映射模型选择器展示加固与智谱/Kimi模糊匹配升级版] - 2026-09-04

### 🛠️ 缺陷修复与体验优化
- **彻底修复模型智能映射选择框仅显示品牌 Badge 的缺陷**：
  - 重构 [`ModelSearchSelect.vue`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/src/renderer/src/components/ModelSearchSelect.vue) 顶部触发器按钮取值逻辑，将写死读取 `selectedModel.model_id` 升级为统一安全解析函数 `getModelId(selectedModel)` 与 `getModelName(selectedModel)`；
  - 彻底解决官方基准模型对象中键名为 `raw_model_id` / `clean_name` 导致 `selectedModel.model_id` 为空文本的根因；
  - 优化视觉样式为 **`[品牌彩色徽章] 具体标准模型名`**（如 `[MOONSHOT (KIMI)] K2.6通用模型`、`[MINIMAX] MiniMax-M3`），完美呈现品牌与模型的双重层级；
- **智谱 GLM-5 系列第一档基准模型全量收录修复**：
  - 优化 [`official_benchmark_service.py`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/backend/app/services/official_benchmark_service.py) 中 `is_tier_one` 阶梯识别算法，改用 `re.search` 支持包含 `"输入长度 [0, 32)"` 等中文前置说明的第一档区间；
  - 增强 `clean_benchmark_model_name` 清洗逻辑，安全过滤 `"输入长度"` 等前置引导词，纯化生成标准基准名 `GLM-5`；
  - 渠道模型 `GLM-5` 现已实现 **1.0 满分精确匹配** 官方 `GLM-5`，同步收录 `GLM-5.1`、`GLM-5-Turbo`、`GLM-5V-Turbo` 等第一档标准模型；
- **Moonshot Kimi 全系列模型智能模糊匹配深度纯化**：
  - 算法自动过滤 `通用模型`、`旗舰模型`、`大模型` 等中文修饰词，并针对 Kimi 增加 `k` 代号前缀自动折叠兼容机制；
  - `kimi-k2.6` / `kimi-2.6` 匹配 `K2.6通用模型` 置信度得分从原本的 0.35 跃升至 **0.95 分**，`kimi-k3` / `kimi-3` 亦 100% 自动匹配 `K3旗舰模型`；
- **新增综合智能模糊匹配自动化测试**：
  - 编写并集成 `test_model_fuzzy_matching.py`，完整覆盖 Kimi、GLM-5、MiniMax、StepFun 等主流厂商模型的清洗、匹配得分与基准联动，测试通过率 100%。

---

## 🚀 [v1.4.4 阶跃星辰 (StepFun) 官方大模型定价与 10 家厂商全量抓取版] - 2026-09-04

### 🌟 重大新增与核心改进
- **全面接入阶跃星辰 (StepFun) 官方大模型定价与快照存证**：
  - 新增阶跃星辰官方计费文档 (`https://platform.stepfun.com/docs/zh/guides/pricing/details`) 自动抓取与解析引擎；
  - 严格收录 Token 计费大模型：旗舰多模态推理 `step-3.7-flash`、推理 `step-3.5-flash` / `step-3.5-flash-2603`、视觉 `step-1o-turbo-vision` 以及 `stepaudio-2.5-realtime` / `stepaudio-2.5-chat` / `step-1o-audio` / `step-audio-2` / `step-audio-r1.5` 等全系列端到端语音大模型；
  - 自动留存网页离线 HTML 快照至本地证据链 (`data/official_snapshots/sample_stepfun.html`)。
- **固化官方定价 10 家大模型厂商全量抓取规则与开发规范**：
  - 在 `AGENTS.md` 与 `.agents/rules/official_pricing_rules.md` 中长效固化 10 家官方厂商名单（境内：阿里百炼、智谱GLM、MiniMax、Moonshot Kimi、DeepSeek、小米 MiMo、阶跃星辰 StepFun；境外：OpenAI、Anthropic Claude、Google Gemini）；
  - 将前端 `OfficialScrapeModal.vue` 一键全网抓取文案与调度同步升级为 10 家大模型厂商并发抓取。
- **官方第一档去阶梯基准库与模型智能归一化扩展**：
  - 将阶跃星辰模型正式纳入第一档去阶梯化官方基准模型池；
  - `official_benchmark_service.py` 与 `ModelSearchSelect.vue` 支持 `stepfun/`、`step-`、`stepaudio-` 前缀智能识别推断与模糊匹配；
  - 渠道模型映射弹窗下拉框动态提供【阶跃星辰 (StepFun) 官方标准】分组。
- **自动化测试套件全覆盖**：
  - 编写并集成 `test_stepfun_official_pricing.py`，全覆盖配置校验、DOM解析精度、数据库持久化、快照证据链与基准折扣换算，通过率 100%。

---

## 🚀 [v1.4.3 模型官网映射动态厂商支持与限免基准修复版] - 2026-09-04

### 🛠️ 缺陷修复与体验优化
- **彻底消除官网模型映射弹窗中的厂商硬编码**：
  - 重构 [`OfficialModelMappingModal.vue`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/src/renderer/src/components/OfficialModelMappingModal.vue)，移除原本硬编码的 8 家厂商列表；
  - 引入响应式计算属性 `benchmarkProviders`，自动从基准库中提取并动态生成包含【小米 (MiMo) 官方标准】在内的全部厂商分组；
  - 解决由于缺少 `xiaomi` 分组导致已匹配模型在下拉选择器中显示为空白、且无法手动选取小米模型的缺陷；
- **支持「限时免费」规格纳入第一档官方基准模型**：
  - 优化 [`official_benchmark_service.py`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/backend/app/services/official_benchmark_service.py) 中的 `is_tier_one` 规则，将包含“免费”的官方规格作为合法的有效基准；
  - 小米 `MiMo-V2.5 TTS`、`TTS VoiceClone`、`TTS VoiceDesign` 正式进入第一档基准模型池；
  - 避免 TTS 模型被错误模糊匹配为 ASR，渠道中的 TTS 模型现在 100% 精确关联官方 TTS（0折限时免费）；
- **组件厂商配置补全**：
  - 在 [`ModelSearchSelect.vue`](file:///Users/niuzhidao/Documents/Program/welltoken-price-dashboard/src/renderer/src/components/ModelSearchSelect.vue) 中补齐 Xiaomi 厂商选项、名称智能推断与品牌橙视觉徽章。

---

## 🚀 [v1.4.2 官方快照对账定位算法精准升级版] - 2026-09-04

### 🛠️ 缺陷修复与体验优化
- **彻底解决模型对账误命中系列标题的问题**：
  - 重构快照行匹配算法，严格区分 `<tbody>` 真实数据行与 `<thead>` / `<th>` 表头及无单价的“系列/规格”概括标题；
  - 引入多维度加权打分排序机制（包含 `<td>` 元素、真实货币价格、单元格精准相等优先），确保不论系列标题与模型名如何重叠（如 `MiMo-V2.5 系列` vs `mimo-v2.5` 数据行），均 100% 精准定位并高亮实际价格数据行及对应的各档价格单元格；
- **新增非表格正文段落回退定位能力**：
  - 当模型未以常规表格呈现时（如小米 `MiMo-V2.5 TTS` 全系列限时免费说明文本段落），自动向下兼容检索正文 `<p>` / `<li>` 并精准进行发光框与内嵌价格标签高亮；
- **补充端到端真实 DOM 渲染自动化测试**：
  - 编写 `test_xiaomi_v25_highlight.py`，完整覆盖 `MiMo-V2.5` 真实价格行防误伤测试、`MiMo-V2.5 Pro` 标准行测试及 `TTS` 段落回退定位测试，通过率 100%。

---

## 🚀 [v1.4.1 小米 (MiMo) 官方定价接入与快照对账定位加固版] - 2026-09-04

### 🌟 重大新增与核心改进
- **全面接入小米 (Xiaomi MiMo) 官方大模型定价与快照存证**：
  - 新增小米官方计费文档 (`https://mimo.mi.com/docs/zh-CN/price/pay-as-you-go`) 自动抓取与动态解析能力；
  - 完整收录最新 `MiMo-V2.5 Pro`、`MiMo-V2.5`、`MiMo-V2.5 ASR`、`MiMo-V2.5 TTS` 等全系列模型，覆盖标准输入、输出、Prompt Cache 命中输入及音频时长计费；
  - 自动留存网页离线 HTML 快照至本地证据链 (`data/official_snapshots/sample_xiaomi.html`)。
- **固化官方定价 9 大厂商全量抓取规则与长期记忆**：
  - 在全局开发规范与规则系统 (`.agents/rules/official_pricing_rules.md`) 中明确 9 大厂商名单（阿里百炼、DeepSeek、智谱 GLM、月之暗面 Kimi、MiniMax、OpenAI、Anthropic Claude、Google Gemini、小米 MiMo）；
  - 强制约束后续全网官方定价同步均自动覆盖包括小米在内的全部 9 家厂商，支持一键并发或独立按需更新。
- **官方快照对账纵横高亮定位引擎深度加固**：
  - **解决模型命名格式差异（连字符 vs 空格）无法命中定位的问题**：引入双向规范化算法，自动将 `MiMo-V2.5 Pro` 与快照 DOM 中的 `mimo-v2.5-pro` 互转互通；
  - **支持模型展示名与原始 ID 多候选目标传递**：前端 `openSnapshotDrawer` 自动并发传递展示名与 `raw_model_id`，全面提高极端命名模型在快照页的命中率；
  - **扩展价格单元格正则匹配**：支持 `¥`、`元`、`/小时`、`免费` 等多样化币种与计量单位，确保行与价格单元格双重发光高亮。
- **中转渠道探查与智能映射联动优化**：
  - 渠道探测第 2 步向向导智能映射过渡时，优先匹配官方定价基准库中的标准模型（包括新收录的小米模型），极大提升模型自动映射成功率与原价比对准确度。

---

## 🚀 [v1.4.0 官方模型定价中心与全量快照对账升级版] - 2026-09-04

### 🌟 重大新增与核心改进
- **官方模型定价中心全新上线**：新增各主流大模型厂商（阿里百炼、DeepSeek、OpenAI、Anthropic Claude、Google Gemini、智谱 GLM、月之暗面 Kimi、MiniMax 等）官方权威定价同步与展示；
- **Google (Gemini) 全量 HTML DOM 动态解析引擎**：彻底重构 Gemini 定价解析器，全面收录 79 款官方规格模型，涵盖最新 Gemini 3.6 Flash、Gemini 3.5 Flash/Lite、Gemini 3 Pro、Imagen 4、Veo 3.1 等全系列，及 Standard、Batch 批处理、Flex 弹性、Priority 优先等完整计费模式；
- **官方快照对账纵横双向高亮定位系统**：
  - 支持直接在快照抽屉中查看官方原始网页 HTML 离线证据链；
  - 引入金色呼吸发光框与智能平滑居中算法，瞬间秒级定位到目标模型与具体的输入/输出单价数值单元格；
  - 支持 OpenAI / Gemini 等选项卡 (Content Switcher / devsite-selector) 模式自动切换与对应面板激活；
  - 引入严格单词边界匹配（Word Boundary），彻底杜绝 `Fable 5` 误伤 `Fable 5.1` 或 `Claude` 厂商名前缀误伤问题；
  - 支持独立 Batch 表格识别与路由，以及 `[0, 200k)`、`[200k+)` 上下文双阶梯精准定位；
- **官方定价数据精细化治理**：
  - 国内厂商（如阿里百炼）专注国内北京地域定价，自动过滤海外及特定代理数据；
  - 智能拆分多阶梯输入/输出单价与上下文阶梯名；
  - 计费模式统一规范化为 Standard、Batch 批处理、Flex 弹性、Priority 优先、限时半价等清晰分类；
- **新增「关于程序」栏目与编译打包版本日志自动化注入**：
  - 在左侧工作台导航「系统设置」正下方新增「关于程序」独立视图；
  - 采用 Apple 风格信息卡片与版本变更日志时间轴，全界面动态同步打包版本号，支持一键复制系统诊断信息。

---

## 🚀 [v1.3.5 CI/CD 跨平台构建与种子包打包加固版] - 2026-08-25

### 🛠️ 缺陷修复与体验优化
- **修复 GitHub Actions 跨平台 PyInstaller 构建失败**：解决 `.gitignore` 误忽略 `data/cache` 目录导致 CI 云端 Runner 在干净环境中无法找到预置种子文件而中断 PyInstaller 编译的问题；
- **优化 pyinstaller.spec 资源收集与容错机制**：在打包规范中引入目录动态探测与自动创建，并深度内嵌 `certifi` 根证书链与 `cryptography` 加密库，确保 Windows/macOS 双端均能稳定编译为独立便携二进制；
- **修复 GitHub Actions Artifacts 上传通配符兼容性**：按操作系统平台精准匹配 `.dmg`、`.exe`、`.zip` 及 `.blockmap` 安装制品，杜绝因跨平台文件名不存在触发的上传报错。

---

## 🚀 [v1.3.4 数据库外键级联容错加固版] - 2026-08-25

### 🛠️ 缺陷修复与体验优化
- **彻底消除 SQLite 外键约束导入报错**：在合并 iCloud 数据包中的渠道映射 (`channel_model_mappings`) 与自定义别名 (`model_aliases`) 时，引入自动补全标准模型骨架机制。即便拉取的配置中包含未收录在 models.dev 官方库中的非标模型 ID（如 `claude-3-opus-custom-test`），也能自动创建元数据骨架并安全合并，100% 杜绝 `(sqlite3.IntegrityError) FOREIGN KEY constraint failed` 异常；
- **优化智能双向合并健壮性**：提升对多端设备不同时间段自定义渠道、模型映射与定价倍率的容错合并能力。

---

## 🚀 [v1.3.3 多层级 iCloud 跨设备同步加固版] - 2026-08-25

### 🛠️ 缺陷修复与体验优化
- **全方位多层级 iCloud 同步自适应发现**：在 `backend/app/services/icloud_sync_service.py` 中引入 5 级自适应检索算法（主路径、`.icloud` 占位符、iCloud 文稿同步目录、macOS Spotlight 元数据引擎全局定位以及递归遍历）；
- **修复拉取时缺少 `import asyncio` 的运行时异常**：彻底修复跨设备 JXA 轮询等待时的异步调度异常；
- **主动触发双端 iCloud 同步唤醒**：在推送到 iCloud 和拉取时，主动调用 macOS 原生 JXA (`NSFileManager.startDownloadingUbiquitousItem`) 唤醒苹果 `bird` 云端守护进程，极大缩短跨设备数据传输的等待延迟；
- **双轨自动化打包与发布 SOP 固化**：提供一键执行本地与云端双轨打包脚本，确保本地 DMG 与 GitHub Actions Release 版本始终 100% 绝对一致。

---

## 🚀 [v1.3.2 深度加固版本] - 2026-08-25

### 🛠️ 缺陷修复与体验优化
- **修复打包环境持久化数据存储**：重构 `backend/app/config.py`，在生产独立运行环境自动定位到系统标准的 `~/Library/Application Support/WellTokenDashboard/data` 目录，彻底消除只读临时目录导致的数据与缓存丢失；
- **解决打包后 Python HTTPS 请求 SSL 证书链验证问题**：在服务端启动时显式注入 `certifi.where()` 根证书链，确保 `models.dev` 及各大渠道在线抓取与同步正常；
- **内嵌离线预置全量种子包 (Seed Cache)**：将 350+ 标准模型与 190+ 供应商完整缓存预置打包进应用分发包，即便在完全无网或严格防火墙环境下也能瞬间秒开全量模型；
- **优化 iCloud 首次使用云端拉取指引文案**：当检测到云端尚无备份文件时给出清晰的引导说明。

---

## 🚀 [v1.3.1 补丁版本] - 2026-08-25

### 🛠️ 缺陷修复与体验优化
- **修复打包应用 Network Error 离线报错**：解决 PyInstaller 打包时由于动态字符串导入导致 `fastapi.middleware.cors` 及子模块缺失的崩溃问题，在 `pyinstaller.spec` 中全量自动收集 `backend.app`、`fastapi`、`starlette`、`uvicorn`、`sqlalchemy` 等所有依赖，并重构服务端为直接实例加载；
- **修复 macOS 窗口无法拖动与红绿灯遮挡问题**：为顶部导航栏注入 `-webkit-app-region: drag` 拖拽支持，同时对所有按钮与输入控件应用 `no-drag` 保持交互灵敏，并为 macOS 原生红绿灯按钮配置 `trafficLightPosition` 避让间距与 `pl-20` 内边距；
- **优化初次启动数据库冷启动健壮性**：在插入内置别名前预置标准模型元数据骨架，防止 SQLite 在空库初始化时触发外键检查失败。

---

## 🚀 [v1.3.0 主版本发布] - 2026-08-25

### 🌟 重大新增与核心改进

#### 1. ☁️ macOS iCloud 原生云端双向同步（自定义渠道商与用户资产配置）
- **iCloud Drive 原生对接**：专用目录 `~/Library/Mobile Documents/com~apple~CloudDocs/WellTokenDashboard/`，实现多台 Mac 设备间自建渠道、模型映射与用户配置无缝漫游；
- **智能双向合并与防冲突算法**：自动以渠道名与端点对齐，两端独有渠道并集保留，同名冲突以更新时间戳为准（Last-Write-Wins），自动重算折算定价与折扣率；
- **滚动版本快照与一键回退**：每次云端推送与合并前自动生成本地快照，在 `backups/` 目录下保留最近 20 份历史快照，支持在 UI 中一键精准版本回滚；
- **端到端加密与安全隐私保护**：采用 PBKDF2-HMAC-SHA256 与 CTR/HMAC 认证流加密，提供可选主密码加密；支持「排除/包含 API Key」独立安全策略；
- **系统设置与渠道管理深度集成**：在【系统设置】中上线完整的苹果风 iCloud 控制面板（状态指标卡、模块勾选、密码管理、Finder 快速跳转、备份快照还原）；在【渠道管理】顶部增加 iCloud 状态胶囊与快捷同步。

---

## 🚀 [v1.2.0 主版本发布] - 2026-08-23

### 🌟 重大新增与核心改进

#### 1. 📊 全网比价散点图模型标识与模型系列双维度切换
- **双维度自由切换**：支持在 **🏷️ 按模型标识 (By Model ID)** 与 **📦 按模型系列 (By Model Series)** 之间一键切换；
- **跨渠道多别名聚合比价**：在「📦 按模型系列」模式下，自动收敛各渠道中转站不规范命名（如 `Qwen/Qwen3.8-Max`、`qwen3.8-max`、`alibaba/qwen3.8-max`），将同一系列下所有渠道的报价统一呈现于同一张散点图内进行性价比全景比对；
- **增强型悬浮 Tooltip 与点选定位**：悬浮数据点时完整展示渠道名、所属系列、实际模型标识、输入单价与实测 TPS；点击散点图任意点，表格自动精准平滑滚动并高亮该条记录。

#### 2. 🗂️ 供应商详情三类视图切换展现
- **📄 平铺清单模式**：经典轻量表格，支持快速列头排序、状态徽标与多字段检索；
- **🎯 按价格分组聚合模式**：折叠卡片化展示各个价格分组（如 default、VIP、折扣组等）的模型款数、平均实测 TPS 与价格区间（最低 ~ 最高），展开即查组内明细；
- **🤖 按模型对比跨组比价模式**：跨分组对比同款模型在不同价格分组中的定价差异，自动高亮 **🏆 最低价 (最优)**，并精准计算其余分组的溢价百分比（如高出 +28.6%）。

#### 3. ⏱️ 供应商详情五维 Fact Grid 指标看板与数据最后更新时间
- **新增第五维核心指标方块**：在供应商详情头部实时显示 **「数据最后更新时间」**；
- **智能人性化时间感知**：突出加粗显示相对时间（如 `8小时前` / `1个月前`），并标注具体月日时分；
- **官方与自定义渠道标记**：清晰区分官方 models.dev 数据源（`m` 标）与自定义自建中转同步（`c` 标）。

#### 4. 🎯 供应商详情价格分组过滤 Popover 重构
- **紧凑多选浮层**：将分组过滤升级为 Apple 风格磨砂下拉弹层，支持快速搜索、全选/清空、模型款数统计与批量多选。

#### 5. 📅 全网比价更新时间范围多维筛选
- **日期范围预设**：新增更新时间筛选器，支持近 1 周、近 1 月、近 3 月、近半年与自定义起止日期筛选。

---

## 🚀 [v1.1.0 主版本发布] - 2026-08-22

### 🌟 重大新增与核心改进

#### 1. 🪟 浮动悬挂抽屉与上下文关联比价（无跳转极速查验）
- **右侧极简磨砂抽屉**：点击任意模型厂商或渠道名称，即时从右侧弹出信息抽屉（`VendorDetailDrawer.vue` / `ChannelDetailDrawer.vue`），无需跳转路由或刷新页面；
- **智能筛选上下文关联**：抽屉自动携带全局比价筛选上下文，支持一键切换「查看符合当前筛选的模型」与「查看该厂商/渠道全量模型」；
- **抽屉内一键反向快捷比价**：在抽屉中点击任一模型的「比价」按钮，即可快速聚焦该模型的全网渠道报价。

#### 2. 🎨 全系统统一单色矢量图标体系 & 官方品牌 Logo 强化
- **全新统一矢量设计系统**：构建了统一的 `SystemIcon.vue` 单色高保真矢量图标组件（遵循 Apple SF Symbols / Lucide 规范），彻底淘汰杂乱混杂的彩色 Emoji；
- **官方品牌矢量 Logo 保留**：完整保留 30+ 原创研发大厂与 190+ 全球中转渠道的官方品牌高保真 Logo（OpenAI, Anthropic, DeepSeek, Google, Alibaba, Meta 等）。

#### 3. 📊 全网聚合比价大表格呼吸感与行间距优化
- **表格架构彻底对齐**：全网比价表格与供应商渠道表 100% 对齐原生 `<table>` 架构，内边距统一优化为 `py-3 px-3`，通栏边框延伸，视觉呼吸感大幅提升；
- **工作台导航模块重命名**：主导航标题精简规范为：`全网比价`、`供应商表`、`模型厂商`、`性能测试`、`系统设置`。

#### 4. 💱 汇率实时折算引擎与动态数据同步升级
- **全球外汇汇率实时同步**：支持从开放外汇 API 动态联网抓取最新 USD/CNY 汇率并持久化存储，彻底消除写死汇率；
- **同步进度与计数动态化**：全面替换写死的固定统计数字，依据数据库实时抓取数量动态展示。

#### 5. 🤖 GitHub Actions 跨平台 CI/CD 自动化构建发版
- **macOS + Windows 全自动化打包**：支持通过 GitHub Actions 自动编译 Python 后端（PyInstaller）与 Electron 前端，自动生成 macOS（`.dmg`, `.zip`）与 Windows（NSIS `.exe`, 便携版 `.exe`）全量安装包；
- **双触发机制**：支持推送 `v*` Git Tag 自动触发，以及在 Actions 面板通过 `workflow_dispatch` 手动一键发版。

---

## 🚀 [v1.0.0 主版本发布] - 2026-08-21

### 🌟 重大新增与核心改进

#### 1. 📊 全网聚合比价多维级联联动与中英文模糊多选
- **四级级联收敛**：实现了 **模型厂商 (Labs) $\rightarrow$ 模型系列 (Series) $\rightarrow$ 模型名称 (Models) $\rightarrow$ 渠道中转站 (Sites)** 的四级严格联动收敛与安全清洗，彻底消除无效脏过滤；
- **中英文别名模糊匹配**：厂商下拉框支持全面的中文别名模糊匹配（例如输入“深度探索”/“深度求索”即时匹配 DeepSeek，输入“通义千问”/“阿里”即时匹配 Alibaba，输入“月之暗面”/“Kimi”即时匹配 Moonshot AI 等）；
- **全量候选项字母 A-Z 严格排序**：四大下拉框候选项全量按 A-Z 字母升序排列，并带有实时匹配报价条数 Badge 徽标；
- **层级筛选状态保留**：在由浅入深逐级选择模型名称时，稳稳保留前面已勾选的厂商与系列，支持精准的多维组合过滤；
- **散点图与数据表格实时联动**：底部的全网价格-TPS 性价比散点图与数据表格无缝联动，直观呈现各渠道的性价比分布。

#### 2. 🤖 厂商与模型系列权威体系重构
- **标准对齐 models.dev/labs/ 官方体系**：将全网大模型精准收敛至 30 家权威大模型研发机构/母厂（如 Alibaba、OpenAI、DeepSeek、Google、Anthropic、Zhipu AI、Moonshot AI、Meta、Mistral、Nvidia、ByteDance、xAI、MiniMax、Xiaomi 等）；
- **层级强归属算法升级**：彻底解决云平台托管前缀（如 `alibaba/deepseek-v4`、`alibaba/glm-5`）导致的厂商与系列混淆问题，清洗全库 3,580 款模型，确保 Alibaba 下仅有纯粹的通义千问系列、DeepSeek 下仅有 DeepSeek-V3/V4/R1 系列；
- **厂商专属详情空间**：点击任意厂商卡片下钻进入专属空间，以扁平规格大表格展示旗下全部模型的上下文窗口、最大输出、输入输出基准价格及支持渠道总数。

#### 3. 🌐 供应商与渠道架构精简与详情下钻
- **公共列表排版精简**：移除了冗长的 API Base URL 与 Env Keys 等占位宽字段，将数据来源独立为「数据来源」列（`● MODELS.DEV` 官方库 / `○ 用户自建中转`），呈现极其宽裕舒缓的视觉呼吸感；
- **供应商专属模型定价看板**：点击任意供应商可下钻进入其详情空间，展示四维 Fact Grid 指标看板及旗下可用模型的实时折算定价大表格；
- **四分类体系与一键收藏**：支持「官方直连」、「中转站渠道」、「自添加网站」以及「⭐ 收藏夹」快速切换与一键置顶查看。

#### 4. 🎨 苹果官网级高级灰白设计系统
- **统一视觉语言**：全面采用苹果官网级浅色高级灰白主题（`#F5F5F7` 背景、`#FFFFFF` 浮雕卡片、`#0071E3` 极光蓝交互点缀、`#34C759` 价格高亮）；
- **流畅数据体验**：数据表格支持横向平滑滚动与动态分页，单页渲染 50 条报价，保持 60 FPS 极致丝滑性能。

---

## 🛠️ 技术栈与依赖架构
- **桌面端内核**：Electron 28 + Vite 5 + TypeScript
- **前端框架**：Vue 3 Composition API + Pinia 状态管理 + TailwindCSS + ECharts 5.5
- **后端引擎**：Python 3.10+ + FastAPI 高并发异步框架 + SQLAlchemy ORM + SQLite
- **数据源对齐**：models.dev 官方 catalog.json / models.json / api.json 规范标准

<template>
  <div class="h-full flex flex-col space-y-3 overflow-y-auto pr-1 select-none">
    <!-- ==================== 卡片 0：macOS iCloud 云端同步 (核心专区) ==================== -->
    <div class="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-4">
      <!-- 头部：标题与状态指示 -->
      <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
        <div class="flex items-center space-x-2.5">
          <div class="w-7 h-7 rounded-xl bg-[#0071E3]/10 flex items-center justify-center text-[#0071E3]">
            <SystemIcon name="cloud" custom-class="w-4 h-4" />
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <span class="font-bold text-sm text-[#1D1D1F]">macOS iCloud 云端同步 (自定义渠道商与用户配置)</span>
              <!-- 状态胶囊 -->
              <span
                v-if="store.icloudStatus?.is_macos && store.icloudStatus?.icloud_available"
                class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6] flex items-center space-x-1"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-[#34C759] animate-pulse"></span>
                <span>iCloud Drive 已连接</span>
              </span>
              <span
                v-else-if="store.icloudStatus?.is_macos"
                class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFF4E5] text-[#B06000] border border-[#FFE2B8]"
              >
                未检测到 iCloud Drive 目录 (已启用本地安全存储)
              </span>
              <span
                v-else
                class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#F2F2F7] text-[#6E6E73] border border-[#E5E5EA]"
              >
                非 macOS 系统 (支持本地 JSON 导入导出)
              </span>
            </div>
            <p class="text-xs text-[#86868B] mt-0.5">
              自建/中转渠道商、API Key、模型映射、自定义别名规则与收藏夹多设备无缝漫游与版本快照恢复
            </p>
          </div>
        </div>

        <!-- 头部右侧动作 -->
        <div class="flex items-center space-x-2">
          <button
            @click="store.openICloudFolder"
            class="text-xs px-3 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1.5 cursor-pointer"
            title="在访达 Finder 中打开同步与备份目录"
          >
            <SystemIcon name="folder" custom-class="w-3.5 h-3.5 text-[#0071E3]" />
            <span>在访达中定位</span>
          </button>
          <button
            @click="openBackupModal"
            class="text-xs px-3 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1.5 cursor-pointer"
          >
            <SystemIcon name="history" custom-class="w-3.5 h-3.5 text-[#AF52DE]" />
            <span>备份快照 ({{ store.icloudStatus?.backups_count || 0 }})</span>
          </button>
        </div>
      </div>

      <!-- 云端同步状态 4 列指标卡 -->
      <div class="grid grid-cols-4 gap-3 text-xs">
        <div class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
          <span class="text-[#86868B] text-[10.5px] block">云端同步主文件</span>
          <div class="flex items-center space-x-1.5 font-bold font-mono text-[#1D1D1F]">
            <span
              class="w-2 h-2 rounded-full"
              :class="store.icloudStatus?.sync_file_exists ? 'bg-[#34C759]' : 'bg-[#86868B]'"
            ></span>
            <span>{{ store.icloudStatus?.sync_file_exists ? 'welltoken_sync.json' : '尚未推送' }}</span>
          </div>
          <div class="text-[10px] text-[#86868B] font-mono">
            {{ store.icloudStatus?.sync_file_size_bytes ? `${(store.icloudStatus.sync_file_size_bytes / 1024).toFixed(1)} KB` : '0 KB' }}
            {{ store.icloudStatus?.is_encrypted ? ' • 🔒 AES加密' : ' • 明文存储' }}
          </div>
        </div>

        <div class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
          <span class="text-[#86868B] text-[10.5px] block">上次云端同步时间</span>
          <div class="font-bold text-[#1D1D1F] text-[11px] truncate" :title="store.icloudStatus?.sync_file_last_modified || '暂无'">
            {{ store.icloudStatus?.sync_file_last_modified || '未执行过推送' }}
          </div>
          <div class="text-[10px] text-[#86868B] truncate font-mono">
            设备: {{ store.icloudStatus?.device_id || '本地Mac' }}
          </div>
        </div>

        <div class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
          <span class="text-[#86868B] text-[10.5px] block">云端自定义资产</span>
          <div class="font-bold font-mono text-[#0071E3] text-sm flex items-center space-x-2">
            <span>{{ store.icloudStatus?.cloud_channels_count || 0 }} 家渠道</span>
            <span class="text-xs font-normal text-[#86868B]">({{ store.icloudStatus?.cloud_mappings_count || 0 }} 映射)</span>
          </div>
          <div class="text-[10px] text-[#86868B] font-mono">
            自定义别名规则: {{ store.icloudStatus?.cloud_aliases_count || 0 }} 条
          </div>
        </div>

        <div class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
          <span class="text-[#86868B] text-[10.5px] block">滚动历史快照</span>
          <div class="font-bold font-mono text-[#AF52DE] text-sm">
            {{ store.icloudStatus?.backups_count || 0 }} 份快照
          </div>
          <div class="text-[10px] text-[#86868B] truncate">
            最新备份: {{ store.icloudStatus?.latest_backup?.created_at?.slice(5, 16) || '暂无' }}
          </div>
        </div>
      </div>

      <!-- 模块勾选与安全策略配置区 (左右两栏) -->
      <div class="grid grid-cols-12 gap-3 text-xs">
        <!-- 模块勾选 -->
        <div class="col-span-6 p-3.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-2.5">
          <div class="font-bold text-[#1D1D1F] text-xs flex items-center justify-between">
            <span>1. 选择同步数据模块 (Sync Modules)</span>
            <span class="text-[10px] text-[#86868B]">按需定制同步内容</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <label class="flex items-center space-x-2 cursor-pointer text-[#1D1D1F]">
              <input
                type="checkbox"
                v-model="icloudCfg.modules.custom_channels"
                @change="saveICloudSettings"
                class="rounded border-[#C7C7CC] text-[#0071E3] focus:ring-[#0071E3]"
              />
              <span>自建/中转渠道商与定价</span>
            </label>
            <label class="flex items-center space-x-2 cursor-pointer text-[#1D1D1F]">
              <input
                type="checkbox"
                v-model="icloudCfg.modules.custom_aliases"
                @change="saveICloudSettings"
                class="rounded border-[#C7C7CC] text-[#0071E3] focus:ring-[#0071E3]"
              />
              <span>全局自定义模型别名</span>
            </label>
            <label class="flex items-center space-x-2 cursor-pointer text-[#1D1D1F]">
              <input
                type="checkbox"
                v-model="icloudCfg.modules.favorites"
                @change="saveICloudSettings"
                class="rounded border-[#C7C7CC] text-[#0071E3] focus:ring-[#0071E3]"
              />
              <span>渠道收藏夹状态</span>
            </label>
            <label class="flex items-center space-x-2 cursor-pointer text-[#1D1D1F]">
              <input
                type="checkbox"
                v-model="icloudCfg.modules.preferences"
                @change="saveICloudSettings"
                class="rounded border-[#C7C7CC] text-[#0071E3] focus:ring-[#0071E3]"
              />
              <span>汇率基准与偏好设置</span>
            </label>
            <label class="flex items-center space-x-2 cursor-pointer text-[#1D1D1F] col-span-2">
              <input
                type="checkbox"
                v-model="icloudCfg.modules.speed_tests"
                @change="saveICloudSettings"
                class="rounded border-[#C7C7CC] text-[#0071E3] focus:ring-[#0071E3]"
              />
              <span>测速历史记录 (最近 100 条性能实测数据)</span>
            </label>
          </div>
        </div>

        <!-- 安全与自动化配置 -->
        <div class="col-span-6 p-3.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-2.5">
          <div class="font-bold text-[#1D1D1F] text-xs flex items-center justify-between">
            <span>2. 安全隐私与自动化策略 (Security & Automation)</span>
            <span class="text-[10px] text-[#34C759]">端到端可选加密</span>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="flex items-center space-x-2 cursor-pointer text-[#1D1D1F]">
                <input
                  type="checkbox"
                  v-model="icloudCfg.includeApiKeys"
                  @change="saveICloudSettings"
                  class="rounded border-[#C7C7CC] text-[#0071E3] focus:ring-[#0071E3]"
                />
                <span class="font-medium">同步包含 API Key</span>
              </label>
              <span class="text-[10.5px] text-[#86868B]">跨设备免重新填 Key</span>
            </div>

            <div class="flex items-center justify-between">
              <label class="flex items-center space-x-2 cursor-pointer text-[#1D1D1F]">
                <input
                  type="checkbox"
                  v-model="icloudCfg.autoSync"
                  @change="saveICloudSettings"
                  class="rounded border-[#C7C7CC] text-[#0071E3] focus:ring-[#0071E3]"
                />
                <span class="font-medium">渠道修改时自动推送到云端</span>
              </label>
              <span class="text-[10.5px] text-[#86868B]">静默即时备份</span>
            </div>

            <div class="pt-1 border-t border-[#E5E5EA]/70">
              <div class="flex items-center justify-between">
                <label class="flex items-center space-x-2 cursor-pointer text-[#1D1D1F]">
                  <input
                    type="checkbox"
                    v-model="icloudCfg.usePassword"
                    @change="saveICloudSettings"
                    class="rounded border-[#C7C7CC] text-[#0071E3] focus:ring-[#0071E3]"
                  />
                  <span class="font-medium flex items-center space-x-1">
                    <SystemIcon name="lock" custom-class="w-3.5 h-3.5 text-[#AF52DE]" />
                    <span>启用端到端主密码加密 (AES-GCM)</span>
                  </span>
                </label>
              </div>
              <div v-if="icloudCfg.usePassword" class="mt-1.5 flex items-center space-x-2">
                <input
                  v-model="icloudCfg.password"
                  @change="saveICloudSettings"
                  type="password"
                  placeholder="设置加密主密码 (跨设备拉取时需输入同一密码)"
                  class="flex-1 bg-[#FFFFFF] border border-[#E5E5EA] focus:border-[#0071E3] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] focus:outline-none font-mono"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 双向同步核心操作按钮组 -->
      <div class="pt-2 flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <!-- 立即推送到 iCloud -->
          <button
            @click="handlePushToICloud"
            :disabled="store.isICloudSyncing"
            class="text-xs px-4 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-60 text-white font-bold shadow-sm transition-all flex items-center space-x-2 cursor-pointer"
          >
            <SystemIcon v-if="store.isICloudSyncing" name="refresh" custom-class="w-3.5 h-3.5 animate-spin" />
            <SystemIcon v-else name="upload" custom-class="w-3.5 h-3.5 text-white" />
            <span>{{ store.isICloudSyncing ? '正在同步至云端...' : '立即打包推送到 iCloud' }}</span>
          </button>

          <!-- 从 iCloud 拉取并智能合并 -->
          <button
            @click="handlePullFromICloud"
            :disabled="store.isICloudSyncing"
            class="text-xs px-4 py-2 rounded-xl bg-[#34C759] hover:bg-[#30B753] active:bg-[#28A745] disabled:opacity-60 text-white font-bold shadow-sm transition-all flex items-center space-x-2 cursor-pointer"
          >
            <SystemIcon v-if="store.isICloudSyncing" name="refresh" custom-class="w-3.5 h-3.5 animate-spin" />
            <SystemIcon v-else name="download" custom-class="w-3.5 h-3.5 text-white" />
            <span>从 iCloud 拉取并智能合并</span>
          </button>
        </div>

        <div class="flex items-center space-x-2">
          <!-- 导出本地配置文件 -->
          <button
            @click="handleExportLocal"
            class="text-xs px-3 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1.5 cursor-pointer"
            title="将当前自定义渠道与配置下载为本地 JSON 文件"
          >
            <SystemIcon name="detail" custom-class="w-3.5 h-3.5" />
            <span>导出配置 JSON</span>
          </button>

          <!-- 导入本地配置文件 -->
          <label
            class="text-xs px-3 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1.5 cursor-pointer"
            title="从本地 JSON 配置文件导入并合并"
          >
            <SystemIcon name="wand" custom-class="w-3.5 h-3.5 text-[#0071E3]" />
            <span>导入配置 JSON</span>
            <input type="file" accept=".json" @change="handleImportLocalFile" class="hidden" />
          </label>
        </div>
      </div>
    </div>

    <!-- 卡片 1：数据源同步调度设置 (苹果灰白卡片) -->
    <div class="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-4">
      <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
        <div class="flex items-center space-x-2">
          <SystemIcon name="refresh" custom-class="w-4 h-4 text-[#0071E3]" />
          <span class="font-bold text-sm text-[#1D1D1F]">全网数据源自动同步与调度策略</span>
          <span class="text-xs text-[#86868B] ml-2">(涵盖 models.dev 的 models.json, catalog.json, api.json 三大核心数据源)</span>
        </div>
        <button
          @click="store.triggerFullSync"
          :disabled="store.syncProgress.isSyncing"
          class="text-xs px-4 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-60 text-white font-medium shadow-sm transition-all flex items-center space-x-1.5 cursor-pointer"
        >
          <SystemIcon v-if="store.syncProgress.isSyncing" name="refresh" custom-class="w-3.5 h-3.5 animate-spin" />
          <SystemIcon v-else name="zap" custom-class="w-3.5 h-3.5" />
          <span>{{ store.syncProgress.isSyncing ? `全网同步中 (${store.syncProgress.progress}%)` : '立即执行全网全量同步' }}</span>
        </button>
      </div>

      <div class="grid grid-cols-3 gap-3 text-xs">
        <!-- models.json -->
        <div class="p-3.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-[#1D1D1F]">1. 模型标准库</span>
            <span class="text-[#34C759] font-mono text-[10px] font-bold">350+ 标准模型</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            源: <span class="text-[#0071E3] font-mono">models.dev/models.json</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            已收录标准模型: <strong class="text-[#1D1D1F] font-mono">{{ store.syncStatus?.models_dev_total_models || 3580 }}</strong> 款
          </div>
        </div>

        <!-- catalog.json -->
        <div class="p-3.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-[#1D1D1F]">2. 供应商渠道库</span>
            <span class="text-[#34C759] font-mono text-[10px] font-bold">190+ 全球供应商</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            源: <span class="text-[#0071E3] font-mono">models.dev/catalog.json</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            收录供应商与渠道: <strong class="text-[#1D1D1F] font-mono">{{ store.syncStatus?.total_active_sites || 193 }}</strong> 家
          </div>
        </div>

        <!-- api.json -->
        <div class="p-3.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-[#1D1D1F]">3. 全网定价大矩阵</span>
            <span class="text-[#34C759] font-mono text-[10px] font-bold">7000+ 实时报价</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            源: <span class="text-[#0071E3] font-mono">models.dev/api.json</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            价格快照与折算条数: <strong class="text-[#1D1D1F] font-mono">{{ store.syncStatus?.total_pricings_cached || 7219 }}</strong> 条
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片 2：数据同步历史审计日志 (Sync Logs) -->
    <div class="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
      <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
        <div class="flex items-center space-x-2">
          <SystemIcon name="detail" custom-class="w-4 h-4 text-[#0071E3]" />
          <span class="font-bold text-sm text-[#1D1D1F]">数据同步历史审计日志 (Sync Audit Logs)</span>
          <span class="text-xs text-[#86868B] font-mono">记录每次抓取时间、条数与性能耗时</span>
        </div>
        <button
          @click="store.fetchSyncStatus"
          class="text-xs text-[#0071E3] hover:underline font-medium cursor-pointer"
        >
          刷新日志
        </button>
      </div>

      <!-- 同步日志数据表 -->
      <div class="overflow-x-auto">
        <table class="w-full text-xs text-left">
          <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA]">
            <tr>
              <th class="py-2.5 px-3">同步时间</th>
              <th class="py-2.5 px-3">数据源端点</th>
              <th class="py-2.5 px-3">同步类型</th>
              <th class="py-2.5 px-3 text-right">模型数</th>
              <th class="py-2.5 px-3 text-right">供应商数</th>
              <th class="py-2.5 px-3 text-right">价格更新条数</th>
              <th class="py-2.5 px-3 text-right">耗时 (ms)</th>
              <th class="py-2.5 px-3 text-center">状态</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#E5E5EA]/60 font-mono">
            <tr v-for="log in store.syncLogs" :key="log.id" class="hover:bg-[#F5F5F7] transition-colors">
              <td class="py-2.5 px-3 text-[#1D1D1F]">{{ formatFullTime(log.created_at) }}</td>
              <td class="py-2.5 px-3 text-[#0071E3] font-sans truncate max-w-[200px]" :title="log.source">{{ log.source }}</td>
              <td class="py-2.5 px-3 text-[#6E6E73] font-sans uppercase">{{ log.sync_type }}</td>
              <td class="py-2.5 px-3 text-right text-[#34C759] font-bold">{{ log.models_count }}</td>
              <td class="py-2.5 px-3 text-right text-[#0071E3] font-bold">{{ log.providers_count }}</td>
              <td class="py-2.5 px-3 text-right text-[#AF52DE] font-bold">{{ log.pricings_count }}</td>
              <td class="py-2.5 px-3 text-right text-[#1D1D1F]">{{ log.duration_ms }} ms</td>
              <td class="py-2.5 px-3 text-center">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase font-sans"
                  :class="log.status === 'success' ? 'bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6]' : 'bg-[#FFE5E5] text-[#FF3B30] border border-[#FFCCCC]'"
                >
                  {{ log.status === 'success' ? '成功' : '失败' }}
                </span>
              </td>
            </tr>

            <tr v-if="store.syncLogs.length === 0">
              <td colspan="8" class="py-8 text-center text-xs text-[#86868B]">
                暂无同步记录
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 卡片 3：实时汇率与数据库维护 (左右 2 列) -->
    <div class="grid grid-cols-2 gap-3">
      <!-- 实时汇率 -->
      <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-2">
          <div class="flex items-center space-x-1.5 font-bold text-xs text-[#1D1D1F]">
            <SystemIcon name="coins" custom-class="w-4 h-4 text-[#0071E3]" />
            <span>全球外汇汇率实时折算</span>
          </div>
          <span class="text-[10px] px-1.5 py-0.2 rounded bg-[#E6F4EA] text-[#34C759] border border-[#CEEAD6] font-mono font-bold">
            实时外汇源已接入
          </span>
        </div>

        <div class="space-y-2.5 text-xs">
          <!-- 汇率数值与源网址 -->
          <div class="grid grid-cols-12 gap-2">
            <div class="col-span-5 space-y-1">
              <label class="block text-[#86868B] text-[10.5px]">USD / CNY 换算基准</label>
              <input
                v-model.number="customRate"
                @change="autoSaveManualRate"
                @keyup.enter="autoSaveManualRate"
                type="number"
                step="0.001"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-2.5 py-1.5 text-[#1D1D1F] font-mono font-bold text-sm focus:outline-none"
              />
            </div>
            <div class="col-span-7 space-y-1">
              <label class="block text-[#86868B] text-[10.5px] flex items-center justify-between">
                <span>汇率获取源网址 (Source URL)</span>
                <a
                  :href="rateSourceUrl"
                  target="_blank"
                  class="text-[#0071E3] hover:underline text-[10px]"
                  title="在新窗口查看外汇源返回"
                >
                  验证源 ↗
                </a>
              </label>
              <input
                v-model="rateSourceUrl"
                @change="autoSaveManualRate"
                @keyup.enter="autoSaveManualRate"
                type="text"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-2.5 py-1.5 text-[#1D1D1F] font-mono text-[11px] focus:outline-none truncate"
              />
            </div>
          </div>

          <!-- 最后一次获取时间信息 -->
          <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] flex items-center justify-between text-[11px]">
            <div class="text-[#86868B] flex items-center space-x-1.5">
              <SystemIcon name="timer" custom-class="w-3.5 h-3.5 text-[#86868B]" />
              <span>最后一次获取汇率时间:</span>
            </div>
            <div class="font-mono text-[#1D1D1F] font-bold">
              {{ formatFullTime(store.syncStatus?.exchange_rate_updated_at) }}
            </div>
          </div>

          <!-- 联网抓取与自动保存一体化主操作按钮 -->
          <div class="pt-1">
            <button
              :disabled="isFetchingRate"
              @click="fetchOnlineRate"
              class="w-full py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-50 text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center space-x-2 cursor-pointer"
            >
              <SystemIcon v-if="isFetchingRate" name="refresh" custom-class="w-3.5 h-3.5 animate-spin" />
              <SystemIcon v-else name="zap" custom-class="w-3.5 h-3.5" />
              <span>{{ isFetchingRate ? '正在连接在线外汇源抓取并持久化...' : '联网抓取最新汇率并自动保存' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 数据库文件维护 -->
      <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
        <div class="border-b border-[#E5E5EA] pb-2 font-bold text-xs text-[#1D1D1F] flex items-center space-x-1.5">
          <SystemIcon name="site" custom-class="w-4 h-4 text-[#0071E3]" />
          <span>本地 SQLite 大数据库资产</span>
        </div>
        <div class="flex items-center justify-between text-xs font-mono">
          <div>
            <div class="text-[#86868B] text-[10px]">存储库大小</div>
            <div class="text-[#34C759] font-bold">{{ store.syncStatus?.db_size_mb || 3.8 }} MB</div>
          </div>
          <div>
            <div class="text-[#86868B] text-[10px]">价格快照总计</div>
            <div class="text-[#0071E3] font-bold">{{ store.syncStatus?.total_pricings_cached || 7219 }} 条</div>
          </div>
          <button
            @click="exportJson"
            class="px-3 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] text-xs font-sans font-medium flex items-center space-x-1.5 cursor-pointer"
          >
            <SystemIcon name="detail" custom-class="w-3.5 h-3.5" />
            <span>导出大数据库 (JSON)</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ==================== 备份快照列表与还原 Modal ==================== -->
    <div
      v-if="showBackupModal"
      class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
    >
      <div class="w-full max-w-2xl bg-white rounded-2xl border border-[#E5E5EA] shadow-2xl p-5 space-y-4 max-h-[85vh] flex flex-col">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
          <div class="flex items-center space-x-2">
            <SystemIcon name="history" custom-class="w-4 h-4 text-[#AF52DE]" />
            <span class="font-bold text-sm text-[#1D1D1F]">iCloud 历史版本快照与回滚还原</span>
            <span class="text-xs text-[#86868B] font-mono">({{ store.icloudBackups.length }} 份可用快照)</span>
          </div>
          <button
            @click="showBackupModal = false"
            class="text-[#86868B] hover:text-[#1D1D1F] p-1 rounded-lg hover:bg-[#F2F2F7] cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div class="text-xs text-[#6E6E73]">
          每次执行云端推送或智能合并前，系统均会自动保存一份本地快照，确保数据随时可精准回退。
        </div>

        <!-- 列表 -->
        <div class="flex-1 overflow-y-auto border border-[#E5E5EA] rounded-xl divide-y divide-[#E5E5EA]/60">
          <div
            v-for="b in store.icloudBackups"
            :key="b.filename"
            class="p-3 hover:bg-[#F9F9FB] flex items-center justify-between text-xs transition-colors"
          >
            <div class="space-y-0.5">
              <div class="flex items-center space-x-2 font-mono font-medium text-[#1D1D1F]">
                <span>{{ b.filename }}</span>
                <span
                  v-if="b.is_pre_merge"
                  class="text-[9.5px] px-1.5 py-0.2 rounded bg-[#FFF4E5] text-[#B06000] border border-[#FFE2B8] font-sans"
                >
                  合并前快照
                </span>
                <span
                  v-else
                  class="text-[9.5px] px-1.5 py-0.2 rounded bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6] font-sans"
                >
                  推送快照
                </span>
              </div>
              <div class="text-[10.5px] text-[#86868B] font-mono">
                时间: {{ b.created_at }} • 大小: {{ (b.size_bytes / 1024).toFixed(1) }} KB
              </div>
            </div>

            <button
              @click="handleRestoreBackup(b.filename)"
              :disabled="store.isICloudSyncing"
              class="px-3 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] hover:text-[#0077ED] font-medium transition-all text-xs flex items-center space-x-1 cursor-pointer"
            >
              <SystemIcon name="rotate-ccw" custom-class="w-3.5 h-3.5" />
              <span>回滚还原此快照</span>
            </button>
          </div>

          <div v-if="store.icloudBackups.length === 0" class="py-12 text-center text-xs text-[#86868B]">
            暂无历史快照记录
          </div>
        </div>

        <div class="flex items-center justify-between pt-2 border-t border-[#E5E5EA]">
          <span class="text-[11px] text-[#86868B]">快照保存在 iCloud Drive backups/ 目录中</span>
          <button
            @click="showBackupModal = false"
            class="px-4 py-1.5 rounded-xl bg-[#0071E3] text-white text-xs font-medium cursor-pointer"
          >
            完成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, reactive } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import SystemIcon from '../components/SystemIcon.vue'
import type { ICloudSyncConfig } from '../types'

const store = useDashboardStore()
const customRate = ref(7.25)
const rateSourceUrl = ref('https://open.er-api.com/v6/latest/USD')
const isFetchingRate = ref(false)
const showBackupModal = ref(false)

// 本地 iCloud 配置双向绑定
const icloudCfg = reactive<ICloudSyncConfig>({
  autoSync: store.icloudConfig.autoSync,
  includeApiKeys: store.icloudConfig.includeApiKeys,
  usePassword: store.icloudConfig.usePassword,
  password: store.icloudConfig.password,
  modules: { ...store.icloudConfig.modules }
})

const saveICloudSettings = () => {
  store.saveICloudConfig(icloudCfg)
}

const openBackupModal = async () => {
  await store.fetchICloudBackups()
  showBackupModal.value = true
}

const handlePushToICloud = async () => {
  saveICloudSettings()
  const res = await store.pushToICloud()
  if (res.success) {
    alert(`✓ ${res.message}`)
  } else {
    alert(`❌ ${res.message}: ${res.error}`)
  }
}

const handlePullFromICloud = async () => {
  if (icloudCfg.usePassword && !icloudCfg.password) {
    const inputPwd = prompt('请输入 iCloud 解密主密码:')
    if (!inputPwd) return
    icloudCfg.password = inputPwd
    saveICloudSettings()
  }

  const res = await store.pullFromICloud()
  if (res.success) {
    alert(`✓ ${res.message}\n已恢复渠道: ${res.report?.created_channels || 0} 个新增, ${res.report?.updated_channels || 0} 个更新\n模型映射: ${res.report?.imported_mappings || 0} 条`)
  } else {
    if (res.error?.includes('解密密码错误') || res.error?.includes('密码')) {
      const inputPwd = prompt(`解密失败，请输入正确的主密码:`)
      if (inputPwd) {
        icloudCfg.password = inputPwd
        saveICloudSettings()
        const retryRes = await store.pullFromICloud(inputPwd)
        if (retryRes.success) {
          alert(`✓ ${retryRes.message}`)
          return
        }
      }
    }
    alert(`❌ ${res.message}: ${res.error}`)
  }
}

const handleRestoreBackup = async (filename: string) => {
  if (!confirm(`确认要将数据恢复回退到历史快照 [${filename}] 吗？当前本地状态会自动生成一份安全备份。`)) {
    return
  }
  const res = await store.restoreICloudBackup(filename)
  if (res.success) {
    alert(`✓ ${res.message}`)
    showBackupModal.value = false
  } else {
    alert(`❌ ${res.message}: ${res.error}`)
  }
}

const handleExportLocal = async () => {
  try {
    const bundle = await store.exportLocalBundle()
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(bundle, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', `welltoken_custom_config_${new Date().toISOString().slice(0, 10)}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  } catch (e: any) {
    alert(`❌ 导出本地配置失败: ${e.message}`)
  }
}

const handleImportLocalFile = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = async (event) => {
    try {
      const rawJson = JSON.parse(event.target?.result as string)
      let pwd = icloudCfg.password
      if (rawJson.is_encrypted && !pwd) {
        pwd = prompt('该文件已加密，请输入解密主密码:') || ''
      }
      const res = await store.importLocalBundle(rawJson, pwd)
      if (res.success) {
        alert(`✓ ${res.message}`)
      } else {
        alert(`❌ ${res.message}: ${res.error}`)
      }
    } catch (err: any) {
      alert(`❌ 解析 JSON 失败: ${err.message}`)
    }
  }
  reader.readAsText(file)
}

const formatFullTime = (timeStr?: string | null) => {
  if (!timeStr) return '刚刚 (实时同步)'
  const d = new Date(timeStr)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
}

// 联网抓取最新汇率并自动持久化保存
const fetchOnlineRate = async () => {
  isFetchingRate.value = true
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/settings/exchange-rate/fetch-online`, {
      source_url: rateSourceUrl.value
    })
    customRate.value = res.data.rate
    rateSourceUrl.value = res.data.source
    await store.fetchComparisonMatrix()
    await store.fetchSyncStatus()
    alert(`✓ 成功同步并自动保存最新汇率: 1 USD = ${res.data.rate} CNY`)
  } catch (e: any) {
    console.error('Fetch online rate failed:', e)
    const errDetail = e.response?.data?.detail || e.message
    alert(`❌ 抓取在线汇率失败: ${errDetail}`)
  } finally {
    isFetchingRate.value = false
  }
}

// 手动输入数值时无感自动保存
const autoSaveManualRate = async () => {
  if (!customRate.value || customRate.value <= 0) return
  try {
    await axios.post(`${store.apiUrl}/api/v1/settings/exchange-rate`, {
      usd_to_cny_rate: customRate.value,
      exchange_rate_source: rateSourceUrl.value
    })
    await store.fetchComparisonMatrix()
    await store.fetchSyncStatus()
  } catch (e: any) {
    console.error('Auto save rate failed:', e)
  }
}

const exportJson = () => {
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(store.comparisonMatrix, null, 2))
  const downloadAnchor = document.createElement('a')
  downloadAnchor.setAttribute('href', dataStr)
  downloadAnchor.setAttribute('download', `welltoken_pricing_${new Date().toISOString().slice(0, 10)}.json`)
  document.body.appendChild(downloadAnchor)
  downloadAnchor.click()
  downloadAnchor.remove()
}

const syncDataFromStore = () => {
  if (store.syncStatus?.usd_to_cny_rate) {
    customRate.value = store.syncStatus.usd_to_cny_rate
  }
  if (store.syncStatus?.exchange_rate_source) {
    rateSourceUrl.value = store.syncStatus.exchange_rate_source
  }
}

onMounted(() => {
  syncDataFromStore()
  store.fetchICloudStatus()
})

watch(() => store.syncStatus, () => {
  syncDataFromStore()
}, { deep: true })
</script>

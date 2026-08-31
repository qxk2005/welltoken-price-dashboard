<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- ==================== 场景 A：供应商与渠道列表表格 ==================== -->
    <template v-if="!selectedProvider">
      <!-- 顶部操作栏与精确分类筛选 (苹果高级灰白风格，言简意赅，防折行) -->
      <div class="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex items-center justify-between flex-nowrap overflow-x-auto">
        <div class="flex items-center space-x-2.5 flex-shrink-0">
          <!-- 从全网比价跳转而来时的返回按钮 -->
          <button
            v-if="store.navigatedFromPriceMatrix"
            @click="store.returnToPriceMatrix()"
            class="px-3 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white transition-all text-xs font-bold flex items-center space-x-1 shadow-sm cursor-pointer flex-shrink-0"
          >
            <span>← 返回全网聚合比价</span>
          </button>

          <!-- 分类切换胶囊按钮组：全部 / 官方 / 中转 / 自建 / 收藏 -->
          <div class="flex items-center space-x-1 bg-[#F2F2F7] p-0.5 rounded-xl border border-[#E5E5EA] flex-shrink-0">
            <button
              v-for="tab in categoryTabs"
              :key="tab.id"
              @click="setCategory(tab.id)"
              class="px-2.5 py-1 text-xs rounded-lg font-medium transition-all flex items-center space-x-1.5 whitespace-nowrap cursor-pointer"
              :class="activeCategory === tab.id ? 'bg-[#0071E3] text-white font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
            >
              <SystemIcon v-if="tab.iconName" :name="tab.iconName" custom-class="w-3.5 h-3.5" />
              <span>{{ tab.name }}</span>
              <span
                class="px-1.5 py-0.2 rounded-full text-[10px] font-mono ml-0.5"
                :class="activeCategory === tab.id ? 'bg-white/20 text-white' : 'bg-[#E5E5EA] text-[#6E6E73]'"
              >
                {{ getCategoryCount(tab.id) }}
              </span>
            </button>
          </div>

          <!-- 供应商即时搜索框 (紧凑型) -->
          <div class="w-48 relative flex-shrink-0">
            <input
              v-model="searchKey"
              type="text"
              placeholder="搜索渠道/供应商..."
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
            />
            <span v-if="searchKey" @click="searchKey = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
          </div>
        </div>

        <!-- 右侧精简化操作按钮组 -->
        <div class="flex items-center space-x-2 flex-shrink-0 pl-2">
          <!-- iCloud 同步状态快捷入口 -->
          <button
            @click="handleQuickICloudSync"
            :title="store.icloudStatus?.is_macos && store.icloudStatus?.icloud_available ? `iCloud 同步: 上次于 ${store.icloudStatus?.sync_file_last_modified || '未同步'}，点击立即推送到 iCloud` : '点击进入设置配置 iCloud 同步'"
            class="text-xs px-2.5 py-1.5 rounded-lg border font-medium transition-all flex items-center space-x-1.5 whitespace-nowrap cursor-pointer"
            :class="store.icloudStatus?.is_macos && store.icloudStatus?.icloud_available ? 'bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border-[#E5E5EA]' : 'bg-[#F9F9FB] text-[#86868B] border-[#E5E5EA]'"
          >
            <SystemIcon v-if="store.isICloudSyncing" name="refresh" custom-class="w-3.5 h-3.5 text-[#0071E3] animate-spin" />
            <SystemIcon v-else name="cloud" custom-class="w-3.5 h-3.5 text-[#0071E3]" />
            <span>{{ store.isICloudSyncing ? 'iCloud 同步中...' : (store.icloudStatus?.icloud_available ? 'iCloud 同步' : 'iCloud 未就绪') }}</span>
          </button>

          <button
            @click="store.triggerFullSync"
            class="text-xs px-3 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1.5 whitespace-nowrap cursor-pointer"
            title="从 models.dev 官方数据库同步最新供应商与渠道"
          >
            <SystemIcon name="refresh" custom-class="w-3.5 h-3.5" />
            <span>同步官方库</span>
          </button>
          <button
            @click="openWizardForAdd"
            class="text-xs px-3 py-1.5 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] text-white font-medium shadow-sm transition-all flex items-center space-x-1.5 whitespace-nowrap cursor-pointer"
          >
            <SystemIcon name="wand" custom-class="w-3.5 h-3.5 text-white" />
            <span>添加渠道向导</span>
          </button>
        </div>
      </div>

      <!-- 供应商与渠道列表式表格 (精简长字段，来源标签独立成列，极度充裕舒适的显示空间) -->
      <div class="flex-1 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden min-h-0">
        <!-- 表格滚动区 -->
        <div class="flex-1 overflow-x-auto overflow-y-auto pr-1">
          <table class="w-full text-left text-xs border-collapse min-w-[1000px]">
            <!-- 表头 (支持点击排序) -->
            <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans select-none">
              <tr>
                <th class="py-3 px-2 text-center w-12">收藏</th>
                <th @click="toggleSort('name')" class="py-3 px-3 cursor-pointer hover:text-[#1D1D1F] transition-colors">
                  供应商 / 渠道名称 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('name') }}</span>
                </th>
                <th class="py-3 px-3 text-center w-28">渠道分类</th>
                <th class="py-3 px-3 text-center w-36">数据来源</th>
                <th @click="toggleSort('model_count')" class="py-3 px-3 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors w-28">
                  收录模型数 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('model_count') }}</span>
                </th>
                <th @click="toggleSort('recharge_rate')" class="py-3 px-3 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors w-24">
                  充值倍率 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('recharge_rate') }}</span>
                </th>
                <th @click="toggleSort('score')" class="py-3 px-3 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors w-24">
                  综合评分 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('score') }}</span>
                </th>
                <th class="py-3 px-3 text-center w-24">实测延迟</th>
                <th class="py-3 px-3 text-center w-20">状态</th>
                <th class="py-3 px-3 text-center w-28">操作</th>
              </tr>
            </thead>

            <!-- 数据行体 -->
            <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
              <tr
                v-for="site in paginatedSites"
                :key="site.id"
                class="hover:bg-[#F5F5F7] transition-colors group"
              >
                <!-- 0. 收藏星标按钮 -->
                <td class="py-3 px-2 text-center w-12">
                  <button
                    @click.stop="store.toggleFavoriteSite(site.id)"
                    class="transition-transform hover:scale-125 focus:outline-none cursor-pointer"
                    :title="store.isSiteFavorite(site.id) ? '点击取消收藏' : '点击加入收藏夹'"
                  >
                    <SystemIcon
                      :name="store.isSiteFavorite(site.id) ? 'star-filled' : 'star'"
                      custom-class="w-4 h-4"
                      :class="store.isSiteFavorite(site.id) ? 'text-amber-500 fill-amber-500' : 'text-[#AEAEB2] hover:text-amber-500'"
                    />
                  </button>
                </td>

                <!-- 1. 供应商名称、Logo 缩写与 ID (点击进入供应商详情页) -->
                <td class="py-3 px-3">
                  <div
                    @click="selectProvider(site)"
                    class="flex items-center space-x-2.5 cursor-pointer group-hover:text-[#0071E3] transition-colors"
                  >
                    <div class="w-8 h-8 rounded-lg bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center p-1.5 flex-shrink-0 group-hover:scale-105 group-hover:bg-[#E8F2FD] transition-all">
                      <ProviderLogo :provider-id="site.provider_id || site.name" custom-class="w-5 h-5" />
                    </div>
                    <div>
                      <div class="flex items-center space-x-1.5">
                        <span class="font-bold text-xs text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors">
                          {{ site.name }}
                        </span>
                        <!-- 智能动态分组徽章 -->
                        <span
                          v-if="site.groups && site.groups.length > 1"
                          class="px-1.5 py-0.2 rounded-md bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[10px] font-mono font-bold inline-flex items-center space-x-1 shadow-2xs cursor-help"
                          :title="`包含 ${site.groups.length} 个分组: ${site.groups.join(', ')}`"
                        >
                          <SystemIcon name="target" custom-class="w-2.5 h-2.5 text-[#8E24AA]" />
                          <span>{{ site.groups.length }}个分组</span>
                        </span>
                        <span
                          v-else-if="site.groups && site.groups.length === 1"
                          class="px-1.5 py-0.2 rounded-md bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[10px] font-mono font-bold inline-flex items-center space-x-1 shadow-2xs"
                          :title="`结算分组: ${site.groups[0]}`"
                        >
                          <SystemIcon name="target" custom-class="w-2.5 h-2.5 text-[#8E24AA]" />
                          <span>{{ site.groups[0] }}</span>
                        </span>
                        <span
                          v-else-if="site.group_name"
                          class="px-1.5 py-0.2 rounded-md bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[10px] font-mono font-bold inline-flex items-center space-x-0.5 shadow-2xs"
                          :title="`结算分组: ${site.group_name}`"
                        >
                          <span>🎯</span>
                          <span>{{ site.group_name }}</span>
                        </span>
                      </div>
                      <div class="text-[11px] text-[#86868B] font-mono mt-0.5">
                        {{ site.provider_id || `site-${site.id}` }}
                      </div>
                    </div>
                  </div>
                </td>

                <!-- 2. 渠道分类 (官方直连 / 中转站渠道 / 自添加网站) -->
                <td class="py-3 px-3 text-center w-28 whitespace-nowrap">
                  <span
                    class="px-2 py-0.5 rounded-md text-[11px] font-medium border whitespace-nowrap inline-block"
                    :class="getCategoryBadgeClass(site)"
                  >
                    {{ getCategoryLabel(site) }}
                  </span>
                </td>

                <!-- 3. 数据来源标签 (单独独立一列，如 MODELS.DEV 官方库 / 用户自建) -->
                <td class="py-3 px-3 text-center w-36 whitespace-nowrap">
                  <span
                    v-if="site.is_official_catalog"
                    class="px-2 py-0.5 rounded-full bg-[#E8F2FD] text-[#0071E3] text-[10px] font-mono border border-[#CCE4FB] font-bold inline-flex items-center space-x-1"
                  >
                    <span>●</span>
                    <span>MODELS.DEV</span>
                  </span>
                  <span
                    v-else
                    class="px-2 py-0.5 rounded-full bg-[#F2F2F7] text-[#6E6E73] text-[10px] font-mono border border-[#E5E5EA] font-medium inline-flex items-center space-x-1"
                  >
                    <span>○</span>
                    <span>用户自建中转</span>
                  </span>
                </td>

                <!-- 4. 收录模型总数 -->
                <td class="py-3 px-3 text-center w-28 whitespace-nowrap">
                  <span
                    @click="selectProvider(site)"
                    class="px-2.5 py-0.5 rounded-full bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6] font-mono font-bold text-xs cursor-pointer hover:bg-[#CEEAD6] transition-colors inline-block"
                    title="点击查看该供应商完整模型价格与详情"
                  >
                    {{ site.model_count || 12 }} 款
                  </span>
                </td>

                <!-- 5. 充值/折算倍率 -->
                <td class="py-3 px-3 text-center font-mono font-bold text-[#1D1D1F] w-24 whitespace-nowrap">
                  {{ site.recharge_rate ? site.recharge_rate.toFixed(2) : '1.00' }}x
                </td>

                <!-- 6. 综合评分 -->
                <td class="py-3 px-3 text-center font-mono text-[11px] w-24 whitespace-nowrap">
                  <ScoreBreakdownTooltip
                    :score="site.score"
                    :latency-ms="site.last_latency_ms"
                    align="center"
                  />
                </td>

                <!-- 7. 实测延迟 -->
                <td class="py-3 px-3 text-center font-mono text-[11px] w-24 whitespace-nowrap">
                  <span class="text-[#0071E3] font-medium">{{ site.last_latency_ms ? site.last_latency_ms.toFixed(0) : '35' }} ms</span>
                </td>

                <!-- 8. 启用/活跃状态 -->
                <td class="py-3 px-3 text-center w-20 whitespace-nowrap">
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      :checked="site.is_active"
                      @change="toggleSiteActive(site)"
                      class="sr-only peer"
                    />
                    <div class="w-8 h-4 bg-[#E5E5EA] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3.5 after:transition-all peer-checked:bg-[#34C759]"></div>
                  </label>
                </td>

                <!-- 9. 快捷操作 (下拉操作气泡菜单) -->
                <td class="py-3 px-3 text-center w-28 whitespace-nowrap relative">
                  <!-- 主操作胶囊按钮 -->
                  <button
                    @click.stop="toggleActionDropdown(site.id)"
                    class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] active:bg-[#D1D1D6] text-[#1D1D1F] border border-[#E5E5EA] text-[11px] font-medium transition-all inline-flex items-center space-x-1"
                    :class="{'bg-[#E8F2FD] border-[#CCE4FB] text-[#0071E3] font-bold': activeActionDropdownSiteId === site.id}"
                  >
                    <span>操作</span>
                    <span class="text-[9px] text-[#86868B] transition-transform duration-150" :class="{'rotate-180': activeActionDropdownSiteId === site.id}">▾</span>
                  </button>

                  <!-- 浮层下拉气泡菜单 (Apple 高级灰白质感) -->
                  <div
                    v-if="activeActionDropdownSiteId === site.id"
                    class="absolute right-3 top-10 w-36 bg-[#FFFFFF] border border-[#E5E5EA] rounded-xl shadow-[0_12px_30px_rgba(0,0,0,0.12)] z-30 py-1 text-left animate-fade-in text-xs divide-y divide-[#F2F2F7]"
                    @click.stop
                  >
                    <div class="py-1">
                      <button
                        @click="selectProvider(site); closeAllDropdowns()"
                        class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#1D1D1F] transition-colors"
                      >
                        <span>📊</span>
                        <span>供应商详情</span>
                      </button>
                      <button
                        @click="goToMatrixWithSite(site.id); closeAllDropdowns()"
                        class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#0071E3] transition-colors"
                      >
                        <span>⚖️</span>
                        <span>全网比价</span>
                      </button>
                      <button
                        @click="goToSpeedTestWithSite(site.id); closeAllDropdowns()"
                        class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#34C759] font-medium transition-colors"
                      >
                        <span>⚡</span>
                        <span>一键测速</span>
                      </button>
                      <a
                        v-if="site.doc_url"
                        :href="site.doc_url"
                        target="_blank"
                        @click="closeAllDropdowns()"
                        class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#AF52DE] transition-colors"
                      >
                        <span>📖</span>
                        <span>官方文档 ↗</span>
                      </a>
                    </div>

                    <div v-if="isCustomSite(site)" class="py-1">
                      <button
                        @click="openEditModal(site); closeAllDropdowns()"
                        class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#FF9500] transition-colors"
                      >
                        <span>✏️</span>
                        <span>编辑配置</span>
                      </button>
                      <button
                        @click="deleteSite(site.id); closeAllDropdowns()"
                        class="w-full px-3 py-1.5 hover:bg-[#FDE8E8] flex items-center space-x-2 text-[#FF3B30] transition-colors"
                      >
                        <span>🗑️</span>
                        <span>删除渠道</span>
                      </button>
                    </div>
                  </div>
                </td>
              </tr>

              <tr v-if="paginatedSites.length === 0">
                <td colspan="10" class="py-16 text-center text-xs text-[#86868B]">
                  <div v-if="activeCategory === 'favorites'" class="flex items-center justify-center space-x-1.5">
                    <SystemIcon name="star" custom-class="w-4 h-4 text-amber-500" />
                    <span>暂无收藏的渠道，点击列表左侧的星标即可快速加入收藏夹！</span>
                  </div>
                  <div v-else>
                    无匹配的供应商与渠道记录
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 底部现代化分页控制栏 (Pagination Bar - 苹果灰白风格) -->
        <div class="pt-3 border-t border-[#E5E5EA] flex items-center justify-between text-xs text-[#6E6E73]">
          <!-- 左侧：总数与每页条数选择器 -->
          <div class="flex items-center space-x-3">
            <span>
              显示第 <strong class="text-[#1D1D1F] font-mono">{{ totalItems > 0 ? startIndex + 1 : 0 }}</strong> -
              <strong class="text-[#1D1D1F] font-mono">{{ Math.min(startIndex + pageSize, totalItems) }}</strong> 条，
              共 <strong class="text-[#0071E3] font-mono">{{ totalItems }}</strong> 家渠道
            </span>

            <div class="flex items-center space-x-1.5">
              <span>每页:</span>
              <select
                v-model.number="pageSize"
                @change="currentPage = 1"
                class="bg-[#F2F2F7] border border-[#E5E5EA] rounded-lg px-2 py-0.5 text-xs text-[#1D1D1F] focus:outline-none focus:border-[#0071E3]"
              >
                <option :value="15">15 条/页</option>
                <option :value="20">20 条/页</option>
                <option :value="30">30 条/页</option>
                <option :value="50">50 条/页</option>
                <option :value="100">100 条/页</option>
              </select>
            </div>
          </div>

          <!-- 右侧：换页按钮与页码控制器 -->
          <div class="flex items-center space-x-1.5 font-mono">
            <button
              :disabled="currentPage <= 1"
              @click="currentPage = 1"
              class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-30 disabled:hover:bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all"
              title="首页"
            >
              «
            </button>
            <button
              :disabled="currentPage <= 1"
              @click="currentPage--"
              class="px-3 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-30 disabled:hover:bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all"
            >
              ‹ 上一页
            </button>

            <!-- 动态页码 Pills -->
            <div class="flex items-center space-x-1 px-1">
              <button
                v-for="p in visiblePages"
                :key="p"
                @click="currentPage = p"
                class="w-7 h-7 rounded-lg text-xs font-bold transition-all"
                :class="currentPage === p ? 'bg-[#0071E3] text-white shadow-xs' : 'bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA]'"
              >
                {{ p }}
              </button>
            </div>

            <button
              :disabled="currentPage >= totalPages"
              @click="currentPage++"
              class="px-3 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-30 disabled:hover:bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all"
            >
              下一页 ›
            </button>
            <button
              :disabled="currentPage >= totalPages"
              @click="currentPage = totalPages"
              class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-30 disabled:hover:bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all"
              title="末页"
            >
              »
            </button>

            <span class="text-[#86868B] text-[11px] ml-2">共 {{ totalPages }} 页</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ==================== 场景 B：供应商详情与专属模型定价规格表 (参考 models.dev/providers/bailing/) ==================== -->
    <template v-else>
      <!-- 1. 顶部 Header 介绍区 -->
      <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3.5">
        <!-- 顶部返回与代码标识 -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <button
              @click="selectedProvider = null"
              class="px-3 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] transition-all text-xs font-medium flex items-center space-x-1 cursor-pointer"
            >
              <span>← 返回渠道列表</span>
            </button>
          </div>

          <div class="flex items-center space-x-2">
            <span class="text-[11px] text-[#86868B]">渠道标识 (Provider ID):</span>
            <code class="px-2 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA] text-[#0071E3] font-mono text-xs font-bold">
              {{ selectedProvider.provider_id || `site-${selectedProvider.id}` }}
            </code>
            <button
              @click="copyText(selectedProvider.provider_id || `site-${selectedProvider.id}`)"
              class="text-xs text-[#6E6E73] hover:text-[#1D1D1F] px-2 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA]"
            >
              复制
            </button>
          </div>
        </div>

        <!-- 供应商大标题、Logo 与操作 -->
        <div class="flex items-start justify-between">
          <div class="flex items-start space-x-3.5">
            <div class="w-12 h-12 rounded-2xl bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center p-2.5 flex-shrink-0">
              <ProviderLogo :provider-id="selectedProvider.provider_id || selectedProvider.name" custom-class="w-7 h-7" />
            </div>
            <div class="space-y-1">
              <div class="flex items-center space-x-2">
                <h2 class="text-xl font-bold text-[#1D1D1F] tracking-tight">{{ selectedProvider.name }}</h2>
                <span
                  class="px-2 py-0.5 rounded-md text-[10px] font-medium border"
                  :class="getCategoryBadgeClass(selectedProvider)"
                >
                  {{ getCategoryLabel(selectedProvider) }}
                </span>
                <!-- 智能动态分组徽章 -->
                <span
                  v-if="detailAvailableGroups.length > 1"
                  class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] flex items-center space-x-1 shadow-2xs cursor-help"
                  :title="`包含 ${detailAvailableGroups.length} 个分组: ${detailAvailableGroups.map(g => g.name).join(', ')}`"
                >
                  <span>🎯 包含 {{ detailAvailableGroups.length }} 个分组</span>
                </span>
                <span
                  v-else-if="detailAvailableGroups.length === 1"
                  class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] flex items-center space-x-1 shadow-2xs"
                >
                  <span>🎯 结算分组:</span>
                  <span>{{ detailAvailableGroups[0].name }}</span>
                </span>
                <span
                  v-else-if="selectedProvider.group_name"
                  class="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] flex items-center space-x-1 shadow-2xs"
                >
                  <span>🎯 结算分组:</span>
                  <span>{{ selectedProvider.group_name }}</span>
                </span>
                <button
                  @click="store.toggleFavoriteSite(selectedProvider.id)"
                  class="text-base ml-2 hover:scale-125 transition-transform"
                >
                  <span v-if="store.isSiteFavorite(selectedProvider.id)" class="text-[#FF9500]">⭐ 已收藏</span>
                  <span v-else class="text-[#AEAEB2] hover:text-[#FF9500]">☆ 收藏该渠道</span>
                </button>
              </div>
              <div class="text-xs text-[#6E6E73] font-mono">
                API Base URL: <span class="text-[#0071E3]">{{ selectedProvider.base_url }}</span>
              </div>
            </div>
          </div>

          <!-- 右侧操作 -->
          <div class="flex items-center space-x-2">
            <button
              v-if="isCustomSite(selectedProvider)"
              @click="openSyncModalForCurrent"
              class="px-3 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] text-xs font-medium flex items-center space-x-1"
              title="使用 Relay-Watch 重新探测当前站点的最新模型并自动映射"
            >
              <span>📡 重新探测模型</span>
            </button>
            <a
              v-if="selectedProvider.doc_url"
              :href="selectedProvider.doc_url"
              target="_blank"
              class="px-3 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] text-xs font-medium flex items-center space-x-1"
            >
              <span>📖 官方开发文档 ↗</span>
            </a>
            <button
              @click="goToSpeedTestWithSite(selectedProvider.id)"
              class="px-3.5 py-1.5 rounded-xl bg-[#34C759] hover:bg-[#2FB34F] text-white text-xs font-bold shadow-sm flex items-center space-x-1"
            >
              <span>⚡</span>
              <span>一键测速</span>
            </button>
          </div>
        </div>

        <!-- 2. 五维 Fact Grid 指标看板 (提供可用模型数 / SDK 驱动 / 环境变量 / 实测评分 / 数据更新时间) -->
        <div class="grid grid-cols-5 gap-3 pt-2 border-t border-[#E5E5EA]">
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">提供可用模型数</div>
            <div class="text-lg font-bold font-mono text-[#0071E3] mt-0.5">
              {{ isDetailLoading ? '...' : `${providerModelsList.length} 款模型` }}
            </div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">SDK 兼容驱动 (Package)</div>
            <div class="text-xs font-bold font-mono text-[#1D1D1F] mt-1 truncate" title="@ai-sdk/openai-compatible">
              @ai-sdk/openai-compatible
            </div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">环境变量标识 (Env Key)</div>
            <div class="text-xs font-bold font-mono text-[#AF52DE] mt-1 truncate" :title="selectedProvider.env_vars || `${selectedProvider.name.toUpperCase().replace(/[^A-Z]/g, '')}_API_KEY`">
              {{ selectedProvider.env_vars || `${selectedProvider.name.toUpperCase().replace(/[^A-Z]/g, '')}_API_KEY` }}
            </div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">实测性能与评分</div>
            <div class="mt-1">
              <ScoreBreakdownTooltip
                :score="selectedProvider.score"
                :latency-ms="selectedProvider.last_latency_ms"
                align="right"
              >
                <span class="text-sm font-bold font-mono text-[#34C759]">
                  {{ selectedProvider.score || 95 }}分 / {{ selectedProvider.last_latency_ms ? selectedProvider.last_latency_ms.toFixed(0) : '35' }}ms
                </span>
              </ScoreBreakdownTooltip>
            </div>
          </div>
          <!-- 5. 数据最后更新时间 (新增方块区域) -->
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider flex items-center justify-between">
              <span>数据最后更新</span>
              <span
                class="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded-full border shadow-2xs"
                :class="getChannelUpdateSourceType(selectedProvider) === 'm'
                  ? 'bg-[#E8F2FD] text-[#0071E3] border-[#CCE4FB]'
                  : 'bg-[#F3E8FD] text-[#8E24AA] border-[#E1BEE7]'"
                :title="getChannelUpdateSourceType(selectedProvider) === 'm' ? '数据源: models.dev 官方平台' : '数据源: 自定义渠道同步'"
              >
                {{ getChannelUpdateSourceType(selectedProvider) }}
              </span>
            </div>
            <div class="mt-1 flex items-baseline space-x-1.5" :title="getChannelFullUpdateTime(selectedProvider)">
              <span class="text-sm font-bold font-mono text-[#1D1D1F]">
                {{ getChannelRelativeUpdateTime(selectedProvider) }}
              </span>
              <span class="text-[10px] text-[#86868B] font-mono truncate">
                {{ getChannelShortUpdateTime(selectedProvider) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. 该供应商所能提供的完整模型与价格数据表格 (支持 3 种视图模式切换) -->
      <div class="flex-1 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden min-h-0">
        <!-- 头部导航栏：标题 + 匹配数 + 三段式视图选择器 + 价格分组胶囊 + 搜索框 -->
        <div class="flex items-center justify-between pb-2.5 border-b border-[#E5E5EA]">
          <div class="flex items-center space-x-2.5 flex-wrap gap-y-1">
            <span class="text-xs font-bold text-[#1D1D1F]">
              📋 旗下可用模型规格与定价清单 (共 {{ providerModelsList.length }} 款)
            </span>
            <span
              v-if="filteredProviderModels.length !== providerModelsList.length"
              class="text-[11px] font-normal text-[#6E6E73] bg-[#F2F2F7] px-2 py-0.5 rounded-full border border-[#E5E5EA]"
            >
              已匹配 <strong class="text-[#0071E3] font-mono">{{ filteredProviderModels.length }}</strong> 款
            </span>

            <!-- 视图模式分段选择器 (Segmented Control) -->
            <div class="inline-flex p-0.5 rounded-xl bg-[#E5E5EA]/70 border border-[#D1D1D6]/60 text-xs select-none">
              <button
                @click="detailViewMode = 'flat'"
                class="px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center space-x-1"
                :class="detailViewMode === 'flat' ? 'bg-[#FFFFFF] text-[#0071E3] font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
              >
                <span>📄 平铺清单</span>
              </button>
              <button
                @click="detailViewMode = 'by-group'"
                class="px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center space-x-1"
                :class="detailViewMode === 'by-group' ? 'bg-[#FFFFFF] text-[#AF52DE] font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
              >
                <span>🎯 按价格分组</span>
              </button>
              <button
                @click="detailViewMode = 'by-model'"
                class="px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center space-x-1"
                :class="detailViewMode === 'by-model' ? 'bg-[#FFFFFF] text-[#FF9500] font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
              >
                <span>🤖 按模型对比</span>
              </button>
            </div>
          </div>

          <!-- 右侧组合工具条：分组下拉胶囊 + 搜索框 -->
          <div class="flex items-center space-x-2">
            <!-- 分组筛选 Apple 胶囊下拉选择器 (当渠道包含价格分组时展示) -->
            <div v-if="detailAvailableGroups.length > 0" class="relative" ref="groupFilterContainerRef">
              <button
                @click.stop="toggleGroupFilterPopover"
                class="px-2.5 py-1 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1.5 cursor-pointer select-none shadow-2xs group"
                :class="isGroupFilterActive
                  ? 'bg-[#F3E8FD] border-[#AF52DE] text-[#8E24AA] font-bold shadow-xs'
                  : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
                :title="`当前价格分组: ${groupFilterSummaryLabel}`"
              >
                <span>🎯</span>
                <span class="max-w-[130px] truncate">{{ groupFilterSummaryLabel }}</span>
                <span class="text-[10px] opacity-60">▾</span>
                <span
                  v-if="isGroupFilterActive"
                  @click.stop="clearGroupFilter"
                  class="hover:text-[#FF3B30] ml-0.5 cursor-pointer font-bold"
                  title="清空分组筛选"
                >✕</span>
              </button>

              <!-- 下拉弹层 Popover -->
              <div
                v-if="isGroupFilterOpen"
                @click.stop
                class="absolute right-0 top-9 w-64 bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-[0_12px_36px_rgba(0,0,0,0.14)] z-30 p-2.5 animate-fade-in text-xs space-y-2"
              >
                <!-- 弹层头部与快捷全选/清空 -->
                <div class="flex items-center justify-between pb-1.5 border-b border-[#E5E5EA]">
                  <div class="flex items-center space-x-1 text-[11px] font-bold text-[#1D1D1F]">
                    <span>🎯 价格分组 ({{ detailAvailableGroups.length }})</span>
                  </div>
                  <div class="flex items-center space-x-2 text-[11px]">
                    <button
                      @click="selectAllGroups"
                      class="text-[#0071E3] hover:underline cursor-pointer font-medium"
                    >
                      全选
                    </button>
                    <span class="text-[#D1D1D6]">|</span>
                    <button
                      @click="clearGroupFilter"
                      class="text-[#FF3B30] hover:underline cursor-pointer font-medium"
                    >
                      清空
                    </button>
                  </div>
                </div>

                <!-- 分组搜索框 (分组多于 4 个时展示) -->
                <div v-if="detailAvailableGroups.length > 4" class="relative">
                  <input
                    v-model="groupSearchQuery"
                    type="text"
                    placeholder="搜索分组名称..."
                    class="w-full bg-[#F2F2F7] border border-[#E5E5EA] rounded-lg px-2 py-1 text-[11px] text-[#1D1D1F] placeholder-[#86868B] focus:bg-white focus:border-[#AF52DE] focus:outline-none transition-all font-mono"
                  />
                  <span v-if="groupSearchQuery" @click="groupSearchQuery = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
                </div>

                <!-- 分组列表 -->
                <div class="max-h-56 overflow-y-auto space-y-0.5 pr-0.5">
                  <!-- 全部分组选项 -->
                  <div
                    @click="toggleAllGroupsOption"
                    class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-[#F2F2F7] cursor-pointer transition-colors"
                    :class="isAllGroupsSelected ? 'bg-[#E8F2FD] text-[#0071E3] font-bold' : 'text-[#1D1D1F]'"
                  >
                    <div class="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        :checked="isAllGroupsSelected"
                        class="rounded text-[#0071E3] focus:ring-0 cursor-pointer w-3.5 h-3.5"
                        @click.stop="toggleAllGroupsOption"
                      />
                      <span>全部分组</span>
                    </div>
                    <span class="text-[10px] font-mono opacity-70">({{ providerModelsList.length }})</span>
                  </div>

                  <!-- 各独立分组项 -->
                  <div
                    v-for="g in searchedAvailableGroups"
                    :key="`grp-${g.name}`"
                    @click="toggleGroupSelection(g.name)"
                    class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-[#F3E8FD]/50 cursor-pointer transition-colors font-mono"
                    :class="selectedGroupNames.includes(g.name) ? 'bg-[#F3E8FD] text-[#8E24AA] font-bold' : 'text-[#1D1D1F]'"
                  >
                    <div class="flex items-center space-x-2 truncate">
                      <input
                        type="checkbox"
                        :checked="selectedGroupNames.includes(g.name)"
                        class="rounded text-[#AF52DE] focus:ring-0 cursor-pointer w-3.5 h-3.5 flex-shrink-0"
                        @click.stop="toggleGroupSelection(g.name)"
                      />
                      <span class="truncate">{{ g.name }}</span>
                    </div>
                    <span class="text-[10px] font-mono text-[#86868B] flex-shrink-0 ml-1.5 bg-[#FFFFFF] px-1.5 py-0.2 rounded-full border border-[#E5E5EA]">
                      {{ g.count }}款
                    </span>
                  </div>

                  <div v-if="searchedAvailableGroups.length === 0" class="py-4 text-center text-[11px] text-[#86868B]">
                    未找到匹配分组
                  </div>
                </div>
              </div>
            </div>

            <!-- 搜索框 -->
            <div class="w-52 relative">
              <input
                v-model="providerModelSearchQuery"
                type="text"
                placeholder="搜索模型名称/标识..."
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
              />
              <span v-if="providerModelSearchQuery" @click="providerModelSearchQuery = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
            </div>

            <!-- 导出 Excel 按钮 -->
            <button
              @click="handleExportChannelModels"
              :disabled="filteredProviderModels.length === 0"
              class="px-2.5 py-1 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#CCE4FB] transition-all text-xs flex items-center space-x-1 cursor-pointer font-medium disabled:opacity-40 flex-shrink-0"
              title="导出当前渠道下筛选的全部可用模型与定价"
            >
              <span>📊</span>
              <span>导出 Excel</span>
            </button>
          </div>
        </div>

        <!-- 聚合视图下的批量折叠/展开快捷按钮 -->
        <div v-if="detailViewMode !== 'flat' && filteredProviderModels.length > 0" class="flex items-center justify-between py-1.5 px-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-xs mt-2 mb-1 flex-shrink-0">
          <div class="text-[11px] text-[#6E6E73] flex items-center space-x-1.5">
            <span v-if="detailViewMode === 'by-group'">
              📦 共聚合 <strong class="text-[#AF52DE] font-mono font-bold">{{ groupedByPricingGroup.length }}</strong> 个价格分组
            </span>
            <span v-else-if="detailViewMode === 'by-model'">
              🤖 共聚合 <strong class="text-[#FF9500] font-mono font-bold">{{ groupedByModel.length }}</strong> 款标准模型（跨组比价）
            </span>
          </div>
          <div class="flex items-center space-x-2 text-[11px]">
            <button
              @click="expandAllGroups"
              class="text-[#0071E3] hover:underline cursor-pointer font-medium flex items-center space-x-0.5"
            >
              <span>▾</span>
              <span>全部展开</span>
            </button>
            <span class="text-[#D1D1D6]">|</span>
            <button
              @click="collapseAllGroups"
              class="text-[#6E6E73] hover:underline cursor-pointer font-medium flex items-center space-x-0.5"
            >
              <span>▸</span>
              <span>全部折叠</span>
            </button>
          </div>
        </div>

        <!-- 内容视图区域 -->
        <div class="flex-1 overflow-x-auto overflow-y-auto pr-1 mt-1 relative">
          <div v-if="isDetailLoading" class="absolute inset-0 bg-white/70 backdrop-blur-xs flex items-center justify-center z-10">
            <div class="text-xs text-[#0071E3] font-medium flex items-center space-x-2">
              <span class="animate-spin">🌀</span>
              <span>正在从后端数据库加载模型定价...</span>
            </div>
          </div>

          <!-- 模式 1：标准平铺清单表格 (detailViewMode === 'flat') -->
          <table v-if="detailViewMode === 'flat'" class="w-full text-left text-xs border-collapse min-w-[980px]">
            <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans select-none">
              <tr>
                <th @click="toggleDetailSort('model_name')" class="py-2.5 px-3 cursor-pointer hover:text-[#0071E3] transition-colors">
                  模型名称 / 标准标识 / 所属分组 <span class="text-[10px] font-mono" :class="detailSortField === 'model_name' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getDetailSortIndicator('model_name') }}</span>
                </th>
                <th @click="toggleDetailSort('context_window')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#0071E3] transition-colors">
                  上下文 (Context) <span class="text-[10px] font-mono" :class="detailSortField === 'context_window' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getDetailSortIndicator('context_window') }}</span>
                </th>
                <th @click="toggleDetailSort('max_output')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#0071E3] transition-colors">
                  最大输出 (Output) <span class="text-[10px] font-mono" :class="detailSortField === 'max_output' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getDetailSortIndicator('max_output') }}</span>
                </th>
                <th @click="toggleDetailSort('calculated_input_usd')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#0071E3] transition-colors">
                  输入单价 ({{ store.currency }}) <span class="text-[10px] font-mono" :class="detailSortField === 'calculated_input_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getDetailSortIndicator('calculated_input_usd') }}</span>
                </th>
                <th @click="toggleDetailSort('calculated_output_usd')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#0071E3] transition-colors">
                  输出单价 ({{ store.currency }}) <span class="text-[10px] font-mono" :class="detailSortField === 'calculated_output_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getDetailSortIndicator('calculated_output_usd') }}</span>
                </th>
                <th class="py-2.5 px-3 text-center">深度推理</th>
                <th class="py-2.5 px-3 text-center">工具调用</th>
                <th @click="toggleDetailSort('last_tested_tps')" class="py-2.5 px-3 text-center cursor-pointer hover:text-[#0071E3] transition-colors">
                  实测 TPS <span class="text-[10px] font-mono" :class="detailSortField === 'last_tested_tps' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getDetailSortIndicator('last_tested_tps') }}</span>
                </th>
                <th class="py-2.5 px-3 text-center">快捷操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
              <tr
                v-for="item in filteredProviderModels"
                :key="item.id || item.model_id"
                class="hover:bg-[#F5F5F7] transition-colors"
              >
                <!-- 模型名称、标准 ID 与所属分组徽章 -->
                <td class="py-2.5 px-3">
                  <div class="flex items-center space-x-2">
                    <span class="font-bold text-[#1D1D1F] text-xs">{{ item.model_name }}</span>
                    <span v-if="item.group_name" class="px-1.5 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-mono font-bold shadow-2xs">
                      🎯 {{ item.group_name }}
                    </span>
                  </div>
                  <div class="flex items-center space-x-1.5 text-[11px] font-mono mt-0.5">
                    <span class="text-[#0071E3]">{{ item.model_id }}</span>
                    <span v-if="item.site_model_name && item.site_model_name !== item.model_id" class="text-[#86868B]">({{ item.site_model_name }})</span>
                  </div>
                </td>

                <!-- 上下文 -->
                <td class="py-2.5 px-3 text-right font-mono text-[#1D1D1F]">
                  {{ formatContextWindow(item.context_window) }}
                </td>

                <!-- 最大输出 -->
                <td class="py-2.5 px-3 text-right font-mono text-[#6E6E73]">
                  {{ item.max_output ? Number(item.max_output).toLocaleString() : '8,192' }}
                </td>

                <!-- 输入单价 (响应全局货币切换) -->
                <td class="py-2.5 px-3 text-right font-mono font-bold text-[#34C759]">
                  {{ store.formatCurrency(item.calculated_input_usd) }}
                </td>

                <!-- 输出单价 (响应全局货币切换) -->
                <td class="py-2.5 px-3 text-right font-mono text-[#1D1D1F]">
                  {{ store.formatCurrency(item.calculated_output_usd) }}
                </td>

                <!-- 深度推理 -->
                <td class="py-2.5 px-3 text-center font-mono">
                  <span v-if="isReasoningModel(item.model_id)" class="text-[#34C759] font-bold">是</span>
                  <span v-else class="text-[#86868B]">-</span>
                </td>

                <!-- 工具调用 -->
                <td class="py-2.5 px-3 text-center font-mono">
                  <span class="text-[#34C759] font-bold">是</span>
                </td>

                <!-- 实测 TPS -->
                <td class="py-2.5 px-3 text-center font-mono text-[#0071E3] font-bold">
                  {{ item.last_tested_tps }} tps
                </td>

                <!-- 快捷操作 (下拉操作气泡菜单) -->
                <td class="py-2.5 px-3 text-center w-28 whitespace-nowrap relative">
                  <button
                    @click.stop="toggleModelActionDropdown(item.id || item.model_id)"
                    class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] active:bg-[#D1D1D6] text-[#1D1D1F] border border-[#E5E5EA] text-[11px] font-medium transition-all inline-flex items-center space-x-1"
                    :class="{'bg-[#E8F2FD] border-[#CCE4FB] text-[#0071E3] font-bold': activeActionDropdownModelId === (item.id || item.model_id)}"
                  >
                    <span>操作</span>
                    <span class="text-[9px] text-[#86868B] transition-transform duration-150" :class="{'rotate-180': activeActionDropdownModelId === (item.id || item.model_id)}">▾</span>
                  </button>

                  <!-- 浮层下拉气泡菜单 -->
                  <div
                    v-if="activeActionDropdownModelId === (item.id || item.model_id)"
                    class="absolute right-3 top-9 w-32 bg-[#FFFFFF] border border-[#E5E5EA] rounded-xl shadow-[0_12px_30px_rgba(0,0,0,0.12)] z-30 py-1 text-left animate-fade-in text-xs"
                    @click.stop
                  >
                    <button
                      @click="goToMatrixWithModel(item.model_id); closeAllDropdowns()"
                      class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#0071E3] transition-colors"
                    >
                      <span>⚖️</span>
                      <span>全网比价</span>
                    </button>
                    <button
                      @click="goToSpeedTestWithModel(item.model_id); closeAllDropdowns()"
                      class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#34C759] font-medium transition-colors"
                    >
                      <span>⚡</span>
                      <span>一键测速</span>
                    </button>
                    <button
                      v-if="isCustomSite(selectedProvider)"
                      @click="removeModelPricing(item); closeAllDropdowns()"
                      class="w-full px-3 py-1.5 hover:bg-[#FDE8E8] flex items-center space-x-2 text-[#FF3B30] transition-colors border-t border-[#F2F2F7]"
                    >
                      <span>🗑️</span>
                      <span>移除定价</span>
                    </button>
                  </div>
                </td>
              </tr>

              <tr v-if="!isDetailLoading && filteredProviderModels.length === 0">
                <td colspan="9" class="py-12 text-center text-xs text-[#86868B]">
                  该供应商暂无更多已收录模型
                </td>
              </tr>
            </tbody>
          </table>

          <!-- 模式 2：按「价格分组」聚合展示折叠卡片 (detailViewMode === 'by-group') -->
          <div v-else-if="detailViewMode === 'by-group'" class="space-y-3 pb-3">
            <div
              v-for="sec in groupedByPricingGroup"
              :key="`sec-grp-${sec.groupName}`"
              class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-xs overflow-hidden transition-all"
            >
              <!-- 分组卡片头部 -->
              <div
                @click="toggleCollapse(sec.groupName)"
                class="flex items-center justify-between p-3 bg-[#F9F9FB] hover:bg-[#F2F2F7] cursor-pointer transition-colors border-b border-[#E5E5EA] select-none"
              >
                <div class="flex items-center space-x-2.5">
                  <span class="px-2.5 py-0.5 rounded-lg bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-xs font-mono font-bold flex items-center space-x-1 shadow-2xs">
                    <span>🎯</span>
                    <span>{{ sec.groupName }}</span>
                  </span>
                  <span class="text-xs font-bold text-[#1D1D1F]">
                    包含 <strong class="text-[#0071E3] font-mono">{{ sec.models.length }}</strong> 款模型
                  </span>
                </div>

                <div class="flex items-center space-x-3 text-xs">
                  <div class="flex items-center space-x-2 text-[11px] text-[#6E6E73] font-mono">
                    <span>输入单价: <strong class="text-[#34C759] font-bold">{{ store.formatCurrency(sec.minInputPrice) }} ~ {{ store.formatCurrency(sec.maxInputPrice) }}</strong></span>
                    <span>•</span>
                    <span>平均: <strong class="text-[#0071E3]">{{ sec.avgTps }} TPS</strong></span>
                  </div>
                  <button class="text-[#86868B] text-xs font-bold transition-transform duration-150" :class="{'rotate-180': !collapsedGroupKeys.has(sec.groupName)}">
                    ▾
                  </button>
                </div>
              </div>

              <!-- 分组卡片内部模型列表 -->
              <div v-if="!collapsedGroupKeys.has(sec.groupName)" class="p-2 overflow-x-auto">
                <table class="w-full text-left text-xs border-collapse min-w-[900px]">
                  <thead class="text-[11px] text-[#6E6E73] bg-[#FFFFFF] border-b border-[#E5E5EA] font-sans select-none">
                    <tr>
                      <th class="py-2 px-2.5">模型名称 / 标准标识</th>
                      <th class="py-2 px-2.5 text-right">上下文 (Context)</th>
                      <th class="py-2 px-2.5 text-right">最大输出 (Output)</th>
                      <th class="py-2 px-2.5 text-right">输入单价 ({{ store.currency }})</th>
                      <th class="py-2 px-2.5 text-right">输出单价 ({{ store.currency }})</th>
                      <th class="py-2 px-2.5 text-center">深度推理</th>
                      <th class="py-2 px-2.5 text-center">工具调用</th>
                      <th class="py-2 px-2.5 text-center">实测 TPS</th>
                      <th class="py-2 px-2.5 text-center">快捷操作</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
                    <tr v-for="item in sec.models" :key="item.id || item.model_id" class="hover:bg-[#F5F5F7] transition-colors">
                      <td class="py-2 px-2.5">
                        <div class="font-bold text-[#1D1D1F] text-xs">{{ item.model_name }}</div>
                        <div class="text-[11px] font-mono text-[#0071E3] mt-0.5">{{ item.model_id }}</div>
                      </td>
                      <td class="py-2 px-2.5 text-right font-mono text-[#1D1D1F]">{{ formatContextWindow(item.context_window) }}</td>
                      <td class="py-2 px-2.5 text-right font-mono text-[#6E6E73]">{{ item.max_output ? Number(item.max_output).toLocaleString() : '8,192' }}</td>
                      <td class="py-2 px-2.5 text-right font-mono font-bold text-[#34C759]">{{ store.formatCurrency(item.calculated_input_usd) }}</td>
                      <td class="py-2 px-2.5 text-right font-mono text-[#1D1D1F]">{{ store.formatCurrency(item.calculated_output_usd) }}</td>
                      <td class="py-2 px-2.5 text-center font-mono">
                        <span v-if="isReasoningModel(item.model_id)" class="text-[#34C759] font-bold">是</span>
                        <span v-else class="text-[#86868B]">-</span>
                      </td>
                      <td class="py-2 px-2.5 text-center font-mono"><span class="text-[#34C759] font-bold">是</span></td>
                      <td class="py-2 px-2.5 text-center font-mono text-[#0071E3] font-bold">{{ item.last_tested_tps }} tps</td>
                      <td class="py-2 px-2.5 text-center whitespace-nowrap">
                        <div class="flex items-center justify-center space-x-1">
                          <button @click="goToMatrixWithModel(item.model_id)" class="px-2 py-0.5 rounded bg-[#F2F2F7] hover:bg-[#E8F2FD] text-[#0071E3] border border-[#E5E5EA] text-[10px] font-medium" title="去全网比价">比价</button>
                          <button @click="goToSpeedTestWithModel(item.model_id)" class="px-2 py-0.5 rounded bg-[#F2F2F7] hover:bg-[#EAF8EE] text-[#34C759] border border-[#E5E5EA] text-[10px] font-medium" title="一键测速">测速</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-if="!isDetailLoading && groupedByPricingGroup.length === 0" class="py-12 text-center text-xs text-[#86868B]">
              暂无匹配的价格分组
            </div>
          </div>

          <!-- 模式 3：按「模型名称」聚合跨分组比价展示折叠卡片 (detailViewMode === 'by-model') -->
          <div v-else-if="detailViewMode === 'by-model'" class="space-y-3 pb-3">
            <div
              v-for="sec in groupedByModel"
              :key="`sec-mdl-${sec.modelKey}`"
              class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-xs overflow-hidden transition-all"
            >
              <!-- 模型卡片头部 -->
              <div
                @click="toggleCollapse(sec.modelKey)"
                class="flex items-center justify-between p-3 bg-[#F9F9FB] hover:bg-[#F2F2F7] cursor-pointer transition-colors border-b border-[#E5E5EA] select-none"
              >
                <div class="flex items-center space-x-2.5">
                  <span class="text-xs font-bold text-[#1D1D1F] flex items-center space-x-1.5">
                    <span>🤖</span>
                    <span>{{ sec.modelName }}</span>
                  </span>
                  <code class="px-2 py-0.5 rounded bg-[#F2F2F7] text-[#0071E3] font-mono text-[11px] border border-[#E5E5EA]">
                    {{ sec.modelId }}
                  </code>
                  <span
                    class="px-2 py-0.2 rounded-full text-[10px] font-bold border"
                    :class="sec.groupCount > 1 ? 'bg-[#FFF8E1] text-[#B78103] border-[#FFE082]' : 'bg-[#F2F2F7] text-[#6E6E73] border-[#E5E5EA]'"
                  >
                    覆盖 {{ sec.groupCount }} 个分组
                  </span>
                </div>

                <div class="flex items-center space-x-3 text-xs">
                  <div class="flex items-center space-x-2 font-mono text-[11px]">
                    <span class="text-[#6E6E73]">
                      最低起步: <strong class="text-[#34C759] font-bold text-xs">{{ store.formatCurrency(sec.minInputPrice) }}</strong>
                    </span>
                    <span v-if="sec.groupCount > 1 && sec.maxInputPrice > sec.minInputPrice" class="text-[#86868B]">
                      (最高: {{ store.formatCurrency(sec.maxInputPrice) }})
                    </span>
                  </div>
                  <button class="text-[#86868B] text-xs font-bold transition-transform duration-150" :class="{'rotate-180': !collapsedGroupKeys.has(sec.modelKey)}">
                    ▾
                  </button>
                </div>
              </div>

              <!-- 模型卡片内部跨分组对比表格 -->
              <div v-if="!collapsedGroupKeys.has(sec.modelKey)" class="p-2 overflow-x-auto">
                <table class="w-full text-left text-xs border-collapse min-w-[850px]">
                  <thead class="text-[11px] text-[#6E6E73] bg-[#FFFFFF] border-b border-[#E5E5EA] font-sans select-none">
                    <tr>
                      <th class="py-2 px-2.5">所属分组</th>
                      <th class="py-2 px-2.5 text-right">输入单价 ({{ store.currency }})</th>
                      <th class="py-2 px-2.5 text-right">输出单价 ({{ store.currency }})</th>
                      <th class="py-2 px-2.5 text-center">价差 / 溢价分析</th>
                      <th class="py-2 px-2.5 text-right">上下文 / 最大输出</th>
                      <th class="py-2 px-2.5 text-center">实测 TPS</th>
                      <th class="py-2 px-2.5 text-center">操作</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
                    <tr
                      v-for="item in sec.items"
                      :key="item.id || `${item.model_id}-${item.group_name}`"
                      class="hover:bg-[#F5F5F7] transition-colors"
                      :class="{'bg-[#EAF8EE]/40': getModelGroupPriceMeta(item, sec.items).isLowest}"
                    >
                      <!-- 所属分组徽章 -->
                      <td class="py-2 px-2.5">
                        <span class="px-2 py-0.5 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[10px] font-mono font-bold shadow-2xs">
                          🎯 {{ item.group_name || '默认分组' }}
                        </span>
                      </td>

                      <!-- 输入单价 (高亮最低价) -->
                      <td class="py-2 px-2.5 text-right font-mono font-bold">
                        <span :class="getModelGroupPriceMeta(item, sec.items).isLowest ? 'text-[#34C759]' : 'text-[#1D1D1F]'">
                          {{ store.formatCurrency(item.calculated_input_usd) }}
                        </span>
                      </td>

                      <!-- 输出单价 -->
                      <td class="py-2 px-2.5 text-right font-mono text-[#1D1D1F]">
                        {{ store.formatCurrency(item.calculated_output_usd) }}
                      </td>

                      <!-- 价差 / 溢价分析徽章 -->
                      <td class="py-2 px-2.5 text-center">
                        <span
                          v-if="getModelGroupPriceMeta(item, sec.items).isLowest"
                          class="px-2 py-0.5 rounded-full bg-[#EAF8EE] text-[#28A745] border border-[#C3E6CB] text-[10px] font-bold shadow-2xs inline-flex items-center space-x-0.5"
                        >
                          <span>🏆</span>
                          <span>最低价 (最优)</span>
                        </span>
                        <span
                          v-else-if="getModelGroupPriceMeta(item, sec.items).diffPercentText"
                          class="px-2 py-0.5 rounded-full bg-[#FFF3E0] text-[#E65100] border border-[#FFE0B2] text-[10px] font-mono font-medium shadow-2xs inline-flex items-center space-x-0.5"
                          :title="`相较该模型最低价高出 ${getModelGroupPriceMeta(item, sec.items).diffText}`"
                        >
                          <span>高出 {{ getModelGroupPriceMeta(item, sec.items).diffPercentText }}</span>
                        </span>
                        <span v-else class="text-[#86868B] text-[10px] font-mono">
                          标准价
                        </span>
                      </td>

                      <!-- 上下文 / 输出 -->
                      <td class="py-2 px-2.5 text-right font-mono text-[11px] text-[#6E6E73]">
                        {{ formatContextWindow(item.context_window) }} / {{ item.max_output ? Number(item.max_output).toLocaleString() : '8K' }}
                      </td>

                      <!-- 实测 TPS -->
                      <td class="py-2 px-2.5 text-center font-mono text-[#0071E3] font-bold">
                        {{ item.last_tested_tps }} tps
                      </td>

                      <!-- 操作 -->
                      <td class="py-2 px-2.5 text-center whitespace-nowrap">
                        <div class="flex items-center justify-center space-x-1">
                          <button @click="goToMatrixWithModel(item.model_id)" class="px-2 py-0.5 rounded bg-[#F2F2F7] hover:bg-[#E8F2FD] text-[#0071E3] border border-[#E5E5EA] text-[10px] font-medium" title="去全网比价">比价</button>
                          <button @click="goToSpeedTestWithModel(item.model_id)" class="px-2 py-0.5 rounded bg-[#F2F2F7] hover:bg-[#EAF8EE] text-[#34C759] border border-[#E5E5EA] text-[10px] font-medium" title="一键测速">测速</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-if="!isDetailLoading && groupedByModel.length === 0" class="py-12 text-center text-xs text-[#86868B]">
              暂无匹配的模型数据
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 4 步向导式添加/重新探测自建渠道 Modal (Relay-Watch & 智能模型归一化) -->
    <AddChannelWizardModal
      v-if="showWizardModal"
      :initial-channel="wizardInitialChannel"
      :initial-step="wizardInitialStep"
      @close="showWizardModal = false; wizardInitialChannel = null; wizardInitialStep = 1"
      @success="onWizardSuccess"
    />

    <!-- 弹窗：编辑渠道基础配置 Modal (Apple 极简浅色高级风格) -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in"
    >
      <div class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl w-[560px] max-w-[94vw] p-6 space-y-4 shadow-[0_20px_50px_rgba(0,0,0,0.15)]">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
          <div class="flex items-center space-x-2">
            <h3 class="font-bold text-sm text-[#1D1D1F]">
              {{ isEditing ? '✏️ 编辑渠道基础配置' : '➕ 添加自建中转站' }}
            </h3>
            <span v-if="isEditing" class="text-[11px] px-2 py-0.5 rounded-md bg-[#F2F2F7] text-[#6E6E73] font-mono">
              ID: {{ currentEditId }}
            </span>
          </div>
          <button @click="showModal = false" class="text-[#86868B] hover:text-[#1D1D1F] text-sm p-1 cursor-pointer">✕</button>
        </div>

        <div class="space-y-3 text-xs">
          <!-- 站点名称 -->
          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">站点名称 (Name) *</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="例如: 我的自建 NewAPI 聚合站"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none transition-colors"
            />
          </div>

          <!-- Base URL -->
          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">API 基础端点地址 (Base URL) *</label>
            <input
              v-model="form.base_url"
              type="text"
              placeholder="https://api.my-newapi.com/v1"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none transition-colors"
            />
          </div>

          <!-- API Key (带明文/密文切换) -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-[#6E6E73] font-medium">中转站 API Key (用于流式测速与模型探测)</label>
              <button
                type="button"
                @click="showApiKeyPlain = !showApiKeyPlain"
                class="text-[11px] text-[#0071E3] hover:underline cursor-pointer"
              >
                {{ showApiKeyPlain ? '🙈 隐藏密文' : '👁️ 查看明文' }}
              </button>
            </div>
            <input
              v-model="form.api_key"
              :type="showApiKeyPlain ? 'text' : 'password'"
              placeholder="sk-..."
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none transition-colors"
            />
          </div>

          <!-- 系统类型 + 结算货币基准 -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">系统类型 (Site Type)</label>
              <select
                v-model="form.site_type"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none"
              >
                <option value="newapi">NewAPI / OneAPI 系统</option>
                <option value="sub2api">Sub2API 系统</option>
                <option value="cloud">云服务商聚合</option>
                <option value="custom">通用自建中转站</option>
              </select>
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">结算货币基准 (Currency)</label>
              <select
                v-model="form.currency"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none font-medium"
              >
                <option value="CNY">人民币 (CNY ¥)</option>
                <option value="USD">美元 (USD $)</option>
              </select>
            </div>
          </div>

          <!-- 默认结算分组 + 充值折算倍率 -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">默认结算分组 (Default Group)</label>
              <input
                v-model="form.group_name"
                type="text"
                placeholder="例如: default, vip, 3.5折"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none"
              />
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">充值折算倍率 (Recharge Rate)</label>
              <input
                v-model.number="form.recharge_rate"
                type="number"
                step="0.01"
                min="0.01"
                placeholder="1.0"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
              />
            </div>
          </div>

          <!-- 备注说明 -->
          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">备注说明 (Notes)</label>
            <input
              v-model="form.notes"
              type="text"
              placeholder="例如: 充值比例 1:1，支持高并发"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none"
            />
          </div>
        </div>

        <div class="flex items-center justify-between pt-3 border-t border-[#E5E5EA]">
          <div>
            <button
              v-if="isEditing"
              @click="openWizardFromEdit"
              type="button"
              class="px-3 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] hover:text-[#0077ED] text-xs font-semibold flex items-center space-x-1.5 transition-colors cursor-pointer"
              title="使用当前配置进入 4 步向导重新探测模型并配置倍率"
            >
              <span>🔄</span>
              <span>进入模型映射向导</span>
            </button>
          </div>

          <div class="flex items-center space-x-2">
            <button
              @click="showModal = false"
              class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] text-xs font-medium cursor-pointer transition-colors"
            >
              取消
            </button>
            <button
              @click="saveChannel"
              :disabled="isSavingChannel"
              class="px-5 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] text-white text-xs font-medium shadow-sm disabled:opacity-50 cursor-pointer transition-colors"
            >
              <span v-if="isSavingChannel">保存中...</span>
              <span v-else>{{ isEditing ? '保存修改' : '确认添加' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import ProviderLogo from '../components/ProviderLogo.vue'
import AddChannelWizardModal from '../components/AddChannelWizardModal.vue'
import ScoreBreakdownTooltip from '../components/ScoreBreakdownTooltip.vue'
import SystemIcon from '../components/SystemIcon.vue'
import type { RelaySite } from '../types'
import { parseUtcDate, formatRelativeTime } from '../utils/timeUtils'
import { exportChannelModelsToExcel } from '../utils/excelExport'

const store = useDashboardStore()
const searchKey = ref('')
const activeCategory = ref('all')
const selectedProvider = ref<RelaySite | null>(null)
const providerModelSearchQuery = ref('')
const providerModelsList = ref<any[]>([])
const isDetailLoading = ref(false)

const handleExportChannelModels = () => {
  if (!selectedProvider.value) return
  exportChannelModelsToExcel(
    selectedProvider.value.name,
    filteredProviderModels.value,
    store.currency as any
  )
}

// 下拉操作菜单激活状态 (互斥打开)
const activeActionDropdownSiteId = ref<number | null>(null)
const activeActionDropdownModelId = ref<any | null>(null)

const toggleActionDropdown = (siteId: number) => {
  if (activeActionDropdownSiteId.value === siteId) {
    activeActionDropdownSiteId.value = null
  } else {
    activeActionDropdownSiteId.value = siteId
    activeActionDropdownModelId.value = null
  }
}

const toggleModelActionDropdown = (modelId: any) => {
  if (activeActionDropdownModelId.value === modelId) {
    activeActionDropdownModelId.value = null
  } else {
    activeActionDropdownModelId.value = modelId
    activeActionDropdownSiteId.value = null
  }
}

const closeAllDropdowns = (e?: MouseEvent) => {
  activeActionDropdownSiteId.value = null
  activeActionDropdownModelId.value = null
  if (isGroupFilterOpen.value && groupFilterContainerRef.value && e && !groupFilterContainerRef.value.contains(e.target as Node)) {
    isGroupFilterOpen.value = false
  }
}

const checkAndApplyTargetChannel = async () => {
  const hashQuery = window.location.hash.includes('?') ? window.location.hash.split('?')[1] : ''
  const urlParams = new URLSearchParams(window.location.search ? window.location.search.slice(1) : hashQuery)
  const queryChannel = urlParams.get('channel') || urlParams.get('site')

  const target = (store.targetChannelSiteName || queryChannel || '').toLowerCase().trim()
  store.targetChannelSiteName = null
  if (target) {
    if (store.relaySites.length === 0) {
      await store.fetchRelaySites()
    }
    const site = store.relaySites.find(
      (s) =>
        s.name.toLowerCase() === target ||
        (s.provider_id && s.provider_id.toLowerCase() === target) ||
        String(s.id) === target
    )
    if (site) {
      await selectProvider(site)
      const queryView = urlParams.get('view')
      if (queryView === 'by-group' || queryView === 'by-model' || queryView === 'flat') {
        detailViewMode.value = queryView
      }
    }
  }
}

onMounted(async () => {
  window.addEventListener('click', closeAllDropdowns)
  await checkAndApplyTargetChannel()
})

watch(
  () => store.targetChannelSiteName,
  async (newVal) => {
    if (newVal) {
      await checkAndApplyTargetChannel()
    }
  }
)

onUnmounted(() => {
  window.removeEventListener('click', closeAllDropdowns)
})

// 向导与弹窗状态
const showWizardModal = ref(false)
const wizardInitialStep = ref(1)
const wizardInitialChannel = ref<any>(null)
const showModal = ref(false)
const isEditing = ref(false)
const isSavingChannel = ref(false)
const showApiKeyPlain = ref(false)
const currentEditId = ref<number | null>(null)
const form = ref({
  name: '',
  base_url: '',
  site_type: 'newapi',
  currency: 'CNY',
  group_name: '',
  recharge_rate: 1.0,
  api_key: '',
  notes: ''
})

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)

// 排序状态
const sortField = ref<string>('score')
const sortOrder = ref<'asc' | 'desc'>('desc')

const openWizardForAdd = () => {
  wizardInitialChannel.value = null
  wizardInitialStep.value = 1
  showWizardModal.value = true
}

const openSyncModalForCurrent = () => {
  wizardInitialChannel.value = selectedProvider.value
  wizardInitialStep.value = 2
  showWizardModal.value = true
}

const openWizardFromEdit = () => {
  const currentSite = store.relaySites.find((s) => s.id === currentEditId.value)
  showModal.value = false
  wizardInitialChannel.value = {
    ...(currentSite || {}),
    id: currentEditId.value,
    ...form.value
  }
  wizardInitialStep.value = 2
  showWizardModal.value = true
}

const handleQuickICloudSync = async () => {
  if (!store.icloudStatus?.icloud_available) {
    store.activeTab = 'settings'
    return
  }
  const res = await store.pushToICloud()
  if (res.success) {
    alert(`✓ 自建渠道商与配置已成功同步到 iCloud Drive`)
  } else {
    alert(`❌ iCloud 同步失败: ${res.error}`)
  }
}

const onWizardSuccess = async (res: any) => {
  await store.fetchRelaySites()
  await store.fetchComparisonMatrix()
  if (selectedProvider.value && selectedProvider.value.id === res.site_id) {
    const updated = store.relaySites.find((s: any) => s.id === res.site_id)
    if (updated) {
      selectedProvider.value = updated
    }
    await selectProvider(selectedProvider.value)
  }
  await store.triggerAutoICloudSyncIfEnabled()
  alert(`🎉 恭喜！中转渠道「${res.site_name}」配置与模型同步成功，已精准收录 ${res.imported_models_count} 款模型！`)
}

// 真正的官方直连母厂 ID 集合 (大模型原创研发母厂一手 API)
const officialLabProviders = new Set([
  'openai',
  'anthropic',
  'deepseek',
  'google',
  'alibaba',
  'moonshotai',
  'zhipuai',
  'meta',
  'mistral',
  'nvidia',
  'cohere',
  'xai',
  'minimax',
  'tencent',
  'bytedance',
  'bytedance-seed',
  'stepfun',
  'baichuan',
  'xiaomi',
  'microsoft',
  'ibm',
  'perplexity',
  'upstage',
  'aisingapore',
  'meituan'
])

// 判定是否属于官方直连 (大模型官方第一手 API 站点)
const isOfficialDirect = (site: RelaySite): boolean => {
  if (!site.is_official_catalog) return false
  const p = (site.provider_id || '').toLowerCase()
  return officialLabProviders.has(p) || (p.startsWith('openai') && !p.includes('compatible')) || (p.startsWith('deepseek') && !p.includes('router'))
}

// 判定是否属于自添加网站 (用户手工添加的自建 NewAPI / OneAPI / Sub2API 站点)
const isCustomSite = (site: RelaySite): boolean => {
  return !site.is_official_catalog || site.site_type === 'newapi' || site.site_type === 'sub2api' || site.site_type === 'custom'
}

// 判定是否属于中转站渠道 (非官方第一手的 API 网站与云端第三方聚合服务商)
const isRelayChannel = (site: RelaySite): boolean => {
  return !isOfficialDirect(site) && !isCustomSite(site)
}

// 业务四大分类 Tab + 收藏夹 (言简意赅，防折行)
const categoryTabs = [
  { id: 'all', name: '全部', iconName: 'site' },
  { id: 'official', name: '官方', iconName: 'shield-check' },
  { id: 'relay', name: '中转', iconName: 'globe' },
  { id: 'custom', name: '自建', iconName: 'settings' },
  { id: 'favorites', name: '收藏', iconName: 'star' }
]

const setCategory = (catId: string) => {
  activeCategory.value = catId
  currentPage.value = 1
}

const getCategoryCount = (catId: string) => {
  if (catId === 'all') return store.relaySites.length
  if (catId === 'official') return store.relaySites.filter(isOfficialDirect).length
  if (catId === 'relay') return store.relaySites.filter(isRelayChannel).length
  if (catId === 'custom') return store.relaySites.filter(isCustomSite).length
  if (catId === 'favorites') return store.relaySites.filter((s) => store.isSiteFavorite(s.id)).length
  return 0
}

const getCategoryLabel = (site: RelaySite) => {
  if (isOfficialDirect(site)) return '官方直连'
  if (isCustomSite(site)) return '自添加网站'
  return '中转站渠道'
}

const getCategoryBadgeClass = (site: RelaySite) => {
  if (isOfficialDirect(site)) {
    return 'bg-[#E8F2FD] text-[#0071E3] border-[#CCE4FB]'
  }
  if (isCustomSite(site)) {
    return 'bg-[#E6F4EA] text-[#137333] border-[#CEEAD6]'
  }
  return 'bg-[#F3E8FF] text-[#9333EA] border-[#E9D5FF]'
}

// 过滤与排序
const filteredAndSortedSites = computed(() => {
  let list = [...store.relaySites]

  if (activeCategory.value === 'official') {
    list = list.filter(isOfficialDirect)
  } else if (activeCategory.value === 'relay') {
    list = list.filter(isRelayChannel)
  } else if (activeCategory.value === 'custom') {
    list = list.filter(isCustomSite)
  } else if (activeCategory.value === 'favorites') {
    list = list.filter((s) => store.isSiteFavorite(s.id))
  }

  if (searchKey.value.trim()) {
    const q = searchKey.value.toLowerCase().trim()
    list = list.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        (s.provider_id && s.provider_id.toLowerCase().includes(q)) ||
        s.base_url.toLowerCase().includes(q)
    )
  }

  // 排序
  list.sort((a: any, b: any) => {
    let valA = a[sortField.value]
    let valB = b[sortField.value]

    if (typeof valA === 'string') {
      return sortOrder.value === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA)
    }
    valA = valA || 0
    valB = valB || 0
    return sortOrder.value === 'asc' ? valA - valB : valB - valA
  })

  return list
})

// 分页计算
const totalItems = computed(() => filteredAndSortedSites.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)))
const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)

const paginatedSites = computed(() => {
  return filteredAndSortedSites.value.slice(startIndex.value, startIndex.value + pageSize.value)
})

// 动态可视页码
const visiblePages = computed(() => {
  const pages: number[] = []
  const max = totalPages.value
  const cur = currentPage.value

  let start = Math.max(1, cur - 2)
  let end = Math.min(max, cur + 2)

  if (end - start < 4) {
    if (start === 1) end = Math.min(max, start + 4)
    else if (end === max) start = Math.max(1, end - 4)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

watch(searchKey, () => {
  currentPage.value = 1
})

const toggleSort = (field: string) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'desc'
  }
  currentPage.value = 1
}

const getSortIndicator = (field: string) => {
  if (sortField.value !== field) return '↕'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

const copyText = (txt: string) => {
  navigator.clipboard.writeText(txt)
}

const toggleSiteActive = async (site: RelaySite) => {
  try {
    site.is_active = !site.is_active
    await axios.put(`${store.apiUrl}/api/v1/channels/${site.id}`, {
      is_active: site.is_active
    })
  } catch (e) {
    console.error('Toggle active failed:', e)
  }
}

// 选中供应商并动态从后端查询该供应商全部模型价格 (解决详情为空的问题)
const selectProvider = async (site: RelaySite) => {
  selectedProvider.value = site
  providerModelSearchQuery.value = ''
  selectedGroupNames.value = []
  groupSearchQuery.value = ''
  isGroupFilterOpen.value = false
  detailViewMode.value = 'flat'
  collapsedGroupKeys.value.clear()
  providerModelsList.value = []
  isDetailLoading.value = true

  try {
    const res = await axios.get(`${store.apiUrl}/api/v1/channels/${site.id}/models`)
    providerModelsList.value = res.data || []
  } catch (e) {
    console.error('Fetch provider models failed:', e)
    providerModelsList.value = store.comparisonMatrix.filter(
      (m) => m.site_name.toLowerCase() === site.name.toLowerCase()
    )
  } finally {
    isDetailLoading.value = false
  }
}

// 视图模式切换与聚合折叠状态
type DetailViewMode = 'flat' | 'by-group' | 'by-model'
const detailViewMode = ref<DetailViewMode>('flat')

// 折叠状态集合 (存储已折叠的 groupName 或 modelKey)
const collapsedGroupKeys = ref<Set<string>>(new Set())

const toggleCollapse = (key: string) => {
  if (collapsedGroupKeys.value.has(key)) {
    collapsedGroupKeys.value.delete(key)
  } else {
    collapsedGroupKeys.value.add(key)
  }
}

const expandAllGroups = () => {
  collapsedGroupKeys.value.clear()
}

const collapseAllGroups = () => {
  if (detailViewMode.value === 'by-group') {
    collapsedGroupKeys.value = new Set(groupedByPricingGroup.value.map((s) => s.groupName))
  } else if (detailViewMode.value === 'by-model') {
    collapsedGroupKeys.value = new Set(groupedByModel.value.map((s) => s.modelKey))
  }
}

// 视图 2：按价格分组聚合数据结构
interface PricingGroupSection {
  groupName: string
  models: any[]
  minInputPrice: number
  maxInputPrice: number
  avgTps: number
}

const groupedByPricingGroup = computed<PricingGroupSection[]>(() => {
  const map = new Map<string, any[]>()
  for (const item of filteredProviderModels.value) {
    const gName = item.group_name || '默认分组 (default)'
    if (!map.has(gName)) {
      map.set(gName, [])
    }
    map.get(gName)!.push(item)
  }

  const sections: PricingGroupSection[] = []
  for (const [groupName, models] of map.entries()) {
    const inputPrices = models.map((m) => m.calculated_input_usd).filter((p) => typeof p === 'number')
    const minInput = inputPrices.length > 0 ? Math.min(...inputPrices) : 0
    const maxInput = inputPrices.length > 0 ? Math.max(...inputPrices) : 0
    const tpsList = models.map((m) => m.last_tested_tps || 50)
    const avgTps = tpsList.length > 0 ? Math.round(tpsList.reduce((a, b) => a + b, 0) / tpsList.length) : 50

    sections.push({
      groupName,
      models,
      minInputPrice: minInput,
      maxInputPrice: maxInput,
      avgTps
    })
  }

  return sections.sort((a, b) => b.models.length - a.models.length || a.groupName.localeCompare(b.groupName))
})

// 视图 3：按模型名称聚合跨组比价数据结构
interface ModelGroupSection {
  modelKey: string
  modelName: string
  modelId: string
  items: any[]
  minInputPrice: number
  maxInputPrice: number
  groupCount: number
}

const groupedByModel = computed<ModelGroupSection[]>(() => {
  const map = new Map<string, any[]>()
  for (const item of filteredProviderModels.value) {
    const key = item.model_id || item.model_name || 'unknown'
    if (!map.has(key)) {
      map.set(key, [])
    }
    map.get(key)!.push(item)
  }

  const sections: ModelGroupSection[] = []
  for (const [modelKey, rawItems] of map.entries()) {
    const items = [...rawItems]
    // 内部按输入单价从低到高升序排列
    items.sort((a, b) => (a.calculated_input_usd || 0) - (b.calculated_input_usd || 0))

    const inputPrices = items.map((m) => m.calculated_input_usd).filter((p) => typeof p === 'number')
    const minInput = inputPrices.length > 0 ? Math.min(...inputPrices) : 0
    const maxInput = inputPrices.length > 0 ? Math.max(...inputPrices) : 0
    const first = items[0]

    sections.push({
      modelKey,
      modelName: first.model_name || first.model_id,
      modelId: first.model_id,
      items,
      minInputPrice: minInput,
      maxInputPrice: maxInput,
      groupCount: items.length
    })
  }

  return sections.sort((a, b) => a.modelName.localeCompare(b.modelName))
})

// 跨组比价溢价与最优标识计算函数
function getModelGroupPriceMeta(item: any, allItems: any[]) {
  const minPrice = allItems.length > 0 ? allItems[0].calculated_input_usd || 0 : 0
  const curPrice = item.calculated_input_usd || 0
  const isLowest = allItems.length > 1 && Math.abs(curPrice - minPrice) < 0.000001
  const isSingle = allItems.length === 1

  let diffText = ''
  let diffPercentText = ''
  if (!isLowest && !isSingle && minPrice > 0) {
    const diff = curPrice - minPrice
    const pct = ((diff / minPrice) * 100).toFixed(1)
    diffText = `+${store.formatCurrency(diff)}`
    diffPercentText = `+${pct}%`
  }

  return {
    isLowest,
    isSingle,
    diffText,
    diffPercentText
  }
}

// 详情页多分组筛选与下拉弹层状态
const selectedGroupNames = ref<string[]>([])
const groupSearchQuery = ref('')
const isGroupFilterOpen = ref(false)
const groupFilterContainerRef = ref<HTMLElement | null>(null)

const detailAvailableGroups = computed(() => {
  const map = new Map<string, number>()
  for (const m of providerModelsList.value) {
    if (m.group_name) {
      map.set(m.group_name, (map.get(m.group_name) || 0) + 1)
    }
  }
  return Array.from(map.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
})

const searchedAvailableGroups = computed(() => {
  if (!groupSearchQuery.value.trim()) return detailAvailableGroups.value
  const q = groupSearchQuery.value.toLowerCase().trim()
  return detailAvailableGroups.value.filter((g) => g.name.toLowerCase().includes(q))
})

const isAllGroupsSelected = computed(() => {
  return (
    selectedGroupNames.value.length === 0 ||
    (detailAvailableGroups.value.length > 0 && selectedGroupNames.value.length === detailAvailableGroups.value.length)
  )
})

const isGroupFilterActive = computed(() => {
  return selectedGroupNames.value.length > 0 && selectedGroupNames.value.length < detailAvailableGroups.value.length
})

const groupFilterSummaryLabel = computed(() => {
  if (selectedGroupNames.value.length === 0 || selectedGroupNames.value.length === detailAvailableGroups.value.length) {
    return `价格分组: 全部 (${detailAvailableGroups.value.length})`
  }
  if (selectedGroupNames.value.length === 1) {
    return `分组: ${selectedGroupNames.value[0]}`
  }
  return `已选 ${selectedGroupNames.value.length} 个分组`
})

const toggleGroupFilterPopover = () => {
  isGroupFilterOpen.value = !isGroupFilterOpen.value
}

const toggleGroupSelection = (gName: string) => {
  if (selectedGroupNames.value.includes(gName)) {
    selectedGroupNames.value = selectedGroupNames.value.filter((g) => g !== gName)
  } else {
    selectedGroupNames.value.push(gName)
    if (selectedGroupNames.value.length === detailAvailableGroups.value.length) {
      selectedGroupNames.value = []
    }
  }
}

const toggleAllGroupsOption = () => {
  selectedGroupNames.value = []
}

const selectAllGroups = () => {
  selectedGroupNames.value = []
}

const clearGroupFilter = () => {
  selectedGroupNames.value = []
}

// 详情页单条定价删除
const removeModelPricing = async (item: any) => {
  if (!selectedProvider.value) return
  if (!confirm(`确定要将模型 "${item.model_name || item.model_id}" (${item.group_name ? `分组: ${item.group_name}` : '默认分组'}) 从该渠道中移除吗？`)) return
  try {
    await axios.delete(`${store.apiUrl}/api/v1/channels/${selectedProvider.value.id}/pricings/${item.id}`)
    providerModelsList.value = providerModelsList.value.filter((m: any) => m.id !== item.id)
    await store.fetchRelaySites()
    await store.fetchComparisonMatrix()
  } catch (e: any) {
    alert(`移除失败: ${e.message}`)
  }
}

// 详情页表格排序状态
const detailSortField = ref<string>('calculated_input_usd')
const detailSortOrder = ref<'asc' | 'desc'>('asc')

const toggleDetailSort = (field: string) => {
  if (detailSortField.value === field) {
    detailSortOrder.value = detailSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    detailSortField.value = field
    detailSortOrder.value = field === 'last_tested_tps' || field === 'context_window' || field === 'max_output' ? 'desc' : 'asc'
  }
}

const getDetailSortIndicator = (field: string) => {
  if (detailSortField.value !== field) return '↕'
  return detailSortOrder.value === 'asc' ? '↑' : '↓'
}

const filteredProviderModels = computed(() => {
  let list = [...providerModelsList.value]

  // 1. 分组多选过滤
  if (selectedGroupNames.value.length > 0 && selectedGroupNames.value.length < detailAvailableGroups.value.length) {
    list = list.filter((m: any) => selectedGroupNames.value.includes(m.group_name))
  }

  // 2. 搜索过滤
  if (providerModelSearchQuery.value.trim()) {
    const q = providerModelSearchQuery.value.toLowerCase().trim()
    list = list.filter(
      (m: any) =>
        (m.model_name && m.model_name.toLowerCase().includes(q)) ||
        (m.model_id && m.model_id.toLowerCase().includes(q)) ||
        (m.site_model_name && m.site_model_name.toLowerCase().includes(q)) ||
        (m.group_name && m.group_name.toLowerCase().includes(q))
    )
  }

  list.sort((a: any, b: any) => {
    let valA = a[detailSortField.value]
    let valB = b[detailSortField.value]

    if (detailSortField.value === 'model_name') {
      const nameA = a.model_name || a.model_id || ''
      const nameB = b.model_name || b.model_id || ''
      return detailSortOrder.value === 'asc' ? nameA.localeCompare(nameB) : nameB.localeCompare(nameA)
    }

    valA = valA !== undefined && valA !== null ? valA : 0
    valB = valB !== undefined && valB !== null ? valB : 0
    return detailSortOrder.value === 'asc' ? valA - valB : valB - valA
  })

  return list
})

const formatContextWindow = (ctx?: number) => {
  if (!ctx) return '128,000'
  return Number(ctx).toLocaleString()
}

const isReasoningModel = (modelId: string) => {
  const m = (modelId || '').toLowerCase()
  return m.includes('r1') || m.includes('reasoner') || m.includes('thinking') || m.includes('o1') || m.includes('o3')
}

const goToMatrixWithSite = (siteId: number) => {
  const site = store.relaySites.find((s) => s.id === siteId)
  store.navigateToPriceMatrix({ siteId, siteName: site?.name })
}

const goToSpeedTestWithSite = (siteId: number) => {
  store.navigateToSpeedTest(siteId)
}

const goToMatrixWithModel = (modelId: string) => {
  store.navigateToPriceMatrix({
    modelId: modelId,
    highlightSiteName: selectedProvider.value?.name
  })
}

const goToSpeedTestWithModel = (modelId: string) => {
  store.navigateToSpeedTest(selectedProvider.value?.id, modelId)
}

const openEditModal = (site: RelaySite) => {
  isEditing.value = true
  currentEditId.value = site.id
  showApiKeyPlain.value = false
  form.value = {
    name: site.name || '',
    base_url: site.base_url || '',
    site_type: site.site_type || 'newapi',
    currency: site.currency || 'CNY',
    group_name: site.group_name || '',
    recharge_rate: site.recharge_rate ?? 1.0,
    api_key: site.api_key || '',
    notes: site.notes || ''
  }
  showModal.value = true
}

const saveChannel = async () => {
  if (!form.value.name.trim() || !form.value.base_url.trim()) {
    alert('站点名称与 API 基础端点地址为必填项！')
    return
  }
  isSavingChannel.value = true
  try {
    if (isEditing.value && currentEditId.value) {
      await axios.put(`${store.apiUrl}/api/v1/channels/${currentEditId.value}`, form.value)
    } else {
      await axios.post(`${store.apiUrl}/api/v1/channels`, form.value)
    }
    await store.fetchRelaySites()
    await store.fetchComparisonMatrix()
    if (selectedProvider.value && selectedProvider.value.id === currentEditId.value) {
      const updated = store.relaySites.find((s: any) => s.id === currentEditId.value)
      if (updated) {
        selectedProvider.value = updated
      }
    }
    showModal.value = false
    await store.triggerAutoICloudSyncIfEnabled()
  } catch (e: any) {
    alert(`保存失败: ${e.response?.data?.detail || e.message}`)
    console.error('Save channel failed:', e)
  } finally {
    isSavingChannel.value = false
  }
}

const deleteSite = async (siteId: number) => {
  if (!confirm('确定要删除该自添加网站吗？')) return
  try {
    await axios.delete(`${store.apiUrl}/api/v1/channels/${siteId}`)
    await store.fetchRelaySites()
    selectedProvider.value = null
    await store.triggerAutoICloudSyncIfEnabled()
  } catch (e) {
    console.error('Delete site failed:', e)
  }
}

// 渠道数据最后更新时间与来源标识计算
const getChannelUpdateSourceType = (site: RelaySite | null): string => {
  if (!site) return 'm'
  return site.is_official_catalog ? 'm' : 'c'
}

const getChannelUpdateTimeRaw = (site: RelaySite | null): string => {
  if (!site) return ''
  if (providerModelsList.value && providerModelsList.value.length > 0) {
    const times = providerModelsList.value
      .map((m: any) => m.source_updated_at || m.updated_at || '')
      .filter((t: string) => !!t)
    if (times.length > 0) {
      times.sort().reverse()
      return times[0]
    }
  }
  if (site.last_sync_time) {
    return typeof site.last_sync_time === 'string' ? site.last_sync_time : new Date(site.last_sync_time).toISOString()
  }
  if (site.updated_at) {
    return typeof site.updated_at === 'string' ? site.updated_at : new Date(site.updated_at).toISOString()
  }
  return ''
}

const getChannelRelativeUpdateTime = (site: RelaySite | null): string => {
  const raw = getChannelUpdateTimeRaw(site)
  if (!raw) return '刚刚'
  return formatRelativeTime(raw)
}

const getChannelShortUpdateTime = (site: RelaySite | null): string => {
  const raw = getChannelUpdateTimeRaw(site)
  if (!raw) return ''
  try {
    const d = parseUtcDate(raw)
    if (!d) return raw.slice(0, 10)
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `(${m}-${day} ${h}:${min})`
  } catch {
    return ''
  }
}

const getChannelFullUpdateTime = (site: RelaySite | null): string => {
  if (!site) return ''
  const raw = getChannelUpdateTimeRaw(site)
  const isModelsDev = getChannelUpdateSourceType(site) === 'm'
  const sourceLabel = isModelsDev ? 'models.dev 官方平台原始时间' : '自建/中转渠道最后同步时间'
  return raw ? `数据源: ${sourceLabel}\n完整时间: ${raw}` : `数据源: ${sourceLabel}`
}
</script>

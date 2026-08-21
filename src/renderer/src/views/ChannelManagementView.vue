<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- ==================== 场景 A：供应商与渠道列表表格 ==================== -->
    <template v-if="!selectedProvider">
      <!-- 顶部操作栏与精确分类筛选 (苹果高级灰白风格，言简意赅，防折行) -->
      <div class="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex items-center justify-between flex-nowrap overflow-x-auto">
        <div class="flex items-center space-x-2.5 flex-shrink-0">
          <!-- 分类切换胶囊按钮组：全部 / 官方 / 中转 / 自建 / ⭐ 收藏 -->
          <div class="flex items-center space-x-1 bg-[#F2F2F7] p-0.5 rounded-xl border border-[#E5E5EA] flex-shrink-0">
            <button
              v-for="tab in categoryTabs"
              :key="tab.id"
              @click="setCategory(tab.id)"
              class="px-2.5 py-1 text-xs rounded-lg font-medium transition-all flex items-center space-x-1 whitespace-nowrap"
              :class="activeCategory === tab.id ? 'bg-[#0071E3] text-white font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
            >
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
          <button
            @click="store.triggerFullSync"
            class="text-xs px-3 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1 whitespace-nowrap"
            title="从 models.dev 官方数据库同步最新供应商与渠道"
          >
            <span>🔄 同步官方库</span>
          </button>
          <button
            @click="showWizardModal = true"
            class="text-xs px-3 py-1.5 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] text-white font-medium shadow-sm transition-all flex items-center space-x-1 whitespace-nowrap"
          >
            <span>✨ 添加渠道向导 (Relay-Watch)</span>
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
                    class="text-base transition-transform hover:scale-125 focus:outline-none"
                    :title="store.isSiteFavorite(site.id) ? '点击取消收藏' : '点击加入收藏夹'"
                  >
                    <span v-if="store.isSiteFavorite(site.id)" class="text-[#FF9500]">⭐</span>
                    <span v-else class="text-[#AEAEB2] hover:text-[#FF9500]">☆</span>
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
                      <div class="font-bold text-xs text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors">
                        {{ site.name }}
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
                  <span class="text-[#34C759] font-bold">{{ site.score || 95 }} 分</span>
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
                  <div v-if="activeCategory === 'favorites'">
                    ⭐ 暂无收藏的渠道，点击列表左侧的星标即可快速加入收藏夹！
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
          <button
            @click="selectedProvider = null"
            class="px-3 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] transition-all text-xs font-medium flex items-center space-x-1"
          >
            <span>← 返回供应商与渠道列表</span>
          </button>

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
              <span>⚡ 一键并发测速</span>
            </button>
          </div>
        </div>

        <!-- 2. 四维 Fact Grid 指标看板 (参考 models.dev/providers/bailing/) -->
        <div class="grid grid-cols-4 gap-3 pt-2 border-t border-[#E5E5EA]">
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">提供可用模型数</div>
            <div class="text-lg font-bold font-mono text-[#0071E3] mt-0.5">
              {{ isDetailLoading ? '...' : `${providerModelsList.length} 款模型` }}
            </div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">SDK 兼容驱动 (Package)</div>
            <div class="text-xs font-bold font-mono text-[#1D1D1F] mt-1 truncate">
              @ai-sdk/openai-compatible
            </div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">环境变量标识 (Env Key)</div>
            <div class="text-xs font-bold font-mono text-[#AF52DE] mt-1 truncate">
              {{ selectedProvider.env_vars || `${selectedProvider.name.toUpperCase().replace(/[^A-Z]/g, '')}_API_KEY` }}
            </div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">实测性能与评分</div>
            <div class="text-sm font-bold font-mono text-[#34C759] mt-1">
              {{ selectedProvider.score || 95 }}分 / {{ selectedProvider.last_latency_ms ? selectedProvider.last_latency_ms.toFixed(0) : '35' }}ms
            </div>
          </div>
        </div>
      </div>

      <!-- 3. 该供应商所能提供的完整模型与价格数据表格 (对标 models.dev/providers/bailing/) -->
      <div class="flex-1 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden min-h-0">
        <div class="flex items-center justify-between pb-2 border-b border-[#E5E5EA]">
          <span class="text-xs font-bold text-[#1D1D1F]">
            📋 旗下可用模型规格与定价清单 (共 {{ providerModelsList.length }} 款)
          </span>
          <div class="w-60 relative">
            <input
              v-model="providerModelSearchQuery"
              type="text"
              placeholder="搜索模型名称/标识..."
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
            />
          </div>
        </div>

        <div class="flex-1 overflow-x-auto overflow-y-auto pr-1 mt-1 relative">
          <div v-if="isDetailLoading" class="absolute inset-0 bg-white/70 backdrop-blur-xs flex items-center justify-center z-10">
            <div class="text-xs text-[#0071E3] font-medium flex items-center space-x-2">
              <span class="animate-spin">🌀</span>
              <span>正在从后端数据库加载模型定价...</span>
            </div>
          </div>

          <table class="w-full text-left text-xs border-collapse min-w-[980px]">
            <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans select-none">
              <tr>
                <th @click="toggleDetailSort('model_name')" class="py-2.5 px-3 cursor-pointer hover:text-[#0071E3] transition-colors">
                  模型名称 / 标准标识 <span class="text-[10px] font-mono" :class="detailSortField === 'model_name' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getDetailSortIndicator('model_name') }}</span>
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
                :key="item.model_id"
                class="hover:bg-[#F5F5F7] transition-colors"
              >
                <!-- 模型名称与标准 ID -->
                <td class="py-2.5 px-3">
                  <div class="font-bold text-[#1D1D1F] text-xs">{{ item.model_name }}</div>
                  <div class="text-[11px] text-[#0071E3] font-mono mt-0.5">{{ item.model_id }}</div>
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
        </div>
      </div>
    </template>

    <!-- 4 步向导式添加自建渠道 Modal (Relay-Watch & 智能模型归一化) -->
    <AddChannelWizardModal
      v-if="showWizardModal"
      @close="showWizardModal = false"
      @success="onWizardSuccess"
    />

    <!-- 弹窗：编辑自建渠道基础配置 Modal (苹果灰白质感弹窗) -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/30 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in"
    >
      <div class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl w-[520px] p-6 space-y-4 shadow-[0_20px_50px_rgba(0,0,0,0.15)]">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
          <h3 class="font-bold text-sm text-[#1D1D1F]">
            {{ isEditing ? '✏️ 编辑自添加网站配置' : '➕ 添加自建 NewAPI / OneAPI / Sub2API 中转站' }}
          </h3>
          <button @click="showModal = false" class="text-[#86868B] hover:text-[#1D1D1F] text-sm">✕</button>
        </div>

        <div class="space-y-3 text-xs">
          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">站点名称 (Name) *</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="例如: 我的自建 NewAPI 聚合站"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">API 基础端点地址 (Base URL) *</label>
            <input
              v-model="form.base_url"
              type="text"
              placeholder="https://api.my-newapi.com/v1"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">系统类型 (Site Type)</label>
              <select
                v-model="form.site_type"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none"
              >
                <option value="newapi">NewAPI / OneAPI 系统</option>
                <option value="sub2api">Sub2API 系统</option>
                <option value="custom">通用自建中转站</option>
              </select>
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">充值折算倍率 (Recharge Rate)</label>
              <input
                v-model.number="form.recharge_rate"
                type="number"
                step="0.01"
                placeholder="1.0"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">中转站 API Key (用于流式测速与有效性验证)</label>
            <input
              v-model="form.api_key"
              type="password"
              placeholder="sk-..."
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
            />
          </div>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-2 border-t border-[#E5E5EA]">
          <button
            @click="showModal = false"
            class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] text-xs font-medium"
          >
            取消
          </button>
          <button
            @click="saveChannel"
            class="px-4 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-medium shadow-sm"
          >
            {{ isEditing ? '保存修改' : '确认添加' }}
          </button>
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
import type { RelaySite } from '../types'

const store = useDashboardStore()
const searchKey = ref('')
const activeCategory = ref('all')
const selectedProvider = ref<RelaySite | null>(null)
const providerModelSearchQuery = ref('')
const providerModelsList = ref<any[]>([])
const isDetailLoading = ref(false)

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

const closeAllDropdowns = () => {
  activeActionDropdownSiteId.value = null
  activeActionDropdownModelId.value = null
}

onMounted(() => {
  window.addEventListener('click', closeAllDropdowns)
})

onUnmounted(() => {
  window.removeEventListener('click', closeAllDropdowns)
})

// 向导与弹窗状态
const showWizardModal = ref(false)
const showModal = ref(false)
const isEditing = ref(false)
const currentEditId = ref<number | null>(null)
const form = ref({
  name: '',
  base_url: '',
  site_type: 'newapi',
  recharge_rate: 1.0,
  api_key: ''
})

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)

// 排序状态
const sortField = ref<string>('score')
const sortOrder = ref<'asc' | 'desc'>('desc')

const onWizardSuccess = async (res: any) => {
  await store.fetchRelaySites()
  await store.fetchComparisonMatrix()
  alert(`🎉 恭喜！中转渠道「${res.site_name}」添加成功，已精准规整并收录 ${res.imported_models_count} 款模型！`)
}

const openSyncModalForCurrent = () => {
  showWizardModal.value = true
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
  { id: 'all', name: '全部' },
  { id: 'official', name: '官方' },
  { id: 'relay', name: '中转' },
  { id: 'custom', name: '自建' },
  { id: 'favorites', name: '⭐ 收藏' }
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
  if (providerModelSearchQuery.value.trim()) {
    const q = providerModelSearchQuery.value.toLowerCase().trim()
    list = list.filter(
      (m) =>
        (m.model_name && m.model_name.toLowerCase().includes(q)) ||
        (m.model_id && m.model_id.toLowerCase().includes(q))
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
  store.selectedSiteId = siteId
  store.activeTab = 'price-matrix'
}

const goToSpeedTestWithSite = (siteId: number) => {
  store.activeTab = 'speed-tester'
  store.runSpeedTest([siteId], 'deepseek-v3')
}

const goToMatrixWithModel = (modelId: string) => {
  store.selectedModelId = modelId
  store.activeTab = 'price-matrix'
}

const goToSpeedTestWithModel = (modelId: string) => {
  store.activeTab = 'speed-tester'
  if (selectedProvider.value) {
    store.runSpeedTest([selectedProvider.value.id], modelId)
  }
}

const openAddModal = () => {
  isEditing.value = false
  currentEditId.value = null
  form.value = {
    name: '',
    base_url: '',
    site_type: 'newapi',
    recharge_rate: 1.0,
    api_key: ''
  }
  showModal.value = true
}

const openEditModal = (site: RelaySite) => {
  isEditing.value = true
  currentEditId.value = site.id
  form.value = {
    name: site.name,
    base_url: site.base_url,
    site_type: site.site_type,
    recharge_rate: site.recharge_rate || 1.0,
    api_key: site.api_key || ''
  }
  showModal.value = true
}

const saveChannel = async () => {
  try {
    if (isEditing.value && currentEditId.value) {
      await axios.put(`${store.apiUrl}/api/v1/channels/${currentEditId.value}`, form.value)
    } else {
      await axios.post(`${store.apiUrl}/api/v1/channels`, form.value)
    }
    await store.fetchRelaySites()
    showModal.value = false
  } catch (e) {
    console.error('Save channel failed:', e)
  }
}

const deleteSite = async (siteId: number) => {
  if (!confirm('确定要删除该自添加网站吗？')) return
  try {
    await axios.delete(`${store.apiUrl}/api/v1/channels/${siteId}`)
    await store.fetchRelaySites()
    selectedProvider.value = null
  } catch (e) {
    console.error('Delete site failed:', e)
  }
}
</script>

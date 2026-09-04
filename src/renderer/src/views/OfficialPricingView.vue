<template>
  <div class="h-full flex flex-col space-y-2.5 overflow-hidden select-none">
    <!-- 顶部四级多维筛选与控制面板 (苹果灰白精致卡片) -->
    <div class="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-2.5 flex-shrink-0">
      <!-- 第一行：多维可搜索筛选器 -->
      <div class="flex items-center justify-between flex-wrap gap-2">
        <div class="flex items-center flex-wrap gap-2">
          <!-- 1. 模型厂商多选下拉 -->
          <div class="relative" ref="providerDropdownRef">
            <button
              @click="isProviderDropdownOpen = !isProviderDropdownOpen"
              class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1.5 cursor-pointer shadow-2xs group"
              :class="store.selectedProviders.length > 0
                ? 'bg-[#E8F2FD] border-[#0071E3] text-[#0071E3] font-bold shadow-xs'
                : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
            >
              <SystemIcon name="provider" custom-class="w-3.5 h-3.5" :class="store.selectedProviders.length > 0 ? 'text-[#0071E3]' : 'text-[#86868B]'" />
              <span>模型厂商</span>
              <span v-if="store.selectedProviders.length > 0" class="px-1.5 py-0.2 rounded-full text-[10px] bg-[#0071E3] text-white">
                {{ store.selectedProviders.length }}
              </span>
              <span class="text-[10px] opacity-60">▾</span>
            </button>

            <!-- 下拉内容 -->
            <div
              v-if="isProviderDropdownOpen"
              class="absolute left-0 top-10 w-64 bg-white border border-[#E5E5EA] rounded-2xl shadow-xl z-40 p-2.5 space-y-2 animate-fade-in text-xs"
            >
              <div class="flex items-center justify-between pb-1.5 border-b border-[#E5E5EA]">
                <span class="font-bold text-[#1D1D1F]">筛选官方厂商</span>
                <button
                  v-if="store.selectedProviders.length > 0"
                  @click="store.selectedProviders = []"
                  class="text-[11px] text-[#FF3B30] hover:underline cursor-pointer"
                >
                  清空
                </button>
              </div>
              <div class="max-h-48 overflow-y-auto space-y-1">
                <div
                  v-for="p in store.providersList"
                  :key="p.code"
                  @click="toggleProvider(p.code)"
                  class="flex items-center justify-between p-1.5 rounded-lg hover:bg-[#F2F2F7] cursor-pointer"
                >
                  <span :class="store.selectedProviders.includes(p.code) ? 'text-[#0071E3] font-bold' : 'text-[#1D1D1F]'">
                    {{ p.name }}
                  </span>
                  <span v-if="store.selectedProviders.includes(p.code)" class="text-[#0071E3] font-bold">✓</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 2. 模型系列下拉 -->
          <div class="relative" ref="seriesDropdownRef">
            <button
              @click="isSeriesDropdownOpen = !isSeriesDropdownOpen"
              class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1.5 cursor-pointer shadow-2xs group"
              :class="store.selectedSeries.length > 0
                ? 'bg-[#E8F2FD] border-[#0071E3] text-[#0071E3] font-bold shadow-xs'
                : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
            >
              <SystemIcon name="series" custom-class="w-3.5 h-3.5" :class="store.selectedSeries.length > 0 ? 'text-[#0071E3]' : 'text-[#86868B]'" />
              <span>模型系列</span>
              <span v-if="store.selectedSeries.length > 0" class="px-1.5 py-0.2 rounded-full text-[10px] bg-[#0071E3] text-white">
                {{ store.selectedSeries.length }}
              </span>
              <span class="text-[10px] opacity-60">▾</span>
            </button>

            <!-- 下拉内容 -->
            <div
              v-if="isSeriesDropdownOpen"
              class="absolute left-0 top-10 w-64 bg-white border border-[#E5E5EA] rounded-2xl shadow-xl z-40 p-2.5 space-y-2 animate-fade-in text-xs"
            >
              <div class="flex items-center justify-between pb-1.5 border-b border-[#E5E5EA]">
                <span class="font-bold text-[#1D1D1F]">筛选模型系列</span>
                <button
                  v-if="store.selectedSeries.length > 0"
                  @click="store.selectedSeries = []"
                  class="text-[11px] text-[#FF3B30] hover:underline cursor-pointer"
                >
                  清空
                </button>
              </div>
              <div class="max-h-48 overflow-y-auto space-y-1">
                <div
                  v-for="s in filteredSeriesOptions"
                  :key="s.series"
                  @click="toggleSeries(s.series)"
                  class="flex items-center justify-between p-1.5 rounded-lg hover:bg-[#F2F2F7] cursor-pointer"
                >
                  <span :class="store.selectedSeries.includes(s.series) ? 'text-[#0071E3] font-bold' : 'text-[#1D1D1F]'">
                    {{ s.series }}
                  </span>
                  <span v-if="store.selectedSeries.includes(s.series)" class="text-[#0071E3] font-bold">✓</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 3. 计费模式筛选胶囊 -->
          <div class="flex items-center bg-[#F2F2F7] rounded-xl p-0.5 border border-[#E5E5EA] text-xs">
            <button
              v-for="mode in billingModes"
              :key="mode.id"
              @click="store.selectedBillingMode = mode.id"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium"
              :class="store.selectedBillingMode === mode.id
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
            >
              {{ mode.label }}
            </button>
          </div>

          <!-- 4. 关键字搜索输入框 -->
          <div class="relative w-56">
            <input
              type="text"
              v-model="store.searchKeyword"
              placeholder="搜索模型、阶梯、备注或标签..."
              class="w-full pl-7 pr-7 py-1.5 bg-[#F2F2F7] border border-[#E5E5EA] rounded-xl text-xs text-[#1D1D1F] focus:bg-white focus:border-[#0071E3] focus:outline-none transition-all placeholder:text-[#86868B]"
            />
            <span class="absolute left-2.5 top-2 text-[#86868B] text-xs">🔍</span>
            <button
              v-if="store.searchKeyword"
              @click="store.searchKeyword = ''"
              class="absolute right-2 top-1.5 text-xs text-[#86868B] hover:text-[#1D1D1F] cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- 右侧快速操作按钮组 -->
        <div class="flex items-center space-x-2">
          <!-- 币种模式切换器 -->
          <div class="flex items-center bg-[#F2F2F7] rounded-xl p-0.5 border border-[#E5E5EA] text-xs">
            <button
              @click="store.setCurrencyMode('original')"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium"
              :class="store.currencyMode === 'original'
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
              title="按官网原标价展示（国外采用美元 $，国内采用人民币 ¥）"
            >
              原币种 ($/¥)
            </button>
            <button
              @click="store.setCurrencyMode('cny')"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium"
              :class="store.currencyMode === 'cny'
                ? 'bg-white text-[#34C759] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
              :title="`基于系统实时汇率 (1 USD ≈ ¥${store.usdToCnyRate}) 统一折合人民币`"
            >
              折合人民币 ¥
            </button>
            <button
              @click="store.setCurrencyMode('usd')"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium"
              :class="store.currencyMode === 'usd'
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
              :title="`基于系统实时汇率 (1 USD ≈ ¥${store.usdToCnyRate}) 统一折合美元`"
            >
              折合美元 $
            </button>
          </div>

          <!-- 自定义列按钮 -->
          <button
            @click="isColModalVisible = true"
            class="px-3 py-1.5 rounded-xl border border-[#E5E5EA] bg-white hover:bg-[#F2F2F7] text-xs text-[#48484A] hover:text-[#1D1D1F] flex items-center space-x-1.5 transition-all shadow-2xs cursor-pointer"
            title="自定义选择表格显隐列"
          >
            <span>列配置</span>
            <span class="text-[10px] opacity-70">⚙</span>
          </button>

          <!-- 导出 Excel 按钮 -->
          <button
            @click="store.exportToExcel"
            class="px-3 py-1.5 rounded-xl border border-[#34C759]/30 bg-[#E8F8EE] hover:bg-[#D5F2DE] text-xs font-bold text-[#34C759] flex items-center space-x-1.5 transition-all shadow-2xs cursor-pointer whitespace-nowrap"
            title="导出当前筛选与列配置后的官方模型价格表 (.xlsx)"
          >
            <span>导出 Excel</span>
            <SystemIcon name="download" custom-class="w-3 h-3" />
          </button>
        </div>
      </div>

      <!-- 第二行：视图模式切换器 + 展开/折叠 + 汇总状态指示 -->
      <div class="flex items-center justify-between pt-1 border-t border-[#E5E5EA]/70 text-xs">
        <div class="flex items-center space-x-2.5">
          <!-- 视图模式胶囊切换 -->
          <div class="flex items-center bg-[#F2F2F7] rounded-xl p-0.5 border border-[#E5E5EA]">
            <button
              @click="store.setViewMode('flat')"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium flex items-center space-x-1 whitespace-nowrap flex-shrink-0"
              :class="store.viewMode === 'flat'
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
            >
              <span>平铺</span>
            </button>
            <button
              @click="store.setViewMode('group-vendor')"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium flex items-center space-x-1 whitespace-nowrap flex-shrink-0"
              :class="store.viewMode === 'group-vendor'
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
            >
              <SystemIcon name="provider" custom-class="w-3 h-3" />
              <span>按厂商</span>
            </button>
            <button
              @click="store.setViewMode('group-series')"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium flex items-center space-x-1 whitespace-nowrap flex-shrink-0"
              :class="store.viewMode === 'group-series'
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
            >
              <SystemIcon name="series" custom-class="w-3 h-3" />
              <span>按系列</span>
            </button>
            <button
              @click="store.setViewMode('tree')"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium flex items-center space-x-1 whitespace-nowrap flex-shrink-0"
              :class="store.viewMode === 'tree'
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
            >
              <SystemIcon name="tree" custom-class="w-3 h-3" />
              <span>树形</span>
            </button>
          </div>

          <!-- 分组模式下的一键展开/折叠按钮 -->
          <div v-if="store.viewMode !== 'flat'" class="flex items-center space-x-1.5 flex-shrink-0">
            <button
              @click="store.expandAll"
              class="px-2 py-1 rounded-lg border border-[#E5E5EA] bg-white hover:bg-[#F2F2F7] text-[11px] text-[#6E6E73] hover:text-[#1D1D1F] transition-all cursor-pointer whitespace-nowrap"
            >
              展开
            </button>
            <button
              @click="store.collapseAll"
              class="px-2 py-1 rounded-lg border border-[#E5E5EA] bg-white hover:bg-[#F2F2F7] text-[11px] text-[#6E6E73] hover:text-[#1D1D1F] transition-all cursor-pointer whitespace-nowrap"
            >
              收起
            </button>
          </div>
        </div>

        <!-- 统计指标（精要不换行，不显示参考汇率） -->
        <div class="flex items-center space-x-3 text-[11px] text-[#86868B] font-mono whitespace-nowrap flex-shrink-0">
          <span>
            共 <strong class="text-[#0071E3] font-bold">{{ store.filteredModels.length }}</strong><span v-if="store.filteredModels.length !== store.allModels.length"> / {{ store.allModels.length }}</span> 条
          </span>
          <span class="text-[#D1D1D6]">•</span>
          <span class="text-[#34C759] font-medium flex items-center space-x-1">
            <span class="w-1.5 h-1.5 rounded-full bg-[#34C759]"></span>
            <span>{{ store.snapshots.length }} 份快照</span>
          </span>
        </div>
      </div>
    </div>

    <!-- 主表格展示区 (支持长列表滚动，无分页全部展示) -->
    <div class="flex-1 bg-white rounded-2xl border border-[#E5E5EA] shadow-2xs overflow-hidden flex flex-col min-h-0">
      <div class="flex-1 overflow-auto">
        <table class="w-full border-collapse text-left text-xs select-text">
          <!-- 表头 -->
          <thead class="sticky top-0 z-20 bg-[#FBFBFD] border-b border-[#E5E5EA] select-none shadow-2xs">
            <tr>
              <th
                v-if="store.visibleColumns.provider_name"
                @click="store.toggleSort('provider_name')"
                class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap cursor-pointer select-none hover:text-[#0071E3] hover:bg-[#F2F2F7] transition-all group"
                title="点击按模型厂商排序 (升序 ➔ 降序 ➔ 默认)"
              >
                <div class="flex items-center space-x-1">
                  <span>模型厂商</span>
                  <span class="text-[10px]" :class="store.sortField === 'provider_name' ? 'text-[#0071E3] font-bold' : 'text-[#86868B] opacity-40 group-hover:opacity-100'">
                    {{ store.sortField === 'provider_name' ? (store.sortOrder === 'asc' ? '▲' : '▼') : '⇅' }}
                  </span>
                </div>
              </th>

              <th
                v-if="store.visibleColumns.series"
                @click="store.toggleSort('series')"
                class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap cursor-pointer select-none hover:text-[#0071E3] hover:bg-[#F2F2F7] transition-all group"
                title="点击按模型系列排序 (升序 ➔ 降序 ➔ 默认)"
              >
                <div class="flex items-center space-x-1">
                  <span>模型系列</span>
                  <span class="text-[10px]" :class="store.sortField === 'series' ? 'text-[#0071E3] font-bold' : 'text-[#86868B] opacity-40 group-hover:opacity-100'">
                    {{ store.sortField === 'series' ? (store.sortOrder === 'asc' ? '▲' : '▼') : '⇅' }}
                  </span>
                </div>
              </th>

              <th
                v-if="store.visibleColumns.model_name"
                @click="store.toggleSort('model_name')"
                class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap min-w-[200px] cursor-pointer select-none hover:text-[#0071E3] hover:bg-[#F2F2F7] transition-all group"
                title="点击按模型规格/阶梯名排序 (升序 ➔ 降序 ➔ 默认)"
              >
                <div class="flex items-center space-x-1">
                  <span>模型规格 / 阶梯名</span>
                  <span class="text-[10px]" :class="store.sortField === 'model_name' ? 'text-[#0071E3] font-bold' : 'text-[#86868B] opacity-40 group-hover:opacity-100'">
                    {{ store.sortField === 'model_name' ? (store.sortOrder === 'asc' ? '▲' : '▼') : '⇅' }}
                  </span>
                </div>
              </th>
              <th v-if="store.visibleColumns.billing_mode" class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap">计费模式</th>
              <th v-if="store.visibleColumns.input_price" class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap text-right">输入单价 (1M)</th>
              <th v-if="store.visibleColumns.output_price" class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap text-right">输出单价 (1M)</th>
              <th v-if="store.visibleColumns.cache_read_price" class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap text-right">缓存读/命中 (1M)</th>
              <th v-if="store.visibleColumns.cache_write_price" class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap text-right">缓存写 (1M)</th>
              <th v-if="store.visibleColumns.remarks" class="py-2.5 px-3 font-bold text-[#1D1D1F] min-w-[180px]">官方备注</th>
              <th v-if="store.visibleColumns.custom_notes" class="py-2.5 px-3 font-bold text-[#1D1D1F] min-w-[150px]">用户自定义备注 / 标签</th>
              <th v-if="store.visibleColumns.price_date" class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap">价格生效时间</th>
              <th v-if="store.visibleColumns.source_anchor" class="py-2.5 px-3 font-bold text-[#1D1D1F] whitespace-nowrap text-center">来源与快照</th>
            </tr>
          </thead>

          <!-- 模式 1：平铺表格 (Flat Table) -->
          <tbody v-if="store.viewMode === 'flat'" class="divide-y divide-[#E5E5EA]/70 font-sans">
            <tr
              v-for="item in store.filteredModels"
              :key="item.id"
              class="hover:bg-[#F9FAFC] transition-colors group"
            >
              <td v-if="store.visibleColumns.provider_name" class="py-2 px-3 whitespace-nowrap">
                <span class="px-2 py-0.5 rounded-md text-[11px] font-bold" :class="getProviderBadgeClass(item.provider)">
                  {{ item.provider_name }}
                </span>
              </td>

              <td v-if="store.visibleColumns.series" class="py-2 px-3 font-mono text-[11px] text-[#6E6E73] whitespace-nowrap">
                {{ item.series }}
              </td>

              <td v-if="store.visibleColumns.model_name" class="py-2 px-3">
                <div class="flex items-center space-x-1.5 flex-wrap">
                  <span class="font-bold text-[#1D1D1F] font-mono text-xs">{{ item.model_name }}</span>
                  <span v-if="item.tier_range && item.tier_range !== '无阶梯'" class="px-1.5 py-0.2 rounded text-[10px] bg-[#F2F2F7] text-[#0071E3] font-mono border border-[#0071E3]/20">
                    {{ item.tier_range }}
                  </span>
                </div>
              </td>

              <td v-if="store.visibleColumns.billing_mode" class="py-2 px-3 whitespace-nowrap">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-medium" :class="getModeBadgeClass(item.billing_mode)">
                  {{ item.billing_mode }}
                </span>
              </td>

              <td v-if="store.visibleColumns.input_price" class="py-2 px-3 font-mono text-right whitespace-nowrap font-bold" :class="getPriceColor(item.input_price)">
                {{ formatPrice(item, 'input_price') }}
              </td>

              <td v-if="store.visibleColumns.output_price" class="py-2 px-3 font-mono text-right whitespace-nowrap font-bold" :class="getPriceColor(item.output_price)">
                {{ formatPrice(item, 'output_price') }}
              </td>

              <td v-if="store.visibleColumns.cache_read_price" class="py-2 px-3 font-mono text-right whitespace-nowrap text-[#34C759]">
                {{ formatPrice(item, 'cache_read_price') }}
              </td>

              <td v-if="store.visibleColumns.cache_write_price" class="py-2 px-3 font-mono text-right whitespace-nowrap text-[#FF9500]">
                {{ formatPrice(item, 'cache_write_price') }}
              </td>

              <td v-if="store.visibleColumns.remarks" class="py-2 px-3 text-xs text-[#6E6E73] leading-relaxed">
                {{ item.remarks || '-' }}
              </td>

              <td v-if="store.visibleColumns.custom_notes" class="py-2 px-3">
                <div class="flex items-center justify-between group/note">
                  <div class="min-w-0 flex-1 space-y-0.5">
                    <div v-if="item.user_tags" class="flex items-center flex-wrap gap-1">
                      <span
                        v-for="t in item.user_tags.split(/[,，]/)"
                        :key="t"
                        class="px-1.5 py-0.2 rounded text-[10px] font-medium bg-[#34C759]/10 text-[#34C759]"
                      >
                        {{ t.trim() }}
                      </span>
                    </div>
                    <div v-if="item.custom_notes" class="text-xs text-[#1D1D1F] font-medium truncate" :title="item.custom_notes">
                      {{ item.custom_notes }}
                    </div>
                    <div v-if="!item.custom_notes && !item.user_tags" class="text-[11px] text-[#86868B] italic">
                      点击添加备注
                    </div>
                  </div>
                  <button
                    @click="store.editingNoteItem = item"
                    class="opacity-0 group-hover/note:opacity-100 ml-1.5 p-1 rounded hover:bg-[#E5E5EA] text-[#0071E3] transition-all cursor-pointer"
                    title="编辑备注与标签"
                  >
                    ✎
                  </button>
                </div>
              </td>

              <td v-if="store.visibleColumns.price_date" class="py-2 px-3 font-mono text-[11px] text-[#86868B] whitespace-nowrap">
                {{ item.price_date || '-' }}
              </td>

              <td v-if="store.visibleColumns.source_anchor" class="py-2 px-3 text-center whitespace-nowrap">
                <button
                  @click="store.openSnapshotDrawer(item)"
                  class="px-2 py-1 rounded-lg border border-[#0071E3]/30 bg-[#F2F7FF] hover:bg-[#0071E3] text-[#0071E3] hover:text-white text-[11px] font-medium transition-all shadow-2xs cursor-pointer flex items-center space-x-1 mx-auto"
                  title="查看完整 HTML 快照与官方证据链"
                >
                  <span>快照对账</span>
                  <span>📄</span>
                </button>
              </td>
            </tr>
          </tbody>

          <!-- 模式 2：按厂商分组 (Grouped by Vendor) -->
          <template v-else-if="store.viewMode === 'group-vendor'">
            <tbody
              v-for="group in store.groupedByVendor"
              :key="group.key"
              class="divide-y divide-[#E5E5EA]/70 font-sans border-b border-[#E5E5EA]"
            >
              <!-- 厂商分组标题栏 -->
              <tr class="bg-[#F9F9FB] hover:bg-[#F2F2F7] cursor-pointer select-none" @click="store.toggleGroup(group.key)">
                <td :colspan="12" class="py-2.5 px-4 font-bold text-xs text-[#1D1D1F]">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                      <span class="text-xs transition-transform duration-200" :class="store.collapsedGroups[group.key] ? '-rotate-90' : ''">▾</span>
                      <span class="px-2 py-0.5 rounded-md text-xs font-bold" :class="getProviderBadgeClass(group.provider)">
                        {{ group.providerName }}
                      </span>
                      <span class="text-xs text-[#86868B] font-mono">({{ group.count }} 个规格模型)</span>
                    </div>
                    <span class="text-[11px] text-[#0071E3] font-normal">
                      {{ store.collapsedGroups[group.key] ? '点击展开' : '点击收起' }}
                    </span>
                  </div>
                </td>
              </tr>

              <!-- 分组展开数据行 -->
              <template v-if="!store.collapsedGroups[group.key]">
                <tr
                  v-for="item in group.items"
                  :key="item.id"
                  class="hover:bg-[#F9FAFC] transition-colors group"
                >
                  <td v-if="store.visibleColumns.provider_name" class="py-2 px-3 whitespace-nowrap pl-6 text-[#86868B]">
                    ↳ {{ item.provider_name }}
                  </td>
                  <td v-if="store.visibleColumns.series" class="py-2 px-3 font-mono text-[11px] text-[#6E6E73] whitespace-nowrap">{{ item.series }}</td>
                  <td v-if="store.visibleColumns.model_name" class="py-2 px-3">
                    <div class="flex items-center space-x-1.5 flex-wrap">
                      <span class="font-bold text-[#1D1D1F] font-mono text-xs">{{ item.model_name }}</span>
                      <span v-if="item.tier_range && item.tier_range !== '无阶梯'" class="px-1.5 py-0.2 rounded text-[10px] bg-[#F2F2F7] text-[#0071E3] font-mono border border-[#0071E3]/20">
                        {{ item.tier_range }}
                      </span>
                    </div>
                  </td>
                  <td v-if="store.visibleColumns.billing_mode" class="py-2 px-3 whitespace-nowrap">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-medium" :class="getModeBadgeClass(item.billing_mode)">{{ item.billing_mode }}</span>
                  </td>
                  <td v-if="store.visibleColumns.input_price" class="py-2 px-3 font-mono text-right whitespace-nowrap font-bold" :class="getPriceColor(item.input_price)">{{ formatPrice(item, 'input_price') }}</td>
                  <td v-if="store.visibleColumns.output_price" class="py-2 px-3 font-mono text-right whitespace-nowrap font-bold" :class="getPriceColor(item.output_price)">{{ formatPrice(item, 'output_price') }}</td>
                  <td v-if="store.visibleColumns.cache_read_price" class="py-2 px-3 font-mono text-right whitespace-nowrap text-[#34C759]">{{ formatPrice(item, 'cache_read_price') }}</td>
                  <td v-if="store.visibleColumns.cache_write_price" class="py-2 px-3 font-mono text-right whitespace-nowrap text-[#FF9500]">{{ formatPrice(item, 'cache_write_price') }}</td>
                  <td v-if="store.visibleColumns.remarks" class="py-2 px-3 text-xs text-[#6E6E73] leading-relaxed">{{ item.remarks || '-' }}</td>
                  <td v-if="store.visibleColumns.custom_notes" class="py-2 px-3">
                    <div class="flex items-center justify-between group/note" @click="store.editingNoteItem = item">
                      <div class="min-w-0 flex-1 space-y-0.5 cursor-pointer">
                        <div v-if="item.user_tags" class="flex items-center flex-wrap gap-1">
                          <span v-for="t in item.user_tags.split(/[,，]/)" :key="t" class="px-1.5 py-0.2 rounded text-[10px] font-medium bg-[#34C759]/10 text-[#34C759]">{{ t.trim() }}</span>
                        </div>
                        <div v-if="item.custom_notes" class="text-xs text-[#1D1D1F] font-medium truncate">{{ item.custom_notes }}</div>
                        <div v-if="!item.custom_notes && !item.user_tags" class="text-[11px] text-[#86868B] italic">添加备注</div>
                      </div>
                      <span class="text-[#0071E3] ml-1">✎</span>
                    </div>
                  </td>
                  <td v-if="store.visibleColumns.price_date" class="py-2 px-3 font-mono text-[11px] text-[#86868B] whitespace-nowrap">{{ item.price_date || '-' }}</td>
                  <td v-if="store.visibleColumns.source_anchor" class="py-2 px-3 text-center whitespace-nowrap">
                    <button @click="store.openSnapshotDrawer(item)" class="px-2 py-1 rounded-lg border border-[#0071E3]/30 bg-[#F2F7FF] hover:bg-[#0071E3] text-[#0071E3] hover:text-white text-[11px] font-medium transition-all shadow-2xs cursor-pointer flex items-center space-x-1 mx-auto">
                      <span>快照对账</span>
                      <span>📄</span>
                    </button>
                  </td>
                </tr>
              </template>
            </tbody>
          </template>

          <!-- 模式 3：按系列分组 (Grouped by Series) -->
          <template v-else-if="store.viewMode === 'group-series'">
            <tbody
              v-for="group in store.groupedBySeries"
              :key="group.key"
              class="divide-y divide-[#E5E5EA]/70 font-sans border-b border-[#E5E5EA]"
            >
              <!-- 系列分组标题栏 -->
              <tr class="bg-[#F9F9FB] hover:bg-[#F2F2F7] cursor-pointer select-none" @click="store.toggleGroup(group.key)">
                <td :colspan="12" class="py-2.5 px-4 font-bold text-xs text-[#1D1D1F]">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                      <span class="text-xs transition-transform duration-200" :class="store.collapsedGroups[group.key] ? '-rotate-90' : ''">▾</span>
                      <span class="font-mono text-xs font-bold text-[#0071E3]">{{ group.series }} 系列</span>
                      <span class="px-2 py-0.2 rounded text-[10px] bg-[#E5E5EA] text-[#48484A]">{{ group.providerName }}</span>
                      <span class="text-xs text-[#86868B] font-mono">({{ group.count }} 个规格)</span>
                    </div>
                    <span class="text-[11px] text-[#0071E3] font-normal">
                      {{ store.collapsedGroups[group.key] ? '点击展开' : '点击收起' }}
                    </span>
                  </div>
                </td>
              </tr>

              <template v-if="!store.collapsedGroups[group.key]">
                <tr
                  v-for="item in group.items"
                  :key="item.id"
                  class="hover:bg-[#F9FAFC] transition-colors group"
                >
                  <td v-if="store.visibleColumns.provider_name" class="py-2 px-3 whitespace-nowrap">
                    <span class="px-2 py-0.5 rounded-md text-[11px] font-bold" :class="getProviderBadgeClass(item.provider)">{{ item.provider_name }}</span>
                  </td>
                  <td v-if="store.visibleColumns.series" class="py-2 px-3 font-mono text-[11px] text-[#6E6E73] whitespace-nowrap">{{ item.series }}</td>
                  <td v-if="store.visibleColumns.model_name" class="py-2 px-3">
                    <div class="flex items-center space-x-1.5 flex-wrap">
                      <span class="font-bold text-[#1D1D1F] font-mono text-xs">{{ item.model_name }}</span>
                      <span v-if="item.tier_range && item.tier_range !== '无阶梯'" class="px-1.5 py-0.2 rounded text-[10px] bg-[#F2F2F7] text-[#0071E3] font-mono border border-[#0071E3]/20">
                        {{ item.tier_range }}
                      </span>
                    </div>
                  </td>
                  <td v-if="store.visibleColumns.billing_mode" class="py-2 px-3 whitespace-nowrap">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-medium" :class="getModeBadgeClass(item.billing_mode)">{{ item.billing_mode }}</span>
                  </td>
                  <td v-if="store.visibleColumns.input_price" class="py-2 px-3 font-mono text-right whitespace-nowrap font-bold" :class="getPriceColor(item.input_price)">{{ formatPrice(item, 'input_price') }}</td>
                  <td v-if="store.visibleColumns.output_price" class="py-2 px-3 font-mono text-right whitespace-nowrap font-bold" :class="getPriceColor(item.output_price)">{{ formatPrice(item, 'output_price') }}</td>
                  <td v-if="store.visibleColumns.cache_read_price" class="py-2 px-3 font-mono text-right whitespace-nowrap text-[#34C759]">{{ formatPrice(item, 'cache_read_price') }}</td>
                  <td v-if="store.visibleColumns.cache_write_price" class="py-2 px-3 font-mono text-right whitespace-nowrap text-[#FF9500]">{{ formatPrice(item, 'cache_write_price') }}</td>
                  <td v-if="store.visibleColumns.remarks" class="py-2 px-3 text-xs text-[#6E6E73] leading-relaxed">{{ item.remarks || '-' }}</td>
                  <td v-if="store.visibleColumns.custom_notes" class="py-2 px-3">
                    <div class="flex items-center justify-between group/note" @click="store.editingNoteItem = item">
                      <div class="min-w-0 flex-1 space-y-0.5 cursor-pointer">
                        <div v-if="item.user_tags" class="flex items-center flex-wrap gap-1">
                          <span v-for="t in item.user_tags.split(/[,，]/)" :key="t" class="px-1.5 py-0.2 rounded text-[10px] font-medium bg-[#34C759]/10 text-[#34C759]">{{ t.trim() }}</span>
                        </div>
                        <div v-if="item.custom_notes" class="text-xs text-[#1D1D1F] font-medium truncate">{{ item.custom_notes }}</div>
                        <div v-if="!item.custom_notes && !item.user_tags" class="text-[11px] text-[#86868B] italic">添加备注</div>
                      </div>
                      <span class="text-[#0071E3] ml-1">✎</span>
                    </div>
                  </td>
                  <td v-if="store.visibleColumns.price_date" class="py-2 px-3 font-mono text-[11px] text-[#86868B] whitespace-nowrap">{{ item.price_date || '-' }}</td>
                  <td v-if="store.visibleColumns.source_anchor" class="py-2 px-3 text-center whitespace-nowrap">
                    <button @click="store.openSnapshotDrawer(item)" class="px-2 py-1 rounded-lg border border-[#0071E3]/30 bg-[#F2F7FF] hover:bg-[#0071E3] text-[#0071E3] hover:text-white text-[11px] font-medium transition-all shadow-2xs cursor-pointer flex items-center space-x-1 mx-auto">
                      <span>快照对账</span>
                      <span>📄</span>
                    </button>
                  </td>
                </tr>
              </template>
            </tbody>
          </template>

          <!-- 模式 4：树形折叠层级 (Tree Hierarchy: 厂商 ➔ 系列 ➔ 具体模型) -->
          <template v-else-if="store.viewMode === 'tree'">
            <tbody
              v-for="vendorNode in store.treeHierarchy"
              :key="vendorNode.key"
              class="divide-y divide-[#E5E5EA]/70 font-sans border-b border-[#E5E5EA]"
            >
              <!-- Level 1: 厂商节点 -->
              <tr class="bg-[#F5F5F7] hover:bg-[#EBEBF0] cursor-pointer select-none" @click="store.toggleGroup(vendorNode.key)">
                <td :colspan="12" class="py-2.5 px-3 font-bold text-xs text-[#1D1D1F]">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                      <span class="text-xs transition-transform duration-200" :class="store.collapsedGroups[vendorNode.key] ? '-rotate-90' : ''">▾</span>
                      <SystemIcon name="provider" custom-class="w-3.5 h-3.5 text-[#0071E3]" />
                      <span class="text-xs font-bold">{{ vendorNode.providerName }}</span>
                      <span class="text-xs text-[#86868B] font-mono">({{ vendorNode.count }} 条规格)</span>
                    </div>
                    <span class="text-[11px] text-[#0071E3] font-normal">
                      {{ store.collapsedGroups[vendorNode.key] ? '展开厂商' : '收起厂商' }}
                    </span>
                  </div>
                </td>
              </tr>

              <!-- Level 2: 系列节点与 Level 3 具体规格 -->
              <template v-if="!store.collapsedGroups[vendorNode.key]">
                <template v-for="seriesNode in vendorNode.seriesNodes" :key="seriesNode.key">
                  <!-- 系列子节点标题 -->
                  <tr class="bg-[#FBFBFD] hover:bg-[#F2F2F7] cursor-pointer select-none" @click="store.toggleGroup(seriesNode.key)">
                    <td :colspan="12" class="py-2 px-3 pl-8 text-xs font-semibold text-[#48484A]">
                      <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                          <span class="text-[11px] transition-transform duration-200" :class="store.collapsedGroups[seriesNode.key] ? '-rotate-90' : ''">▾</span>
                          <SystemIcon name="series" custom-class="w-3 h-3 text-[#34C759]" />
                          <span class="font-mono text-xs font-bold text-[#1D1D1F]">{{ seriesNode.series }}</span>
                          <span class="text-[11px] text-[#86868B] font-mono">({{ seriesNode.count }} 条)</span>
                        </div>
                        <span class="text-[11px] text-[#86868B]">
                          {{ store.collapsedGroups[seriesNode.key] ? '展开系列' : '收起系列' }}
                        </span>
                      </div>
                    </td>
                  </tr>

                  <!-- Level 3: 具体模型与阶梯行 -->
                  <template v-if="!store.collapsedGroups[seriesNode.key]">
                    <tr
                      v-for="item in seriesNode.items"
                      :key="item.id"
                      class="hover:bg-[#F9FAFC] transition-colors group"
                    >
                      <td v-if="store.visibleColumns.provider_name" class="py-2 px-3 whitespace-nowrap pl-12 text-[#86868B] font-mono text-[11px]">
                        ↳ {{ item.provider_name }}
                      </td>
                      <td v-if="store.visibleColumns.series" class="py-2 px-3 font-mono text-[11px] text-[#86868B] whitespace-nowrap">{{ item.series }}</td>
                      <td v-if="store.visibleColumns.model_name" class="py-2 px-3">
                        <div class="flex items-center space-x-1.5 flex-wrap">
                          <span class="font-bold text-[#1D1D1F] font-mono text-xs">{{ item.model_name }}</span>
                          <span v-if="item.tier_range && item.tier_range !== '无阶梯'" class="px-1.5 py-0.2 rounded text-[10px] bg-[#F2F2F7] text-[#0071E3] font-mono border border-[#0071E3]/20">
                            {{ item.tier_range }}
                          </span>
                        </div>
                      </td>
                      <td v-if="store.visibleColumns.billing_mode" class="py-2 px-3 whitespace-nowrap">
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-medium" :class="getModeBadgeClass(item.billing_mode)">{{ item.billing_mode }}</span>
                      </td>
                      <td v-if="store.visibleColumns.input_price" class="py-2 px-3 font-mono text-right whitespace-nowrap font-bold" :class="getPriceColor(item.input_price)">{{ formatPrice(item, 'input_price') }}</td>
                      <td v-if="store.visibleColumns.output_price" class="py-2 px-3 font-mono text-right whitespace-nowrap font-bold" :class="getPriceColor(item.output_price)">{{ formatPrice(item, 'output_price') }}</td>
                      <td v-if="store.visibleColumns.cache_read_price" class="py-2 px-3 font-mono text-right whitespace-nowrap text-[#34C759]">{{ formatPrice(item, 'cache_read_price') }}</td>
                      <td v-if="store.visibleColumns.cache_write_price" class="py-2 px-3 font-mono text-right whitespace-nowrap text-[#FF9500]">{{ formatPrice(item, 'cache_write_price') }}</td>
                      <td v-if="store.visibleColumns.remarks" class="py-2 px-3 text-xs text-[#6E6E73] leading-relaxed">{{ item.remarks || '-' }}</td>
                      <td v-if="store.visibleColumns.custom_notes" class="py-2 px-3">
                        <div class="flex items-center justify-between group/note" @click="store.editingNoteItem = item">
                          <div class="min-w-0 flex-1 space-y-0.5 cursor-pointer">
                            <div v-if="item.user_tags" class="flex items-center flex-wrap gap-1">
                              <span v-for="t in item.user_tags.split(/[,，]/)" :key="t" class="px-1.5 py-0.2 rounded text-[10px] font-medium bg-[#34C759]/10 text-[#34C759]">{{ t.trim() }}</span>
                            </div>
                            <div v-if="item.custom_notes" class="text-xs text-[#1D1D1F] font-medium truncate">{{ item.custom_notes }}</div>
                            <div v-if="!item.custom_notes && !item.user_tags" class="text-[11px] text-[#86868B] italic">添加备注</div>
                          </div>
                          <span class="text-[#0071E3] ml-1">✎</span>
                        </div>
                      </td>
                      <td v-if="store.visibleColumns.price_date" class="py-2 px-3 font-mono text-[11px] text-[#86868B] whitespace-nowrap">{{ item.price_date || '-' }}</td>
                      <td v-if="store.visibleColumns.source_anchor" class="py-2 px-3 text-center whitespace-nowrap">
                        <button @click="store.openSnapshotDrawer(item)" class="px-2 py-1 rounded-lg border border-[#0071E3]/30 bg-[#F2F7FF] hover:bg-[#0071E3] text-[#0071E3] hover:text-white text-[11px] font-medium transition-all shadow-2xs cursor-pointer flex items-center space-x-1 mx-auto">
                          <span>快照对账</span>
                          <span>📄</span>
                        </button>
                      </td>
                    </tr>
                  </template>
                </template>
              </template>
            </tbody>
          </template>
        </table>

        <!-- 空数据提示 -->
        <div v-if="store.filteredModels.length === 0 && !store.isLoading" class="p-12 text-center text-[#86868B] space-y-2">
          <div class="text-2xl">🔍</div>
          <div class="text-sm font-medium text-[#1D1D1F]">未找到符合当前筛选条件的官方模型规格</div>
          <div class="text-xs">请尝试清除部分筛选条件或在上方搜索框重置关键字</div>
        </div>

        <!-- 加载中 -->
        <div v-if="store.isLoading" class="p-12 text-center text-[#0071E3] space-y-2">
          <div class="w-6 h-6 border-2 border-[#0071E3] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <div class="text-xs font-medium">正在加载官方模型价格数据...</div>
        </div>
      </div>
    </div>

    <!-- 弹窗与抽屉组件 -->
    <OfficialColumnConfigModal
      :visible="isColModalVisible"
      @close="isColModalVisible = false"
    />

    <OfficialNoteEditModal />

    <OfficialScrapeModal />

    <SnapshotPreviewDrawer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useOfficialPricingStore, OfficialModelPrice } from '../stores/officialPricingStore'
import SystemIcon from '../components/SystemIcon.vue'
import OfficialColumnConfigModal from '../components/OfficialColumnConfigModal.vue'
import OfficialNoteEditModal from '../components/OfficialNoteEditModal.vue'
import OfficialScrapeModal from '../components/OfficialScrapeModal.vue'
import SnapshotPreviewDrawer from '../components/SnapshotPreviewDrawer.vue'

const store = useOfficialPricingStore()

const isColModalVisible = ref(false)
const isProviderDropdownOpen = ref(false)
const isSeriesDropdownOpen = ref(false)

const billingModes = [
  { id: 'all', label: '全部模式' },
  { id: 'Standard', label: 'Standard' },
  { id: 'Batch 批处理', label: 'Batch 批处理' },
  { id: 'Flex 弹性', label: 'Flex 弹性' },
  { id: 'Priority 优先', label: 'Priority 优先' },
  { id: '闲时半价', label: '闲时半价' }
]

// 级联过滤出的系列列表
const filteredSeriesOptions = computed(() => {
  if (store.selectedProviders.length === 0) {
    return store.seriesList
  }
  return store.seriesList.filter((s) => store.selectedProviders.includes(s.provider))
})

onMounted(async () => {
  await store.fetchOfficialPrices()
  await store.fetchSnapshots()
})

function toggleProvider(code: string) {
  const idx = store.selectedProviders.indexOf(code)
  if (idx >= 0) {
    store.selectedProviders.splice(idx, 1)
  } else {
    store.selectedProviders.push(code)
  }
}

function toggleSeries(series: string) {
  const idx = store.selectedSeries.indexOf(series)
  if (idx >= 0) {
    store.selectedSeries.splice(idx, 1)
  } else {
    store.selectedSeries.push(series)
  }
}

// 格式化价格输出，响应当前币种模式
function formatPrice(item: OfficialModelPrice, field: 'input_price' | 'output_price' | 'cache_read_price' | 'cache_write_price'): string {
  const val = item[field]
  if (val === 0) return '0.00'

  if (store.currencyMode === 'cny') {
    let cnyVal = 0
    if (field === 'input_price') cnyVal = item.converted_input_cny ?? val
    else if (field === 'output_price') cnyVal = item.converted_output_cny ?? val
    else if (field === 'cache_read_price') cnyVal = item.converted_cache_read_cny ?? val
    else if (field === 'cache_write_price') cnyVal = item.converted_cache_write_cny ?? val
    return `¥ ${cnyVal.toFixed(3)}`
  } else if (store.currencyMode === 'usd') {
    let usdVal = 0
    if (field === 'input_price') usdVal = item.converted_input_usd ?? val
    else if (field === 'output_price') usdVal = item.converted_output_usd ?? val
    else if (field === 'cache_read_price') usdVal = item.converted_cache_read_usd ?? val
    else if (field === 'cache_write_price') usdVal = item.converted_cache_write_usd ?? val
    return `$ ${usdVal.toFixed(3)}`
  } else {
    const sym = item.currency === 'USD' ? '$' : '¥'
    return `${sym} ${val.toFixed(3)}`
  }
}

function getPriceColor(price: number): string {
  if (price === 0) return 'text-[#34C759]'
  if (price > 20) return 'text-[#FF3B30]'
  if (price > 5) return 'text-[#FF9500]'
  return 'text-[#1D1D1F]'
}

function getProviderBadgeClass(provider: string): string {
  switch (provider) {
    case 'openai':
      return 'bg-[#10A37F]/10 text-[#10A37F] border border-[#10A37F]/20'
    case 'anthropic':
      return 'bg-[#D97706]/10 text-[#D97706] border border-[#D97706]/20'
    case 'google':
      return 'bg-[#4285F4]/10 text-[#4285F4] border border-[#4285F4]/20'
    case 'deepseek':
      return 'bg-[#0066FF]/10 text-[#0066FF] border border-[#0066FF]/20'
    case 'zhipuai':
      return 'bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20'
    case 'moonshotai':
      return 'bg-[#0071E3]/10 text-[#0071E3] border border-[#0071E3]/20'
    case 'minimax':
      return 'bg-[#EC4899]/10 text-[#EC4899] border border-[#EC4899]/20'
    case 'alibaba':
      return 'bg-[#FF6A00]/10 text-[#FF6A00] border border-[#FF6A00]/20'
    case 'xiaomi':
      return 'bg-[#FF6900]/10 text-[#FF6900] border border-[#FF6900]/20'
    default:
      return 'bg-[#86868B]/10 text-[#86868B]'
  }
}

function getModeBadgeClass(mode: string): string {
  if (mode.includes('Batch')) return 'bg-[#5856D6]/10 text-[#5856D6] border border-[#5856D6]/20'
  if (mode.includes('Flex')) return 'bg-[#FF9500]/10 text-[#FF9500] border border-[#FF9500]/20'
  if (mode.includes('闲时')) return 'bg-[#34C759]/10 text-[#34C759] border border-[#34C759]/20'
  if (mode.includes('Tiered') || mode.includes('阶梯')) return 'bg-[#0071E3]/10 text-[#0071E3] border border-[#0071E3]/20'
  return 'bg-[#F2F2F7] text-[#6E6E73]'
}
</script>

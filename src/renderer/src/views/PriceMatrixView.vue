<template>
  <div class="h-full flex flex-col space-y-2.5 overflow-hidden select-none">
    <!-- 顶部四级联动多维筛选栏 (苹果灰白卡片) -->
    <div class="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-2">
      <!-- 第一行：四大维度可搜索多选下拉 + 收藏快捷切换 (全部支持字母 A-Z 升序排序) -->
      <div class="flex items-center justify-between flex-wrap gap-2">
        <div class="flex items-center flex-wrap gap-2">
          <!-- 1. 模型厂商多选 (A-Z 排序，支持中文别名模糊搜索 如“深度探索”) -->
          <MultiSelectFilter
            label="模型厂商"
            icon="🏢"
            :options="sortedProviderOptions"
            :model-value="selectedProviders"
            @update:model-value="handleProviderChange"
          />

          <!-- 2. 模型系列多选 (A-Z 排序，根据已选厂商级联收敛) -->
          <MultiSelectFilter
            label="模型系列"
            icon="📦"
            :options="sortedSeriesOptions"
            :model-value="selectedSeries"
            @update:model-value="handleSeriesChange"
          />

          <!-- 3. 模型名称多选 (A-Z 排序，保留前面的厂商与系列) -->
          <MultiSelectFilter
            label="模型名称"
            icon="🤖"
            :options="sortedModelOptions"
            :model-value="selectedModels"
            @update:model-value="handleModelChange"
          />

          <!-- 4. 渠道中转站多选 (A-Z 排序，支持模糊搜索 如“七牛”, “OpenRouter”, “硅基”) -->
          <MultiSelectFilter
            label="渠道中转站"
            icon="🌐"
            :options="sortedSiteOptions"
            :model-value="selectedSites"
            @update:model-value="handleSiteChange"
          />

          <!-- 5. 仅看已收藏渠道快捷胶囊 -->
          <button
            @click="toggleOnlyFavorites"
            class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1"
            :class="onlyFavorites ? 'bg-[#FFF8E1] border-[#FFE082] text-[#B78103] font-bold shadow-xs' : 'bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
          >
            <span>{{ onlyFavorites ? '⭐ 已开启仅看收藏' : '☆ 仅看已收藏渠道' }}</span>
            <span v-if="store.favoriteSiteIds.length > 0" class="text-[10px] font-mono opacity-80">({{ store.favoriteSiteIds.length }})</span>
          </button>

          <!-- 6. 隐藏 0 元 / 未标价条目快捷切换胶囊 -->
          <button
            @click="toggleExcludeZero"
            class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1"
            :class="excludeZeroPrice ? 'bg-[#EBF5FF] border-[#B9E1FF] text-[#0071E3] font-bold shadow-xs' : 'bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
            title="点击切换是否过滤输入与输出单价均为 0 的免费/占位/未标价条目"
          >
            <span>{{ excludeZeroPrice ? '🚫 隐藏 0 元/未标价' : '👁️ 显示 0 元/未标价' }}</span>
          </button>
        </div>

        <!-- 右侧：快捷操作与匹配统计 -->
        <div class="flex items-center space-x-2 text-xs">
          <span class="text-[#6E6E73]">
            全网匹配: <strong class="text-[#0071E3] font-mono font-bold">{{ totalRecords }}</strong> 条报价
          </span>
          <button
            v-if="hasAnyFilter || onlyFavorites"
            @click="resetAllFilters"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#FFE5E5] text-[#6E6E73] hover:text-[#FF3B30] border border-[#E5E5EA] transition-all text-xs"
          >
            重置筛选
          </button>
        </div>
      </div>

      <!-- 第二行：分类聚合卡片模式已选筛选条 (始终保持单行优雅展示，杜绝占用表格视口空间) -->
      <div v-if="hasAnyFilter || onlyFavorites || store.highlightBenchmarkSiteName" class="flex items-center justify-between pt-1.5 border-t border-[#E5E5EA] text-xs relative">
        <div class="flex items-center space-x-1.5 flex-wrap gap-y-1 overflow-visible">
          <span class="text-[11px] text-[#86868B] font-medium flex-shrink-0">当前筛选:</span>

          <!-- 1. 收藏状态 Chip -->
          <span
            v-if="onlyFavorites"
            class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#FFF8E1] border border-[#FFE082] text-[#B78103] text-[11px] font-medium"
          >
            <span>⭐ 仅看收藏</span>
            <button @click="onlyFavorites = false" class="hover:text-[#8C6300] ml-0.5 cursor-pointer">✕</button>
          </span>

          <!-- 2. 模型厂商 Dimension Pill & Popover -->
          <div v-if="selectedProviders.length > 0" class="relative inline-block" @click.stop>
            <span
              @click="selectedProviders.length > 1 ? toggleDimensionPopover('provider') : null"
              class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E8F2FD] border border-[#CCE4FB] text-[#0071E3] text-[11px] font-medium transition-all"
              :class="selectedProviders.length > 1 ? 'cursor-pointer hover:bg-[#D9EAFE] hover:border-[#B6D9FD]' : ''"
            >
              <span>🏢 {{ selectedProviders.length === 1 ? getProviderLabel(selectedProviders[0]) : `模型厂商: ${selectedProviders.length} 个` }}</span>
              <span v-if="selectedProviders.length > 1" class="text-[9px] text-[#0071E3]">▾</span>
              <button @click.stop="handleProviderChange([])" class="hover:text-[#004BB3] ml-0.5 cursor-pointer font-bold" title="清除所有选中的厂商">✕</button>
            </span>

            <!-- Popover Dropdown -->
            <div
              v-if="activePopoverDimension === 'provider'"
              class="absolute left-0 top-7 w-72 bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-[0_12px_32px_rgba(0,0,0,0.12)] z-30 p-2.5 animate-fade-in text-xs space-y-2"
            >
              <div class="flex items-center justify-between pb-1.5 border-b border-[#E5E5EA]">
                <span class="font-bold text-[#1D1D1F] text-xs">已选厂商 ({{ selectedProviders.length }})</span>
                <button @click="handleProviderChange([]); closeDimensionPopover()" class="text-[11px] text-[#FF3B30] hover:underline cursor-pointer">清空厂商</button>
              </div>
              <div class="max-h-48 overflow-y-auto pr-1 flex flex-wrap gap-1">
                <span
                  v-for="p in selectedProviders"
                  :key="`pop-p-${p}`"
                  class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E8F2FD] border border-[#CCE4FB] text-[#0071E3] text-[11px]"
                >
                  <span>{{ getProviderLabel(p) }}</span>
                  <button @click="removeProvider(p)" class="hover:text-[#FF3B30] ml-0.5 cursor-pointer font-bold">✕</button>
                </span>
              </div>
            </div>
          </div>

          <!-- 3. 模型系列 Dimension Pill & Popover -->
          <div v-if="selectedSeries.length > 0" class="relative inline-block" @click.stop>
            <span
              @click="selectedSeries.length > 1 ? toggleDimensionPopover('series') : null"
              class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#F3E8FF] border border-[#E9D5FF] text-[#9333EA] text-[11px] font-medium transition-all"
              :class="selectedSeries.length > 1 ? 'cursor-pointer hover:bg-[#EBD4FD] hover:border-[#DEC0FA]' : ''"
            >
              <span>📦 {{ selectedSeries.length === 1 ? selectedSeries[0] : `模型系列: ${selectedSeries.length} 个` }}</span>
              <span v-if="selectedSeries.length > 1" class="text-[9px] text-[#9333EA]">▾</span>
              <button @click.stop="handleSeriesChange([])" class="hover:text-[#6B21A8] ml-0.5 cursor-pointer font-bold" title="清除所有选中的系列">✕</button>
            </span>

            <!-- Popover Dropdown -->
            <div
              v-if="activePopoverDimension === 'series'"
              class="absolute left-0 top-7 w-72 bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-[0_12px_32px_rgba(0,0,0,0.12)] z-30 p-2.5 animate-fade-in text-xs space-y-2"
            >
              <div class="flex items-center justify-between pb-1.5 border-b border-[#E5E5EA]">
                <span class="font-bold text-[#1D1D1F] text-xs">已选模型系列 ({{ selectedSeries.length }})</span>
                <button @click="handleSeriesChange([]); closeDimensionPopover()" class="text-[11px] text-[#FF3B30] hover:underline cursor-pointer">清空系列</button>
              </div>
              <div class="max-h-48 overflow-y-auto pr-1 flex flex-wrap gap-1">
                <span
                  v-for="s in selectedSeries"
                  :key="`pop-s-${s}`"
                  class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#F3E8FF] border border-[#E9D5FF] text-[#9333EA] text-[11px]"
                >
                  <span>{{ s }}</span>
                  <button @click="removeSeries(s)" class="hover:text-[#FF3B30] ml-0.5 cursor-pointer font-bold">✕</button>
                </span>
              </div>
            </div>
          </div>

          <!-- 4. 模型名称 Dimension Pill & Popover (支持多达 80+ 款模型聚合与弹窗搜索管理) -->
          <div v-if="selectedModels.length > 0" class="relative inline-block" @click.stop>
            <span
              @click="selectedModels.length > 1 ? toggleDimensionPopover('model') : null"
              class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E6F4EA] border border-[#CEEAD6] text-[#137333] text-[11px] font-medium transition-all"
              :class="selectedModels.length > 1 ? 'cursor-pointer hover:bg-[#D5EFE0] hover:border-[#B5E4C6] shadow-2xs' : ''"
            >
              <span>🤖 {{ selectedModels.length === 1 ? selectedModels[0] : `模型名称: ${selectedModels.length} 款` }}</span>
              <span v-if="selectedModels.length > 1" class="text-[9px] text-[#137333]">▾</span>
              <button @click.stop="handleModelChange([])" class="hover:text-[#0D5324] ml-0.5 cursor-pointer font-bold" title="清除所有选中的模型">✕</button>
            </span>

            <!-- Popover Dropdown -->
            <div
              v-if="activePopoverDimension === 'model'"
              class="absolute left-0 top-7 w-88 bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-[0_16px_36px_rgba(0,0,0,0.15)] z-30 p-3 animate-fade-in text-xs space-y-2.5"
            >
              <div class="flex items-center justify-between pb-1.5 border-b border-[#E5E5EA]">
                <div class="flex items-center space-x-1">
                  <span class="font-bold text-[#1D1D1F] text-xs">已选模型清单</span>
                  <span class="text-[11px] text-[#86868B] font-mono">({{ selectedModels.length }} 款)</span>
                </div>
                <button @click="handleModelChange([]); closeDimensionPopover()" class="text-[11px] text-[#FF3B30] hover:underline cursor-pointer font-medium">清空所有模型</button>
              </div>

              <!-- 搜索过滤输入框 (当模型数 > 4 时展示) -->
              <div v-if="selectedModels.length > 4" class="relative">
                <input
                  v-model="popoverSearchQuery"
                  type="text"
                  placeholder="在已选模型中搜索..."
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-mono"
                />
                <span v-if="popoverSearchQuery" @click="popoverSearchQuery = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
              </div>

              <!-- 模型标签流 (内部滚动) -->
              <div class="max-h-52 overflow-y-auto pr-1 flex flex-wrap gap-1.5">
                <span
                  v-for="m in filteredPopoverModels"
                  :key="`pop-m-${m}`"
                  class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E6F4EA] border border-[#CEEAD6] text-[#137333] text-[11px] font-mono group"
                >
                  <span class="truncate max-w-[200px]" :title="m">{{ m }}</span>
                  <button @click="removeModel(m)" class="text-[#86868B] group-hover:text-[#FF3B30] ml-0.5 cursor-pointer font-bold">✕</button>
                </span>
                <div v-if="filteredPopoverModels.length === 0" class="py-4 text-center text-[#86868B] text-xs w-full">
                  无匹配的已选模型
                </div>
              </div>
            </div>
          </div>

          <!-- 5. 渠道中转站 Dimension Pill & Popover -->
          <div v-if="selectedSites.length > 0" class="relative inline-block" @click.stop>
            <span
              @click="selectedSites.length > 1 ? toggleDimensionPopover('site') : null"
              class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#FFF0E6] border border-[#FFD8BF] text-[#D4380D] text-[11px] font-medium transition-all"
              :class="selectedSites.length > 1 ? 'cursor-pointer hover:bg-[#FFE6D6] hover:border-[#FFCCA8]' : ''"
            >
              <span>🌐 {{ selectedSites.length === 1 ? selectedSites[0] : `渠道中转: ${selectedSites.length} 家` }}</span>
              <span v-if="selectedSites.length > 1" class="text-[9px] text-[#D4380D]">▾</span>
              <button @click.stop="handleSiteChange([])" class="hover:text-[#A82805] ml-0.5 cursor-pointer font-bold" title="清除所有选中的渠道">✕</button>
            </span>

            <!-- Popover Dropdown -->
            <div
              v-if="activePopoverDimension === 'site'"
              class="absolute left-0 top-7 w-72 bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-[0_12px_32px_rgba(0,0,0,0.12)] z-30 p-2.5 animate-fade-in text-xs space-y-2"
            >
              <div class="flex items-center justify-between pb-1.5 border-b border-[#E5E5EA]">
                <span class="font-bold text-[#1D1D1F] text-xs">已选渠道 ({{ selectedSites.length }})</span>
                <button @click="handleSiteChange([]); closeDimensionPopover()" class="text-[11px] text-[#FF3B30] hover:underline cursor-pointer">清空渠道</button>
              </div>
              <div class="max-h-48 overflow-y-auto pr-1 flex flex-wrap gap-1">
                <span
                  v-for="st in selectedSites"
                  :key="`pop-st-${st}`"
                  class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#FFF0E6] border border-[#FFD8BF] text-[#D4380D] text-[11px]"
                >
                  <span>{{ st }}</span>
                  <button @click="removeSite(st)" class="hover:text-[#FF3B30] ml-0.5 cursor-pointer font-bold">✕</button>
                </span>
              </div>
            </div>
          </div>

          <!-- 6. 基准渠道指示 Chip -->
          <span
            v-if="store.highlightBenchmarkSiteName"
            class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-[#E8F2FD] border border-[#0071E3] text-[#0071E3] text-[11px] font-bold shadow-2xs animate-fade-in"
          >
            <span>🎯 比价基准: {{ store.highlightBenchmarkSiteName }}</span>
            <button @click="store.highlightBenchmarkSiteName = null" class="hover:text-[#FF3B30] ml-1 font-bold cursor-pointer" title="清除基准高亮">✕</button>
          </span>
        </div>

        <!-- 右侧：一键清空全部筛选 -->
        <button
          v-if="hasAnyFilter || onlyFavorites"
          @click="resetAllFilters"
          class="text-[11px] text-[#86868B] hover:text-[#FF3B30] transition-colors whitespace-nowrap pl-2 cursor-pointer flex items-center space-x-0.5 flex-shrink-0"
        >
          <span>✕ 清空筛选</span>
        </button>
      </div>
    </div>

    <!-- 主体：极速 60 FPS 比价矩阵表格 (Apple 风格无缝表格) -->
    <div class="flex-1 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex flex-col min-h-0 relative">
      <!-- 表头 (支持点击多列排序) -->
      <div class="grid grid-cols-12 gap-2 pb-2 border-b border-[#E5E5EA] text-[11px] font-semibold text-[#86868B] px-3 select-none">
        <div @click="toggleSort('series')" class="col-span-2 cursor-pointer hover:text-[#0071E3] transition-colors flex items-center space-x-1">
          <span>模型系列 / 厂商</span>
          <span class="text-[10px] font-mono" :class="sortField === 'series' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('series') }}</span>
        </div>
        <div @click="toggleSort('model_id')" class="col-span-3 cursor-pointer hover:text-[#0071E3] transition-colors flex items-center space-x-1">
          <span>模型标准标识</span>
          <span class="text-[10px] font-mono" :class="sortField === 'model_id' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('model_id') }}</span>
        </div>
        <div @click="toggleSort('site_name')" class="col-span-2 cursor-pointer hover:text-[#0071E3] transition-colors flex items-center space-x-1">
          <span>渠道 / 供应商</span>
          <span class="text-[10px] font-mono" :class="sortField === 'site_name' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('site_name') }}</span>
        </div>
        <div class="col-span-1">类型</div>
        <div @click="toggleSort('calculated_input_usd')" class="col-span-1 text-right cursor-pointer hover:text-[#0071E3] transition-colors flex items-center justify-end space-x-1">
          <span>输入单价 ({{ store.currency }})</span>
          <span class="text-[10px] font-mono" :class="sortField === 'calculated_input_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('calculated_input_usd') }}</span>
        </div>
        <div @click="toggleSort('calculated_output_usd')" class="col-span-1 text-right cursor-pointer hover:text-[#0071E3] transition-colors flex items-center justify-end space-x-1">
          <span>输出单价 ({{ store.currency }})</span>
          <span class="text-[10px] font-mono" :class="sortField === 'calculated_output_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('calculated_output_usd') }}</span>
        </div>
        <div @click="toggleSort('model_ratio')" class="col-span-1 text-center cursor-pointer hover:text-[#0071E3] transition-colors flex items-center justify-center space-x-1">
          <span>倍率</span>
          <span class="text-[10px] font-mono" :class="sortField === 'model_ratio' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('model_ratio') }}</span>
        </div>
        <div @click="toggleSort('last_tested_tps')" class="col-span-1 text-right cursor-pointer hover:text-[#0071E3] transition-colors flex items-center justify-end space-x-1">
          <span>实测 TPS</span>
          <span class="text-[10px] font-mono" :class="sortField === 'last_tested_tps' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('last_tested_tps') }}</span>
        </div>
      </div>

      <!-- 数据行列表 (仅渲染当前页 50 条，极速流畅 60 FPS) -->
      <div class="flex-1 overflow-y-auto divide-y divide-[#E5E5EA]/60 pr-1 mt-1 relative">
        <div v-if="isLoading" class="absolute inset-0 bg-white/70 backdrop-blur-xs flex items-center justify-center z-10">
          <div class="text-xs text-[#0071E3] font-medium flex items-center space-x-2">
            <span class="animate-spin">🌀</span>
            <span>加载报价数据中...</span>
          </div>
        </div>

        <div
          v-for="row in pagedItems"
          :key="row.id"
          :id="`price-row-${row.id}`"
          @click="selectRow(row)"
          class="grid grid-cols-12 gap-2 items-center px-3 py-3 text-xs transition-all duration-200 cursor-pointer rounded-xl relative my-0.5"
          :class="[
            selectedRow?.id === row.id
              ? 'bg-[#E8F2FD] border-2 border-[#0071E3] shadow-md ring-2 ring-[#0071E3]/25 font-medium'
              : 'hover:bg-[#F5F5F7] border border-transparent',
            isBenchmarkRow(row) && selectedRow?.id !== row.id
              ? 'bg-[#E8F2FD]/50 border-2 border-[#0071E3]/60 shadow-xs'
              : ''
          ]"
        >
          <!-- 系列与厂商 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <button
              @click.stop="openVendorDrawer(row.provider)"
              class="px-1.5 py-0.2 rounded bg-[#F2F2F7] hover:bg-[#0071E3] hover:text-white text-[#1D1D1F] border border-[#E5E5EA] text-[10px] font-mono font-bold transition-all cursor-pointer shadow-2xs group/btn flex items-center space-x-0.5"
              :title="`点击在右侧查看 ${row.provider.toUpperCase()} 厂商所有模型规格与详情`"
            >
              <span>{{ row.provider.toUpperCase() }}</span>
              <span class="text-[9px] text-[#0071E3] group-hover/btn:text-white transition-colors">📋</span>
            </button>
            <span class="text-[#1D1D1F] font-medium truncate text-[11px]">{{ row.series || '通用' }}</span>
          </div>

          <!-- 模型标识 -->
          <div class="col-span-3 flex items-center space-x-1.5 truncate">
            <span class="font-bold text-[#0071E3] font-mono truncate text-xs" :title="row.model_id">{{ row.model_id }}</span>
          </div>

          <!-- 渠道站点与收藏星标 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <button
              @click.stop="toggleFavoriteByName(row.site_name)"
              class="text-xs transition-transform hover:scale-125 focus:outline-none cursor-pointer"
              :title="isSiteNameFavorite(row.site_name) ? '点击取消收藏' : '点击收藏该渠道'"
            >
              <span v-if="isSiteNameFavorite(row.site_name)" class="text-[#FF9500]">⭐</span>
              <span v-else class="text-[#AEAEB2] hover:text-[#FF9500]">☆</span>
            </button>
            <div class="flex items-center space-x-1 truncate">
              <button
                @click.stop="openChannelDrawer(row.site_name)"
                class="font-semibold text-[#1D1D1F] hover:text-[#0071E3] hover:underline cursor-pointer truncate text-xs transition-colors text-left flex items-center space-x-0.5 group/ch"
                :title="`点击在右侧查看「${row.site_name}」渠道详情与可用模型定价`"
              >
                <span class="truncate">{{ row.site_name }}</span>
                <span class="text-[9px] text-[#0071E3] opacity-70 group-hover/ch:opacity-100">📋</span>
              </button>
              <!-- 当前比价基准渠道徽标 -->
              <span
                v-if="isBenchmarkRow(row)"
                class="px-1.5 py-0.2 rounded-full bg-[#0071E3] text-white text-[9px] font-bold flex-shrink-0 shadow-xs flex items-center space-x-0.5 animate-pulse"
                title="这是你在渠道详情中发起全网比价的原渠道（比价基准）"
              >
                <span>🎯 基准</span>
              </span>
              <span
                v-if="row.group_name"
                class="px-1 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-mono font-bold truncate flex-shrink-0 shadow-2xs"
                :title="`结算分组: ${row.group_name}`"
              >
                {{ row.group_name }}
              </span>
            </div>
          </div>

          <!-- 类型徽标 -->
          <div class="col-span-1">
            <span
              class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold uppercase"
              :class="getTypeBadgeClass(row.site_type)"
            >
              {{ row.site_type }}
            </span>
          </div>

          <!-- 输入价格 -->
          <div class="col-span-1 text-right font-mono font-bold text-[#34C759] text-xs">
            {{ formatPrice(row.calculated_input_usd, row.calculated_input_cny) }}
          </div>

          <!-- 输出价格 -->
          <div class="col-span-1 text-right font-mono text-[#1D1D1F] text-xs">
            {{ formatPrice(row.calculated_output_usd, row.calculated_output_cny) }}
          </div>

          <!-- 倍率 -->
          <div class="col-span-1 text-center font-mono text-[#6E6E73] font-semibold text-xs">
            {{ row.model_ratio }}x
          </div>

          <!-- 实测 TPS -->
          <div class="col-span-1 text-right font-mono text-[#0071E3] font-bold text-xs">
            {{ row.last_tested_tps }} <span class="text-[9px] text-[#86868B] font-normal">tps</span>
          </div>
        </div>

        <!-- 空状态 A: 库内完全无数据 (首次使用引导) -->
        <div v-if="!isLoading && pagedItems.length === 0 && !hasAnyFilter && !onlyFavorites && totalRecords === 0" class="py-16 px-6 text-center space-y-4 max-w-md mx-auto animate-fade-in">
          <div class="w-14 h-14 rounded-2xl bg-[#E8F2FD] border border-[#CCE4FB] text-[#0071E3] text-2xl flex items-center justify-center mx-auto shadow-xs">
            📡
          </div>
          <div class="space-y-1">
            <h4 class="font-bold text-[#1D1D1F] text-sm">本地数据库暂无全网比价数据</h4>
            <p class="text-[#6E6E73] text-xs leading-relaxed">
              系统当前尚未同步大模型数据。您可以一键从 models.dev 官方基准库拉取 7,000+ 比价条目，或手动配置中转渠道。
            </p>
          </div>
          <div class="flex items-center justify-center space-x-3 pt-2">
            <button
              @click="triggerSync"
              :disabled="isSyncingAll"
              class="px-4 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-50 text-white font-bold text-xs shadow-sm transition-all flex items-center space-x-1.5 cursor-pointer"
            >
              <span v-if="isSyncingAll" class="animate-spin">⏳</span>
              <span v-else>⚡</span>
              <span>{{ isSyncingAll ? '正在全网同步...' : '立即从 models.dev 同步' }}</span>
            </button>
            <button
              @click="showAddModal = true"
              class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] font-medium text-xs border border-[#E5E5EA] transition-all flex items-center space-x-1 cursor-pointer"
            >
              <span>➕</span>
              <span>添加供应商与渠道</span>
            </button>
          </div>
        </div>

        <!-- 空状态 B: 筛选器无匹配 -->
        <div v-else-if="!isLoading && pagedItems.length === 0" class="py-12 text-center text-xs text-[#86868B] space-y-2">
          <div>无匹配的大模型比价数据，请调整筛选条件</div>
          <button
            v-if="hasAnyFilter || onlyFavorites"
            @click="resetAllFilters"
            class="px-3 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#FFE5E5] text-[#0071E3] hover:text-[#FF3B30] border border-[#E5E5EA] transition-all text-xs font-medium cursor-pointer"
          >
            重置所有筛选
          </button>
        </div>
      </div>

      <!-- 底部精致高性能分页控制栏 (苹果浅灰按钮组) -->
      <div class="pt-2.5 border-t border-[#E5E5EA] flex items-center justify-between text-xs text-[#6E6E73]">
        <!-- 左侧信息 -->
        <div class="flex items-center space-x-3 text-[11px]">
          <span>
            第 <strong class="text-[#1D1D1F] font-mono">{{ currentPage }}</strong> / <span class="font-mono">{{ totalPages }}</span> 页
            (共 <strong class="text-[#0071E3] font-mono">{{ totalRecords }}</strong> 条)
          </span>
          <div class="flex items-center space-x-1">
            <span>每页</span>
            <select
              v-model="pageSize"
              @change="handlePageSizeChange"
              class="bg-[#F2F2F7] border border-[#E5E5EA] rounded-md px-1.5 py-0.5 text-[#1D1D1F] font-mono text-xs focus:outline-none focus:border-[#0071E3]"
            >
              <option :value="20">20 条</option>
              <option :value="50">50 条</option>
              <option :value="100">100 条</option>
            </select>
          </div>
        </div>

        <!-- 中间页码翻页控制器 -->
        <div class="flex items-center space-x-1 font-mono">
          <button
            :disabled="currentPage <= 1"
            @click="changePage(1)"
            class="px-2 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-40 text-[#1D1D1F] border border-[#E5E5EA] text-[11px]"
            title="首页"
          >
            «
          </button>
          <button
            :disabled="currentPage <= 1"
            @click="changePage(currentPage - 1)"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-40 text-[#1D1D1F] border border-[#E5E5EA] text-[11px]"
          >
            ◀ 上一页
          </button>

          <!-- 数字页码按钮组 -->
          <div class="flex items-center space-x-1">
            <button
              v-for="p in visiblePages"
              :key="`page-${p}`"
              @click="changePage(p)"
              class="w-7 h-7 rounded-lg text-[11px] font-bold transition-all flex items-center justify-center"
              :class="
                currentPage === p
                  ? 'bg-[#0071E3] text-white shadow-xs'
                  : 'bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA]'
              "
            >
              {{ p }}
            </button>
          </div>

          <button
            :disabled="currentPage >= totalPages"
            @click="changePage(currentPage + 1)"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-40 text-[#1D1D1F] border border-[#E5E5EA] text-[11px]"
          >
            下一页 ▶
          </button>
          <button
            :disabled="currentPage >= totalPages"
            @click="changePage(totalPages)"
            class="px-2 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-40 text-[#1D1D1F] border border-[#E5E5EA] text-[11px]"
            title="末页"
          >
            »
          </button>
        </div>
      </div>
    </div>

    <!-- 底部：全网价格-TPS 性价比散点图 (ECharts 浅色苹果风格) -->
    <div class="h-44 flex-shrink-0 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] p-2.5 shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex flex-col min-h-[170px]">
      <div class="flex items-center justify-between pb-1.5 border-b border-[#E5E5EA]">
        <div class="flex items-center space-x-2 text-xs text-[#1D1D1F]">
          <span class="font-bold flex items-center space-x-1">
            <span>📈</span>
            <span>全网性价比散点分布</span>
          </span>
          <span class="text-[#D1D1D6]">•</span>
          <span class="text-[11px] text-[#6E6E73] font-medium">当前分析模型:</span>
          <!-- 智能模型选择器：可直接下拉切换当前列表中的任意模型 -->
          <div class="relative">
            <select
              v-model="manualScatterModelId"
              class="bg-[#F2F2F7] hover:bg-[#E8F2FD] focus:bg-[#FFFFFF] border border-[#CCE4FB] text-[#0071E3] font-mono text-xs font-bold rounded-lg px-2 py-0.5 focus:outline-none transition-all cursor-pointer shadow-2xs"
            >
              <option v-for="m in currentAvailableModelIds" :key="m" :value="m">
                {{ m }}
              </option>
            </select>
          </div>
          <span class="text-[10px] text-[#86868B] font-normal hidden lg:inline">| 💡 点击表格任一行或在此切换模型，越偏左上角综合性价比越高</span>
        </div>

        <div class="text-[11px] font-mono text-[#86868B]">
          全网接入 <strong class="text-[#0071E3]">{{ currentScatterItemsCount }}</strong> 个渠道节点
        </div>
      </div>
      <div class="flex-1 w-full relative min-h-0 mt-0.5">
        <div ref="scatterChartRef" class="w-full h-full"></div>
      </div>
    </div>

    <!-- 添加中转渠道向导弹窗 -->
    <AddChannelWizardModal
      v-if="showAddModal"
      @close="showAddModal = false"
      @saved="onModalSaved"
    />

    <!-- 右侧滑出：渠道详情与可用模型抽屉 (不跳页、无刷新，带筛选继承与范围切换) -->
    <ChannelDetailDrawer
      :visible="isChannelDrawerVisible"
      :site-name="targetChannelSiteName"
      :filter-context="drawerFilterContext"
      @close="closeChannelDrawer"
      @compare-model="handleDrawerCompareModel"
    />

    <!-- 右侧滑出：模型厂商详情与全系模型规格抽屉 (不跳页、无刷新，带筛选继承与范围切换) -->
    <VendorDetailDrawer
      :visible="isVendorDrawerVisible"
      :provider-id="targetVendorProviderId"
      :filter-context="drawerFilterContext"
      @close="closeVendorDrawer"
      @compare-model="handleDrawerCompareModel"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { useDashboardStore } from '../stores/dashboardStore'
import MultiSelectFilter, { type FilterOption } from '../components/MultiSelectFilter.vue'
import AddChannelWizardModal from '../components/AddChannelWizardModal.vue'
import ChannelDetailDrawer from '../components/ChannelDetailDrawer.vue'
import VendorDetailDrawer from '../components/VendorDetailDrawer.vue'
import type { ComparisonItem } from '../types'

const store = useDashboardStore()
const showAddModal = ref(false)
const isSyncingAll = ref(false)

// 右侧滑出抽屉状态控制 (支持厂商详情与渠道详情独立展开)
const isChannelDrawerVisible = ref(false)
const targetChannelSiteName = ref<string | null>(null)

const isVendorDrawerVisible = ref(false)
const targetVendorProviderId = ref<string | null>(null)

const drawerFilterContext = computed(() => {
  return {
    providers: selectedProviders.value,
    series: selectedSeries.value,
    models: selectedModels.value,
    availableModelIds: currentAvailableModelIds.value
  }
})

const openChannelDrawer = (siteName: string) => {
  targetChannelSiteName.value = siteName
  isChannelDrawerVisible.value = true
}

const closeChannelDrawer = () => {
  isChannelDrawerVisible.value = false
  targetChannelSiteName.value = null
}

const openVendorDrawer = (providerId: string) => {
  targetVendorProviderId.value = providerId
  isVendorDrawerVisible.value = true
}

const closeVendorDrawer = () => {
  isVendorDrawerVisible.value = false
  targetVendorProviderId.value = null
}

const handleDrawerCompareModel = (modelId: string) => {
  selectedModels.value = [modelId]
  handleModelChange([modelId])
}

async function triggerSync() {
  isSyncingAll.value = true
  try {
    await store.triggerFullSync()
    await fetchFilterOptions()
    await fetchPaginatedMatrix()
  } catch (e: any) {
    alert(`同步失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isSyncingAll.value = false
  }
}

async function onModalSaved() {
  showAddModal.value = false
  await store.fetchRelaySites()
  await store.fetchComparisonMatrix()
  await fetchFilterOptions()
  await fetchPaginatedMatrix()
}

// 厂商中文与别名映射表 (支持用户输入“深度探索”、“通义千问”、“Kimi”等模糊搜索)
const labNamesCn: Record<string, string> = {
  openai: 'OpenAI (ChatGPT)',
  anthropic: 'Anthropic (Claude)',
  google: 'Google (谷歌/Gemini)',
  deepseek: 'DeepSeek (深度求索/深度探索)',
  alibaba: 'Alibaba (阿里巴巴/通义千问/Qwen)',
  moonshotai: 'Moonshot AI (月之暗面/Kimi)',
  zhipuai: 'Zhipu AI (智谱/GLM)',
  bytedance: 'ByteDance (字节跳动/豆包)',
  tencent: 'Tencent (腾讯/混元)',
  minimax: 'MiniMax (名之梦)',
  meta: 'Meta (Facebook/Llama)',
  mistral: 'Mistral AI (欧洲顶尖开源)',
  nvidia: 'Nvidia (英伟达/Nemotron)',
  xai: 'xAI (马斯克/Grok)',
  cohere: 'Cohere (Command R)',
  stepfun: 'StepFun (阶跃星辰/跃问)',
  baichuan: 'Baichuan (百川智能)',
  xiaomi: 'Xiaomi (小米大模型)',
  microsoft: 'Microsoft (微软/MAI)',
  cloudflare: 'Cloudflare (Workers AI)',
  upstage: 'Upstage (Solar)',
  perplexity: 'Perplexity (AI 搜索)',
  meituan: 'Meituan (美团大模型)',
  internlm: 'InternLM (书生·浦语)',
  '01-ai': '01.AI (零一万物/Yi)',
  other: '其他独立研究机构 (Other)'
}

// 选中的多维筛选状态
const selectedProviders = ref<string[]>([])
const selectedSeries = ref<string[]>([])
const selectedModels = ref<string[]>([])
const selectedSites = ref<string[]>([])
const onlyFavorites = ref(false)

// 筛选候选项原始数据
const rawProviderOptions = ref<FilterOption[]>([])
const rawSeriesOptions = ref<FilterOption[]>([])
const rawModelOptions = ref<FilterOption[]>([])
const rawSiteOptions = ref<FilterOption[]>([])

// 1. 厂商候选列表：带中文别名 + 按字母 A-Z 严格排序 (除 other 置底)
const sortedProviderOptions = computed<FilterOption[]>(() => {
  const mapped = rawProviderOptions.value.map((opt) => {
    const key = opt.value.toLowerCase()
    const cnName = labNamesCn[key]
    return {
      value: opt.value,
      label: cnName || opt.label || opt.value,
      count: opt.count
    }
  })

  return mapped.sort((a, b) => {
    if (a.value === 'other') return 1
    if (b.value === 'other') return -1
    return a.label.localeCompare(b.label, 'zh-CN', { sensitivity: 'base' })
  })
})

// 2. 系列候选列表：按字母 A-Z 严格升序排序
const sortedSeriesOptions = computed<FilterOption[]>(() => {
  return [...rawSeriesOptions.value].sort((a, b) => {
    return a.label.localeCompare(b.label, 'zh-CN', { numeric: true, sensitivity: 'base' })
  })
})

// 3. 模型候选列表：按字母 A-Z 严格升序排序
const sortedModelOptions = computed<FilterOption[]>(() => {
  return [...rawModelOptions.value].sort((a, b) => {
    return a.label.localeCompare(b.label, 'zh-CN', { numeric: true, sensitivity: 'base' })
  })
})

// 4. 渠道候选列表：按字母 A-Z 严格升序排序
const sortedSiteOptions = computed<FilterOption[]>(() => {
  return [...rawSiteOptions.value].sort((a, b) => {
    return a.label.localeCompare(b.label, 'zh-CN', { numeric: true, sensitivity: 'base' })
  })
})

const getProviderLabel = (p: string) => {
  const key = p.toLowerCase()
  return labNamesCn[key] || p.toUpperCase()
}

// 分页状态
const pagedItems = ref<ComparisonItem[]>([])
const totalRecords = ref(0)
const totalPages = ref(1)
const currentPage = ref(1)
const pageSize = ref(50)
const isLoading = ref(false)

const scatterChartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const selectedRow = ref<ComparisonItem | null>(null)

// 构造标准的 URLSearchParams 请求参数，彻底解决 Axios 数组带 [] 导致 FastAPI 忽略参数的问题
const buildSearchParams = (paramsObj: Record<string, any>): URLSearchParams => {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(paramsObj)) {
    if (Array.isArray(v)) {
      for (const item of v) {
        if (item) sp.append(k, item)
      }
    } else if (v !== undefined && v !== null && v !== '') {
      sp.append(k, String(v))
    }
  }
  return sp
}

// 0 价格/未标价条目过滤状态 (默认开启隐藏)
const excludeZeroPrice = ref(true)

// 异步获取筛选器候选选项 (根据已选维度进行四级级联联动收敛)
const fetchFilterOptions = async (
  customProviders?: string[],
  customSeries?: string[],
  customModels?: string[]
) => {
  try {
    const providersToUse = customProviders !== undefined ? customProviders : selectedProviders.value
    const seriesToUse = customSeries !== undefined ? customSeries : selectedSeries.value
    const modelsToUse = customModels !== undefined ? customModels : selectedModels.value

    const params: Record<string, any> = {
      exclude_zero: excludeZeroPrice.value
    }
    if (providersToUse.length > 0) params.provider = providersToUse
    if (seriesToUse.length > 0) params.series = seriesToUse
    if (modelsToUse.length > 0) params.model = modelsToUse
    if (selectedSites.value.length > 0) params.site = selectedSites.value

    const sp = buildSearchParams(params)
    const res = await axios.get(`${store.apiUrl}/api/v1/comparison/filter-options?${sp.toString()}`)
    rawProviderOptions.value = res.data.providers || []
    rawSeriesOptions.value = res.data.series || []
    rawModelOptions.value = res.data.models || []
    rawSiteOptions.value = res.data.sites || []
  } catch (e) {
    console.error('Fetch filter options failed:', e)
  }
}

// 排序状态
const sortField = ref<string>('calculated_input_usd')
const sortOrder = ref<'asc' | 'desc'>('asc')

const toggleSort = (field: string) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    // 实测 TPS 默认从高到低排序，价格/倍率默认从低到高排序
    sortOrder.value = field === 'last_tested_tps' ? 'desc' : 'asc'
  }
  currentPage.value = 1
  fetchPaginatedMatrix()
}

const getSortIndicator = (field: string) => {
  if (sortField.value !== field) return '↕'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

// 异步分页拉取比价数据
const fetchPaginatedMatrix = async () => {
  isLoading.value = true
  try {
    let effectiveSites = [...selectedSites.value]
    if (onlyFavorites.value) {
      const favNames = store.favoriteSites.map((s) => s.name)
      if (favNames.length > 0) {
        effectiveSites = effectiveSites.length > 0 ? effectiveSites.filter((n) => favNames.includes(n)) : favNames
      } else {
        effectiveSites = ['__NONE__']
      }
    }

    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
      sort_by: sortField.value,
      sort_order: sortOrder.value,
      exclude_zero: excludeZeroPrice.value
    }
    if (selectedProviders.value.length > 0) params.provider = selectedProviders.value
    if (selectedSeries.value.length > 0) params.series = selectedSeries.value
    if (selectedModels.value.length > 0) params.model = selectedModels.value
    if (effectiveSites.length > 0) params.site = effectiveSites

    const sp = buildSearchParams(params)
    const res = await axios.get(`${store.apiUrl}/api/v1/comparison/paginated?${sp.toString()}`)
    pagedItems.value = res.data.items || []
    totalRecords.value = res.data.total || 0
    totalPages.value = res.data.total_pages || res.data.pages || 1
    currentPage.value = res.data.page || 1

    if (pagedItems.value.length > 0 && !selectedRow.value) {
      selectedRow.value = pagedItems.value[0]
    }
    updateScatterChart()
  } catch (e) {
    console.error('Fetch paginated matrix failed:', e)
  } finally {
    isLoading.value = false
  }
}

// ==================== 核心联动控制规则 ====================

// 1. 用户变更【模型厂商】-> 触发系列与模型收敛，清洗失效已选项
const handleProviderChange = async (newProviders: string[]) => {
  selectedProviders.value = newProviders
  currentPage.value = 1

  // 刷新级联候选项
  await fetchFilterOptions(newProviders, [], [])

  // 若已选系列不在新候选池中，清空系列
  if (selectedSeries.value.length > 0) {
    const validSeries = new Set(rawSeriesOptions.value.map((s) => s.value))
    selectedSeries.value = selectedSeries.value.filter((s) => validSeries.has(s))
  }
  // 若已选模型不在新候选池中，清空模型
  if (selectedModels.value.length > 0) {
    const validModels = new Set(rawModelOptions.value.map((m) => m.value))
    selectedModels.value = selectedModels.value.filter((m) => validModels.has(m))
  }

  fetchPaginatedMatrix()
}

// 2. 用户变更【模型系列】-> 触发模型收敛，清洗失效模型
const handleSeriesChange = async (newSeries: string[]) => {
  selectedSeries.value = newSeries
  currentPage.value = 1

  await fetchFilterOptions(selectedProviders.value, newSeries, [])

  if (selectedModels.value.length > 0) {
    const validModels = new Set(rawModelOptions.value.map((m) => m.value))
    selectedModels.value = selectedModels.value.filter((m) => validModels.has(m))
  }

  fetchPaginatedMatrix()
}

// 3. 用户选择【模型名称】-> 严格保留前面已选的厂商与系列，共同组合筛选！
const handleModelChange = (newModels: string[]) => {
  selectedModels.value = newModels
  currentPage.value = 1

  fetchPaginatedMatrix()
}

// 4. 渠道变更
const handleSiteChange = (newSites: string[]) => {
  selectedSites.value = newSites
  currentPage.value = 1
  fetchPaginatedMatrix()
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  fetchPaginatedMatrix()
}

const toggleOnlyFavorites = () => {
  onlyFavorites.value = !onlyFavorites.value
  currentPage.value = 1
  fetchPaginatedMatrix()
}

const toggleExcludeZero = () => {
  excludeZeroPrice.value = !excludeZeroPrice.value
  currentPage.value = 1
  fetchFilterOptions()
  fetchPaginatedMatrix()
}

const isSiteNameFavorite = (siteName: string): boolean => {
  const site = store.relaySites.find((s) => s.name === siteName)
  return site ? store.isSiteFavorite(site.id) : false
}

const toggleFavoriteByName = (siteName: string) => {
  const site = store.relaySites.find((s) => s.name === siteName)
  if (site) {
    store.toggleFavoriteSite(site.id)
  }
}

const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchPaginatedMatrix()
}

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

const isBenchmarkRow = (row: ComparisonItem) => {
  if (!store.highlightBenchmarkSiteName) return false
  return (row.site_name || '').toLowerCase() === store.highlightBenchmarkSiteName.toLowerCase()
}

const hasAnyFilter = computed(() => {
  return (
    selectedProviders.value.length > 0 ||
    selectedSeries.value.length > 0 ||
    selectedModels.value.length > 0 ||
    selectedSites.value.length > 0 ||
    !excludeZeroPrice.value ||
    !!store.highlightBenchmarkSiteName
  )
})

const resetAllFilters = () => {
  selectedProviders.value = []
  selectedSeries.value = []
  selectedModels.value = []
  selectedSites.value = []
  onlyFavorites.value = false
  excludeZeroPrice.value = true
  store.highlightBenchmarkSiteName = null
  currentPage.value = 1
  fetchFilterOptions()
  fetchPaginatedMatrix()
}

const checkAndApplyTargetFilters = () => {
  let changed = false
  if (store.targetModelFilter) {
    selectedModels.value = [store.targetModelFilter]
    selectedProviders.value = []
    selectedSeries.value = []
    selectedSites.value = []
    store.targetModelFilter = null
    changed = true
  }
  if (store.targetSiteFilter) {
    selectedSites.value = [store.targetSiteFilter]
    store.targetSiteFilter = null
    changed = true
  }
  if (store.targetProviderFilter) {
    selectedProviders.value = [store.targetProviderFilter]
    store.targetProviderFilter = null
    changed = true
  }
  return changed
}

// 快捷筛选分类聚合卡片模式与管理弹窗状态
const activePopoverDimension = ref<'provider' | 'series' | 'model' | 'site' | null>(null)
const popoverSearchQuery = ref('')

const toggleDimensionPopover = (dim: 'provider' | 'series' | 'model' | 'site') => {
  if (activePopoverDimension.value === dim) {
    activePopoverDimension.value = null
  } else {
    activePopoverDimension.value = dim
    popoverSearchQuery.value = ''
  }
}

const closeDimensionPopover = () => {
  activePopoverDimension.value = null
  popoverSearchQuery.value = ''
}

const filteredPopoverModels = computed(() => {
  if (!popoverSearchQuery.value.trim()) return selectedModels.value
  const q = popoverSearchQuery.value.toLowerCase().trim()
  return selectedModels.value.filter((m) => m.toLowerCase().includes(q))
})

const removeProvider = (p: string) => {
  const next = selectedProviders.value.filter((item) => item !== p)
  handleProviderChange(next)
}

const removeSeries = (s: string) => {
  const next = selectedSeries.value.filter((item) => item !== s)
  handleSeriesChange(next)
}

const removeModel = (m: string) => {
  const next = selectedModels.value.filter((item) => item !== m)
  handleModelChange(next)
}

const removeSite = (st: string) => {
  selectedSites.value = selectedSites.value.filter((item) => item !== st)
  handleSiteChange(selectedSites.value)
}

const selectRow = (row: ComparisonItem) => {
  selectedRow.value = row
  manualScatterModelId.value = row.model_id
  updateScatterChart()
}

const selectAndScrollToRow = (row: ComparisonItem) => {
  selectedRow.value = row
  manualScatterModelId.value = row.model_id
  updateScatterChart()

  nextTick(() => {
    const el = document.getElementById(`price-row-${row.id}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

const formatPrice = (usd: number, cny: number) => {
  if (store.currency === 'USD') {
    return `$${usd.toFixed(3)}`
  }
  return `¥${(cny || usd * (store.usdToCnyRate || 7.25)).toFixed(3)}`
}

// 监听全局货币切换与基准渠道，实时重绘散点图
watch(() => [store.currency, store.highlightBenchmarkSiteName], () => {
  updateScatterChart()
})

const getTypeBadgeClass = (type: string) => {
  if (type === 'official') return 'bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]'
  if (type === 'cloud') return 'bg-[#F3E8FF] text-[#9333EA] border border-[#E9D5FF]'
  if (type === 'newapi') return 'bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6]'
  return 'bg-[#FFF8E1] text-[#B78103] border border-[#FFE082]'
}

// 手动选择分析的散点图模型
const manualScatterModelId = ref<string>('')

// 当前表格页面内所有不重复的模型 ID 清单
const currentAvailableModelIds = computed<string[]>(() => {
  const set = new Set<string>()
  pagedItems.value.forEach((it) => {
    if (it.model_id) set.add(it.model_id)
  })
  return Array.from(set)
})

const activeScatterModelId = computed(() => {
  if (manualScatterModelId.value && currentAvailableModelIds.value.includes(manualScatterModelId.value)) {
    return manualScatterModelId.value
  }
  if (selectedRow.value && currentAvailableModelIds.value.includes(selectedRow.value.model_id)) {
    return selectedRow.value.model_id
  }
  return currentAvailableModelIds.value[0] || 'deepseek-v3'
})

const currentScatterItemsCount = computed(() => {
  return pagedItems.value.filter((item) => item.model_id === activeScatterModelId.value).length
})

watch(activeScatterModelId, () => {
  updateScatterChart()
})

const initScatterChart = () => {
  if (!scatterChartRef.value) return
  chartInstance = echarts.init(scatterChartRef.value)

  // 点击散点图中的数据点，自动高亮并平滑定位到表格对应的行
  chartInstance.on('click', (params: any) => {
    if (params.componentType === 'series') {
      const d = params.data
      const itemId = d[4]
      const siteName = d[2]
      const targetItem = pagedItems.value.find((it) => it.id === itemId) || pagedItems.value.find((it) => it.site_name === siteName)
      if (targetItem) {
        selectAndScrollToRow(targetItem)
      }
    }
  })

  updateScatterChart()
}

const updateScatterChart = () => {
  if (!chartInstance) return

  const targetModelId = activeScatterModelId.value
  const targetItems = pagedItems.value.filter((item) => item.model_id === targetModelId)

  const data = targetItems.map((item) => [
    store.currency === 'USD' ? item.calculated_input_usd : item.calculated_input_cny,
    item.last_tested_tps || 50,
    item.site_name,
    item.model_ratio,
    item.id
  ])

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    grid: {
      left: 50,
      right: 30,
      top: 15,
      bottom: 25
    },
    tooltip: {
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E5EA',
      textStyle: { color: '#1D1D1F', fontSize: 11 },
      formatter: (params: any) => {
        const d = params.data
        const isBm = store.highlightBenchmarkSiteName && (d[2] || '').toLowerCase() === store.highlightBenchmarkSiteName.toLowerCase()
        const isSel = selectedRow.value?.id === d[4] || (selectedRow.value && selectedRow.value.site_name === d[2])
        return `
          <div class="font-sans font-bold text-[#1D1D1F] flex items-center space-x-1">
            <span>${d[2]}</span>
            ${isBm ? '<span class="text-[#0071E3] font-bold text-[10px] ml-1">🎯(比价基准)</span>' : ''}
            ${isSel ? '<span class="text-[#FF9500] font-bold text-[10px] ml-1">📍(当前选中)</span>' : ''}
          </div>
          <div class="text-[#6E6E73] text-[10px]">输入价格: <strong class="text-[#34C759]">${store.currency === 'USD' ? '$' : '¥'}${d[0]}</strong></div>
          <div class="text-[#6E6E73] text-[10px]">实测速率: <strong class="text-[#0071E3]">${d[1]} TPS</strong></div>
          <div class="text-[9px] text-[#0071E3] mt-0.5 font-sans">💡 点击可直接定位列表并高亮</div>
        `
      }
    },
    xAxis: {
      type: 'value',
      name: `价格 (${store.currency})`,
      nameLocation: 'end',
      nameTextStyle: { color: '#86868B', fontSize: 10 },
      splitLine: { lineStyle: { color: '#E5E5EA', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#D1D1D6' } },
      axisLabel: { color: '#6E6E73', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: 'TPS',
      nameTextStyle: { color: '#86868B', fontSize: 10 },
      splitLine: { lineStyle: { color: '#E5E5EA', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#D1D1D6' } },
      axisLabel: { color: '#6E6E73', fontSize: 10 }
    },
    series: [
      {
        type: 'scatter',
        cursor: 'pointer',
        symbolSize: (dataItem: any) => {
          const siteName = dataItem[2] || ''
          const itemId = dataItem[4]
          if (selectedRow.value?.id === itemId || (selectedRow.value && selectedRow.value.site_name === siteName)) {
            return 22
          }
          if (store.highlightBenchmarkSiteName && siteName.toLowerCase() === store.highlightBenchmarkSiteName.toLowerCase()) {
            return 18
          }
          return 14
        },
        data: data,
        itemStyle: {
          color: (params: any) => {
            const siteName = params.data[2] || ''
            const itemId = params.data[4]
            if (selectedRow.value?.id === itemId || (selectedRow.value && selectedRow.value.site_name === siteName)) {
              return '#0071E3'
            }
            if (store.highlightBenchmarkSiteName && siteName.toLowerCase() === store.highlightBenchmarkSiteName.toLowerCase()) {
              return '#FF9500'
            }
            const ratio = params.data[3] || 1.0
            return ratio < 1.0 ? '#34C759' : '#0071E3'
          },
          borderWidth: (params: any) => {
            const siteName = params.data[2] || ''
            const itemId = params.data[4]
            if (selectedRow.value?.id === itemId || (selectedRow.value && selectedRow.value.site_name === siteName)) {
              return 3
            }
            return 1
          },
          borderColor: (params: any) => {
            const siteName = params.data[2] || ''
            const itemId = params.data[4]
            if (selectedRow.value?.id === itemId || (selectedRow.value && selectedRow.value.site_name === siteName)) {
              return '#FFD60A'
            }
            return '#FFFFFF'
          },
          shadowBlur: 8,
          shadowColor: 'rgba(0, 113, 227, 0.3)'
        }
      }
    ]
  }

  chartInstance.setOption(option)
  nextTick(() => {
    chartInstance?.resize()
  })
}

onMounted(async () => {
  checkAndApplyTargetFilters()
  await fetchFilterOptions()
  await fetchPaginatedMatrix()
  initScatterChart()
  window.addEventListener('resize', handleResize)
  window.addEventListener('click', closeDimensionPopover)
})

watch(
  () => [store.targetModelFilter, store.targetSiteFilter, store.targetProviderFilter],
  async () => {
    const changed = checkAndApplyTargetFilters()
    if (changed) {
      currentPage.value = 1
      await fetchFilterOptions()
      await fetchPaginatedMatrix()
    }
  }
)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('click', closeDimensionPopover)
  chartInstance?.dispose()
})

const handleResize = () => {
  chartInstance?.resize()
}
</script>

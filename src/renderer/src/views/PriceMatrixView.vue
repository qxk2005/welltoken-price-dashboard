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
            icon-name="provider"
            :options="sortedProviderOptions"
            :model-value="selectedProviders"
            @update:model-value="handleProviderChange"
          />

          <!-- 2. 模型系列多选 (A-Z 排序，根据已选厂商级联收敛) -->
          <MultiSelectFilter
            label="模型系列"
            icon-name="series"
            :options="sortedSeriesOptions"
            :model-value="selectedSeries"
            @update:model-value="handleSeriesChange"
          />

          <!-- 3. 模型名称多选 (A-Z 排序，保留前面的厂商与系列) -->
          <MultiSelectFilter
            label="模型名称"
            icon-name="cpu"
            :options="sortedModelOptions"
            :model-value="selectedModels"
            @update:model-value="handleModelChange"
          />

          <!-- 4. 渠道中转站多选 (A-Z 排序，支持模糊搜索 如“七牛”, “OpenRouter”, “硅基”) -->
          <MultiSelectFilter
            label="渠道中转站"
            icon-name="site"
            :options="sortedSiteOptions"
            :model-value="selectedSites"
            @update:model-value="handleSiteChange"
          />

          <!-- 5. 更新日期范围筛选胶囊与下拉弹层 -->
          <div class="relative" ref="dateFilterContainerRef">
            <button
              @click.stop="toggleDateFilterPopover"
              class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1.5 cursor-pointer shadow-2xs group select-none"
              :class="isDateFilterActive
                ? 'bg-[#E8F2FD] border-[#0071E3] text-[#0071E3] font-bold shadow-xs'
                : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
              :title="`当前更新日期范围: ${dateFilterLabel}`"
            >
              <SystemIcon name="calendar" custom-class="w-3.5 h-3.5" :class="isDateFilterActive ? 'text-[#0071E3]' : 'text-[#86868B] group-hover:text-[#1D1D1F]'" />
              <span>{{ dateFilterLabel }}</span>
              <span class="text-[10px] opacity-60">▾</span>
              <!-- 已选状态下的一键清除按钮 -->
              <span
                v-if="isDateFilterActive"
                @click.stop="clearDateFilter"
                class="hover:text-[#FF3B30] ml-1 cursor-pointer font-bold"
                title="清除日期筛选"
              >✕</span>
            </button>

            <!-- 日期范围弹层 Popover -->
            <div
              v-if="isDateFilterOpen"
              class="absolute left-0 top-10 w-72 bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-[0_12px_36px_rgba(0,0,0,0.14)] z-40 p-3 animate-fade-in text-xs space-y-3"
            >
              <div class="flex items-center justify-between pb-2 border-b border-[#E5E5EA]">
                <div class="flex items-center space-x-1.5 font-bold text-[#1D1D1F]">
                  <SystemIcon name="calendar" custom-class="w-3.5 h-3.5 text-[#0071E3]" />
                  <span>更新日期范围</span>
                </div>
                <button
                  v-if="isDateFilterActive"
                  @click="clearDateFilter"
                  class="text-[11px] text-[#FF3B30] hover:underline cursor-pointer"
                >
                  重置
                </button>
              </div>

              <!-- 快捷预设按钮 -->
              <div class="space-y-1.5">
                <div class="text-[11px] text-[#86868B] font-medium">快捷预设</div>
                <div class="grid grid-cols-3 gap-1.5">
                  <button
                    v-for="preset in datePresets"
                    :key="preset.id"
                    @click="applyDatePreset(preset.id)"
                    class="px-2 py-1.5 rounded-lg text-center transition-all cursor-pointer text-xs font-medium border"
                    :class="selectedDatePreset === preset.id
                      ? 'bg-[#0071E3] text-white border-[#0071E3] shadow-xs font-bold'
                      : 'bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border-[#E5E5EA]'"
                  >
                    {{ preset.label }}
                  </button>
                </div>
              </div>

              <!-- 自定义起止时间 -->
              <div class="space-y-2 pt-2 border-t border-[#E5E5EA]/80">
                <div class="text-[11px] text-[#86868B] font-medium flex items-center justify-between">
                  <span>自定义起止日期</span>
                  <span v-if="selectedDatePreset === 'custom'" class="text-[10px] text-[#0071E3] font-bold">已启用自定义</span>
                </div>
                <div class="space-y-1.5 font-mono">
                  <div class="flex items-center space-x-2">
                    <span class="text-[10px] text-[#86868B] w-8">起始:</span>
                    <input
                      type="date"
                      v-model="customDateStart"
                      class="flex-1 bg-[#F2F2F7] border border-[#E5E5EA] rounded-lg px-2 py-1 text-xs text-[#1D1D1F] focus:bg-white focus:border-[#0071E3] focus:outline-none transition-all"
                    />
                  </div>
                  <div class="flex items-center space-x-2">
                    <span class="text-[10px] text-[#86868B] w-8">截止:</span>
                    <input
                      type="date"
                      v-model="customDateEnd"
                      class="flex-1 bg-[#F2F2F7] border border-[#E5E5EA] rounded-lg px-2 py-1 text-xs text-[#1D1D1F] focus:bg-white focus:border-[#0071E3] focus:outline-none transition-all"
                    />
                  </div>
                </div>
                <div class="flex items-center justify-end space-x-2 pt-1">
                  <button
                    @click="isDateFilterOpen = false"
                    class="px-2.5 py-1 rounded-lg text-[#6E6E73] hover:bg-[#F2F2F7] text-xs cursor-pointer"
                  >
                    取消
                  </button>
                  <button
                    @click="applyCustomDateRange"
                    :disabled="!customDateStart && !customDateEnd"
                    class="px-3 py-1 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] disabled:opacity-40 text-white text-xs font-bold shadow-xs cursor-pointer transition-all"
                  >
                    应用区间
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 6. 仅看已收藏渠道快捷胶囊 -->
          <button
            @click="toggleOnlyFavorites"
            class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1.5 cursor-pointer shadow-2xs"
            :class="onlyFavorites ? 'bg-[#FFF8E1] border-[#FFE082] text-[#B78103] font-bold shadow-xs' : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
          >
            <SystemIcon :name="onlyFavorites ? 'star-filled' : 'star'" custom-class="w-3.5 h-3.5" :class="onlyFavorites ? 'text-amber-500 fill-amber-500' : 'text-[#86868B]'" />
            <span>{{ onlyFavorites ? '已开启仅看收藏' : '仅看已收藏渠道' }}</span>
            <span v-if="store.favoriteSiteIds.length > 0" class="text-[10px] font-mono opacity-80">({{ store.favoriteSiteIds.length }})</span>
          </button>

          <!-- 6. 隐藏 0 元 / 未标价条目快捷切换胶囊 -->
          <button
            @click="toggleExcludeZero"
            class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1.5 cursor-pointer shadow-2xs"
            :class="excludeZeroPrice ? 'bg-[#EBF5FF] border-[#B9E1FF] text-[#0071E3] font-bold shadow-xs' : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
            title="点击切换是否过滤输入与输出单价均为 0 的免费/占位/未标价条目"
          >
            <SystemIcon :name="excludeZeroPrice ? 'ban' : 'eye'" custom-class="w-3.5 h-3.5" :class="excludeZeroPrice ? 'text-[#0071E3]' : 'text-[#86868B]'" />
            <span>{{ excludeZeroPrice ? '已隐藏 0 元/未标价' : '显示全部 (含 0 元)' }}</span>
          </button>
        </div>

        <!-- 右侧：快捷操作与匹配统计 -->
        <div class="flex items-center space-x-2 text-xs">
          <span class="text-[#6E6E73]">
            全网匹配: <strong class="text-[#0071E3] font-mono font-bold">{{ totalRecords }}</strong> 条报价
          </span>

          <!-- 自定义列设置按钮 -->
          <button
            @click="showColumnConfigModal = true"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] transition-all text-xs flex items-center space-x-1 cursor-pointer font-medium"
            title="自定义表格显示列与显示顺序"
          >
            <span>🎛️</span>
            <span>自定义列</span>
          </button>

          <button
            @click="handleExportPriceMatrix"
            :disabled="isExporting || totalRecords === 0"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#CCE4FB] transition-all text-xs flex items-center space-x-1 cursor-pointer font-medium disabled:opacity-50"
            title="导出当前筛选条件下的全量比价数据为 Excel 文件"
          >
            <span v-if="isExporting" class="animate-spin">⏳</span>
            <span v-else>📊</span>
            <span>{{ isExporting ? '正在导出...' : '导出 Excel' }}</span>
          </button>
          <button
            v-if="hasAnyFilter || onlyFavorites"
            @click="resetAllFilters"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#FFE5E5] text-[#6E6E73] hover:text-[#FF3B30] border border-[#E5E5EA] transition-all text-xs flex items-center space-x-1 cursor-pointer"
          >
            <SystemIcon name="rotate-ccw" custom-class="w-3 h-3" />
            <span>重置筛选</span>
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
            <SystemIcon name="star-filled" custom-class="w-3 h-3 text-amber-500 fill-amber-500" />
            <span>仅看收藏</span>
            <button @click="onlyFavorites = false" class="hover:text-[#8C6300] ml-0.5 cursor-pointer">✕</button>
          </span>

          <!-- 2. 模型厂商 Dimension Pill & Popover -->
          <div v-if="selectedProviders.length > 0" class="relative inline-block" @click.stop>
            <span
              @click="selectedProviders.length > 1 ? toggleDimensionPopover('provider') : null"
              class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E8F2FD] border border-[#CCE4FB] text-[#0071E3] text-[11px] font-medium transition-all"
              :class="selectedProviders.length > 1 ? 'cursor-pointer hover:bg-[#D9EAFE] hover:border-[#B6D9FD]' : ''"
            >
              <SystemIcon name="provider" custom-class="w-3 h-3 text-[#0071E3]" />
              <span>{{ selectedProviders.length === 1 ? getProviderLabel(selectedProviders[0]) : `模型厂商: ${selectedProviders.length} 个` }}</span>
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
              <SystemIcon name="series" custom-class="w-3 h-3 text-[#9333EA]" />
              <span>{{ selectedSeries.length === 1 ? selectedSeries[0] : `模型系列: ${selectedSeries.length} 个` }}</span>
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

          <!-- 4. 模型名称 Dimension Pill & Popover -->
          <div v-if="selectedModels.length > 0" class="relative inline-block" @click.stop>
            <span
              @click="selectedModels.length > 1 ? toggleDimensionPopover('model') : null"
              class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E8F8EE] border border-[#B7EB8F] text-[#389E0D] text-[11px] font-medium transition-all"
              :class="selectedModels.length > 1 ? 'cursor-pointer hover:bg-[#D9F7BE] hover:border-[#95DE64]' : ''"
            >
              <SystemIcon name="model" custom-class="w-3 h-3 text-[#389E0D]" />
              <span>{{ selectedModels.length === 1 ? selectedModels[0] : `模型: ${selectedModels.length} 个` }}</span>
              <span v-if="selectedModels.length > 1" class="text-[9px] text-[#389E0D]">▾</span>
              <button @click.stop="handleModelChange([])" class="hover:text-[#135200] ml-0.5 cursor-pointer font-bold" title="清除所有选中的模型">✕</button>
            </span>

            <!-- Popover Dropdown -->
            <div
              v-if="activePopoverDimension === 'model'"
              class="absolute left-0 top-7 w-80 bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-[0_16px_36px_rgba(0,0,0,0.15)] z-30 p-3 animate-fade-in text-xs space-y-2.5"
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

              <div class="max-h-48 overflow-y-auto pr-1 flex flex-wrap gap-1">
                <span
                  v-for="m in filteredPopoverModels"
                  :key="`pop-m-${m}`"
                  class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E8F8EE] border border-[#B7EB8F] text-[#389E0D] text-[11px] font-mono"
                >
                  <span class="truncate max-w-[180px]">{{ m }}</span>
                  <button @click="removeModel(m)" class="hover:text-[#FF3B30] ml-0.5 cursor-pointer font-bold">✕</button>
                </span>
                <div v-if="filteredPopoverModels.length === 0" class="py-3 text-center text-[#86868B] text-xs w-full">
                  无匹配的已选模型
                </div>
              </div>
            </div>
          </div>

          <!-- 5. 渠道/中转站 Dimension Pill & Popover -->
          <div v-if="selectedSites.length > 0" class="relative inline-block" @click.stop>
            <span
              @click="selectedSites.length > 1 ? toggleDimensionPopover('site') : null"
              class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#FFF0E6] border border-[#FFD8BF] text-[#D4380D] text-[11px] font-medium transition-all"
              :class="selectedSites.length > 1 ? 'cursor-pointer hover:bg-[#FFE7BA] hover:border-[#FFC069]' : ''"
            >
              <SystemIcon name="channel" custom-class="w-3 h-3 text-[#D4380D]" />
              <span>{{ selectedSites.length === 1 ? selectedSites[0] : `渠道: ${selectedSites.length} 个` }}</span>
              <span v-if="selectedSites.length > 1" class="text-[9px] text-[#D4380D]">▾</span>
              <button @click.stop="handleSiteChange([])" class="hover:text-[#871400] ml-0.5 cursor-pointer font-bold" title="清除所有选中的渠道">✕</button>
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

          <!-- 6. 更新时间范围 Chip -->
          <span
            v-if="isDateFilterActive"
            class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-[#E8F2FD] border border-[#CCE4FB] text-[#0071E3] text-[11px] font-medium shadow-2xs animate-fade-in"
          >
            <SystemIcon name="calendar" custom-class="w-3 h-3 text-[#0071E3]" />
            <span>更新时间: {{ dateFilterLabel }}</span>
            <button @click.stop="clearDateFilter" class="hover:text-[#FF3B30] ml-0.5 cursor-pointer font-bold" title="清除更新时间筛选">✕</button>
          </span>

          <!-- 7. 基准渠道指示 Chip -->
          <span
            v-if="store.highlightBenchmarkSiteName"
            class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-[#E8F2FD] border border-[#0071E3] text-[#0071E3] text-[11px] font-bold shadow-2xs animate-fade-in"
          >
            <SystemIcon name="target" custom-class="w-3 h-3 text-[#0071E3]" />
            <span>比价基准: {{ store.highlightBenchmarkSiteName }}</span>
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
    <div class="flex-1 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex flex-col min-h-0 relative overflow-hidden">
      <!-- 表格滚动区 -->
      <div class="flex-1 overflow-x-auto overflow-y-auto pr-1 relative">
        <div v-if="isLoading" class="absolute inset-0 bg-white/70 backdrop-blur-xs flex items-center justify-center z-20">
          <div class="text-xs text-[#0071E3] font-medium flex items-center space-x-2">
            <span class="animate-spin">🌀</span>
            <span>加载报价数据中...</span>
          </div>
        </div>

        <table class="w-full text-left text-xs border-collapse min-w-full table-fixed">
          <!-- 表头 (支持点击多列排序与鼠标拖拽调整列宽) -->
          <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans select-none whitespace-nowrap">
            <tr>
              <!-- 固定首列：模型标准标识 -->
              <th
                @click="toggleSort('model_id')"
                class="py-3 px-2 cursor-pointer hover:text-[#1D1D1F] transition-colors relative group/th"
                :style="{ width: getMatrixColWidth('model_id'), minWidth: getMatrixColWidth('model_id') }"
              >
                <div class="truncate pr-2">
                  模型标准标识 <span class="text-[10px] font-mono" :class="sortField === 'model_id' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('model_id') }}</span>
                </div>
                <!-- 拖拽列宽手柄 -->
                <div
                  class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                  @mousedown.stop="startMatrixResize('model_id', $event)"
                  @dblclick.stop="resetMatrixColWidth('model_id')"
                  title="按住拖拽调整列宽，双击恢复默认"
                ></div>
              </th>

              <!-- 动态配置列表头 -->
              <template v-for="col in visibleMatrixColumns" :key="col.key">
                <th
                  v-if="col.key === 'series'"
                  @click="toggleSort('series')"
                  class="py-3 px-2 cursor-pointer hover:text-[#1D1D1F] transition-colors relative group/th"
                  :style="{ width: getMatrixColWidth('series'), minWidth: getMatrixColWidth('series') }"
                >
                  <div class="truncate pr-2">
                    模型系列 / 厂商 <span class="text-[10px] font-mono" :class="sortField === 'series' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('series') }}</span>
                  </div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('series', $event)"
                    @dblclick.stop="resetMatrixColWidth('series')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>

                <th
                  v-else-if="col.key === 'site_name'"
                  @click="toggleSort('site_name')"
                  class="py-3 px-2 cursor-pointer hover:text-[#1D1D1F] transition-colors relative group/th"
                  :style="{ width: getMatrixColWidth('site_name'), minWidth: getMatrixColWidth('site_name') }"
                >
                  <div class="truncate pr-2">
                    渠道 / 供应商 <span class="text-[10px] font-mono" :class="sortField === 'site_name' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('site_name') }}</span>
                  </div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('site_name', $event)"
                    @dblclick.stop="resetMatrixColWidth('site_name')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>

                <th
                  v-else-if="col.key === 'site_type'"
                  class="py-3 px-1.5 text-center relative group/th"
                  :style="{ width: getMatrixColWidth('site_type'), minWidth: getMatrixColWidth('site_type') }"
                >
                  <div class="truncate pr-1">类型</div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('site_type', $event)"
                    @dblclick.stop="resetMatrixColWidth('site_type')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>

                <th
                  v-else-if="col.key === 'input_price'"
                  @click="toggleSort('calculated_input_usd')"
                  class="py-3 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors relative group/th"
                  :style="{ width: getMatrixColWidth('input_price'), minWidth: getMatrixColWidth('input_price') }"
                >
                  <div class="truncate pr-2">
                    输入单价 <span class="text-[10px] font-mono" :class="sortField === 'calculated_input_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('calculated_input_usd') }}</span>
                  </div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('input_price', $event)"
                    @dblclick.stop="resetMatrixColWidth('input_price')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>

                <th
                  v-else-if="col.key === 'output_price'"
                  @click="toggleSort('calculated_output_usd')"
                  class="py-3 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors relative group/th"
                  :style="{ width: getMatrixColWidth('output_price'), minWidth: getMatrixColWidth('output_price') }"
                >
                  <div class="truncate pr-2">
                    输出单价 <span class="text-[10px] font-mono" :class="sortField === 'calculated_output_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('calculated_output_usd') }}</span>
                  </div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('output_price', $event)"
                    @dblclick.stop="resetMatrixColWidth('output_price')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>

                <th
                  v-else-if="col.key === 'cache_price'"
                  @click="toggleSort('calculated_cache_usd')"
                  class="py-3 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors relative group/th"
                  :style="{ width: getMatrixColWidth('cache_price'), minWidth: getMatrixColWidth('cache_price') }"
                >
                  <div class="truncate pr-2">
                    命中缓存 <span class="text-[10px] font-mono" :class="sortField === 'calculated_cache_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('calculated_cache_usd') }}</span>
                  </div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('cache_price', $event)"
                    @dblclick.stop="resetMatrixColWidth('cache_price')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>

                <th
                  v-else-if="col.key === 'model_ratio'"
                  @click="toggleSort('model_ratio')"
                  class="py-3 px-1.5 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors relative group/th"
                  :style="{ width: getMatrixColWidth('model_ratio'), minWidth: getMatrixColWidth('model_ratio') }"
                >
                  <div class="truncate pr-1">
                    倍率 <span class="text-[10px] font-mono" :class="sortField === 'model_ratio' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('model_ratio') }}</span>
                  </div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('model_ratio', $event)"
                    @dblclick.stop="resetMatrixColWidth('model_ratio')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>

                <th
                  v-else-if="col.key === 'tps'"
                  @click="toggleSort('last_tested_tps')"
                  class="py-3 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors relative group/th"
                  :style="{ width: getMatrixColWidth('tps'), minWidth: getMatrixColWidth('tps') }"
                >
                  <div class="truncate pr-2">
                    实测 TPS <span class="text-[10px] font-mono" :class="sortField === 'last_tested_tps' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('last_tested_tps') }}</span>
                  </div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('tps', $event)"
                    @dblclick.stop="resetMatrixColWidth('tps')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>

                <th
                  v-else-if="col.key === 'updated_at'"
                  class="py-3 px-2 text-right select-none relative group/th"
                  :style="{ width: getMatrixColWidth('updated_at'), minWidth: getMatrixColWidth('updated_at') }"
                >
                  <div class="flex items-center justify-end space-x-1 pr-2 truncate">
                    <span
                      @click="toggleTimeDisplayMode"
                      class="cursor-pointer hover:text-[#0071E3] transition-colors inline-flex items-center space-x-1"
                      :title="`当前模式: ${timeDisplayMode === 'relative' ? '人性化相对时间' : '绝对日期时间'}。点击表头文字一键切换`"
                    >
                      <span>更新时间</span>
                      <span class="text-[9px] font-normal text-[#86868B]">({{ timeDisplayMode === 'relative' ? '相对' : '绝对' }})</span>
                    </span>
                    <button
                      @click.stop="toggleSort('updated_at')"
                      class="p-0.5 hover:bg-[#E5E5EA] rounded cursor-pointer transition-colors"
                      title="点击按更新时间升/降序排序"
                    >
                      <span class="text-[10px] font-mono" :class="sortField === 'updated_at' || sortField === 'source_updated_at' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">
                        {{ getSortIndicator('updated_at') }}
                      </span>
                    </button>
                  </div>
                  <div
                    class="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-[#0071E3]/40 active:bg-[#0071E3] transition-colors z-20"
                    @mousedown.stop="startMatrixResize('updated_at', $event)"
                    @dblclick.stop="resetMatrixColWidth('updated_at')"
                    title="按住拖拽调整列宽，双击恢复默认"
                  ></div>
                </th>
              </template>
            </tr>
          </thead>

          <!-- 数据行体 -->
          <tbody v-if="pagedItems.length > 0" class="divide-y divide-[#E5E5EA]/60 font-sans">
            <tr
              v-for="row in pagedItems"
              :key="row.id"
              :id="`price-row-${row.id}`"
              @click="selectRow(row)"
              class="hover:bg-[#F5F5F7] transition-colors cursor-pointer"
              :class="[
                selectedRow?.id === row.id
                  ? 'bg-[#E8F2FD] font-medium'
                  : '',
                isBenchmarkRow(row) && selectedRow?.id !== row.id
                  ? 'bg-[#E8F2FD]/50'
                  : ''
              ]"
            >
              <!-- 1. 模型标准标识 与 梯度/分段定价标签 (双行紧凑布局) -->
              <td class="py-2 px-2" :style="{ width: getMatrixColWidth('model_id'), minWidth: getMatrixColWidth('model_id') }">
                <div class="flex flex-col space-y-0.5 truncate">
                  <div class="font-bold text-[#0071E3] font-mono truncate text-xs" :title="row.model_id">
                    {{ row.model_id }}
                  </div>
                  <!-- 第 2 行：分段/区间定价或自定义别名徽章 -->
                  <div
                    v-if="row.site_model_name && row.site_model_name !== row.model_id"
                    class="inline-flex items-center space-x-1 text-[#86868B] text-[10px] font-mono truncate max-w-[280px]"
                    :title="`渠道定价规格/区间说明: ${row.site_model_name}`"
                  >
                    <span
                      v-if="isTieredModel(row.site_model_name)"
                      class="px-1 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-bold shrink-0 leading-tight"
                    >
                      分段
                    </span>
                    <span class="truncate">{{ row.site_model_name }}</span>
                  </div>
                </div>
              </td>

              <!-- 动态配置列单元格 -->
              <template v-for="col in visibleMatrixColumns" :key="col.key">
                <!-- 模型系列与厂商 (双行紧凑布局) -->
                <td v-if="col.key === 'series'" class="py-2 px-2" :style="{ width: getMatrixColWidth('series'), minWidth: getMatrixColWidth('series') }">
                  <div class="flex flex-col space-y-0.5 truncate">
                    <div class="flex items-center space-x-1">
                      <button
                        @click.stop="openVendorDrawer(row.provider)"
                        class="px-1.5 py-0.2 rounded bg-[#F2F2F7] hover:bg-[#0071E3] hover:text-white text-[#1D1D1F] border border-[#E5E5EA] text-[10px] font-mono font-bold transition-all cursor-pointer shadow-2xs group/btn inline-flex items-center space-x-0.5 flex-shrink-0"
                        :title="`点击在右侧查看 ${row.provider.toUpperCase()} 厂商所有模型规格与详情`"
                      >
                        <span>{{ row.provider.toUpperCase() }}</span>
                        <SystemIcon name="detail" custom-class="w-2.5 h-2.5 text-[#0071E3] group-hover/btn:text-white" />
                      </button>
                    </div>
                    <div class="text-[#6E6E73] font-medium truncate text-[11px]">
                      {{ row.series || '通用' }}
                    </div>
                  </div>
                </td>

                <!-- 渠道站点与收藏星标 (双行紧凑布局) -->
                <td v-else-if="col.key === 'site_name'" class="py-2 px-2" :style="{ width: getMatrixColWidth('site_name'), minWidth: getMatrixColWidth('site_name') }">
                  <div class="flex flex-col space-y-0.5 truncate">
                    <div class="flex items-center space-x-1.5 truncate">
                      <button
                        @click.stop="toggleFavoriteByName(row.site_name)"
                        class="transition-transform hover:scale-125 focus:outline-none cursor-pointer flex-shrink-0"
                        :title="isSiteNameFavorite(row.site_name) ? '点击取消收藏' : '点击收藏该渠道'"
                      >
                        <SystemIcon
                          :name="isSiteNameFavorite(row.site_name) ? 'star-filled' : 'star'"
                          custom-class="w-3.5 h-3.5"
                          :class="isSiteNameFavorite(row.site_name) ? 'text-amber-500 fill-amber-500' : 'text-[#AEAEB2] hover:text-amber-500'"
                        />
                      </button>
                      <button
                        @click.stop="openChannelDrawer(row.site_name)"
                        class="font-semibold text-[#1D1D1F] hover:text-[#0071E3] hover:underline cursor-pointer truncate text-xs transition-colors text-left flex items-center space-x-1 group/ch"
                        :title="`点击在右侧查看「${row.site_name}」渠道详情与可用模型定价`"
                      >
                        <span class="truncate">{{ row.site_name }}</span>
                        <SystemIcon name="detail" custom-class="w-2.5 h-2.5 text-[#0071E3] opacity-60 group-hover/ch:opacity-100" />
                      </button>
                      <!-- 当前比价基准渠道徽标 -->
                      <span
                        v-if="isBenchmarkRow(row)"
                        class="px-1.5 py-0.2 rounded-full bg-[#0071E3] text-white text-[9px] font-bold flex-shrink-0 shadow-xs flex items-center space-x-0.5 animate-pulse"
                        title="这是你在渠道详情中发起全网比价的原渠道（比价基准）"
                      >
                        <SystemIcon name="target" custom-class="w-2.5 h-2.5" />
                        <span>基准</span>
                      </span>
                    </div>

                    <!-- 结算分组第二行 -->
                    <div v-if="row.group_name" class="flex items-center space-x-1">
                      <span
                        class="px-1 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-mono font-bold truncate flex-shrink-0 shadow-2xs inline-flex items-center space-x-0.5"
                        :title="`结算分组: ${row.group_name}`"
                      >
                        <SystemIcon name="target" custom-class="w-2 h-2 text-[#8E24AA]" />
                        <span>{{ row.group_name }}</span>
                      </span>
                    </div>
                  </div>
                </td>

                <!-- 类型徽标 -->
                <td v-else-if="col.key === 'site_type'" class="py-2 px-1.5 text-center" :style="{ width: getMatrixColWidth('site_type'), minWidth: getMatrixColWidth('site_type') }">
                  <span
                    class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold uppercase"
                    :class="getTypeBadgeClass(row.site_type)"
                  >
                    {{ row.site_type }}
                  </span>
                </td>

                <!-- 输入价格 -->
                <td v-else-if="col.key === 'input_price'" class="py-2 px-2 text-right font-mono font-bold text-[#34C759] text-xs" :style="{ width: getMatrixColWidth('input_price'), minWidth: getMatrixColWidth('input_price') }">
                  {{ formatPrice(row.calculated_input_usd, row.calculated_input_cny) }}
                </td>

                <!-- 输出价格 -->
                <td v-else-if="col.key === 'output_price'" class="py-2 px-2 text-right font-mono text-[#1D1D1F] text-xs" :style="{ width: getMatrixColWidth('output_price'), minWidth: getMatrixColWidth('output_price') }">
                  {{ formatPrice(row.calculated_output_usd, row.calculated_output_cny) }}
                </td>

                <!-- 命中缓存单价 -->
                <td v-else-if="col.key === 'cache_price'" class="py-2 px-2 text-right font-mono font-semibold text-xs" :style="{ width: getMatrixColWidth('cache_price'), minWidth: getMatrixColWidth('cache_price') }">
                  <span v-if="(row.calculated_cache_usd && row.calculated_cache_usd > 0) || (row.calculated_cache_cny && row.calculated_cache_cny > 0)" class="text-[#8E24AA]">
                    {{ formatPrice(row.calculated_cache_usd, row.calculated_cache_cny || (row.calculated_cache_usd * (store.usdToCnyRate || 7.25))) }}
                  </span>
                  <span v-else class="text-[#AEAEB2] font-normal">-</span>
                </td>

                <!-- 倍率 -->
                <td v-else-if="col.key === 'model_ratio'" class="py-2 px-1.5 text-center font-mono text-[#6E6E73] font-semibold text-xs" :style="{ width: getMatrixColWidth('model_ratio'), minWidth: getMatrixColWidth('model_ratio') }">
                  {{ row.model_ratio }}x
                </td>

                <!-- 实测 TPS -->
                <td v-else-if="col.key === 'tps'" class="py-2 px-2 text-right font-mono text-[#0071E3] font-bold text-xs" :style="{ width: getMatrixColWidth('tps'), minWidth: getMatrixColWidth('tps') }">
                  {{ row.last_tested_tps }} <span class="text-[9px] text-[#86868B] font-normal">tps</span>
                </td>

                <!-- 数据更新时间 (区分 models.dev 原生时间与手工渠道同步时间) -->
                <td v-else-if="col.key === 'updated_at'" class="py-2 px-2 text-right whitespace-nowrap" :style="{ width: getMatrixColWidth('updated_at'), minWidth: getMatrixColWidth('updated_at') }">
                  <div class="flex items-center justify-end space-x-1.5" :title="getSourceTimeTooltip(row)">
                    <span
                      class="w-4 h-4 rounded inline-flex items-center justify-center font-mono font-bold text-[10px] flex-shrink-0"
                      :class="row.is_official_catalog !== false && row.source_time_type !== 'manual'
                        ? 'bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]'
                        : 'bg-[#E8F8EE] text-[#34C759] border border-[#34C759]/20'"
                    >
                      {{ row.is_official_catalog !== false && row.source_time_type !== 'manual' ? 'm' : 'c' }}
                    </span>
                    <span class="font-mono text-xs text-[#6E6E73]">
                      {{ formatSourceTime(row) }}
                    </span>
                  </div>
                </td>
              </template>
            </tr>
          </tbody>
        </table>

        <!-- 空状态 A: 库内完全无数据 (首次使用引导) -->
        <div v-if="!isLoading && pagedItems.length === 0 && !hasAnyFilter && !onlyFavorites && totalRecords === 0" class="py-16 px-6 text-center space-y-4 max-w-md mx-auto animate-fade-in">
          <div class="w-14 h-14 rounded-2xl bg-[#E8F2FD] border border-[#CCE4FB] text-[#0071E3] flex items-center justify-center mx-auto shadow-xs">
            <SystemIcon name="price-matrix" custom-class="w-7 h-7 text-[#0071E3]" />
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
              <SystemIcon v-if="isSyncingAll" name="refresh" custom-class="w-3.5 h-3.5 animate-spin" />
              <SystemIcon v-else name="zap" custom-class="w-3.5 h-3.5" />
              <span>{{ isSyncingAll ? '正在全网同步...' : '立即从 models.dev 同步' }}</span>
            </button>
            <button
              @click="showAddModal = true"
              class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] font-medium text-xs border border-[#E5E5EA] transition-all flex items-center space-x-1 cursor-pointer"
            >
              <SystemIcon name="plus" custom-class="w-3.5 h-3.5" />
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
        <div class="flex items-center space-x-2 text-xs text-[#1D1D1F] flex-wrap gap-y-1">
          <span class="font-bold flex items-center space-x-1.5">
            <SystemIcon name="chart" custom-class="w-3.5 h-3.5 text-[#0071E3]" />
            <span>全网性价比散点分布</span>
          </span>
          <span class="text-[#D1D1D6]">•</span>

          <!-- 维度模式分段选择器 (Segmented Control) -->
          <div class="inline-flex p-0.5 rounded-lg bg-[#E5E5EA]/70 border border-[#D1D1D6]/60 text-[11px] select-none">
            <button
              @click="setScatterDimensionMode('model')"
              class="px-2 py-0.5 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center space-x-1"
              :class="scatterDimensionMode === 'model' ? 'bg-[#FFFFFF] text-[#0071E3] font-bold shadow-2xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
              title="按具体的模型标准标识进行精准比价"
            >
              <span>🏷️ 按模型标识</span>
            </button>
            <button
              @click="setScatterDimensionMode('series')"
              class="px-2 py-0.5 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center space-x-1"
              :class="scatterDimensionMode === 'series' ? 'bg-[#FFFFFF] text-[#AF52DE] font-bold shadow-2xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
              title="按模型系列聚合展示该系列下所有渠道的报价分布（适合跨渠道多别名比价）"
            >
              <span>📦 按模型系列</span>
            </button>
          </div>

          <span class="text-[#D1D1D6]">•</span>
          <span class="text-[11px] text-[#6E6E73] font-medium">
            {{ scatterDimensionMode === 'model' ? '当前分析模型:' : '当前分析系列:' }}
          </span>

          <!-- 动态智能选择器：在模型模式下选模型标识，在系列模式下选模型系列 -->
          <div class="relative">
            <select
              v-if="scatterDimensionMode === 'model'"
              v-model="manualScatterModelId"
              class="bg-[#F2F2F7] hover:bg-[#E8F2FD] focus:bg-[#FFFFFF] border border-[#CCE4FB] text-[#0071E3] font-mono text-xs font-bold rounded-lg px-2 py-0.5 focus:outline-none transition-all cursor-pointer shadow-2xs"
            >
              <option v-for="m in currentAvailableModelIds" :key="m" :value="m">
                {{ m }}
              </option>
            </select>

            <select
              v-else
              v-model="manualScatterSeries"
              class="bg-[#F3E8FD]/60 hover:bg-[#F3E8FD] focus:bg-[#FFFFFF] border border-[#E1BEE7] text-[#8E24AA] font-mono text-xs font-bold rounded-lg px-2 py-0.5 focus:outline-none transition-all cursor-pointer shadow-2xs"
            >
              <option v-for="s in currentAvailableSeries" :key="s" :value="s">
                {{ s }}
              </option>
            </select>
          </div>
          <span class="text-[10px] text-[#86868B] font-normal hidden lg:inline">| 💡 点击表格任一行或在此切换，越偏左上角综合性价比越高</span>
        </div>

        <div class="text-[11px] font-mono text-[#86868B]">
          <span v-if="scatterDimensionMode === 'model'">
            全网接入 <strong class="text-[#0071E3]">{{ currentScatterItemsCount }}</strong> 个渠道节点
          </span>
          <span v-else>
            该系列共覆盖 <strong class="text-[#8E24AA]">{{ currentScatterItemsCount }}</strong> 个渠道报价
          </span>
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

    <!-- 自定义表格显示列与排序配置 Modal -->
    <TableColumnConfigModal
      :show="showColumnConfigModal"
      :storage-key="PRICE_MATRIX_STORAGE_KEY"
      :default-columns="DEFAULT_MATRIX_COLUMNS"
      fixed-start-label="模型标准标识"
      @close="showColumnConfigModal = false"
      @update:columns="onUpdateMatrixColumns"
      @reset-widths="resetMatrixWidths"
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
import TableColumnConfigModal, { type TableColumnDef } from '../components/TableColumnConfigModal.vue'
import { useTableResizable } from '../composables/useTableResizable'
import SystemIcon from '../components/SystemIcon.vue'
import type { ComparisonItem } from '../types'
import { parseUtcDate, formatRelativeTime } from '../utils/timeUtils'
import { exportPriceMatrixToExcel } from '../utils/excelExport'

const store = useDashboardStore()
const showAddModal = ref(false)
const isSyncingAll = ref(false)
const isExporting = ref(false)

// 列宽调整 (可拖拽 resize 与持久化)
const DEFAULT_MATRIX_COL_WIDTHS = {
  model_id: 260,
  series: 130,
  site_name: 180,
  site_type: 75,
  input_price: 100,
  output_price: 100,
  cache_price: 105,
  model_ratio: 65,
  tps: 85,
  updated_at: 135
}

const {
  getWidth: getMatrixColWidth,
  startResize: startMatrixResize,
  resetWidths: resetMatrixWidths,
  resetColumnWidth: resetMatrixColWidth
} = useTableResizable({
  storageKey: 'welltoken_col_widths_price_matrix',
  defaultWidths: DEFAULT_MATRIX_COL_WIDTHS,
  minWidth: 55,
  maxWidth: 700
})

// 自定义列配置
const showColumnConfigModal = ref(false)
const PRICE_MATRIX_STORAGE_KEY = 'welltoken_col_config_price_matrix'
const DEFAULT_MATRIX_COLUMNS: TableColumnDef[] = [
  { key: 'series', label: '模型系列 / 厂商', visible: true },
  { key: 'site_name', label: '渠道 / 供应商', visible: true },
  { key: 'site_type', label: '类型', visible: true },
  { key: 'input_price', label: '输入单价', visible: true },
  { key: 'output_price', label: '输出单价', visible: true },
  { key: 'cache_price', label: '命中缓存单价', visible: true },
  { key: 'model_ratio', label: '倍率', visible: true },
  { key: 'tps', label: '实测 TPS', visible: true },
  { key: 'updated_at', label: '更新时间', visible: true },
]

const loadMatrixColumns = (): TableColumnDef[] => {
  try {
    const saved = localStorage.getItem(PRICE_MATRIX_STORAGE_KEY)
    if (saved) {
      const parsed: TableColumnDef[] = JSON.parse(saved)
      const merged: TableColumnDef[] = []
      for (const p of parsed) {
        const d = DEFAULT_MATRIX_COLUMNS.find(col => col.key === p.key)
        if (d) {
          merged.push({ key: p.key, label: d.label, visible: p.visible !== false })
        }
      }
      for (const d of DEFAULT_MATRIX_COLUMNS) {
        if (!merged.some(m => m.key === d.key)) {
          merged.push({ ...d })
        }
      }
      return merged
    }
  } catch (e) {
    console.warn('加载全网比价列配置失败:', e)
  }
  return DEFAULT_MATRIX_COLUMNS.map(c => ({ ...c }))
}

const matrixColumns = ref<TableColumnDef[]>(loadMatrixColumns())
const visibleMatrixColumns = computed(() => matrixColumns.value.filter(c => c.visible))
const onUpdateMatrixColumns = (newCols: TableColumnDef[]) => {
  matrixColumns.value = newCols
}

const handleExportPriceMatrix = async () => {
  if (totalRecords.value === 0) {
    alert('当前筛选条件下无数据可导出')
    return
  }

  isExporting.value = true
  try {
    let exportItems: ComparisonItem[] = []

    // 如果当前内存中的条目已经包含了全部匹配数据，直接使用
    if (pagedItems.value.length >= totalRecords.value) {
      exportItems = pagedItems.value
    } else {
      // 否则拉取全部匹配数据 (最高 5000 条)
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
        page: 1,
        page_size: Math.min(totalRecords.value, 5000),
        sort_by: sortField.value,
        sort_order: sortOrder.value,
        exclude_zero: excludeZeroPrice.value
      }
      if (selectedProviders.value.length > 0) params.provider = selectedProviders.value
      if (selectedSeries.value.length > 0) params.series = selectedSeries.value
      if (selectedModels.value.length > 0) params.model = selectedModels.value
      if (effectiveSites.length > 0) params.site = effectiveSites
      if (activeDateStart.value) params.date_start = activeDateStart.value
      if (activeDateEnd.value) params.date_end = activeDateEnd.value

      const sp = buildSearchParams(params)
      const res = await axios.get(`${store.apiUrl}/api/v1/comparison/paginated?${sp.toString()}`)
      exportItems = res.data.items || []
    }

    exportPriceMatrixToExcel(exportItems, store.currency as any, store.usdToCnyRate || 7.25)
  } catch (e: any) {
    console.error('Export Excel failed:', e)
    alert(`导出 Excel 失败: ${e.message || '网络连接超时'}`)
  } finally {
    isExporting.value = false
  }
}

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

// 更新日期范围筛选状态与预设配置
type DatePresetType = 'all' | '7d' | '30d' | '90d' | '180d' | 'custom'

const datePresets = [
  { id: 'all' as DatePresetType, label: '不限' },
  { id: '7d' as DatePresetType, label: '近1周' },
  { id: '30d' as DatePresetType, label: '近1月' },
  { id: '90d' as DatePresetType, label: '近3月' },
  { id: '180d' as DatePresetType, label: '近半年' },
  { id: 'custom' as DatePresetType, label: '自定义' }
]

const selectedDatePreset = ref<DatePresetType>('all')
const customDateStart = ref<string>('')
const customDateEnd = ref<string>('')
const activeDateStart = ref<string>('')
const activeDateEnd = ref<string>('')
const isDateFilterOpen = ref(false)
const dateFilterContainerRef = ref<HTMLElement | null>(null)

const isDateFilterActive = computed(() => {
  return selectedDatePreset.value !== 'all' || !!activeDateStart.value || !!activeDateEnd.value
})

const dateFilterLabel = computed(() => {
  if (selectedDatePreset.value === '7d') return '更新: 近1周'
  if (selectedDatePreset.value === '30d') return '更新: 近1月'
  if (selectedDatePreset.value === '90d') return '更新: 近3月'
  if (selectedDatePreset.value === '180d') return '更新: 近半年'
  if (selectedDatePreset.value === 'custom') {
    if (activeDateStart.value && activeDateEnd.value) {
      return `${activeDateStart.value.slice(5)} ~ ${activeDateEnd.value.slice(5)}`
    }
    if (activeDateStart.value) return `自 ${activeDateStart.value.slice(5)} 起`
    if (activeDateEnd.value) return `至 ${activeDateEnd.value.slice(5)} 止`
    return '自定义日期'
  }
  return '更新时间: 全部'
})

function formatDateString(d: Date): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const toggleDateFilterPopover = () => {
  isDateFilterOpen.value = !isDateFilterOpen.value
}

const applyDatePreset = (presetId: DatePresetType) => {
  selectedDatePreset.value = presetId
  const now = new Date()
  const todayStr = formatDateString(now)

  if (presetId === 'all') {
    activeDateStart.value = ''
    activeDateEnd.value = ''
    customDateStart.value = ''
    customDateEnd.value = ''
    isDateFilterOpen.value = false
    currentPage.value = 1
    fetchFilterOptions()
    fetchPaginatedMatrix()
    return
  }

  if (presetId === '7d') {
    const d = new Date()
    d.setDate(d.getDate() - 7)
    activeDateStart.value = formatDateString(d)
    activeDateEnd.value = todayStr
  } else if (presetId === '30d') {
    const d = new Date()
    d.setDate(d.getDate() - 30)
    activeDateStart.value = formatDateString(d)
    activeDateEnd.value = todayStr
  } else if (presetId === '90d') {
    const d = new Date()
    d.setDate(d.getDate() - 90)
    activeDateStart.value = formatDateString(d)
    activeDateEnd.value = todayStr
  } else if (presetId === '180d') {
    const d = new Date()
    d.setDate(d.getDate() - 180)
    activeDateStart.value = formatDateString(d)
    activeDateEnd.value = todayStr
  } else if (presetId === 'custom') {
    // 切换至自定义，保持弹层打开以便用户选择日期
    return
  }

  isDateFilterOpen.value = false
  currentPage.value = 1
  fetchFilterOptions()
  fetchPaginatedMatrix()
}

const applyCustomDateRange = () => {
  selectedDatePreset.value = 'custom'
  activeDateStart.value = customDateStart.value
  activeDateEnd.value = customDateEnd.value
  isDateFilterOpen.value = false
  currentPage.value = 1
  fetchFilterOptions()
  fetchPaginatedMatrix()
}

const clearDateFilter = () => {
  selectedDatePreset.value = 'all'
  activeDateStart.value = ''
  activeDateEnd.value = ''
  customDateStart.value = ''
  customDateEnd.value = ''
  isDateFilterOpen.value = false
  currentPage.value = 1
  fetchFilterOptions()
  fetchPaginatedMatrix()
}

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
    if (activeDateStart.value) params.date_start = activeDateStart.value
    if (activeDateEnd.value) params.date_end = activeDateEnd.value

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
    // 实测 TPS 与更新时间默认从高到低 / 最新排序，价格/倍率默认从低到高排序
    sortOrder.value = field === 'last_tested_tps' || field === 'updated_at' || field === 'source_updated_at' ? 'desc' : 'asc'
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
    if (activeDateStart.value) params.date_start = activeDateStart.value
    if (activeDateEnd.value) params.date_end = activeDateEnd.value

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
    isDateFilterActive.value ||
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
  selectedDatePreset.value = 'all'
  activeDateStart.value = ''
  activeDateEnd.value = ''
  customDateStart.value = ''
  customDateEnd.value = ''
  isDateFilterOpen.value = false
  currentPage.value = 1
  fetchFilterOptions()
  fetchPaginatedMatrix()
}

const checkAndApplyTargetFilters = () => {
  let changed = false
  const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams()
  const qMode = urlParams.get('scatter_mode')
  if (qMode === 'series' || qMode === 'model') {
    scatterDimensionMode.value = qMode
  }

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
  if (row.series) {
    manualScatterSeries.value = row.series
  }
  updateScatterChart()
}

const selectAndScrollToRow = (row: ComparisonItem) => {
  selectedRow.value = row
  manualScatterModelId.value = row.model_id
  if (row.series) {
    manualScatterSeries.value = row.series
  }
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

// 时间列展示格式 (默认: 人性化相对时间 'relative'，支持一键切换为 'absolute' 紧凑绝对时间)
const timeDisplayMode = ref<'relative' | 'absolute'>('relative')

const toggleTimeDisplayMode = () => {
  timeDisplayMode.value = timeDisplayMode.value === 'relative' ? 'absolute' : 'relative'
}

const formatSourceTime = (row: ComparisonItem): string => {
  const raw = row.source_updated_at || (row.is_official_catalog !== false && row.source_time_type !== 'manual' ? '' : row.updated_at)
  if (!raw) return '—'

  // 绝对时间模式: 如 2026-04-24 或 04-24 14:30
  if (timeDisplayMode.value === 'absolute') {
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
      return raw
    }
    const d = parseUtcDate(raw)
    if (d) {
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const h = String(d.getHours()).padStart(2, '0')
      const min = String(d.getMinutes()).padStart(2, '0')
      if (raw.length <= 10) return raw
      return `${m}-${day} ${h}:${min}`
    }
    return raw
  }

  // 相对时间模式: 如 4个月前, 10分钟前, 刚刚
  return formatRelativeTime(raw)
}

const getSourceTimeTooltip = (row: ComparisonItem): string => {
  const isOfficial = row.is_official_catalog !== false && row.source_time_type !== 'manual'
  const rawTime = row.source_updated_at || row.updated_at || ''
  if (isOfficial) {
    return `[m 标 = models.dev 官方基准更新时间] ${rawTime}\n（点击表头文字可切换 相对时间/绝对日期 样式）`
  }
  return `[c 标 = 自定义渠道最后同步时间] ${rawTime}\n（点击表头文字可切换 相对时间/绝对日期 样式）`
}

// 判断模型是否属于区间/分段定价模型
const isTieredModel = (siteModelName?: string): boolean => {
  if (!siteModelName) return false
  return /\[|\~|\～|\+∞|分段|时段|阶梯|区间/.test(siteModelName)
}

// 散点图分析维度切换 ('model' = 按模型标识, 'series' = 按模型系列)
type ScatterDimensionMode = 'model' | 'series'
const scatterDimensionMode = ref<ScatterDimensionMode>('model')

const setScatterDimensionMode = (mode: ScatterDimensionMode) => {
  scatterDimensionMode.value = mode
  if (selectedRow.value) {
    if (mode === 'model' && selectedRow.value.model_id) {
      manualScatterModelId.value = selectedRow.value.model_id
    } else if (mode === 'series' && selectedRow.value.series) {
      manualScatterSeries.value = selectedRow.value.series
    }
  }
  updateScatterChart()
}

// 手动选择分析的散点图模型与系列
const manualScatterModelId = ref<string>('')
const manualScatterSeries = ref<string>('')

// 当前表格页面内所有不重复的模型 ID 清单
const currentAvailableModelIds = computed<string[]>(() => {
  const set = new Set<string>()
  pagedItems.value.forEach((it) => {
    if (it.model_id) set.add(it.model_id)
  })
  return Array.from(set)
})

// 当前表格页面内所有不重复的模型系列清单
const currentAvailableSeries = computed<string[]>(() => {
  const set = new Set<string>()
  pagedItems.value.forEach((it) => {
    if (it.series) set.add(it.series)
    else set.add('通用系列')
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

const activeScatterSeries = computed(() => {
  if (manualScatterSeries.value && currentAvailableSeries.value.includes(manualScatterSeries.value)) {
    return manualScatterSeries.value
  }
  if (selectedRow.value && selectedRow.value.series && currentAvailableSeries.value.includes(selectedRow.value.series)) {
    return selectedRow.value.series
  }
  return currentAvailableSeries.value[0] || '通用系列'
})

const currentScatterItemsCount = computed(() => {
  if (scatterDimensionMode.value === 'model') {
    return pagedItems.value.filter((item) => item.model_id === activeScatterModelId.value).length
  } else {
    const s = activeScatterSeries.value
    return pagedItems.value.filter((item) => (item.series || '通用系列') === s).length
  }
})

watch([activeScatterModelId, activeScatterSeries, scatterDimensionMode], () => {
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

  let targetItems: ComparisonItem[] = []
  if (scatterDimensionMode.value === 'model') {
    const targetModelId = activeScatterModelId.value
    targetItems = pagedItems.value.filter((item) => item.model_id === targetModelId)
  } else {
    const targetSeries = activeScatterSeries.value
    targetItems = pagedItems.value.filter((item) => (item.series || '通用系列') === targetSeries)
  }

  // data: [price, tps, site_name, model_ratio, id, model_id, series, model_name, site_model_name]
  const data = targetItems.map((item) => [
    store.currency === 'USD' ? item.calculated_input_usd : item.calculated_input_cny,
    item.last_tested_tps || 50,
    item.site_name,
    item.model_ratio,
    item.id,
    item.model_id,
    item.series || '通用系列',
    item.model_name || item.model_id,
    item.site_model_name || ''
  ])

  const option: any = {
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
        const modelId = d[5] || ''
        const seriesName = d[6] || ''
        const siteModelName = d[8] || ''
        const isSeriesMode = scatterDimensionMode.value === 'series'
        const hasTierOrAlias = siteModelName && siteModelName !== modelId
        return `
          <div class="font-sans font-bold text-[#1D1D1F] flex items-center space-x-1">
            <span>${d[2]}</span>
            ${isBm ? '<span class="text-[#0071E3] font-bold text-[10px] ml-1">🎯(比价基准)</span>' : ''}
            ${isSel ? '<span class="text-[#FF9500] font-bold text-[10px] ml-1">📍(当前选中)</span>' : ''}
          </div>
          ${isSeriesMode ? `<div class="text-[#8E24AA] text-[10px] font-mono mt-0.5">📦 系列: ${seriesName} | 🏷️ 标识: ${modelId}</div>` : ''}
          ${hasTierOrAlias ? `<div class="text-[#AF52DE] text-[10px] font-mono mt-0.5">📊 规格区间: <strong>${siteModelName}</strong></div>` : ''}
          <div class="text-[#6E6E73] text-[10px] mt-0.5">输入价格: <strong class="text-[#34C759] font-mono font-bold">${store.currency === 'USD' ? '$' : '¥'}${Number(d[0]).toFixed(3)}</strong></div>
          <div class="text-[#6E6E73] text-[10px]">实测速率: <strong class="text-[#0071E3] font-mono font-bold">${d[1]} TPS</strong></div>
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

const handleGlobalClick = (e: MouseEvent) => {
  closeDimensionPopover()
  if (isDateFilterOpen.value && dateFilterContainerRef.value && !dateFilterContainerRef.value.contains(e.target as Node)) {
    isDateFilterOpen.value = false
  }
}

onMounted(async () => {
  checkAndApplyTargetFilters()
  await fetchFilterOptions()
  await fetchPaginatedMatrix()
  initScatterChart()
  window.addEventListener('resize', handleResize)
  window.addEventListener('click', handleGlobalClick)
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
  window.removeEventListener('click', handleGlobalClick)
  chartInstance?.dispose()
})

const handleResize = () => {
  chartInstance?.resize()
}
</script>

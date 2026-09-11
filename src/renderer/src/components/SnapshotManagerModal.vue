<template>
  <div
    v-if="store.snapshotManagerDrawer.visible"
    class="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs transition-opacity duration-300 select-none"
    @click.self="store.closeSnapshotManager"
  >
    <div
      class="w-full max-w-3xl h-full bg-[#FFFFFF] shadow-2xl flex flex-col border-l border-[#E5E5EA] animate-slide-left overflow-hidden"
    >
      <!-- 顶部标题栏 -->
      <div class="px-6 py-4 border-b border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between flex-shrink-0">
        <div class="flex items-center space-x-3 min-w-0">
          <div class="w-9 h-9 rounded-xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center font-bold flex-shrink-0 shadow-2xs">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <div class="min-w-0">
            <div class="flex items-center space-x-2">
              <h3 class="text-base font-bold text-[#1D1D1F] truncate">
                官方快照版本管理
              </h3>
              <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#0071E3]/10 text-[#0071E3] border border-[#0071E3]/20">
                {{ store.snapshotManagerDrawer.groups.length }} 个批次版本
              </span>
            </div>
            <p class="text-xs text-[#86868B] truncate mt-0.5">
              按统一抓取日期聚合留存各厂商快照，支持查阅网页证据、检视模型明细与自动回滚
            </p>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <!-- 全部展开/收起 -->
          <button
            @click="toggleExpandAll"
            class="px-2.5 py-1.5 rounded-xl border border-[#E5E5EA] bg-white hover:bg-[#F2F2F7] text-xs font-medium text-[#48484A] hover:text-[#1D1D1F] transition-all cursor-pointer shadow-2xs"
          >
            {{ allExpanded ? '全部收起' : '全部展开' }}
          </button>

          <!-- 刷新按钮 -->
          <button
            @click="store.fetchGroupedSnapshots"
            class="px-3 py-1.5 rounded-xl border border-[#E5E5EA] bg-white hover:bg-[#F2F2F7] text-xs font-medium text-[#48484A] hover:text-[#1D1D1F] flex items-center space-x-1.5 transition-all shadow-2xs cursor-pointer"
            title="刷新快照列表"
          >
            <span :class="{ 'animate-spin': store.snapshotManagerDrawer.loading }">⟳</span>
            <span>刷新</span>
          </button>

          <!-- 关闭按钮 -->
          <button
            @click="store.closeSnapshotManager"
            class="w-8 h-8 rounded-xl hover:bg-[#F2F2F7] text-[#86868B] hover:text-[#1D1D1F] flex items-center justify-center transition-all cursor-pointer"
            title="关闭 (ESC)"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- 厂商快捷筛选器 -->
      <div class="px-6 py-2.5 bg-[#F5F5F7] border-b border-[#E5E5EA] flex items-center space-x-1.5 overflow-x-auto text-xs flex-shrink-0">
        <button
          @click="selectedProviderFilter = 'all'"
          class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium whitespace-nowrap"
          :class="selectedProviderFilter === 'all'
            ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
            : 'text-[#86868B] hover:text-[#1D1D1F]'"
        >
          全部厂商
        </button>
        <button
          v-for="prov in distinctProviders"
          :key="prov.code"
          @click="selectedProviderFilter = prov.code"
          class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium whitespace-nowrap"
          :class="selectedProviderFilter === prov.code
            ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
            : 'text-[#86868B] hover:text-[#1D1D1F]'"
        >
          {{ prov.name }}
        </button>
      </div>

      <!-- 提示条 -->
      <div class="px-6 py-2.5 bg-[#FFFBE6] border-b border-[#FFE58F] text-[11px] text-[#D48806] flex items-center space-x-2 flex-shrink-0">
        <span>💡</span>
        <span>
          以抓取日期为基准统一管理。若删除<strong>当前生效基准</strong>（单厂商或整批），系统将<strong>全自动回退至上一历史有效快照</strong>并刷新前台。
        </span>
      </div>

      <!-- 主体折叠列表容器 -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4 bg-[#FAFAFC]">
        <div v-if="store.snapshotManagerDrawer.loading" class="py-20 text-center text-[#86868B] space-y-2">
          <div class="inline-block animate-spin text-2xl text-[#0071E3]">⟳</div>
          <div class="text-xs font-medium">正在加载官方快照批次...</div>
        </div>

        <div v-else-if="filteredGroups.length === 0" class="py-20 text-center text-[#86868B] space-y-2">
          <div class="text-3xl">📭</div>
          <div class="text-xs font-medium">暂无符合条件的快照记录</div>
        </div>

        <template v-else>
          <!-- 按日期分组手风琴卡片 -->
          <div
            v-for="group in filteredGroups"
            :key="group.snapshot_date"
            class="rounded-2xl border transition-all duration-200 overflow-hidden bg-white shadow-2xs"
            :class="group.is_current
              ? 'border-[#34C759]/40 ring-1 ring-[#34C759]/20'
              : 'border-[#E5E5EA] hover:border-[#B0B0B8]'"
          >
            <!-- 日期卡片 Header -->
            <div
              class="px-5 py-3.5 flex items-center justify-between cursor-pointer select-none transition-colors"
              :class="group.is_current ? 'bg-[#34C759]/5 hover:bg-[#34C759]/10' : 'bg-[#F9F9FB] hover:bg-[#F2F2F7]'"
              @click="store.toggleDateGroupExpanded(group.snapshot_date)"
            >
              <div class="flex items-center space-x-3 min-w-0">
                <!-- 旋转箭头 -->
                <span
                  class="text-xs text-[#86868B] transition-transform duration-200 inline-block"
                  :class="{ 'rotate-90': isExpanded(group.snapshot_date) }"
                >
                  ▶
                </span>

                <!-- 日期标识 -->
                <div class="flex items-center space-x-2">
                  <span class="text-sm font-bold text-[#1D1D1F]">
                    📅 {{ group.snapshot_date }} 批次
                  </span>
                  <!-- 当前生效状态 Badge -->
                  <span
                    v-if="group.is_current"
                    class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#34C759]/15 text-[#248A3D] border border-[#34C759]/30 flex items-center space-x-1"
                  >
                    <span class="w-1.5 h-1.5 rounded-full bg-[#34C759] animate-pulse"></span>
                    <span>当前生效基准</span>
                  </span>
                  <span
                    v-else
                    class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#E5E5EA] text-[#636366]"
                  >
                    历史归档
                  </span>
                </div>

                <!-- 统计指标 -->
                <span class="text-xs text-[#86868B]">
                  {{ group.providers.length }} 家厂商 · 共 {{ group.total_models }} 款模型
                </span>
              </div>

              <!-- 右侧操作 -->
              <div class="flex items-center space-x-2" @click.stop>
                <!-- 一键删除整批次按钮 -->
                <button
                  @click="confirmDeleteDateBatch(group.snapshot_date, group.is_current)"
                  :disabled="store.snapshotManagerDrawer.deletingDate === group.snapshot_date"
                  class="px-2.5 py-1 rounded-lg border border-[#FF3B30]/30 hover:bg-[#FF3B30]/10 text-[11px] font-medium text-[#FF3B30] transition-all cursor-pointer flex items-center space-x-1"
                  title="删除该日期的所有厂商快照"
                >
                  <span v-if="store.snapshotManagerDrawer.deletingDate === group.snapshot_date" class="animate-spin">⟳</span>
                  <span v-else>🗑️</span>
                  <span>删除此批次</span>
                </button>
              </div>
            </div>

            <!-- 展开后的 10 家厂商卡片网格 -->
            <div
              v-show="isExpanded(group.snapshot_date)"
              class="p-4 border-t border-[#E5E5EA]/70 grid grid-cols-1 md:grid-cols-2 gap-3 bg-[#FFFFFF]"
            >
              <div
                v-for="p in group.providers"
                :key="p.snapshot_id"
                class="p-3.5 rounded-xl border border-[#E5E5EA] hover:border-[#0071E3]/40 bg-[#FAFAFC] hover:bg-[#FFFFFF] transition-all duration-150 flex flex-col justify-between space-y-2.5 shadow-2xs group/card"
              >
                <!-- 厂商卡片头部 -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2 min-w-0">
                    <span
                      class="px-2 py-0.5 rounded-md text-[11px] font-bold border truncate"
                      :class="getProviderBadgeStyle(p.provider)"
                    >
                      {{ p.provider_name }}
                    </span>
                    <span class="text-[10px] text-[#86868B]">
                      #{{ p.snapshot_id }}
                    </span>
                  </div>

                  <span
                    v-if="p.is_current"
                    class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#34C759]/15 text-[#248A3D] border border-[#34C759]/30"
                  >
                    生效中
                  </span>
                </div>

                <!-- 抓取信息与收录模型 -->
                <div class="text-xs space-y-1">
                  <div class="text-[11px] text-[#1D1D1F] font-medium truncate" :title="p.page_title">
                    {{ p.page_title || '官方定价网页' }}
                  </div>
                  <div class="flex items-center space-x-2 text-[11px] text-[#86868B]">
                    <span>时间: {{ formatTime(p.captured_at) }}</span>
                    <span>·</span>
                    <span>模型: <strong class="text-[#1D1D1F]">{{ p.models_count }}</strong> 款</span>
                    <span>·</span>
                    <span>{{ formatBytes(p.file_size_bytes) }}</span>
                  </div>
                </div>

                <!-- 操作按钮组 -->
                <div class="pt-2 border-t border-[#E5E5EA]/60 flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <!-- 查阅网页 -->
                    <button
                      @click="viewWebSnapshot(p)"
                      class="px-2 py-1 rounded-md text-[11px] font-medium bg-[#0071E3]/10 text-[#0071E3] hover:bg-[#0071E3]/20 transition-all cursor-pointer flex items-center space-x-1"
                      title="打开当时抓取的离线原始 HTML 网页证据"
                    >
                      <span>📄 查阅网页</span>
                    </button>

                    <!-- 查看模型明细 -->
                    <button
                      @click="store.openSnapshotModelDetail(p)"
                      class="px-2 py-1 rounded-md text-[11px] font-medium bg-[#F2F2F7] text-[#1D1D1F] hover:bg-[#E5E5EA] transition-all cursor-pointer flex items-center space-x-1"
                      title="查看该快照收录的所有模型及单价"
                    >
                      <span>📋 查看模型 ({{ p.models_count }})</span>
                    </button>
                  </div>

                  <!-- 删除单快照 -->
                  <button
                    @click="confirmDeleteProviderSnapshot(p)"
                    :disabled="store.snapshotManagerDrawer.deletingId === p.snapshot_id"
                    class="px-1.5 py-1 text-[11px] text-[#86868B] hover:text-[#FF3B30] hover:bg-[#FF3B30]/10 rounded transition-all cursor-pointer"
                    title="删除该厂商快照并自动回滚生效前一版本"
                  >
                    <span v-if="store.snapshotManagerDrawer.deletingId === p.snapshot_id" class="animate-spin">⟳</span>
                    <span v-else>🗑️</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 底部统计与关闭栏 -->
      <div class="px-6 py-3.5 border-t border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between text-xs text-[#86868B] flex-shrink-0">
        <div>
          共收录 {{ totalSnapshotsCount }} 份官方对账网页快照
        </div>
        <button
          @click="store.closeSnapshotManager"
          class="px-4 py-1.5 rounded-xl border border-[#D1D1D6] bg-white hover:bg-[#F2F2F7] text-xs font-semibold text-[#1D1D1F] transition-all shadow-2xs cursor-pointer"
        >
          完成并关闭
        </button>
      </div>
    </div>

    <!-- 弹窗：查看指定快照收录的模型明细 -->
    <div
      v-if="store.snapshotManagerDrawer.modelDetailModal.visible"
      class="fixed inset-0 z-60 flex items-center justify-center bg-black/40 backdrop-blur-xs select-none"
      @click.self="store.closeSnapshotModelDetail"
    >
      <div class="w-full max-w-2xl max-h-[85vh] bg-white rounded-2xl shadow-2xl flex flex-col border border-[#E5E5EA] overflow-hidden animate-scale-up">
        <!-- 模态框 Header -->
        <div class="px-6 py-4 border-b border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between flex-shrink-0">
          <div>
            <div class="flex items-center space-x-2">
              <h4 class="text-sm font-bold text-[#1D1D1F]">
                {{ store.snapshotManagerDrawer.modelDetailModal.providerName }} · 快照收录模型清单
              </h4>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#0071E3]/10 text-[#0071E3]">
                共 {{ store.snapshotManagerDrawer.modelDetailModal.models.length }} 款
              </span>
            </div>
            <p class="text-[11px] text-[#86868B] mt-0.5">
              快照时间: {{ store.snapshotManagerDrawer.modelDetailModal.capturedAt }}
            </p>
          </div>

          <button
            @click="store.closeSnapshotModelDetail"
            class="w-7 h-7 rounded-lg hover:bg-[#E5E5EA] text-[#86868B] hover:text-[#1D1D1F] flex items-center justify-center cursor-pointer transition-all"
          >
            ✕
          </button>
        </div>

        <!-- 搜索过滤 -->
        <div class="px-6 py-2 border-b border-[#E5E5EA] bg-[#FAFAFC] flex-shrink-0">
          <input
            v-model="modelSearchKeyword"
            type="text"
            placeholder="搜索模型规格、系列或计费模式..."
            class="w-full px-3 py-1.5 text-xs rounded-lg border border-[#D1D1D6] focus:border-[#0071E3] focus:outline-none bg-white"
          />
        </div>

        <!-- 模型列表表格 -->
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="store.snapshotManagerDrawer.modelDetailModal.loading" class="py-12 text-center text-[#86868B] text-xs">
            正在载入模型明细...
          </div>
          <div v-else-if="filteredModalModels.length === 0" class="py-12 text-center text-[#86868B] text-xs">
            未检索到匹配的模型记录
          </div>
          <table v-else class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-[#E5E5EA] text-[#86868B] text-[11px]">
                <th class="py-2 px-2.5 font-medium">模型规格</th>
                <th class="py-2 px-2 font-medium">系列</th>
                <th class="py-2 px-2 font-medium">计费模式</th>
                <th class="py-2 px-2 text-right font-medium">输入单价 (1M)</th>
                <th class="py-2 px-2 text-right font-medium">输出单价 (1M)</th>
                <th class="py-2 px-2 text-right font-medium">缓存命中 (1M)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#F2F2F7]">
              <tr
                v-for="m in filteredModalModels"
                :key="m.id"
                class="hover:bg-[#F9F9FB] transition-colors"
              >
                <td class="py-2 px-2.5 font-semibold text-[#1D1D1F] truncate max-w-[200px]" :title="m.model_name">
                  {{ m.model_name }}
                </td>
                <td class="py-2 px-2 text-[#86868B]">
                  {{ m.series }}
                </td>
                <td class="py-2 px-2 text-[#48484A]">
                  {{ m.billing_mode }}
                </td>
                <td class="py-2 px-2 text-right font-mono text-[#0071E3]">
                  {{ m.currency === 'USD' ? '$' : '¥' }}{{ m.input_price }}
                </td>
                <td class="py-2 px-2 text-right font-mono text-[#1D1D1F]">
                  {{ m.currency === 'USD' ? '$' : '¥' }}{{ m.output_price }}
                </td>
                <td class="py-2 px-2 text-right font-mono text-[#86868B]">
                  <span v-if="m.cache_read_price !== null">
                    {{ m.currency === 'USD' ? '$' : '¥' }}{{ m.cache_read_price }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 模态框 Footer -->
        <div class="px-6 py-3 border-t border-[#E5E5EA] bg-[#FBFBFD] flex justify-end flex-shrink-0">
          <button
            @click="store.closeSnapshotModelDetail"
            class="px-4 py-1.5 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-medium cursor-pointer transition-all shadow-2xs"
          >
            关闭清单
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  useOfficialPricingStore,
  type SnapshotProviderItem,
  type SnapshotDateGroup,
  type SnapshotModelItem
} from '../stores/officialPricingStore'

const store = useOfficialPricingStore()

const selectedProviderFilter = ref<string>('all')
const modelSearchKeyword = ref<string>('')

// 抽屉内所有厂商选项
const distinctProviders = computed(() => {
  const map = new Map<string, string>()
  for (const group of store.snapshotManagerDrawer.groups) {
    for (const p of group.providers) {
      if (!map.has(p.provider)) {
        map.set(p.provider, p.provider_name)
      }
    }
  }
  return Array.from(map.entries()).map(([code, name]) => ({ code, name }))
})

// 快照总数统计
const totalSnapshotsCount = computed(() => {
  return store.snapshotManagerDrawer.groups.reduce((acc, g) => acc + g.providers.length, 0)
})

// 按厂商过滤后的日期组列表
const filteredGroups = computed(() => {
  if (selectedProviderFilter.value === 'all') {
    return store.snapshotManagerDrawer.groups
  }
  return store.snapshotManagerDrawer.groups
    .map((g) => {
      const matchedProviders = g.providers.filter((p) => p.provider === selectedProviderFilter.value)
      if (matchedProviders.length === 0) return null
      return {
        ...g,
        providers: matchedProviders,
        total_models: matchedProviders.reduce((acc, p) => acc + p.models_count, 0)
      } as SnapshotDateGroup
    })
    .filter((g): g is SnapshotDateGroup => g !== null)
})

// 是否展开某个日期
function isExpanded(date: string): boolean {
  return store.snapshotManagerDrawer.expandedDates.includes(date)
}

// 全部展开 / 全部收起
const allExpanded = computed(() => {
  if (store.snapshotManagerDrawer.groups.length === 0) return false
  return store.snapshotManagerDrawer.groups.every((g) => isExpanded(g.snapshot_date))
})

function toggleExpandAll() {
  if (allExpanded.value) {
    store.snapshotManagerDrawer.expandedDates = []
  } else {
    store.snapshotManagerDrawer.expandedDates = store.snapshotManagerDrawer.groups.map((g) => g.snapshot_date)
  }
}

// 格式化时间 (去掉日期前缀，仅显示具体时间)
function formatTime(capturedAt: string): string {
  if (!capturedAt) return ''
  const parts = capturedAt.split(' ')
  return parts.length > 1 ? parts[1] : capturedAt
}

// 文件体积格式化
function formatBytes(bytes: number): string {
  if (!bytes || bytes <= 0) return '0 B'
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  return `${(kb / 1024).toFixed(1)} MB`
}

// 厂商卡片 Badge 样式映射
function getProviderBadgeStyle(provider: string): string {
  switch (provider.toLowerCase()) {
    case 'openai':
      return 'bg-[#10A37F]/10 text-[#10A37F] border-[#10A37F]/30'
    case 'anthropic':
      return 'bg-[#D97706]/10 text-[#D97706] border-[#D97706]/30'
    case 'google':
      return 'bg-[#1A73E8]/10 text-[#1A73E8] border-[#1A73E8]/30'
    case 'alibaba':
      return 'bg-[#FF6A00]/10 text-[#FF6A00] border-[#FF6A00]/30'
    case 'deepseek':
      return 'bg-[#0066FF]/10 text-[#0066FF] border-[#0066FF]/30'
    case 'zhipuai':
      return 'bg-[#4338CA]/10 text-[#4338CA] border-[#4338CA]/30'
    case 'minimax':
      return 'bg-[#EC4899]/10 text-[#EC4899] border-[#EC4899]/30'
    case 'moonshotai':
      return 'bg-[#8B5CF6]/10 text-[#8B5CF6] border-[#8B5CF6]/30'
    case 'stepfun':
      return 'bg-[#06B6D4]/10 text-[#06B6D4] border-[#06B6D4]/30'
    case 'xiaomi':
      return 'bg-[#F97316]/10 text-[#F97316] border-[#F97316]/30'
    default:
      return 'bg-[#F2F2F7] text-[#48484A] border-[#D1D1D6]'
  }
}

// 查看离线 HTML 快照网页
function viewWebSnapshot(p: SnapshotProviderItem) {
  store.snapshotDrawer.visible = true
  store.snapshotDrawer.snapshotId = p.snapshot_id
  store.snapshotDrawer.sourceUrl = p.source_url
  store.snapshotDrawer.modelName = ''
  store.snapshotDrawer.pageTitle = p.page_title || `${p.provider_name} 官方定价`
  store.snapshotDrawer.highlightTarget = ''
}

// 删除单个厂商快照二次确认
async function confirmDeleteProviderSnapshot(p: SnapshotProviderItem) {
  const msg = p.is_current
    ? `快照 #${p.snapshot_id} (${p.provider_name}) 当前正在生效！\n删除后系统将全自动将 ${p.provider_name} 回滚至上一历史有效快照，并重新生效。\n\n确认删除吗？`
    : `确认删除快照 #${p.snapshot_id} (${p.provider_name}) 吗？此操作将彻底删除此快照及绑定的历史价格记录。`

  if (window.confirm(msg)) {
    const res = await store.deleteSnapshotVersion(p.snapshot_id)
    if (res.success) {
      alert(`✅ ${res.message}`)
    } else {
      alert(`❌ ${res.message}`)
    }
  }
}

// 删除整批次快照二次确认
async function confirmDeleteDateBatch(date: string, isCurrent: boolean) {
  const msg = isCurrent
    ? `⚠️ 警告：${date} 批次快照当前正在全盘生效中！\n一键整批删除后，系统将自动回退所有厂商至上一日期的历史有效快照，并物理清理相关磁盘文件。\n\n确定要整批删除 ${date} 的全部快照吗？`
    : `确认整批删除 ${date} 日期的全部厂商快照吗？此操作不可逆。`

  if (window.confirm(msg)) {
    const res = await store.deleteSnapshotDateBatch(date)
    if (res.success) {
      alert(`✅ ${res.message}`)
    } else {
      alert(`❌ ${res.message}`)
    }
  }
}

// 模态框内的模型过滤
const filteredModalModels = computed<SnapshotModelItem[]>(() => {
  const list = store.snapshotManagerDrawer.modelDetailModal.models
  const kw = modelSearchKeyword.value.trim().toLowerCase()
  if (!kw) return list
  return list.filter((m) =>
    m.model_name.toLowerCase().includes(kw) ||
    m.series.toLowerCase().includes(kw) ||
    m.billing_mode.toLowerCase().includes(kw)
  )
})
</script>

<style scoped>
@keyframes slideLeft {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes scaleUp {
  from {
    transform: scale(0.95);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.animate-slide-left {
  animation: slideLeft 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-scale-up {
  animation: scaleUp 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>

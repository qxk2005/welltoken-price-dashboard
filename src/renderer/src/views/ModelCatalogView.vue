<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- ==================== 场景 A：纯粹厂商大全列表 (严格对齐 models.dev/labs/ 30大权威厂商体系) ==================== -->
    <template v-if="!selectedLab">
      <!-- 顶部操作栏 -->
      <div class="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold text-[#1D1D1F]">大模型研发机构与厂商 (共 {{ officialLabsList.length }} 家权威机构)</span>
            <span class="text-xs text-[#86868B] font-mono">| 标准对齐 models.dev/labs/ 官方体系</span>
          </div>

          <!-- 搜索输入框 -->
          <div class="w-64 relative">
            <input
              v-model="labSearchQuery"
              type="text"
              placeholder="搜索厂商 (如 阿里, DeepSeek, OpenAI)..."
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
            />
            <span v-if="labSearchQuery" @click="labSearchQuery = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
          </div>
        </div>

        <button
          @click="store.syncModelsDev"
          class="text-xs px-3.5 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1"
        >
          <span>🔄 从 models.dev 同步最新厂商库</span>
        </button>
      </div>

      <!-- 厂商卡片流 (3 列纯厂商卡片，绝不混入具体模型，纯粹、干净、权威) -->
      <div class="flex-1 overflow-y-auto pr-1">
        <div class="grid grid-cols-3 gap-3.5">
          <div
            v-for="lab in filteredLabs"
            :key="lab.id"
            @click="selectLab(lab)"
            class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] hover:border-[#0071E3]/50 hover:shadow-[0_8px_24px_rgba(0,113,227,0.06)] transition-all cursor-pointer flex flex-col justify-between space-y-3 group"
          >
            <!-- 厂商头部：官方高保真矢量 Logo、名称、英文 ID -->
            <div class="flex items-start space-x-3.5">
              <div class="w-11 h-11 rounded-2xl bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center p-2.5 flex-shrink-0 group-hover:scale-105 group-hover:bg-[#E8F2FD] transition-all">
                <LabLogo :lab-id="lab.id" custom-class="w-7 h-7" />
              </div>
              <div class="truncate flex-1">
                <div class="font-bold text-sm text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors truncate">
                  {{ lab.displayName }}
                </div>
                <div class="text-[11px] text-[#86868B] font-mono mt-0.5">
                  {{ lab.id }}
                </div>
              </div>
            </div>

            <!-- 厂商官方中文定位介绍 (纯粹厂商信息) -->
            <p class="text-xs text-[#6E6E73] leading-relaxed line-clamp-2 h-8">
              {{ lab.description }}
            </p>

            <!-- 底部：收录模型总数、全网渠道覆盖与进入箭头 (无任何模型混杂) -->
            <div class="pt-2.5 border-t border-[#E5E5EA] flex items-center justify-between text-xs font-mono">
              <div class="flex items-center space-x-3 text-[#6E6E73]">
                <span>模型: <strong class="text-[#0071E3] font-bold">{{ lab.models.length }}</strong> 款</span>
                <span class="text-[#D1D1D6]">•</span>
                <span>渠道: <strong class="text-[#34C759] font-bold">{{ lab.providersCount }}</strong> 家</span>
              </div>
              <span class="text-[#0071E3] font-sans font-bold group-hover:translate-x-1 transition-transform text-xs">
                查看模型列表 →
              </span>
            </div>
          </div>
        </div>

        <div v-if="filteredLabs.length === 0" class="py-16 text-center text-xs text-[#86868B]">
          无匹配的大模型厂商或研究机构
        </div>
      </div>
    </template>

    <!-- ==================== 场景 B：点击厂商后，进入该厂商专属模型列表规格表 (对齐 models.dev/labs/alibaba/) ==================== -->
    <template v-else>
      <!-- 1. 顶部厂商介绍 Header 区 -->
      <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
        <!-- 顶部返回与代码标识 -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <button
              @click="selectedLabId = null"
              class="px-3 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] transition-all text-xs font-medium flex items-center space-x-1 cursor-pointer"
            >
              <span>← 返回厂商大全</span>
            </button>
          </div>

          <div class="flex items-center space-x-2">
            <span class="text-[11px] text-[#86868B]">官方机构标识:</span>
            <code class="px-2 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA] text-[#0071E3] font-mono text-xs font-bold">
              {{ selectedLab.id }}
            </code>
            <button
              @click="copyText(selectedLab.id)"
              class="text-xs text-[#6E6E73] hover:text-[#1D1D1F] px-2 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA]"
              title="复制标识"
            >
              {{ isCopied ? '✓ 已复制' : '复制' }}
            </button>
          </div>
        </div>

        <!-- 厂商大标题、官方 Logo 与简介文案 (中文) -->
        <div class="flex items-start justify-between">
          <div class="flex items-start space-x-3.5 max-w-3xl">
            <div class="w-12 h-12 rounded-2xl bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center p-2.5 flex-shrink-0">
              <LabLogo :lab-id="selectedLab.id" custom-class="w-7 h-7" />
            </div>
            <div class="space-y-1">
              <h2 class="text-xl font-bold text-[#1D1D1F] tracking-tight flex items-center space-x-2">
                <span>{{ selectedLab.displayName }}</span>
              </h2>
              <p class="text-xs text-[#6E6E73] leading-relaxed">
                {{ selectedLab.description }}
              </p>
            </div>
          </div>

          <!-- 搜索过滤 -->
          <div class="w-60 relative">
            <input
              v-model="modelSearchQuery"
              type="text"
              placeholder="在当前厂商中搜索模型..."
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1.5 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
            />
            <span v-if="modelSearchQuery" @click="modelSearchQuery = ''" class="absolute right-2 top-1.5 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
          </div>
        </div>

        <!-- 2. 核心指标统计网格 (Fact Grid - 对应 models.dev 的 3 项指标看板) -->
        <div class="grid grid-cols-4 gap-3 pt-2 border-t border-[#E5E5EA]">
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">标准收录模型数</div>
            <div class="text-lg font-bold font-mono text-[#0071E3] mt-0.5">{{ selectedLab.models.length }} 款</div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">全网接入供应商/渠道</div>
            <div class="text-lg font-bold font-mono text-[#34C759] mt-0.5">{{ selectedLab.providersCount }} 家</div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">旗下核心模型系列</div>
            <div class="text-lg font-bold font-mono text-[#AF52DE] mt-0.5">{{ selectedLab.families.length }} 个系列</div>
          </div>
          <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
            <div class="text-[10px] text-[#86868B] font-medium uppercase tracking-wider">数据标准更新时间</div>
            <div class="text-sm font-bold font-mono text-[#1D1D1F] mt-1">2026-08 实时同步</div>
          </div>
        </div>
      </div>

      <!-- 3. 高级对齐数据表格 (Enhanced Data Table - 完美汉化对齐 models.dev/labs/alibaba/) -->
      <div class="flex-1 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden min-h-0">
        <!-- 数据表格滚动容器 -->
        <div class="flex-1 overflow-x-auto overflow-y-auto pr-1">
          <table class="w-full text-left text-xs border-collapse min-w-[980px]">
            <!-- 表头 (支持点击排序) -->
            <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans select-none">
              <tr>
                <th @click="toggleSort('name')" class="py-2.5 px-3 cursor-pointer hover:text-[#1D1D1F] transition-colors">
                  模型名称 / 标准标识 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('name') }}</span>
                </th>
                <th @click="toggleSort('active_relay_count')" class="py-2.5 px-2 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors w-20">
                  接入渠道 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('active_relay_count') }}</span>
                </th>
                <th @click="toggleSort('context_window')" class="py-2.5 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors w-20">
                  上下文 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('context_window') }}</span>
                </th>
                <th @click="toggleSort('max_output')" class="py-2.5 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors w-20">
                  最大输出 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('max_output') }}</span>
                </th>
                <th class="py-2.5 px-2 text-center w-18">模态</th>
                <th class="py-2.5 px-2 text-center w-16">推理</th>
                <th class="py-2.5 px-2 text-center w-16">工具</th>
                <th class="py-2.5 px-2 text-center w-16">结构化</th>
                <th @click="toggleSort('official_input_price')" class="py-2.5 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors w-24">
                  官方输入 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('official_input_price') }}</span>
                </th>
                <th @click="toggleSort('official_output_price')" class="py-2.5 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors w-24">
                  官方输出 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('official_output_price') }}</span>
                </th>
                <th @click="toggleSort('lowest_price_usd')" class="py-2.5 px-2 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors w-24">
                  全网最低 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('lowest_price_usd') }}</span>
                </th>
                <th class="py-2.5 px-2 text-center w-20">操作</th>
              </tr>
            </thead>

            <!-- 数据行体 (渲染当前页 50 条，极速流畅 60 FPS) -->
            <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
              <tr
                v-for="model in paginatedModels"
                :key="model.model_id"
                class="hover:bg-[#F5F5F7] transition-colors group"
              >
                <!-- 1. 模型大名称 + 标准 ID -->
                <td class="py-2.5 px-3">
                  <div class="font-bold text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors text-xs">
                    {{ model.name }}
                  </div>
                  <div class="text-[11px] text-[#0071E3] font-mono mt-0.5">
                    {{ model.model_id }}
                  </div>
                </td>

                <!-- 2. 接入渠道数 (纯数字，无绿色背景) -->
                <td class="py-2.5 px-2 text-center">
                  <span
                    @click="goToMatrix(model.model_id)"
                    class="font-mono font-bold text-xs text-[#0071E3] hover:underline cursor-pointer"
                    title="点击查看所有接入该模型的供应商"
                  >
                    {{ model.active_relay_count || 0 }}
                  </span>
                </td>

                <!-- 3. 上下文窗口 (紧凑 K/M 显示) -->
                <td class="py-2.5 px-2 text-right font-mono text-[#1D1D1F]" :title="`${Number(model.context_window || 128000).toLocaleString()} tokens`">
                  {{ formatCompactTokens(model.context_window) }}
                </td>

                <!-- 4. 最大输出 (紧凑 K/M 显示) -->
                <td class="py-2.5 px-2 text-right font-mono text-[#6E6E73]" :title="`${Number(model.max_output || 8192).toLocaleString()} tokens`">
                  {{ formatCompactTokens(model.max_output) }}
                </td>

                <!-- 5. 输入模态 (精致 Icon 替代文字) -->
                <td class="py-2.5 px-2 text-center whitespace-nowrap">
                  <div class="inline-flex items-center space-x-1 text-xs">
                    <span title="支持文本输入 (Text)">📄</span>
                    <span v-if="isVisionModel(model.model_id, model.name)" title="支持视觉图像识别 (Vision)">🖼️</span>
                    <span v-if="isVideoModel(model.model_id)" title="支持视频输入 (Video)">🎬</span>
                  </div>
                </td>

                <!-- 6. 深度推理 -->
                <td class="py-2.5 px-2 text-center font-mono">
                  <span v-if="isReasoningModel(model.model_id, model.name)" class="text-[#34C759] font-bold">是</span>
                  <span v-else class="text-[#86868B]">-</span>
                </td>

                <!-- 7. 工具调用 -->
                <td class="py-2.5 px-2 text-center font-mono">
                  <span class="text-[#34C759] font-bold">是</span>
                </td>

                <!-- 8. 结构化输出 -->
                <td class="py-2.5 px-2 text-center font-mono">
                  <span class="text-[#34C759] font-bold">是</span>
                </td>

                <!-- 9. 官方输入单价 (独立列，响应全局货币切换) -->
                <td class="py-2.5 px-2 text-right font-mono font-medium text-[#1D1D1F]">
                  {{ formatOfficialPrice(model.official_input_price) }}
                </td>

                <!-- 10. 官方输出单价 (独立列，响应全局货币切换) -->
                <td class="py-2.5 px-2 text-right font-mono font-medium text-[#1D1D1F]">
                  {{ formatOfficialPrice(model.official_output_price) }}
                </td>

                <!-- 11. 全网最低单价 (响应全局货币切换) -->
                <td class="py-2.5 px-2 text-right font-mono font-bold text-[#34C759]">
                  {{ store.formatCurrency(model.lowest_price_usd) }}/1M
                </td>

                <!-- 12. 快捷操作 (精简下拉气泡菜单) -->
                <td class="py-2.5 px-2 text-center w-20 whitespace-nowrap relative">
                  <button
                    @click.stop="toggleModelActionDropdown(model.model_id)"
                    class="px-2 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] active:bg-[#D1D1D6] text-[#1D1D1F] border border-[#E5E5EA] text-[11px] font-medium transition-all inline-flex items-center space-x-1"
                    :class="{'bg-[#E8F2FD] border-[#CCE4FB] text-[#0071E3] font-bold': activeActionDropdownModelId === model.model_id}"
                  >
                    <span>操作</span>
                    <span class="text-[9px] text-[#86868B] transition-transform duration-150" :class="{'rotate-180': activeActionDropdownModelId === model.model_id}">▾</span>
                  </button>

                  <!-- 浮层气泡下拉菜单 -->
                  <div
                    v-if="activeActionDropdownModelId === model.model_id"
                    class="absolute right-2 top-9 w-32 bg-[#FFFFFF] border border-[#E5E5EA] rounded-xl shadow-[0_12px_30px_rgba(0,0,0,0.12)] z-30 py-1 text-left animate-fade-in text-xs divide-y divide-[#F2F2F7]"
                    @click.stop
                  >
                    <button
                      @click="goToMatrix(model.model_id); closeAllDropdowns()"
                      class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#0071E3] transition-colors"
                    >
                      <span>⚖️</span>
                      <span>全网比价</span>
                    </button>
                    <button
                      @click="goToSpeedTest(model.model_id); closeAllDropdowns()"
                      class="w-full px-3 py-1.5 hover:bg-[#F2F2F7] flex items-center space-x-2 text-[#34C759] font-medium transition-colors"
                    >
                      <span>⚡</span>
                      <span>一键测速</span>
                    </button>
                  </div>
                </td>
              </tr>

              <tr v-if="paginatedModels.length === 0">
                <td colspan="12" class="py-12 text-center text-xs text-[#86868B]">
                  当前厂商下无匹配的模型记录
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 底部轻量分页工具栏 (防卡顿极速 60 FPS) -->
        <div v-if="totalPages > 1" class="pt-2 border-t border-[#E5E5EA] flex items-center justify-between text-xs select-none">
          <div class="flex items-center space-x-2 text-[#86868B]">
            <span>第 <strong class="text-[#1D1D1F]">{{ currentPage }}</strong> / {{ totalPages }} 页</span>
            <span>(共 <strong class="text-[#0071E3] font-mono">{{ totalItems }}</strong> 款模型)</span>
            <span class="text-[#D1D1D6]">•</span>
            <span>每页</span>
            <select
              v-model.number="pageSize"
              class="bg-[#F2F2F7] border border-[#E5E5EA] rounded-lg px-2 py-0.5 text-xs text-[#1D1D1F] focus:outline-none"
            >
              <option :value="20">20 条</option>
              <option :value="50">50 条</option>
              <option :value="100">100 条</option>
            </select>
          </div>

          <div class="flex items-center space-x-1">
            <button
              :disabled="currentPage === 1"
              @click="currentPage = 1"
              class="px-2 py-1 rounded-lg border border-[#E5E5EA] bg-[#FFFFFF] hover:bg-[#F2F2F7] disabled:opacity-30 text-[#1D1D1F] transition-all text-xs cursor-pointer"
              title="第一页"
            >
              «
            </button>
            <button
              :disabled="currentPage === 1"
              @click="currentPage--"
              class="px-2.5 py-1 rounded-lg border border-[#E5E5EA] bg-[#FFFFFF] hover:bg-[#F2F2F7] disabled:opacity-30 text-[#1D1D1F] transition-all text-xs cursor-pointer"
            >
              上一页
            </button>

            <button
              v-for="p in visiblePages"
              :key="`page-${p}`"
              @click="currentPage = p"
              class="px-2.5 py-1 rounded-lg border text-xs font-mono transition-all cursor-pointer"
              :class="currentPage === p ? 'bg-[#0071E3] text-white border-[#0071E3] font-bold shadow-xs' : 'bg-[#FFFFFF] text-[#1D1D1F] border-[#E5E5EA] hover:bg-[#F2F2F7]'"
            >
              {{ p }}
            </button>

            <button
              :disabled="currentPage === totalPages"
              @click="currentPage++"
              class="px-2.5 py-1 rounded-lg border border-[#E5E5EA] bg-[#FFFFFF] hover:bg-[#F2F2F7] disabled:opacity-30 text-[#1D1D1F] transition-all text-xs cursor-pointer"
            >
              下一页
            </button>
            <button
              :disabled="currentPage === totalPages"
              @click="currentPage = totalPages"
              class="px-2 py-1 rounded-lg border border-[#E5E5EA] bg-[#FFFFFF] hover:bg-[#F2F2F7] disabled:opacity-30 text-[#1D1D1F] transition-all text-xs cursor-pointer"
              title="最后一页"
            >
              »
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'
import LabLogo from '../components/LabLogo.vue'
import type { ModelMetadata } from '../types'

interface OfficialLabDef {
  id: string
  displayName: string
  description: string
  providersCount: number
}

interface LabItem extends OfficialLabDef {
  models: ModelMetadata[]
  families: string[]
}

const store = useDashboardStore()
const selectedLabId = ref<string | null>(null)
const selectedLab = computed<LabItem | null>(() => {
  if (!selectedLabId.value) return null
  const target = selectedLabId.value.toLowerCase().trim()
  return (
    officialLabsList.value.find((l) => {
      const lid = l.id.toLowerCase()
      const dName = l.displayName.toLowerCase()
      return lid === target || lid.includes(target) || target.includes(lid) || dName.includes(target)
    }) || null
  )
})
const labSearchQuery = ref('')
const modelSearchQuery = ref('')
const isCopied = ref(false)
const activeActionDropdownModelId = ref<string | null>(null)

// 排序状态
const sortField = ref<string>('context_window')
const sortOrder = ref<'asc' | 'desc'>('desc')

const toggleModelActionDropdown = (modelId: string) => {
  if (activeActionDropdownModelId.value === modelId) {
    activeActionDropdownModelId.value = null
  } else {
    activeActionDropdownModelId.value = modelId
  }
}

const closeAllDropdowns = () => {
  activeActionDropdownModelId.value = null
}

onMounted(() => {
  window.addEventListener('click', closeAllDropdowns)
})

onUnmounted(() => {
  window.removeEventListener('click', closeAllDropdowns)
})

// 官方 30 大权威 Labs 研发机构定义清单 (对标 models.dev/labs/)
const officialLabsDef: OfficialLabDef[] = [
  {
    id: 'alibaba',
    displayName: 'Alibaba (阿里巴巴通义千问 Qwen)',
    description: '阿里巴巴通义实验室 (Qwen) 打造全开源与云端托管的多语言大模型矩阵，涵盖 Qwen3.8、Qwen2.5 等推理、代码、多模态与智能体工作流。',
    providersCount: 72
  },
  {
    id: 'openai',
    displayName: 'OpenAI (GPT / o1 / o3)',
    description: 'OpenAI 是全球领先的人工智能研发机构，开创了 GPT-5、GPT-4o、o1/o3 深度推理系列，在通用智能与代码生成领域处于前沿。',
    providersCount: 82
  },
  {
    id: 'anthropic',
    displayName: 'Anthropic (Claude)',
    description: 'Anthropic 专注于研发安全可控的 Claude 系列模型，在长上下文 (200k+)、复杂分析、编码助手和多模态理解方面表现卓越。',
    providersCount: 50
  },
  {
    id: 'deepseek',
    displayName: 'DeepSeek (深度求索)',
    description: '深度求索 (DeepSeek) 专注于研发原创先进开源大模型，凭借 V3 架构与 R1 深度思考推理模型，以超高性价比重塑全网格局。',
    providersCount: 81
  },
  {
    id: 'google',
    displayName: 'Google DeepMind (Gemini / Gemma)',
    description: 'Google DeepMind 推出 Gemini 原生多模态大模型系列，具备 100万~200万超大上下文窗口，擅长跨视频、音频与长文本推理。',
    providersCount: 66
  },
  {
    id: 'meta',
    displayName: 'Meta (Llama)',
    description: 'Meta AI 领导全球顶级开源大模型生态，Llama 3 系列为全行业开发者提供极高自由度与强大的微调部署能力。',
    providersCount: 34
  },
  {
    id: 'moonshotai',
    displayName: 'Moonshot AI (月之暗面 Kimi)',
    description: '月之暗面 (Moonshot AI) 是国内长文本大模型开创者，Kimi 系列支持超长上下文与深度思考推理能力，赋能高难度专业工作流。',
    providersCount: 87
  },
  {
    id: 'zhipuai',
    displayName: 'Zhipu AI (智谱清言 GLM)',
    description: '智谱 AI (Zhipu AI) 源自清华团队，致力于打造 GLM 大模型基座，涵盖对话、代码、多模态及智能体工具调用体系。',
    providersCount: 56
  },
  {
    id: 'mistral',
    displayName: 'Mistral AI (Codestral / Pixtral)',
    description: 'Mistral AI 是欧洲顶尖开源大模型团队，在小参数极致效率、代码理解与多语言性能上极具优势。',
    providersCount: 28
  },
  {
    id: 'nvidia',
    displayName: 'Nvidia (Nemotron)',
    description: 'NVIDIA Nemotron 家族为推理、RAG、安全与多模态智能体提供全开源权重、训练配方与极速算力部署方案。',
    providersCount: 33
  },
  {
    id: 'bytedance',
    displayName: 'ByteDance (字节跳动 Doubao / Seed)',
    description: '字节跳动推出豆包 (Doubao) 与 Seed 基础大模型，具备超强多模态理解与高并发吞吐能力。',
    providersCount: 38
  },
  {
    id: 'tencent',
    displayName: 'Tencent (腾讯混元 Hunyuan)',
    description: '腾讯混元 (Hunyuan) 大模型具备强大的中文理解、长文创作、数理逻辑与多模态生成能力。',
    providersCount: 22
  },
  {
    id: 'xai',
    displayName: 'xAI (Grok)',
    description: '埃隆·马斯克创立的 xAI，Grok 系列主打实时世界知识获取、深度推理与无过滤编程辅助。',
    providersCount: 16
  },
  {
    id: 'minimax',
    displayName: 'MiniMax (稀宇科技)',
    description: 'MiniMax 致力于研发通用智能模型，自研 MoE 架构与全模态大模型，在超长文本与语音视觉交互上领先。',
    providersCount: 48
  },
  {
    id: 'cohere',
    displayName: 'Cohere (Command)',
    description: 'Cohere 专注于企业级 AI，Command 系列多语言模型在 RAG 检索增强、安全智能体与工作流中表现突出。',
    providersCount: 14
  },
  {
    id: 'microsoft',
    displayName: 'Microsoft (Phi)',
    description: '微软研发的 Phi 系列小语言模型，以极致的数据集质量在小参数规模下实现了卓越的推理与编码表现。',
    providersCount: 18
  },
  {
    id: 'stepfun',
    displayName: 'StepFun (阶跃星辰 Step)',
    description: '阶跃星辰研发 Step 系列多模态大模型，在图像视频理解、超长文本以及复杂工具调度上深度优化。',
    providersCount: 17
  },
  {
    id: 'xiaomi',
    displayName: 'Xiaomi (小米 MiLM)',
    description: '小米端云协同大模型，聚焦移动端与边缘计算高能效比，赋能澎湃智能生态。',
    providersCount: 12
  },
  {
    id: 'baichuan',
    displayName: 'Baichuan (百川智能)',
    description: '百川智能由王小川创立，专注于通用医疗与知识增强大模型，中文医疗与综合常识表现优异。',
    providersCount: 15
  },
  {
    id: 'perplexity',
    displayName: 'Perplexity (Sonar)',
    description: 'Perplexity Sonar 模型将搜索与网络事实核查作为原生能力，提供带引文的可靠研究型智能体。',
    providersCount: 12
  },
  {
    id: 'ibm',
    displayName: 'IBM (Granite)',
    description: 'IBM Granite 专注企业代码与合规场景，提供透明、合规的开源语言模型。',
    providersCount: 8
  },
  {
    id: 'meituan',
    displayName: 'Meituan (美团 LongCat)',
    description: '美团 LongCat 模型专为长文本理解与商业生活服务场景深度定制。',
    providersCount: 5
  },
  {
    id: 'arcee-ai',
    displayName: 'Arcee AI (Trinity)',
    description: 'Arcee AI 专注于开源轻量高效推理大模型，主打高部署性与低算力消耗。',
    providersCount: 8
  },
  {
    id: 'poolside',
    displayName: 'Poolside (Laguna)',
    description: 'Poolside 研发专注软件开发全生命周期的代码大模型。',
    providersCount: 10
  },
  {
    id: 'sakana',
    displayName: 'Sakana AI (Fugu)',
    description: 'Sakana AI 源自日本，探索受自然启发的模型融合与多智能体进化路由架构。',
    providersCount: 11
  },
  {
    id: 'sarvam',
    displayName: 'Sarvam AI',
    description: '专注于印度多语言与本土场景的开源推理大模型研发机构。',
    providersCount: 3
  },
  {
    id: 'upstage',
    displayName: 'Upstage (Solar)',
    description: '韩国 Upstage 研发 Solar 系列大模型，在文档理解与商业问答中表现优异。',
    providersCount: 9
  },
  {
    id: 'thinkingmachines',
    displayName: 'Thinking Machines',
    description: '前沿智能体与通用大模型研发机构。',
    providersCount: 21
  },
  {
    id: 'aisingapore',
    displayName: 'AI Singapore (Sea-Lion)',
    description: '新加坡国家级 AI 研究院，开发东南亚多语言大模型。',
    providersCount: 2
  },
  {
    id: 'community',
    displayName: 'Open Source Community (全网开源社区)',
    description: '收录全球开源社区、独立开发者及学术机构发布的其他优质大语言模型。',
    providersCount: 45
  }
]

// 将模型严格归属到 30 大权威 Lab 下
const assignModelToLab = (m: ModelMetadata): string => {
  const mId = m.model_id.toLowerCase()
  const p = (m.provider || '').toLowerCase()

  if (mId.includes('qwen') || p.includes('alibaba') || p.includes('qwen')) return 'alibaba'
  if (mId.includes('deepseek') || p.includes('deepseek')) return 'deepseek'
  if (mId.includes('gpt') || mId.includes('o1') || mId.includes('o3') || mId.includes('whisper') || p.includes('openai')) return 'openai'
  if (mId.includes('claude') || p.includes('anthropic')) return 'anthropic'
  if (mId.includes('gemini') || mId.includes('gemma') || p.includes('google')) return 'google'
  if (mId.includes('llama') || p.includes('meta')) return 'meta'
  if (mId.includes('kimi') || mId.includes('moonshot') || p.includes('moonshotai')) return 'moonshotai'
  if (mId.includes('glm') || mId.includes('chatglm') || p.includes('zhipu')) return 'zhipuai'
  if (mId.includes('doubao') || mId.includes('seed') || p.includes('bytedance')) return 'bytedance'
  if (mId.includes('hunyuan') || mId.includes('hy') || p.includes('tencent')) return 'tencent'
  if (mId.includes('mistral') || mId.includes('codestral') || mId.includes('pixtral') || p.includes('mistral')) return 'mistral'
  if (mId.includes('nemotron') || p.includes('nvidia')) return 'nvidia'
  if (mId.includes('command') || p.includes('cohere')) return 'cohere'
  if (mId.includes('grok') || p.includes('xai')) return 'xai'
  if (mId.includes('minimax') || p.includes('minimax')) return 'minimax'
  if (mId.includes('step') || p.includes('stepfun')) return 'stepfun'
  if (mId.includes('sonar') || p.includes('perplexity')) return 'perplexity'
  if (mId.includes('phi') || p.includes('microsoft')) return 'microsoft'
  if (mId.includes('granite') || p.includes('ibm')) return 'ibm'
  if (mId.includes('mimo') || mId.includes('milm') || p.includes('xiaomi')) return 'xiaomi'
  if (mId.includes('baichuan') || p.includes('baichuan')) return 'baichuan'
  if (mId.includes('longcat') || p.includes('meituan')) return 'meituan'
  if (mId.includes('trinity') || p.includes('arcee')) return 'arcee-ai'
  if (mId.includes('laguna') || p.includes('poolside')) return 'poolside'
  if (mId.includes('sakana') || p.includes('fugu')) return 'sakana'
  if (mId.includes('sarvam') || p.includes('sarvam')) return 'sarvam'
  if (mId.includes('solar') || p.includes('upstage')) return 'upstage'
  if (mId.includes('sea-lion') || p.includes('aisingapore')) return 'aisingapore'

  return 'community'
}

// 自动聚合 30 大官方 Labs
const officialLabsList = computed<LabItem[]>(() => {
  const map: Record<string, ModelMetadata[]> = {}
  officialLabsDef.forEach((def) => {
    map[def.id] = []
  })

  store.modelsCatalog.forEach((m) => {
    const labId = assignModelToLab(m)
    if (map[labId]) {
      map[labId].push(m)
    } else {
      map['community'].push(m)
    }
  })

  return officialLabsDef.map((def) => {
    const models = map[def.id] || []
    const familiesSet = new Set<string>()
    models.forEach((m) => {
      if (m.series) familiesSet.add(m.series)
      else if (m.family) familiesSet.add(m.family.replace(/-/g, ' ').toUpperCase())
      else familiesSet.add('通用系列')
    })

    return {
      ...def,
      models,
      families: Array.from(familiesSet)
    }
  })
})

const filteredLabs = computed(() => {
  if (!labSearchQuery.value.trim()) return officialLabsList.value
  const q = labSearchQuery.value.toLowerCase().trim()
  return officialLabsList.value.filter(
    (lab) =>
      lab.displayName.toLowerCase().includes(q) ||
      lab.id.toLowerCase().includes(q) ||
      lab.description.toLowerCase().includes(q)
  )
})

const selectLab = (lab: LabItem) => {
  selectedLabId.value = lab.id
  modelSearchQuery.value = ''
  sortField.value = 'context_window'
  sortOrder.value = 'desc'
}

const copyText = (txt: string) => {
  navigator.clipboard.writeText(txt)
  isCopied.value = true
  setTimeout(() => (isCopied.value = false), 2000)
}

const formatCompactTokens = (num?: number) => {
  if (!num) return '-'
  const n = Number(num)
  if (n >= 1000000) {
    const m = n / 1000000
    return m % 1 === 0 ? `${m}M` : `${m.toFixed(1).replace(/\.0$/, '')}M`
  }
  if (n >= 1000) {
    const k = n / 1000
    return k % 1 === 0 ? `${k}K` : `${k.toFixed(1).replace(/\.0$/, '')}K`
  }
  return String(n)
}

const formatOfficialPrice = (priceUsd?: number) => {
  if (priceUsd === undefined || priceUsd === null) return '$0.000'
  if (store.currency === 'USD') {
    return `$${Number(priceUsd).toFixed(3)}`
  } else {
    return `¥${(Number(priceUsd) * store.usdToCnyRate).toFixed(3)}`
  }
}

const isVisionModel = (id: string, name: string) => {
  const s = (id + ' ' + name).toLowerCase()
  return s.includes('vl') || s.includes('vision') || s.includes('4o') || s.includes('gemini') || s.includes('claude') || s.includes('max')
}

const isVideoModel = (id: string) => {
  const s = id.toLowerCase()
  return s.includes('video') || s.includes('gemini') || s.includes('qwen3.8') || s.includes('qwen3.7')
}

const isReasoningModel = (id: string, name: string) => {
  const s = (id + ' ' + name).toLowerCase()
  return s.includes('r1') || s.includes('reasoner') || s.includes('thinking') || s.includes('o1') || s.includes('o3')
}

// 排序与筛选模型
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

const sortedAndFilteredModels = computed(() => {
  if (!selectedLab.value) return []
  let list = [...selectedLab.value.models]

  if (modelSearchQuery.value.trim()) {
    const q = modelSearchQuery.value.toLowerCase().trim()
    list = list.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.model_id.toLowerCase().includes(q) ||
        (m.series && m.series.toLowerCase().includes(q))
    )
  }

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

// 分页状态 (针对 OpenAI 等 400+ 款大厂商提供防卡顿分页与极速响应)
const currentPage = ref(1)
const pageSize = ref(50)
const totalItems = computed(() => sortedAndFilteredModels.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)))
const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)

const paginatedModels = computed(() => {
  return sortedAndFilteredModels.value.slice(startIndex.value, startIndex.value + pageSize.value)
})

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

watch([modelSearchQuery, selectedLabId], () => {
  currentPage.value = 1
})

const goToMatrix = (modelId: string) => {
  store.navigateToPriceMatrix({ modelId })
}

const goToSpeedTest = (modelId: string) => {
  store.navigateToSpeedTest(undefined, modelId)
}

const checkAndApplyTargetLab = async () => {
  if (store.targetLabProvider) {
    const target = store.targetLabProvider.toLowerCase().trim()
    store.targetLabProvider = null
    if (store.modelsCatalog.length === 0) {
      await store.fetchModelsCatalog()
    }
    const matched = officialLabsList.value.find((l) => {
      const lid = l.id.toLowerCase()
      const dName = l.displayName.toLowerCase()
      return (
        lid === target ||
        lid.includes(target) ||
        target.includes(lid) ||
        dName.includes(target)
      )
    })
    if (matched) {
      selectedLabId.value = matched.id
    } else {
      selectedLabId.value = 'community'
    }
  }
}

onMounted(async () => {
  window.addEventListener('click', closeAllDropdowns)
  await checkAndApplyTargetLab()
})

watch(
  () => store.targetLabProvider,
  async (newVal) => {
    if (newVal) {
      await checkAndApplyTargetLab()
    }
  }
)
</script>

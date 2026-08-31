<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 overflow-hidden select-none font-sans">
      <!-- 半透明磨砂遮罩背景 (点击关闭) -->
      <div
        @click="close"
        class="fixed inset-0 bg-black/30 backdrop-blur-xs transition-opacity animate-fade-in"
      ></div>

      <!-- 右侧滑出主体面板 -->
      <div class="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div class="w-screen max-w-2xl bg-[#F5F5F7] shadow-2xl flex flex-col overflow-hidden animate-slide-left border-l border-[#E5E5EA]">
          <!-- 1. 顶部 Header 厂商基本信息 -->
          <div class="p-4 bg-[#FFFFFF] border-b border-[#E5E5EA] space-y-3 flex-shrink-0 shadow-xs">
            <!-- 顶部返回与代码标识 -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="px-2.5 py-1 rounded-lg bg-[#E8F2FD] text-[#0071E3] text-xs font-bold font-mono flex items-center space-x-1.5">
                  <SystemIcon name="models" custom-class="w-3.5 h-3.5 text-[#0071E3]" />
                  <span>大模型研发机构与厂商详情</span>
                </span>
              </div>

              <div class="flex items-center space-x-2">
                <span class="text-[11px] text-[#86868B]">官方机构标识:</span>
                <code class="px-2 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA] text-[#0071E3] font-mono text-xs font-bold">
                  {{ currentLab?.id || providerId || '-' }}
                </code>
                <button
                  @click="copyText(currentLab?.id || providerId || '')"
                  class="text-xs text-[#6E6E73] hover:text-[#1D1D1F] px-2 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA] cursor-pointer"
                >
                  {{ isCopied ? '✓ 已复制' : '复制' }}
                </button>
                <button
                  @click="close"
                  class="w-7 h-7 rounded-full bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center text-sm font-bold transition-all ml-2 cursor-pointer"
                  title="关闭 (Esc)"
                >
                  ✕
                </button>
              </div>
            </div>

            <!-- 厂商大标题、官方 Logo 与简介文案 -->
            <div v-if="currentLab" class="flex items-start space-x-3.5">
              <div class="w-12 h-12 rounded-2xl bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center p-2.5 flex-shrink-0">
                <LabLogo :lab-id="currentLab.id" custom-class="w-7 h-7" />
              </div>
              <div class="space-y-1">
                <h2 class="text-lg font-bold text-[#1D1D1F] tracking-tight">
                  {{ currentLab.displayName }}
                </h2>
                <p class="text-xs text-[#6E6E73] leading-relaxed">
                  {{ currentLab.description }}
                </p>
              </div>
            </div>

            <!-- 2. 核心指标统计网格 (Fact Grid) -->
            <div v-if="currentLab" class="grid grid-cols-4 gap-2 pt-2 border-t border-[#E5E5EA]">
              <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
                <div class="text-[10px] text-[#86868B] font-medium uppercase">标准收录模型数</div>
                <div class="text-base font-bold font-mono text-[#0071E3] mt-0.5">{{ vendorModels.length }} 款</div>
              </div>
              <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
                <div class="text-[10px] text-[#86868B] font-medium uppercase">全网接入渠道</div>
                <div class="text-base font-bold font-mono text-[#34C759] mt-0.5">{{ currentLab.providersCount }} 家</div>
              </div>
              <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
                <div class="text-[10px] text-[#86868B] font-medium uppercase">核心模型系列</div>
                <div class="text-base font-bold font-mono text-[#AF52DE] mt-0.5">{{ vendorFamiliesCount }} 个系列</div>
              </div>
              <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
                <div class="text-[10px] text-[#86868B] font-medium uppercase">数据规范标准</div>
                <div class="text-xs font-bold font-mono text-[#1D1D1F] mt-1">models.dev 实时</div>
              </div>
            </div>
          </div>

          <!-- 3. 该厂商全系模型规格与定价清单 -->
          <div class="flex-1 flex flex-col p-3 overflow-hidden min-h-0 bg-[#FFFFFF] m-3 rounded-2xl border border-[#E5E5EA] shadow-xs">
            <!-- 头部控制栏：支持筛选范围切换 (当前比价筛选 vs 查看全部) -->
            <div class="flex items-center justify-between pb-2 border-b border-[#E5E5EA] flex-shrink-0 flex-wrap gap-2">
              <div class="flex items-center space-x-2">
                <span class="text-xs font-bold text-[#1D1D1F]">
                  📋 模型清单
                </span>

                <!-- 模式切换 Segmented Control (有父级筛选时展示) -->
                <div v-if="hasActiveParentFilters" class="inline-flex p-0.5 rounded-lg bg-[#E5E5EA]/70 border border-[#D1D1D6]/60 text-xs">
                  <button
                    @click="viewScope = 'filtered'"
                    class="px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center space-x-1"
                    :class="viewScope === 'filtered' ? 'bg-[#FFFFFF] text-[#0071E3] font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
                  >
                    <span>✨ 筛选项结果</span>
                    <span
                      class="px-1.5 py-0.2 rounded-full text-[10px] font-mono"
                      :class="viewScope === 'filtered' ? 'bg-[#E8F2FD] text-[#0071E3]' : 'bg-[#E5E5EA] text-[#86868B]'"
                    >
                      {{ matchingFilterModels.length }}
                    </span>
                  </button>
                  <button
                    @click="viewScope = 'all'"
                    class="px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center space-x-1"
                    :class="viewScope === 'all' ? 'bg-[#FFFFFF] text-[#1D1D1F] font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
                  >
                    <span>🌐 查看全部</span>
                    <span
                      class="px-1.5 py-0.2 rounded-full text-[10px] font-mono"
                      :class="viewScope === 'all' ? 'bg-[#F2F2F7] text-[#1D1D1F]' : 'bg-[#E5E5EA] text-[#86868B]'"
                    >
                      {{ vendorModels.length }}
                    </span>
                  </button>
                </div>
              </div>

              <!-- 0 元过滤切换按钮 -->
              <button
                @click="excludeZeroPrice = !excludeZeroPrice"
                class="px-2 py-1 rounded-lg border text-[11px] font-medium transition-all flex items-center space-x-1 cursor-pointer select-none"
                :class="excludeZeroPrice ? 'bg-[#EBF5FF] border-[#B9E1FF] text-[#0071E3] font-bold shadow-2xs' : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
                title="过滤掉官方未标价或价格为 0 的模型"
              >
                <span>{{ excludeZeroPrice ? '🚫 已隐藏 0 元' : '👁️ 显示全部 (含 0 元)' }}</span>
              </button>

              <!-- 搜索框 -->
              <div class="w-36 relative">
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="搜索模型/系列..."
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
                />
                <span v-if="searchQuery" @click="searchQuery = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
              </div>

              <!-- 导出 Excel 按钮 -->
              <button
                @click="handleExportVendorModels"
                :disabled="filteredModels.length === 0"
                class="px-2 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#CCE4FB] transition-all text-xs flex items-center space-x-1 cursor-pointer font-medium disabled:opacity-40 flex-shrink-0"
                title="导出当前抽屉中筛选的模型清单与最低价"
              >
                <span>📊</span>
                <span>导出</span>
              </button>
            </div>

            <!-- 当前筛选上下文指示条 (当处于 filtered 模式时) -->
            <div v-if="hasActiveParentFilters && viewScope === 'filtered'" class="flex items-center justify-between px-2.5 py-1.5 rounded-xl bg-[#E8F2FD]/70 border border-[#CCE4FB] text-[11px] text-[#0071E3] mt-2 mb-1 flex-shrink-0">
              <div class="flex items-center space-x-1.5 truncate">
                <span class="font-bold flex items-center space-x-1">
                  <span>🎯</span>
                  <span>已继承比价筛选:</span>
                </span>
                <span class="font-mono truncate">{{ activeFilterSummaryText }}</span>
              </div>
              <button @click="viewScope = 'all'" class="text-[11px] text-[#0071E3] hover:underline font-medium whitespace-nowrap ml-2 cursor-pointer flex-shrink-0">
                切换至全部 ({{ vendorModels.length }}款) ➔
              </button>
            </div>

            <!-- 数据表格 -->
            <div class="flex-1 overflow-x-auto overflow-y-auto pr-1 mt-1">
              <table class="w-full text-left text-xs border-collapse min-w-[580px]">
                <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans">
                  <tr>
                    <th class="py-2 px-2.5">模型名称 / 标准标识</th>
                    <th class="py-2 px-2 text-right w-16">上下文</th>
                    <th class="py-2 px-2 text-right w-18">官方单价</th>
                    <th class="py-2 px-2 text-right w-18">全网最低</th>
                    <th class="py-2 px-2 text-center w-20">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
                  <tr
                    v-for="model in pagedModels"
                    :key="model.model_id"
                    class="hover:bg-[#F5F5F7] transition-colors group"
                  >
                    <!-- 模型名称 + 标准 ID -->
                    <td class="py-2 px-2.5">
                      <div class="font-bold text-[#1D1D1F] group-hover:text-[#0071E3] text-xs">
                        {{ model.name }}
                      </div>
                      <div class="text-[10px] text-[#0071E3] font-mono">
                        {{ model.model_id }}
                      </div>
                    </td>

                    <!-- 上下文窗口 -->
                    <td class="py-2 px-2 text-right font-mono text-[#1D1D1F] text-[11px]">
                      {{ formatCompactTokens(model.context_window) }}
                    </td>

                    <!-- 官方单价 -->
                    <td class="py-2 px-2 text-right font-mono text-[#1D1D1F] text-[11px]">
                      {{ formatOfficialPrice(model.official_input_price) }}
                    </td>

                    <!-- 全网最低 -->
                    <td class="py-2 px-2 text-right font-mono font-bold text-[#34C759] text-[11px]">
                      {{ store.formatCurrency(model.lowest_price_usd) }}
                    </td>

                    <!-- 快捷比价/测速 -->
                    <td class="py-2 px-2 text-center whitespace-nowrap">
                      <button
                        @click="triggerModelCompare(model.model_id)"
                        class="px-2 py-0.5 rounded bg-[#E8F2FD] hover:bg-[#0071E3] text-[#0071E3] hover:text-white border border-[#CCE4FB] text-[10px] font-medium transition-all cursor-pointer mr-1 inline-flex items-center space-x-0.5"
                        title="在全网比价中只查看接入该模型的所有渠道"
                      >
                        <SystemIcon name="chart" custom-class="w-2.5 h-2.5" />
                        <span>比价</span>
                      </button>
                    </td>
                  </tr>

                  <tr v-if="filteredModels.length === 0">
                    <td colspan="5" class="py-12 text-center text-xs text-[#86868B]">
                      <div class="space-y-1">
                        <div>{{ viewScope === 'filtered' ? '当前厂商下暂无符合当前比价筛选条件的模型' : '无匹配的模型记录' }}</div>
                        <button
                          v-if="viewScope === 'filtered' && vendorModels.length > 0"
                          @click="viewScope = 'all'"
                          class="text-[#0071E3] hover:underline cursor-pointer text-xs font-medium"
                        >
                          点击查看该厂商全系 {{ vendorModels.length }} 款模型 ➔
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 底部分页控制栏 -->
            <div v-if="totalPages > 1" class="pt-2 border-t border-[#E5E5EA] flex items-center justify-between text-xs select-none flex-shrink-0">
              <div class="text-[11px] text-[#86868B]">
                第 <strong class="text-[#1D1D1F]">{{ currentPage }}</strong> / {{ totalPages }} 页 (共 {{ filteredModels.length }} 款)
              </div>
              <div class="flex items-center space-x-1">
                <button
                  :disabled="currentPage === 1"
                  @click="currentPage--"
                  class="px-2 py-0.5 rounded bg-[#FFFFFF] border border-[#E5E5EA] hover:bg-[#F2F2F7] disabled:opacity-30 text-[11px] cursor-pointer"
                >
                  上一页
                </button>
                <button
                  :disabled="currentPage === totalPages"
                  @click="currentPage++"
                  class="px-2 py-0.5 rounded bg-[#FFFFFF] border border-[#E5E5EA] hover:bg-[#F2F2F7] disabled:opacity-30 text-[11px] cursor-pointer"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'
import LabLogo from './LabLogo.vue'
import SystemIcon from './SystemIcon.vue'
import type { ModelMetadata } from '../types'
import { exportVendorModelsToExcel } from '../utils/excelExport'

export interface FilterContext {
  providers?: string[]
  series?: string[]
  models?: string[]
  availableModelIds?: string[]
}

interface OfficialLabDef {
  id: string
  displayName: string
  description: string
  providersCount: number
}

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
    displayName: 'ByteDance (字节跳动豆包 / Seed)',
    description: '字节跳动打造豆包大模型家族，涵盖通用对话、文生图、语音与多模态交互。',
    providersCount: 42
  },
  {
    id: 'tencent',
    displayName: 'Tencent (腾讯混元 Hunyuan)',
    description: '腾讯混元大模型拥有全链路自研体系，涵盖通用大模型、文生图、3D生成及文生视频前沿模型。',
    providersCount: 20
  },
  {
    id: 'xai',
    displayName: 'xAI (Grok)',
    description: '由埃隆·马斯克创立的前沿 AI 机构，研发 Grok-3 等顶尖大模型。',
    providersCount: 26
  },
  {
    id: 'minimax',
    displayName: 'MiniMax (名之梦 / abab)',
    description: 'MiniMax 自研通用大模型底座，在文本、语音和视频生成三位一体多模态领域表现出众。',
    providersCount: 38
  },
  {
    id: 'cohere',
    displayName: 'Cohere (Command R+)',
    description: 'Cohere 专注于企业级智能体、高精度 RAG 搜索召回与多语言多步推理。',
    providersCount: 25
  },
  {
    id: 'microsoft',
    displayName: 'Microsoft (Phi)',
    description: '微软轻量高能 SLM (Small Language Models) 先锋，Phi 系列主打端侧高推理质量。',
    providersCount: 19
  },
  {
    id: 'stepfun',
    displayName: 'StepFun (阶跃星辰 / 跃问)',
    description: '阶跃星辰专注于万亿参数 MoE 与超长多模态大模型研发。',
    providersCount: 18
  },
  {
    id: 'xiaomi',
    displayName: 'Xiaomi (小米 MiLM / MiMo)',
    description: '小米端云协同大模型矩阵，深入智能手机与多设备万物互联终端。',
    providersCount: 16
  },
  {
    id: 'baichuan',
    displayName: 'Baichuan (百川智能)',
    description: '百川智能专注于通用医疗与知识增强大模型，中文医疗与综合常识表现优异。',
    providersCount: 15
  },
  {
    id: 'perplexity',
    displayName: 'Perplexity (Sonar)',
    description: 'Perplexity Sonar 模型将搜索与网络事实核查作为原生能力。',
    providersCount: 12
  },
  {
    id: 'ibm',
    displayName: 'IBM (Granite)',
    description: 'IBM Granite 专注企业代码与合规场景，提供透明、合规的开源语言模型。',
    providersCount: 8
  },
  {
    id: 'community',
    displayName: 'Open Source Community (全网开源社区)',
    description: '收录全球开源社区、独立开发者及学术机构发布的其他优质大语言模型。',
    providersCount: 45
  }
]

const props = defineProps<{
  visible: boolean
  providerId: string | null
  filterContext?: FilterContext
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'compare-model', modelId: string): void
}>()

const store = useDashboardStore()
const isCopied = ref(false)
const searchQuery = ref('')
const excludeZeroPrice = ref(true)
const currentPage = ref(1)
const pageSize = ref(30)
const viewScope = ref<'filtered' | 'all'>('filtered')

const handleExportVendorModels = () => {
  if (!currentLab.value) return
  exportVendorModelsToExcel(
    currentLab.value.displayName || currentLab.value.id,
    filteredModels.value,
    store.currency as any,
    store.usdToCnyRate || 7.25
  )
}

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

  return 'community'
}

const currentLab = computed<OfficialLabDef>(() => {
  if (!props.providerId) return officialLabsDef[0]
  const target = props.providerId.toLowerCase().trim()
  const matched = officialLabsDef.find(
    (l) => l.id.toLowerCase() === target || target.includes(l.id.toLowerCase()) || l.id.toLowerCase().includes(target)
  )
  if (matched) return matched

  return {
    id: props.providerId,
    displayName: `${props.providerId.toUpperCase()} 模型研发机构`,
    description: `收录 ${props.providerId.toUpperCase()} 旗下的全系列标准大语言模型。`,
    providersCount: 10
  }
})

const vendorModels = computed<ModelMetadata[]>(() => {
  const labId = currentLab.value.id
  return store.modelsCatalog.filter((m) => assignModelToLab(m) === labId)
})

const vendorFamiliesCount = computed(() => {
  const set = new Set<string>()
  vendorModels.value.forEach((m) => {
    if (m.series) set.add(m.series)
    else if (m.family) set.add(m.family)
    else set.add('通用')
  })
  return set.size
})

const hasActiveParentFilters = computed(() => {
  if (!props.filterContext) return false
  return (
    (props.filterContext.series && props.filterContext.series.length > 0) ||
    (props.filterContext.models && props.filterContext.models.length > 0) ||
    (props.filterContext.availableModelIds && props.filterContext.availableModelIds.length > 0)
  )
})

const activeFilterSummaryText = computed(() => {
  if (!props.filterContext) return ''
  const parts: string[] = []
  if (props.filterContext.series && props.filterContext.series.length > 0) {
    parts.push(`系列: ${props.filterContext.series.join(', ')}`)
  }
  if (props.filterContext.models && props.filterContext.models.length > 0) {
    parts.push(`模型: ${props.filterContext.models.length > 2 ? `${props.filterContext.models.length}款` : props.filterContext.models.join(', ')}`)
  }
  return parts.join(' | ') || '全网比价筛选条件'
})

// 计算符合父级筛选条件的当前厂商模型子集
const matchingFilterModels = computed(() => {
  if (!hasActiveParentFilters.value) return vendorModels.value
  const targetModelIds = new Set(
    (props.filterContext?.availableModelIds || []).map((m) => m.toLowerCase().trim())
  )
  const explicitModels = new Set(
    (props.filterContext?.models || []).map((m) => m.toLowerCase().trim())
  )
  const explicitSeries = (props.filterContext?.series || []).map((s) => s.toLowerCase().trim())

  return vendorModels.value.filter((item) => {
    const mId = (item.model_id || '').toLowerCase().trim()
    const mName = (item.name || '').toLowerCase().trim()
    const mSeries = (item.series || item.family || '').toLowerCase().trim()

    // 1. 精确指定模型
    if (explicitModels.size > 0) {
      if (explicitModels.has(mId) || explicitModels.has(mName)) return true
    }

    // 2. 指定系列
    if (explicitSeries.length > 0) {
      if (
        explicitSeries.some((s) => {
          const sNorm = s.replace(/[^a-z0-9]/g, '')
          const mNorm = mId.replace(/[^a-z0-9]/g, '')
          const serNorm = mSeries.replace(/[^a-z0-9]/g, '')
          return (
            mSeries.includes(s) ||
            mId.includes(s) ||
            mName.includes(s) ||
            (sNorm && mNorm.includes(sNorm)) ||
            (sNorm && serNorm.includes(sNorm))
          )
        })
      ) {
        return true
      }
    }

    // 3. 当前比价收敛的模型 ID
    if (targetModelIds.size > 0) {
      if (targetModelIds.has(mId) || targetModelIds.has(mName)) return true
      for (const t of targetModelIds) {
        const tNorm = t.replace(/[^a-z0-9]/g, '')
        const mNorm = mId.replace(/[^a-z0-9]/g, '')
        if (mId.includes(t) || t.includes(mId) || (tNorm && mNorm.includes(tNorm))) return true
      }
    }

    return false
  })
})

const baseListByScope = computed(() => {
  if (viewScope.value === 'filtered' && hasActiveParentFilters.value) {
    return matchingFilterModels.value
  }
  return vendorModels.value
})

const filteredModels = computed(() => {
  let list = baseListByScope.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.model_id.toLowerCase().includes(q) ||
        (m.series && m.series.toLowerCase().includes(q))
    )
  }
  if (excludeZeroPrice.value) {
    list = list.filter(
      (m) => (m.official_input_price && m.official_input_price > 0) || (m.lowest_price_usd && m.lowest_price_usd > 0)
    )
  }
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredModels.value.length / pageSize.value)))

const pagedModels = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredModels.value.slice(start, start + pageSize.value)
})

watch([searchQuery, excludeZeroPrice], () => {
  currentPage.value = 1
})

watch(
  () => [props.visible, props.providerId],
  ([visible]) => {
    if (visible) {
      searchQuery.value = ''
      currentPage.value = 1
      viewScope.value = hasActiveParentFilters.value ? 'filtered' : 'all'
    }
  },
  { immediate: true }
)

const formatCompactTokens = (num?: number) => {
  if (!num) return '-'
  const n = Number(num)
  if (n >= 1000000) return `${(n / 1000000).toFixed(0)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(0)}K`
  return String(n)
}

const formatOfficialPrice = (priceUsd?: number) => {
  if (priceUsd === undefined || priceUsd === null) return '$0.000'
  if (store.currency === 'USD') {
    return `$${Number(priceUsd).toFixed(3)}`
  }
  return `¥${(Number(priceUsd) * (store.usdToCnyRate || 7.25)).toFixed(3)}`
}

const copyText = (txt?: string) => {
  if (!txt) return
  navigator.clipboard.writeText(txt)
  isCopied.value = true
  setTimeout(() => (isCopied.value = false), 2000)
}

const close = () => {
  emit('close')
}

const triggerModelCompare = (modelId: string) => {
  emit('compare-model', modelId)
  close()
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.visible) {
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
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

.animate-slide-left {
  animation: slideLeft 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>

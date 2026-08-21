<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- ==================== 场景 A：厂商与机构大全列表 (参考 models.dev/labs/) ==================== -->
    <template v-if="!selectedLab">
      <!-- 顶部操作栏 -->
      <div class="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold text-[#1D1D1F]">大模型研发机构与厂商 (共 {{ labsList.length }} 家)</span>
            <span class="text-xs text-[#86868B] font-mono">| 标准对齐 models.dev/labs/ 官方架构</span>
          </div>

          <!-- 搜索输入框 -->
          <div class="w-64 relative">
            <input
              v-model="labSearchQuery"
              type="text"
              placeholder="搜索厂商 (如 Alibaba, DeepSeek, OpenAI)..."
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
            />
            <span v-if="labSearchQuery" @click="labSearchQuery = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
          </div>
        </div>

        <button
          @click="store.syncModelsDev"
          class="text-xs px-3 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1"
        >
          <span>🔄 从 models.dev 重新同步模型库</span>
        </button>
      </div>

      <!-- 厂商卡片流 (3 列 Grid 布局，纯白苹果质感卡片 + 官方矢量 Logo 图标) -->
      <div class="flex-1 overflow-y-auto pr-1">
        <div class="grid grid-cols-3 gap-3">
          <div
            v-for="lab in filteredLabs"
            :key="lab.id"
            @click="selectLab(lab)"
            class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] hover:border-[#B3D7FF] hover:shadow-[0_6px_20px_rgba(0,0,0,0.04)] transition-all cursor-pointer flex flex-col justify-between space-y-3 group"
          >
            <!-- 厂商头部：官方矢量 Logo、名称、模型总数 Badge -->
            <div class="flex items-start justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center p-2 group-hover:scale-105 group-hover:bg-[#E8F2FD] transition-all">
                  <LabLogo :lab-id="lab.id" custom-class="w-6 h-6" />
                </div>
                <div>
                  <div class="font-bold text-sm text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors">
                    {{ lab.displayName }}
                  </div>
                  <div class="text-[11px] text-[#86868B] font-mono mt-0.5">
                    {{ lab.id }}
                  </div>
                </div>
              </div>

              <!-- 模型数量 Badge -->
              <span class="px-2 py-0.5 rounded-full bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB] text-xs font-mono font-bold">
                {{ lab.models.length }} 款模型
              </span>
            </div>

            <!-- 系列预览 Chips 胶囊 -->
            <div class="space-y-1">
              <div class="text-[10px] text-[#86868B] uppercase tracking-wider font-semibold">核心模型系列:</div>
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="fam in lab.families.slice(0, 4)"
                  :key="fam"
                  class="px-2 py-0.5 rounded-md bg-[#F2F2F7] border border-[#E5E5EA] text-[#1D1D1F] text-[10px] font-mono font-medium"
                >
                  {{ fam }}
                </span>
                <span v-if="lab.families.length > 4" class="text-[10px] text-[#86868B] font-mono self-center">
                  +{{ lab.families.length - 4 }} 系列
                </span>
              </div>
            </div>

            <!-- 底部进入按钮引导 -->
            <div class="pt-2 border-t border-[#E5E5EA] flex items-center justify-between text-xs text-[#6E6E73]">
              <span class="text-[11px] text-[#86868B]">点击进入厂商模型标准规格表</span>
              <span class="text-[#0071E3] group-hover:translate-x-1 transition-transform font-bold">浏览详情 →</span>
            </div>
          </div>
        </div>

        <div v-if="filteredLabs.length === 0" class="py-16 text-center text-xs text-[#86868B]">
          无匹配的厂商或研究机构
        </div>
      </div>
    </template>

    <!-- ==================== 场景 B：厂商详情与完整汉化对齐数据表格 (参考 models.dev/labs/alibaba/) ==================== -->
    <template v-else>
      <!-- 1. 顶部厂商介绍 Header 区 -->
      <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
        <!-- 顶部返回与代码标识 -->
        <div class="flex items-center justify-between">
          <button
            @click="selectedLab = null"
            class="px-3 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] transition-all text-xs font-medium flex items-center space-x-1"
          >
            <span>← 返回厂商大全 (Labs)</span>
          </button>

          <div class="flex items-center space-x-2">
            <span class="text-[11px] text-[#86868B]">厂商标识:</span>
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
                {{ getLabDescription(selectedLab.id) }}
              </p>
            </div>
          </div>

          <!-- 搜索过滤 -->
          <div class="w-60 relative">
            <input
              v-model="modelSearchQuery"
              type="text"
              placeholder="搜索模型名称/标识..."
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
            <div class="text-lg font-bold font-mono text-[#34C759] mt-0.5">{{ getLabTotalProvidersCount() }} 家</div>
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
                <th @click="toggleSort('active_relay_count')" class="py-2.5 px-3 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors">
                  接入渠道 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('active_relay_count') }}</span>
                </th>
                <th @click="toggleSort('context_window')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors">
                  上下文 (Context) <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('context_window') }}</span>
                </th>
                <th @click="toggleSort('max_output')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors">
                  最大输出 (Output) <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('max_output') }}</span>
                </th>
                <th class="py-2.5 px-3 text-center">输入模态</th>
                <th class="py-2.5 px-3 text-center">深度推理</th>
                <th class="py-2.5 px-3 text-center">工具调用</th>
                <th class="py-2.5 px-3 text-center">结构化输出</th>
                <th @click="toggleSort('official_input_price')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors">
                  官方单价 (输入/输出) <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('official_input_price') }}</span>
                </th>
                <th @click="toggleSort('lowest_price_usd')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors">
                  全网最低 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('lowest_price_usd') }}</span>
                </th>
                <th class="py-2.5 px-3 text-center">快捷操作</th>
              </tr>
            </thead>

            <!-- 数据行体 -->
            <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
              <tr
                v-for="model in sortedAndFilteredModels"
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

                <!-- 2. 接入渠道数 -->
                <td class="py-2.5 px-3 text-center">
                  <span
                    @click="goToMatrix(model.model_id)"
                    class="px-2 py-0.5 rounded-full bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6] font-mono font-bold text-xs cursor-pointer hover:bg-[#CEEAD6] transition-colors"
                    title="点击查看所有提供该模型的供应商"
                  >
                    {{ model.active_relay_count || 12 }} 家
                  </span>
                </td>

                <!-- 3. 上下文窗口 -->
                <td class="py-2.5 px-3 text-right font-mono text-[#1D1D1F]">
                  {{ formatContextWindow(model.context_window) }}
                </td>

                <!-- 4. 最大输出 -->
                <td class="py-2.5 px-3 text-right font-mono text-[#6E6E73]">
                  {{ model.max_output ? Number(model.max_output).toLocaleString() : '8,192' }}
                </td>

                <!-- 5. 输入模态 -->
                <td class="py-2.5 px-3 text-center">
                  <div class="inline-flex items-center space-x-1 text-[11px]">
                    <span class="px-1.5 py-0.2 rounded bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA]" title="支持文本">文本</span>
                    <span v-if="isVisionModel(model.model_id, model.name)" class="px-1.5 py-0.2 rounded bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]" title="支持视觉图像">图像</span>
                    <span v-if="isVideoModel(model.model_id)" class="px-1.5 py-0.2 rounded bg-[#F3E8FF] text-[#9333EA] border border-[#E9D5FF]" title="支持视频">视频</span>
                  </div>
                </td>

                <!-- 6. 深度推理 -->
                <td class="py-2.5 px-3 text-center font-mono">
                  <span v-if="isReasoningModel(model.model_id, model.name)" class="text-[#34C759] font-bold">是</span>
                  <span v-else class="text-[#86868B]">-</span>
                </td>

                <!-- 7. 工具调用 -->
                <td class="py-2.5 px-3 text-center font-mono">
                  <span class="text-[#34C759] font-bold">是</span>
                </td>

                <!-- 8. 结构化输出 -->
                <td class="py-2.5 px-3 text-center font-mono">
                  <span class="text-[#34C759] font-bold">是</span>
                </td>

                <!-- 9. 官方输入/输出单价 -->
                <td class="py-2.5 px-3 text-right font-mono font-medium text-[#1D1D1F]">
                  ${{ model.official_input_price }} / ${{ model.official_output_price }}
                </td>

                <!-- 10. 全网最低单价 -->
                <td class="py-2.5 px-3 text-right font-mono font-bold text-[#34C759]">
                  ${{ model.lowest_price_usd }}/1M
                </td>

                <!-- 11. 快捷操作 -->
                <td class="py-2.5 px-3 text-center font-mono text-[11px] whitespace-nowrap">
                  <button
                    @click="goToMatrix(model.model_id)"
                    class="text-[#0071E3] hover:underline mr-2 transition-colors font-medium"
                  >
                    [全网比价]
                  </button>
                  <button
                    @click="goToSpeedTest(model.model_id)"
                    class="text-[#34C759] hover:underline transition-colors font-bold"
                  >
                    [流式实测]
                  </button>
                </td>
              </tr>

              <tr v-if="sortedAndFilteredModels.length === 0">
                <td colspan="11" class="py-12 text-center text-xs text-[#86868B]">
                  无匹配的模型规格记录
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'
import LabLogo from '../components/LabLogo.vue'
import type { ModelMetadata } from '../types'

interface LabItem {
  id: string
  displayName: string
  models: ModelMetadata[]
  families: string[]
}

const store = useDashboardStore()
const selectedLab = ref<LabItem | null>(null)
const labSearchQuery = ref('')
const modelSearchQuery = ref('')
const isCopied = ref(false)

// 排序状态
const sortField = ref<string>('context_window')
const sortOrder = ref<'asc' | 'desc'>('desc')

// 厂商中英文友好名称映射表 (对齐 models.dev/labs/)
const labDisplayNameMap: Record<string, string> = {
  alibaba: 'Alibaba (阿里巴巴通义千问 Qwen)',
  openai: 'OpenAI (GPT / o1 / o3)',
  anthropic: 'Anthropic (Claude)',
  google: 'Google DeepMind (Gemini / Gemma)',
  deepseek: 'DeepSeek (深度求索)',
  moonshotai: 'Moonshot AI (月之暗面 Kimi)',
  zhipuai: 'Zhipu AI (智谱清言 GLM)',
  meta: 'Meta (Llama)',
  mistral: 'Mistral AI',
  nvidia: 'Nvidia (Nemotron)',
  cohere: 'Cohere (Command)',
  bytedance: 'ByteDance (字节跳动 Doubao)',
  'bytedance-seed': 'ByteDance Seed',
  xai: 'xAI (Grok)',
  minimax: 'MiniMax (稀宇科技)',
  xiaomi: 'Xiaomi (小米 MiLM)',
  tencent: 'Tencent (腾讯混元 Hunyuan)',
  baichuan: 'Baichuan (百川智能)',
  stepfun: 'StepFun (阶跃星辰)',
  perplexity: 'Perplexity (Sonar)',
  ibm: 'IBM (Granite)',
  meituan: 'Meituan (美团 LongCat)',
  microsoft: 'Microsoft (Phi)',
  poolside: 'Poolside',
  sakana: 'Sakana AI',
  sarvam: 'Sarvam AI',
  upstage: 'Upstage (Solar)'
}

// 厂商深度介绍文案 (中文)
const labDescriptions: Record<string, string> = {
  alibaba: '阿里巴巴通义实验室 (Qwen) 打造全开源与云端托管的多语言大模型矩阵，涵盖 Qwen3.8、Qwen2.5 等深度推理、代码生成、多模态视觉与长程智能体工作流。',
  openai: 'OpenAI 是全球领先的人工智能研发机构，开创了 GPT 系列、o1/o3 深度推理系列，在通用智能、代码生成及复杂推理领域处于行业前沿。',
  anthropic: 'Anthropic 专注于研发安全可控的 Claude 系列模型，在长上下文窗口 (200k+)、复杂逻辑分析、编码助手和多模态理解方面表现卓越。',
  deepseek: '深度求索 (DeepSeek) 专注于研发原创先进开源大模型，凭借 V3 架构与 R1 深度思考推理模型，以超高性价比与极致生成效率重塑全网格局。',
  google: 'Google DeepMind 推出 Gemini 原生多模态大模型系列，具备 100万~200万超大上下文窗口，擅长跨视频、音频、文档与长文本的联合推理。',
  moonshotai: '月之暗面 (Moonshot AI) 是国内长文本大模型开创者，Kimi 系列支持超长上下文与深度思考推理能力，赋能高难度专业工作流。',
  zhipuai: '智谱 AI (Zhipu AI) 源自清华团队，致力于打造 GLM 大模型基座，涵盖对话、代码、多模态及智能体工具调用体系。',
  meta: 'Meta AI 领导全球顶级开源大模型生态，Llama 系列为全行业开发者提供极高自由度与强大的微调部署能力。',
  mistral: 'Mistral AI 是欧洲顶尖开源与商用大模型团队，在小参数极致效率、代码理解与多语言性能上极具优势。'
}

const getLabDescription = (labId: string) => {
  return labDescriptions[labId.toLowerCase()] || `${selectedLab.value?.displayName || labId} 致力于研发先进大语言模型与多模态技术，提供高可用 API 与开源权重。`
}

// 将模型严格规范化归属到正确的 Lab 厂商下 (解决 QWEN 误识别为厂商的问题)
const normalizeModelToLab = (m: ModelMetadata): string => {
  const mId = m.model_id.toLowerCase()
  const p = (m.provider || '').toLowerCase()

  if (mId.startsWith('qwen') || p === 'qwen' || p.includes('alibaba') || mId.includes('qwen')) {
    return 'alibaba'
  }
  if (mId.startsWith('deepseek') || p === 'deepseek') {
    return 'deepseek'
  }
  if (mId.startsWith('gpt') || mId.startsWith('o1') || mId.startsWith('o3') || mId.startsWith('whisper') || p === 'openai') {
    return 'openai'
  }
  if (mId.startsWith('claude') || p === 'anthropic') {
    return 'anthropic'
  }
  if (mId.startsWith('gemini') || mId.startsWith('gemma') || p === 'google') {
    return 'google'
  }
  if (mId.startsWith('llama') || p === 'meta') {
    return 'meta'
  }
  if (mId.startsWith('kimi') || mId.startsWith('moonshot') || p === 'moonshotai') {
    return 'moonshotai'
  }
  if (mId.startsWith('glm') || mId.startsWith('chatglm') || p === 'zhipuai') {
    return 'zhipuai'
  }
  if (mId.startsWith('doubao') || mId.startsWith('seed') || p === 'bytedance' || p === 'bytedance-seed') {
    return 'bytedance'
  }
  if (mId.startsWith('hunyuan') || mId.startsWith('hy') || p === 'tencent') {
    return 'tencent'
  }
  if (mId.startsWith('mistral') || mId.startsWith('codestral') || mId.startsWith('pixtral') || p === 'mistral') {
    return 'mistral'
  }
  if (mId.startsWith('nemotron') || p === 'nvidia') {
    return 'nvidia'
  }
  if (mId.startsWith('command') || p === 'cohere') {
    return 'cohere'
  }
  if (mId.startsWith('grok') || p === 'xai') {
    return 'xai'
  }
  if (mId.startsWith('minimax') || p === 'minimax') {
    return 'minimax'
  }
  if (mId.startsWith('step') || p === 'stepfun') {
    return 'stepfun'
  }
  if (mId.startsWith('sonar') || p === 'perplexity') {
    return 'perplexity'
  }
  if (mId.startsWith('mimo') || mId.startsWith('milm') || p === 'xiaomi') {
    return 'xiaomi'
  }
  if (mId.includes('/')) {
    const pre = mId.split('/')[0]
    if (labDisplayNameMap[pre]) return pre
  }

  return p && p !== 'other' ? p : 'other'
}

const labsList = computed<LabItem[]>(() => {
  const map: Record<string, ModelMetadata[]> = {}

  store.modelsCatalog.forEach((m) => {
    const labId = normalizeModelToLab(m)
    if (labId === 'other') return // 过滤杂质

    if (!map[labId]) {
      map[labId] = []
    }
    map[labId].push(m)
  })

  return Object.keys(map).map((labId) => {
    const models = map[labId]
    const familiesSet = new Set<string>()
    models.forEach((m) => {
      if (m.series) familiesSet.add(m.series)
      else if (m.family) familiesSet.add(m.family.replace(/-/g, ' ').toUpperCase())
      else familiesSet.add('通用系列')
    })

    return {
      id: labId,
      displayName: labDisplayNameMap[labId] || labId.toUpperCase(),
      models,
      families: Array.from(familiesSet)
    }
  }).sort((a, b) => b.models.length - a.models.length)
})

const filteredLabs = computed(() => {
  if (!labSearchQuery.value.trim()) return labsList.value
  const q = labSearchQuery.value.toLowerCase().trim()
  return labsList.value.filter(
    (lab) => lab.displayName.toLowerCase().includes(q) || lab.id.toLowerCase().includes(q)
  )
})

const selectLab = (lab: LabItem) => {
  selectedLab.value = lab
  modelSearchQuery.value = ''
  sortField.value = 'context_window'
  sortOrder.value = 'desc'
}

const getLabTotalProvidersCount = () => {
  return store.relaySites.length || 72
}

const copyText = (txt: string) => {
  navigator.clipboard.writeText(txt)
  isCopied.value = true
  setTimeout(() => (isCopied.value = false), 2000)
}

const formatContextWindow = (ctx: number) => {
  if (!ctx) return '128,000'
  return Number(ctx).toLocaleString()
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

const goToMatrix = (modelId: string) => {
  store.selectedModelId = modelId
  store.activeTab = 'price-matrix'
}

const goToSpeedTest = (modelId: string) => {
  store.activeTab = 'speed-tester'
  const siteIds = store.activeSites.slice(0, 3).map((s) => s.id)
  store.runSpeedTest(siteIds, modelId)
}
</script>

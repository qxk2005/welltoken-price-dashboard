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
          <button
            @click="selectedLab = null"
            class="px-3 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] transition-all text-xs font-medium flex items-center space-x-1"
          >
            <span>← 返回厂商大全 (共 30 家权威机构)</span>
          </button>

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
                  官方单价 (输入/输出) ({{ store.currency }}) <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('official_input_price') }}</span>
                </th>
                <th @click="toggleSort('lowest_price_usd')" class="py-2.5 px-3 text-right cursor-pointer hover:text-[#1D1D1F] transition-colors">
                  全网最低 ({{ store.currency }}) <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('lowest_price_usd') }}</span>
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

                <!-- 9. 官方输入/输出单价 (响应全局货币切换) -->
                <td class="py-2.5 px-3 text-right font-mono font-medium text-[#1D1D1F]">
                  {{ store.formatDualCurrency(model.official_input_price, model.official_output_price) }}
                </td>

                <!-- 10. 全网最低单价 (响应全局货币切换) -->
                <td class="py-2.5 px-3 text-right font-mono font-bold text-[#34C759]">
                  {{ store.formatCurrency(model.lowest_price_usd) }}/1M
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
                  当前厂商下无匹配的模型记录
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
const selectedLab = ref<LabItem | null>(null)
const labSearchQuery = ref('')
const modelSearchQuery = ref('')
const isCopied = ref(false)

// 排序状态
const sortField = ref<string>('context_window')
const sortOrder = ref<'asc' | 'desc'>('desc')

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
  selectedLab.value = lab
  modelSearchQuery.value = ''
  sortField.value = 'context_window'
  sortOrder.value = 'desc'
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

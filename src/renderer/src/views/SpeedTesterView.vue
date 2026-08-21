<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none font-sans">
    <!-- 主体左右分栏布局 (左侧：控制面板；右侧：实时看板与逐次明细) -->
    <div class="flex-1 grid grid-cols-12 gap-3 overflow-hidden min-h-0">
      
      <!-- ==================== 左侧：渠道测速与连通性检测 控制面板 (4 列) ==================== -->
      <div class="col-span-4 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-4 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3.5 overflow-y-auto">
        <!-- 标题区 -->
        <div>
          <div class="flex items-center justify-between">
            <h2 class="font-bold text-sm text-[#1D1D1F] flex items-center space-x-1.5">
              <span>⚡</span>
              <span>渠道测速与连通性检测</span>
            </h2>
            <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]">
              DIAGNOSTIC
            </span>
          </div>
          <p class="text-[11px] text-[#86868B] mt-1 leading-relaxed">
            使用您临时填写的 API Key 进行现场请求检测，评估真实 TTFT 首字延迟、TTFB、总耗时与吞吐量稳定性。
          </p>
        </div>

        <!-- 表单区 -->
        <div class="space-y-3 text-xs">
          <!-- 1. 目标渠道与 API Base (下拉选择) -->
          <div class="space-y-1">
            <label class="font-medium text-[#1D1D1F] flex items-center justify-between">
              <span>目标渠道与 API Base</span>
              <span v-if="isLoadingModels" class="text-[10px] text-[#0071E3] animate-pulse">正在加载渠道模型...</span>
            </label>
            <select
              v-model="selectedSiteId"
              @change="handleSiteChange"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-xs text-[#1D1D1F] focus:outline-none transition-all cursor-pointer font-sans"
            >
              <option :value="null" disabled>请选择待测渠道...</option>
              <option v-for="site in store.activeSites" :key="site.id" :value="site.id">
                {{ site.name }} ({{ site.base_url }})
              </option>
            </select>
          </div>

          <!-- 2. API Base 端点 URL -->
          <div class="space-y-1">
            <label class="font-medium text-[#6E6E73] text-[11px]">API Base 端点 URL</label>
            <input
              v-model="form.baseUrl"
              type="text"
              placeholder="https://api.openai.com/v1"
              class="w-full bg-[#F9F9FB] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-1.5 text-xs text-[#1D1D1F] font-mono focus:outline-none transition-all"
            />
          </div>

          <!-- 3. 临时 API Key (本地内存检测，绝不上报持久化) -->
          <div class="space-y-1">
            <label class="font-medium text-[#6E6E73] text-[11px] flex items-center justify-between">
              <span>临时 API Key (本地内存检测，绝不上传)</span>
              <span v-if="form.apiKey" class="text-[10px] text-[#34C759] font-mono">● 已填入</span>
            </label>
            <div class="relative">
              <input
                v-model="form.apiKey"
                :type="showApiKey ? 'text' : 'password'"
                placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
                class="w-full bg-[#F9F9FB] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-1.5 pr-8 text-xs text-[#1D1D1F] font-mono focus:outline-none transition-all"
              />
              <button
                @click="showApiKey = !showApiKey"
                type="button"
                class="absolute right-2.5 top-2 text-xs text-[#86868B] hover:text-[#1D1D1F]"
              >
                {{ showApiKey ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <!-- 4. 测试模型 ID (下拉列表选择) -->
          <div class="space-y-1">
            <label class="font-medium text-[#1D1D1F] flex items-center justify-between">
              <span>测试模型 ID (Model ID)</span>
              <span class="text-[10px] text-[#86868B]">共 {{ currentSiteModels.length }} 款可用</span>
            </label>
            <div v-if="currentSiteModels.length > 0">
              <select
                v-model="form.modelId"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-xs text-[#1D1D1F] font-mono focus:outline-none transition-all cursor-pointer"
              >
                <option v-for="m in currentSiteModels" :key="m.model_id" :value="m.model_id">
                  {{ m.model_name || m.model_id }} ({{ m.model_id }})
                </option>
              </select>
            </div>
            <div v-else>
              <input
                v-model="form.modelId"
                type="text"
                placeholder="如 deepseek-v3, gpt-4o, glm-5.2..."
                class="w-full bg-[#F9F9FB] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-1.5 text-xs text-[#1D1D1F] font-mono focus:outline-none transition-all"
              />
            </div>
          </div>

          <!-- 5. 重复检测次数 & 并发度 (双列) -->
          <div class="grid grid-cols-2 gap-2.5">
            <div class="space-y-1">
              <label class="font-medium text-[#6E6E73] text-[11px]">重复检测次数</label>
              <select
                v-model="form.rounds"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] rounded-xl px-2.5 py-1.5 text-xs text-[#1D1D1F] focus:outline-none cursor-pointer"
              >
                <option :value="1">单次探测 (1 次)</option>
                <option :value="3">标准压测 (3 次)</option>
                <option :value="5">深度压测 (5 次)</option>
                <option :value="10">极限压测 (10 次)</option>
              </select>
            </div>

            <div class="space-y-1">
              <label class="font-medium text-[#6E6E73] text-[11px]">并发检测并发度</label>
              <select
                v-model="form.concurrency"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] rounded-xl px-2.5 py-1.5 text-xs text-[#1D1D1F] focus:outline-none cursor-pointer"
              >
                <option :value="1">串行 (1 并发)</option>
                <option :value="2">双线程 (2 并发)</option>
                <option :value="5">多并发 (5 并发)</option>
                <option :value="10">高并发 (10 并发)</option>
              </select>
            </div>
          </div>

          <!-- 6. Prompt 模板模式 -->
          <div class="space-y-1">
            <label class="font-medium text-[#6E6E73] text-[11px]">Prompt 探针模板</label>
            <select
              v-model="form.promptType"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] rounded-xl px-2.5 py-1.5 text-xs text-[#1D1D1F] focus:outline-none cursor-pointer"
            >
              <option value="standard">标准 100 字文本 + VERIFIED 真实性防作弊探针</option>
              <option value="reasoning">复杂逻辑数理推导 (测试 Think 思考耗时)</option>
              <option value="code">Python 算法代码生成 (高密度吐字测试)</option>
            </select>
          </div>
        </div>

        <!-- 开始测试按钮 -->
        <div class="pt-2">
          <button
            :disabled="isTesting || !selectedSiteId || !form.modelId"
            @click="startBenchmark"
            class="w-full py-2.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-40 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center space-x-2"
          >
            <span v-if="isTesting" class="animate-spin text-sm">🌀</span>
            <span v-else>⚡</span>
            <span>{{ isTesting ? `正在并发压测中 (${form.rounds}轮)...` : '开始渠道性能检测' }}</span>
          </button>
        </div>
      </div>

      <!-- ==================== 右侧：实时检测指标看板 + 逐次明细列表 (8 列) ==================== -->
      <div class="col-span-8 flex flex-col space-y-3 overflow-hidden min-h-0">
        
        <!-- 1. 实时检测指标看板 (4 块 Apple 质感大字看板) -->
        <div class="bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-4 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-xs text-[#1D1D1F]">实时检测指标看板</span>
              <span v-if="benchmarkResult" class="text-[10px] text-[#86868B] font-mono">
                渠道: {{ benchmarkResult.site_name }} • 模型: {{ benchmarkResult.model_id }}
              </span>
            </div>
            <div class="flex items-center space-x-2 text-[11px]">
              <span v-if="isTesting" class="text-[#0071E3] font-bold animate-pulse flex items-center space-x-1">
                <span class="w-2 h-2 rounded-full bg-[#0071E3] animate-ping"></span>
                <span>正在执行流式检测...</span>
              </span>
              <span v-else-if="benchmarkResult" class="text-[#34C759] font-bold flex items-center space-x-1">
                <span>✓ 压测完成</span>
                <span class="text-[10px] bg-[#E6F4EA] text-[#34C759] border border-[#CEEAD6] px-1.5 py-0.2 rounded font-mono">
                  评级 {{ benchmarkResult.grade }} ({{ benchmarkResult.score }}分)
                </span>
              </span>
              <span v-else class="text-[#86868B]">就绪状态 • 等待测试</span>
            </div>
          </div>

          <!-- 指标卡片网格 -->
          <div class="grid grid-cols-4 gap-3">
            <!-- 指标 1：TTFT -->
            <div class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
              <div class="text-[10.5px] text-[#6E6E73] font-medium">TTFT (首 Token 耗时)</div>
              <div class="text-xl font-bold font-mono text-[#1D1D1F] tracking-tight">
                {{ benchmarkResult ? benchmarkResult.avg_ttft_ms : '-' }}
                <span class="text-xs font-normal text-[#86868B]">ms</span>
              </div>
              <div class="text-[10px] text-[#86868B] flex items-center justify-between">
                <span>最高: {{ benchmarkResult ? benchmarkResult.max_ttft_ms : '-' }}</span>
                <span>最低: {{ benchmarkResult ? benchmarkResult.min_ttft_ms : '-' }}</span>
              </div>
            </div>

            <!-- 指标 2：TTFB -->
            <div class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
              <div class="text-[10.5px] text-[#6E6E73] font-medium">TTFB (首字节耗时)</div>
              <div class="text-xl font-bold font-mono text-[#1D1D1F] tracking-tight">
                {{ benchmarkResult ? benchmarkResult.avg_ttfb_ms : '-' }}
                <span class="text-xs font-normal text-[#86868B]">ms</span>
              </div>
              <div class="text-[10px] text-[#86868B] truncate">
                TCP+TLS 握手及建连
              </div>
            </div>

            <!-- 指标 3：吞吐量 TPS -->
            <div class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
              <div class="text-[10.5px] text-[#6E6E73] font-medium">吞吐量 (Generation Speed)</div>
              <div class="text-xl font-bold font-mono text-[#34C759] tracking-tight">
                {{ benchmarkResult ? benchmarkResult.avg_tps : '-' }}
                <span class="text-xs font-normal text-[#86868B]">tok/s</span>
              </div>
              <div class="text-[10px] text-[#86868B] flex items-center justify-between">
                <span>最高: {{ benchmarkResult ? benchmarkResult.max_tps : '-' }}</span>
                <span>最低: {{ benchmarkResult ? benchmarkResult.min_tps : '-' }}</span>
              </div>
            </div>

            <!-- 指标 4：首 Token 稳定性 (Jitter / ITL) -->
            <div class="p-3 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
              <div class="text-[10.5px] text-[#6E6E73] font-medium">首 Token 稳定性 (Jitter)</div>
              <div class="text-xl font-bold font-mono text-[#0071E3] tracking-tight">
                {{ benchmarkResult ? `±${benchmarkResult.jitter_ms}` : '-' }}
                <span class="text-xs font-normal text-[#86868B]">ms</span>
              </div>
              <div class="text-[10px] text-[#86868B] flex items-center justify-between">
                <span>ITL: {{ benchmarkResult ? `${benchmarkResult.avg_itl_ms}ms` : '-' }}</span>
                <span>总耗时: {{ benchmarkResult ? `${benchmarkResult.avg_duration_s}s` : '-' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. 逐次检测明细与耗时列表 (Detailed Execution Table) -->
        <div class="flex-1 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden min-h-0">
          <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-2 mb-1">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-xs text-[#1D1D1F]">逐次检测明细与耗时曲线</span>
              <span v-if="benchmarkResult" class="text-[10px] text-[#86868B] font-mono">
                (已完成 {{ benchmarkResult.details.length }} 轮压测)
              </span>
            </div>
            <div v-if="benchmarkResult" class="text-[10px] text-[#6E6E73] font-mono">
              总 Token: {{ benchmarkResult.total_prompt_tokens }} in / {{ benchmarkResult.total_completion_tokens }} out
            </div>
          </div>

          <!-- 表格滚动区 -->
          <div class="flex-1 overflow-x-auto overflow-y-auto pr-1">
            <table class="w-full text-left text-xs border-collapse min-w-[700px]">
              <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans select-none">
                <tr>
                  <th class="py-2.5 px-3 text-center w-14">轮次</th>
                  <th class="py-2.5 px-3 text-center w-24">并发 ID</th>
                  <th class="py-2.5 px-3 text-center w-20">状态码</th>
                  <th class="py-2.5 px-3 text-right w-20">TTFB</th>
                  <th class="py-2.5 px-3 text-right w-24">TTFT (首字)</th>
                  <th class="py-2.5 px-3 text-right w-20">ITL</th>
                  <th class="py-2.5 px-3 text-right w-20">总耗时</th>
                  <th class="py-2.5 px-3 text-right w-24">吞吐速率</th>
                  <th class="py-2.5 px-3 text-center w-28">Token 消耗</th>
                  <th class="py-2.5 px-3 text-center w-24">返回内容</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#E5E5EA]/70 font-mono text-[11px]">
                <tr
                  v-for="item in (benchmarkResult?.details || [])"
                  :key="item.round_index"
                  class="hover:bg-[#F5F5F7] transition-colors"
                >
                  <td class="py-2 px-3 text-center font-bold text-[#1D1D1F]">
                    #{{ item.round_index }}
                  </td>
                  <td class="py-2 px-3 text-center text-[#86868B]">
                    {{ item.thread_id }}
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span
                      v-if="item.is_success"
                      class="px-1.5 py-0.2 rounded bg-[#E6F4EA] text-[#34C759] border border-[#CEEAD6] text-[10px] font-bold font-sans"
                    >
                      200 OK
                    </span>
                    <span
                      v-else
                      class="px-1.5 py-0.2 rounded bg-[#FDE8E8] text-[#FF3B30] border border-[#FCD2D2] text-[10px] font-bold font-sans"
                      :title="item.error_msg"
                    >
                      {{ item.status_code || 'Error' }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-right text-[#6E6E73]">
                    {{ item.ttfb_ms }} ms
                  </td>
                  <td class="py-2 px-3 text-right text-[#0071E3] font-bold">
                    {{ item.ttft_ms }} ms
                  </td>
                  <td class="py-2 px-3 text-right text-[#86868B]">
                    {{ item.itl_ms }} ms
                  </td>
                  <td class="py-2 px-3 text-right text-[#1D1D1F]">
                    {{ item.total_duration_s }} s
                  </td>
                  <td class="py-2 px-3 text-right text-[#34C759] font-bold">
                    {{ item.tps }} tok/s
                  </td>
                  <td class="py-2 px-3 text-center text-[#86868B]">
                    {{ item.prompt_tokens }} in / {{ item.completion_tokens }} out
                  </td>
                  <td class="py-2 px-3 text-center">
                    <button
                      @click="openResponseModal(item)"
                      class="px-2 py-0.5 rounded-md bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] text-[10px] font-sans font-medium transition-all"
                    >
                      💬 查看输出
                    </button>
                  </td>
                </tr>

                <tr v-if="!benchmarkResult || benchmarkResult.details.length === 0">
                  <td colspan="10" class="py-12 text-center text-xs text-[#86868B] font-sans">
                    {{ isTesting ? '正在并发压测并采集每轮明细...' : '请在左侧选择渠道与模型，点击「开始渠道性能检测」' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 弹窗：模型返回内容实时检视 Modal ==================== -->
    <div
      v-if="selectedDetailForPreview"
      class="fixed inset-0 bg-black/35 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in"
    >
      <div class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl w-[640px] max-h-[80vh] flex flex-col shadow-[0_20px_50px_rgba(0,0,0,0.18)] overflow-hidden font-sans text-xs">
        <div class="px-5 py-3.5 border-b border-[#E5E5EA] flex items-center justify-between bg-[#F9F9FB]">
          <div class="flex items-center space-x-2">
            <span class="text-base">💬</span>
            <h3 class="font-bold text-sm text-[#1D1D1F]">
              第 #{{ selectedDetailForPreview.round_index }} 轮测试模型流式返回输出
            </h3>
            <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#E8F2FD] text-[#0071E3]">
              {{ selectedDetailForPreview.tps }} tok/s • {{ selectedDetailForPreview.completion_tokens }} tokens
            </span>
          </div>
          <button
            @click="selectedDetailForPreview = null"
            class="text-[#86868B] hover:text-[#1D1D1F] text-xs font-bold"
          >
            ✕
          </button>
        </div>

        <div class="p-5 overflow-y-auto space-y-3 font-mono leading-relaxed text-[#1D1D1F]">
          <div class="p-3 bg-[#F2F2F7] rounded-xl text-[11px] text-[#6E6E73] border border-[#E5E5EA]">
            <strong>Prompt 探针:</strong> 请在回答的第一行严格只输出单词【VERIFIED】，随后用大约100字简要介绍区块链与大模型结合的潜力。
          </div>
          <div class="p-3.5 bg-[#F9F9FB] rounded-xl text-xs border border-[#E5E5EA] whitespace-pre-wrap">
            {{ selectedDetailForPreview.response_content || '（该轮请求未返回有效内容）' }}
          </div>
        </div>

        <div class="px-5 py-3 border-t border-[#E5E5EA] flex items-center justify-between bg-[#F9F9FB]">
          <span class="text-[11px] text-[#86868B] font-mono">
            TTFT: {{ selectedDetailForPreview.ttft_ms }}ms • ITL: {{ selectedDetailForPreview.itl_ms }}ms • 总耗时: {{ selectedDetailForPreview.total_duration_s }}s
          </span>
          <button
            @click="copyContent(selectedDetailForPreview.response_content)"
            class="px-3 py-1 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] text-white font-medium transition-all"
          >
            复制回答内容
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import type { RelaySite } from '../types'

const store = useDashboardStore()

const selectedSiteId = ref<number | null>(null)
const isLoadingModels = ref(false)
const isTesting = ref(false)
const showApiKey = ref(false)
const currentSiteModels = ref<any[]>([])
const benchmarkResult = ref<any>(null)
const selectedDetailForPreview = ref<any>(null)

const form = reactive({
  baseUrl: '',
  apiKey: '',
  modelId: 'deepseek-v3',
  rounds: 3,
  concurrency: 1,
  promptType: 'standard'
})

onMounted(async () => {
  if (store.activeSites.length === 0) {
    await store.fetchRelaySites()
  }

  // 默认选中第一个渠道或之前选中的渠道
  if (store.selectedSiteId && store.activeSites.some((s) => s.id === store.selectedSiteId)) {
    selectedSiteId.value = store.selectedSiteId
  } else if (store.activeSites.length > 0) {
    selectedSiteId.value = store.activeSites[0].id
  }

  if (selectedSiteId.value) {
    handleSiteChange()
  }
})

// 切换渠道时自动填充配置并拉取模型列表
const handleSiteChange = async () => {
  if (!selectedSiteId.value) return
  const site = store.activeSites.find((s) => s.id === selectedSiteId.value)
  if (!site) return

  form.baseUrl = site.base_url || ''
  form.apiKey = site.api_key || ''

  // 联动拉取该渠道收录的所有模型
  isLoadingModels.value = true
  try {
    const res = await axios.get(`${store.apiUrl}/api/v1/channels/${site.id}/models`)
    currentSiteModels.value = res.data || []
    if (currentSiteModels.value.length > 0) {
      // 优先保留之前的模型选择，否则选第一个
      const exist = currentSiteModels.value.find((m) => m.model_id === form.modelId)
      if (!exist) {
        form.modelId = currentSiteModels.value[0].model_id
      }
    } else {
      form.modelId = 'deepseek-v3'
    }
  } catch (e) {
    console.error('Fetch channel models failed:', e)
    currentSiteModels.value = []
  } finally {
    isLoadingModels.value = false
  }
}

// 启动压测
const startBenchmark = async () => {
  if (!selectedSiteId.value || !form.modelId) return
  isTesting.value = true
  benchmarkResult.value = null

  try {
    const payload = {
      site_id: selectedSiteId.value,
      model_id: form.modelId,
      custom_api_key: form.apiKey,
      custom_base_url: form.baseUrl,
      rounds: form.rounds,
      concurrency: form.concurrency,
      prompt_type: form.promptType
    }

    const res = await axios.post(`${store.apiUrl}/api/v1/speed-test/benchmark`, payload)
    benchmarkResult.value = res.data

    // 自动刷新大盘比价与渠道列表，让最新 TPS 与延迟立刻呈现在矩阵中
    await store.fetchRelaySites()
    await store.fetchComparisonMatrix()
  } catch (e: any) {
    alert(`性能压测失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isTesting.value = false
  }
}

const openResponseModal = (item: any) => {
  selectedDetailForPreview.value = item
}

const copyContent = (text: string) => {
  if (!text) return
  navigator.clipboard.writeText(text)
  alert('✓ 回答内容已成功复制到剪贴板！')
}
</script>

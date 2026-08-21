<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none font-sans">
    <!-- 主体左右分栏布局 (左侧：控制面板；右侧：实时看板 + 逐次明细 + 执行过程日志) -->
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

      <!-- ==================== 右侧：实时指标看板 + 逐次明细 + 过程日志 (8 列) ==================== -->
      <div class="col-span-8 flex flex-col space-y-2.5 overflow-hidden min-h-0">
        
        <!-- 1. 实时检测指标看板 (4 块 Apple 质感大字看板) -->
        <div class="bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3.5 shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-2.5">
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
          <div class="grid grid-cols-4 gap-2.5">
            <!-- 指标 1：TTFT -->
            <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
              <div class="text-[10.5px] text-[#6E6E73] font-medium">TTFT (首 Token 耗时)</div>
              <div class="text-lg font-bold font-mono text-[#1D1D1F] tracking-tight">
                {{ benchmarkResult ? benchmarkResult.avg_ttft_ms : '-' }}
                <span class="text-xs font-normal text-[#86868B]">ms</span>
              </div>
              <div class="text-[9.5px] text-[#86868B] flex items-center justify-between">
                <span>最高: {{ benchmarkResult ? benchmarkResult.max_ttft_ms : '-' }}</span>
                <span>最低: {{ benchmarkResult ? benchmarkResult.min_ttft_ms : '-' }}</span>
              </div>
            </div>

            <!-- 指标 2：TTFB -->
            <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
              <div class="text-[10.5px] text-[#6E6E73] font-medium">TTFB (首字节耗时)</div>
              <div class="text-lg font-bold font-mono text-[#1D1D1F] tracking-tight">
                {{ benchmarkResult ? benchmarkResult.avg_ttfb_ms : '-' }}
                <span class="text-xs font-normal text-[#86868B]">ms</span>
              </div>
              <div class="text-[9.5px] text-[#86868B] truncate">
                TCP+TLS 握手及建连
              </div>
            </div>

            <!-- 指标 3：吞吐量 TPS -->
            <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
              <div class="text-[10.5px] text-[#6E6E73] font-medium">吞吐量 (Generation Speed)</div>
              <div class="text-lg font-bold font-mono text-[#34C759] tracking-tight">
                {{ benchmarkResult ? benchmarkResult.avg_tps : '-' }}
                <span class="text-xs font-normal text-[#86868B]">tok/s</span>
              </div>
              <div class="text-[9.5px] text-[#86868B] flex items-center justify-between">
                <span>最高: {{ benchmarkResult ? benchmarkResult.max_tps : '-' }}</span>
                <span>最低: {{ benchmarkResult ? benchmarkResult.min_tps : '-' }}</span>
              </div>
            </div>

            <!-- 指标 4：首 Token 稳定性 (Jitter / ITL) -->
            <div class="p-2.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1">
              <div class="text-[10.5px] text-[#6E6E73] font-medium">首 Token 稳定性 (Jitter)</div>
              <div class="text-lg font-bold font-mono text-[#0071E3] tracking-tight">
                {{ benchmarkResult ? `±${benchmarkResult.jitter_ms}` : '-' }}
                <span class="text-xs font-normal text-[#86868B]">ms</span>
              </div>
              <div class="text-[9.5px] text-[#86868B] flex items-center justify-between">
                <span>ITL: {{ benchmarkResult ? `${benchmarkResult.avg_itl_ms}ms` : '-' }}</span>
                <span>总耗时: {{ benchmarkResult ? `${benchmarkResult.avg_duration_s}s` : '-' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. 逐次检测明细与耗时列表 (Detailed Execution Table) -->
        <div class="flex-1 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden min-h-[140px] max-h-[220px]">
          <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-1.5 mb-1">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-xs text-[#1D1D1F]">逐次检测明细与耗时列表</span>
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
            <table class="w-full text-left text-xs border-collapse min-w-[650px]">
              <thead class="text-[10.5px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans select-none">
                <tr>
                  <th class="py-2 px-2 text-center w-12">轮次</th>
                  <th class="py-2 px-2 text-center w-20">并发 ID</th>
                  <th class="py-2 px-2 text-center w-18">状态码</th>
                  <th class="py-2 px-2 text-right w-18">TTFB</th>
                  <th class="py-2 px-2 text-right w-20">TTFT(首字)</th>
                  <th class="py-2 px-2 text-right w-16">ITL</th>
                  <th class="py-2 px-2 text-right w-18">总耗时</th>
                  <th class="py-2 px-2 text-right w-20">吞吐速率</th>
                  <th class="py-2 px-2 text-center w-24">Token 消耗</th>
                  <th class="py-2 px-2 text-center w-20">返回内容</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#E5E5EA]/70 font-mono text-[10.5px]">
                <tr
                  v-for="item in (benchmarkResult?.details || [])"
                  :key="item.round_index"
                  class="hover:bg-[#F5F5F7] transition-colors"
                >
                  <td class="py-1.5 px-2 text-center font-bold text-[#1D1D1F]">
                    #{{ item.round_index }}
                  </td>
                  <td class="py-1.5 px-2 text-center text-[#86868B]">
                    {{ item.thread_id }}
                  </td>
                  <td class="py-1.5 px-2 text-center">
                    <span
                      v-if="item.is_success"
                      class="px-1.5 py-0.2 rounded bg-[#E6F4EA] text-[#34C759] border border-[#CEEAD6] text-[9.5px] font-bold font-sans"
                    >
                      200 OK
                    </span>
                    <span
                      v-else
                      class="px-1.5 py-0.2 rounded bg-[#FDE8E8] text-[#FF3B30] border border-[#FCD2D2] text-[9.5px] font-bold font-sans"
                      :title="item.error_msg"
                    >
                      {{ item.status_code || 'Error' }}
                    </span>
                  </td>
                  <td class="py-1.5 px-2 text-right text-[#6E6E73]">
                    {{ item.ttfb_ms }} ms
                  </td>
                  <td class="py-1.5 px-2 text-right text-[#0071E3] font-bold">
                    {{ item.ttft_ms }} ms
                  </td>
                  <td class="py-1.5 px-2 text-right text-[#86868B]">
                    {{ item.itl_ms }} ms
                  </td>
                  <td class="py-1.5 px-2 text-right text-[#1D1D1F]">
                    {{ item.total_duration_s }} s
                  </td>
                  <td class="py-1.5 px-2 text-right text-[#34C759] font-bold">
                    {{ item.tps }} tok/s
                  </td>
                  <td class="py-1.5 px-2 text-center text-[#86868B]">
                    {{ item.prompt_tokens }} in / {{ item.completion_tokens }} out
                  </td>
                  <td class="py-1.5 px-2 text-center">
                    <button
                      @click="openResponseModal(item)"
                      class="px-1.5 py-0.2 rounded bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] text-[10px] font-sans font-medium transition-all"
                    >
                      💬 查看输出
                    </button>
                  </td>
                </tr>

                <tr v-if="!benchmarkResult || benchmarkResult.details.length === 0">
                  <td colspan="10" class="py-8 text-center text-xs text-[#86868B] font-sans">
                    {{ isTesting ? '正在并发压测并采集每轮明细...' : '请在左侧选择渠道与模型，点击「开始渠道性能检测」' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 3. 右下方：实时测试日志与执行过程控制台 (Live Process Logs) -->
        <div class="h-44 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden">
          <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-1.5 mb-1.5">
            <div class="flex items-center space-x-2">
              <span class="w-2 h-2 rounded-full" :class="isTesting ? 'bg-[#34C759] animate-pulse' : 'bg-[#AEAEB2]'"></span>
              <span class="font-bold text-xs text-[#1D1D1F]">压测执行过程与诊断日志流水 (Live Process Logs)</span>
              <span class="text-[10px] text-[#86868B] font-mono">({{ executionLogs.length }} 条记录)</span>
            </div>
            <div class="flex items-center space-x-2">
              <button
                @click="executionLogs = []"
                class="text-[10.5px] text-[#86868B] hover:text-[#0071E3] transition-colors"
              >
                清空日志
              </button>
            </div>
          </div>

          <!-- 日志滚动窗口 -->
          <div
            ref="logContainerRef"
            class="flex-1 bg-[#F9F9FB] border border-[#E5E5EA] rounded-xl p-2.5 overflow-y-auto font-mono text-[10.5px] space-y-1 select-text"
          >
            <div
              v-for="(log, idx) in executionLogs"
              :key="idx"
              class="leading-relaxed flex items-start space-x-1.5"
              :class="getLogClass(log.type)"
            >
              <span class="text-[#86868B] flex-shrink-0 text-[9.5px]">[{{ log.time }}]</span>
              <span class="flex-shrink-0">{{ log.icon }}</span>
              <span class="break-all">{{ log.message }}</span>
            </div>
            <div v-if="executionLogs.length === 0" class="text-[#86868B] py-6 text-center text-xs font-sans">
              暂无压测日志流水，请在左侧点击「开始渠道性能检测」
            </div>
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import type { RelaySite } from '../types'

interface ExecutionLog {
  time: string
  icon: string
  type: 'info' | 'success' | 'warn' | 'error' | 'process'
  message: string
}

const store = useDashboardStore()

const selectedSiteId = ref<number | null>(null)
const isLoadingModels = ref(false)
const isTesting = ref(false)
const showApiKey = ref(false)
const currentSiteModels = ref<any[]>([])
const benchmarkResult = ref<any>(null)
const selectedDetailForPreview = ref<any>(null)
const executionLogs = ref<ExecutionLog[]>([])
const logContainerRef = ref<HTMLElement | null>(null)

const form = reactive({
  baseUrl: '',
  apiKey: '',
  modelId: 'deepseek-v3',
  rounds: 3,
  concurrency: 1,
  promptType: 'standard'
})

const appendLog = (type: 'info' | 'success' | 'warn' | 'error' | 'process', icon: string, message: string) => {
  const now = new Date()
  const timeStr = now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0')
  executionLogs.value.push({ time: timeStr, icon, type, message })
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
    }
  })
}

const getLogClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'text-[#137333]'
    case 'error':
      return 'text-[#D93025] font-bold'
    case 'warn':
      return 'text-[#E37400]'
    case 'process':
      return 'text-[#1A73E8]'
    default:
      return 'text-[#3C4043]'
  }
}

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

  appendLog('info', '🎯', `已选定渠道:【${site.name}】(Base URL: ${form.baseUrl})`)

  // 联动拉取该渠道收录的所有模型
  isLoadingModels.value = true
  try {
    const res = await axios.get(`${store.apiUrl}/api/v1/channels/${site.id}/models`)
    currentSiteModels.value = res.data || []
    if (currentSiteModels.value.length > 0) {
      const exist = currentSiteModels.value.find((m) => m.model_id === form.modelId)
      if (!exist) {
        form.modelId = currentSiteModels.value[0].model_id
      }
      appendLog('info', '📦', `成功加载该渠道旗下的 ${currentSiteModels.value.length} 款可用模型`)
    } else {
      form.modelId = 'deepseek-v3'
      appendLog('warn', '⚠️', `该渠道暂未在库中录入特定模型，已使用默认模型 deepseek-v3`)
    }
  } catch (e: any) {
    console.error('Fetch channel models failed:', e)
    currentSiteModels.value = []
    appendLog('error', '❌', `拉取渠道模型列表失败: ${e.message}`)
  } finally {
    isLoadingModels.value = false
  }
}

// 启动压测
const startBenchmark = async () => {
  if (!selectedSiteId.value || !form.modelId) return
  const site = store.activeSites.find((s) => s.id === selectedSiteId.value)
  const siteName = site ? site.name : `Site-${selectedSiteId.value}`

  isTesting.value = true
  benchmarkResult.value = null

  appendLog('info', '⚡', `启动性能压测: 目标渠道【${siteName}】(${form.baseUrl}), 模型【${form.modelId}】`)
  appendLog('process', '⚙️', `配置参数: 重复 ${form.rounds} 轮, 并发度 ${form.concurrency} 线程, 探针模式【${form.promptType}】`)
  appendLog('process', '🚀', `正在连接端点发起高精度并发流式压测...`)

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

    const res = await axios.post(`${store.apiUrl}/api/v1/speed-test/benchmark`, payload, {
      timeout: 60000 // 允许 60 秒宽裕超时
    })
    benchmarkResult.value = res.data

    appendLog('success', '✓', `压测执行完毕！收到全部 ${res.data.details.length} 轮测试详情:`)
    for (const d of res.data.details) {
      if (d.is_success) {
        appendLog('success', '●', `[${d.thread_id}] 状态: 200 OK | TTFB: ${d.ttfb_ms}ms | TTFT: ${d.ttft_ms}ms | ITL: ${d.itl_ms}ms | TPS: ${d.tps}tok/s | 生成: ${d.completion_tokens} tokens`)
      } else {
        appendLog('error', '❌', `[${d.thread_id}] 请求异常: ${d.error_msg || d.status_code}`)
      }
    }

    appendLog('info', '📊', `指标聚合汇总: 平均 TTFT ${res.data.avg_ttft_ms}ms, 平均 TPS ${res.data.avg_tps}tok/s, 稳定性 Jitter ±${res.data.jitter_ms}ms, 评级 ${res.data.grade} (${res.data.score}分)`)
    appendLog('info', '💾', `元数据已自动回写至数据库（渠道延迟、综合评分与分组模型实测 TPS）`)

    // 自动刷新大盘比价与渠道列表
    await store.fetchRelaySites()
    await store.fetchComparisonMatrix()
    appendLog('info', '🔄', `大盘比价矩阵与渠道列表已同步最新实测指标`)
  } catch (e: any) {
    const errMsg = e.response?.data?.detail || e.message
    appendLog('error', '❌', `性能压测遇到异常: ${errMsg}`)
    console.error('Benchmark failed:', e)
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

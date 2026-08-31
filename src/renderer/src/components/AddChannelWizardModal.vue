<template>
  <div class="fixed inset-0 bg-black/35 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in select-none">
    <div
      class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl flex flex-col shadow-[0_20px_60px_rgba(0,0,0,0.18)] overflow-hidden font-sans text-xs transition-all duration-300"
      :class="currentStep === 3 ? 'w-[1140px] max-w-[96vw] max-h-[90vh]' : 'w-[940px] max-w-[92vw] max-h-[88vh]'"
    >
      
      <!-- 1. 弹窗顶部：标题与关闭按钮 -->
      <div class="px-6 py-4 border-b border-[#E5E5EA] flex items-center justify-between bg-[#F9F9FB]">
        <div class="flex items-center space-x-2">
          <span class="text-base">{{ props.initialChannel ? '📡' : '🚀' }}</span>
          <h3 class="font-bold text-sm text-[#1D1D1F]">
            <span v-if="props.initialChannel">重新探测与同步模型 ({{ props.initialChannel.name }})</span>
            <span v-else>添加供应商与中转渠道向导 (Relay-Watch & Smart Mapping)</span>
          </h3>
        </div>
        <button
          @click="emit('close')"
          class="w-7 h-7 rounded-full bg-[#E5E5EA] hover:bg-[#D1D1D6] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center text-xs font-bold transition-all"
        >
          ✕
        </button>
      </div>

      <!-- 2. 步骤指示器 (Apple 精简胶囊进度条) -->
      <div class="px-6 py-3 bg-[#FFFFFF] border-b border-[#E5E5EA] flex items-center justify-between">
        <div
          v-for="(step, idx) in steps"
          :key="step.number"
          class="flex items-center space-x-2 cursor-default"
          :class="{
            'text-[#0071E3] font-bold': currentStep === step.number,
            'text-[#34C759] font-medium': currentStep > step.number,
            'text-[#86868B]': currentStep < step.number
          }"
        >
          <div
            class="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-mono transition-all"
            :class="
              currentStep === step.number
                ? 'bg-[#0071E3] text-white shadow-xs'
                : currentStep > step.number
                ? 'bg-[#E6F4EA] text-[#34C759] border border-[#CEEAD6]'
                : 'bg-[#F2F2F7] text-[#86868B] border border-[#E5E5EA]'
            "
          >
            <span v-if="currentStep > step.number">✓</span>
            <span v-else>{{ step.number }}</span>
          </div>
          <span class="text-xs">{{ step.title }}</span>
          <span v-if="idx < steps.length - 1" class="text-[#D1D1D6] ml-2">›</span>
        </div>
      </div>

      <!-- 3. 步骤主体内容区 -->
      <div class="p-6 flex-1 overflow-y-auto min-h-[360px] bg-[#FFFFFF]">
        
        <!-- ==================== Step 1: 基础配置 ==================== -->
        <div v-if="currentStep === 1" class="space-y-4 animate-fade-in">
          <!-- 快捷操作区：models.dev + 硅基流动 + 阿里百炼 三列并排 -->
          <div class="grid grid-cols-3 gap-3">
            <!-- 1. models.dev 一键导入 (蓝色系) -->
            <div class="p-3.5 bg-gradient-to-br from-[#F0F7FF] to-[#F5FAFF] rounded-2xl border border-[#CCE4FB] flex flex-col justify-between shadow-xs">
              <div class="space-y-1">
                <div class="flex items-center space-x-1.5">
                  <span class="text-base">⚡</span>
                  <span class="font-bold text-[#0071E3] text-xs truncate">models.dev 全网库</span>
                  <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#0071E3] text-white shrink-0">推荐</span>
                </div>
                <p class="text-[11px] text-[#6E6E73] leading-relaxed line-clamp-2">
                  一键获取 {{ store.syncStatus?.total_active_sites || store.relaySites.length || 193 }} 家供应商渠道。
                </p>
              </div>
              <button
                type="button"
                @click="handleOneClickSync"
                :disabled="isSyncingModelsDev"
                class="mt-2.5 w-full px-3 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-50 text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center space-x-1 cursor-pointer"
              >
                <span v-if="isSyncingModelsDev" class="animate-spin text-xs">⏳</span>
                <span v-else>🚀</span>
                <span class="truncate">{{ isSyncingModelsDev ? '同步中...' : '一键全量同步' }}</span>
              </button>
            </div>

            <!-- 2. 硅基流动 SiliconFlow 一键爬取 (紫色系) -->
            <div class="p-3.5 bg-gradient-to-br from-[#F3F0FF] to-[#F9F7FF] rounded-2xl border border-[#D8CCFF] flex flex-col justify-between shadow-xs">
              <div class="space-y-1">
                <div class="flex items-center space-x-1.5">
                  <span class="text-base">🔮</span>
                  <span class="font-bold text-[#6E29F6] text-xs truncate">硅基流动 SiliconFlow</span>
                  <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#6E29F6] text-white shrink-0">爬取</span>
                </div>
                <p class="text-[11px] text-[#6E6E73] leading-relaxed line-clamp-2">
                  自动爬取硅基流动官网全部模型定价，含分段定价。
                </p>
              </div>
              <button
                type="button"
                @click="handleOneClickSiliconFlow"
                :disabled="isProbing"
                class="mt-2.5 w-full px-3 py-1.5 rounded-xl bg-[#6E29F6] hover:bg-[#5d20d8] active:bg-[#4A148C] disabled:opacity-50 text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center space-x-1 cursor-pointer"
              >
                <span v-if="isProbing && form.site_type === 'siliconflow'" class="animate-spin text-xs">⏳</span>
                <span v-else>🔮</span>
                <span class="truncate">{{ (isProbing && form.site_type === 'siliconflow') ? '爬取中...' : '爬取官网定价' }}</span>
              </button>
            </div>

            <!-- 3. 阿里百炼 Model Studio 一键爬取 (橙色系) -->
            <div class="p-3.5 bg-gradient-to-br from-[#FFF5ED] to-[#FFF9F5] rounded-2xl border border-[#FFD8BF] flex flex-col justify-between shadow-xs">
              <div class="space-y-1">
                <div class="flex items-center space-x-1.5">
                  <span class="text-base">🟠</span>
                  <span class="font-bold text-[#FF6A00] text-xs truncate">阿里百炼 Model Studio</span>
                  <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#FF6A00] text-white shrink-0">官方</span>
                </div>
                <p class="text-[11px] text-[#6E6E73] leading-relaxed line-clamp-2">
                  自动爬取阿里百炼通义千问与开源模型定价与阶梯计费。
                </p>
              </div>
              <button
                type="button"
                @click="handleOneClickBailian"
                :disabled="isProbing"
                class="mt-2.5 w-full px-3 py-1.5 rounded-xl bg-[#FF6A00] hover:bg-[#E65F00] active:bg-[#CC5400] disabled:opacity-50 text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center space-x-1 cursor-pointer"
              >
                <span v-if="isProbing && form.site_type === 'aliyun_bailian'" class="animate-spin text-xs">⏳</span>
                <span v-else>🟠</span>
                <span class="truncate">{{ (isProbing && form.site_type === 'aliyun_bailian') ? '爬取中...' : '爬取百炼定价' }}</span>
              </button>
            </div>
          </div>

          <div class="p-3 bg-[#F2F2F7]/70 rounded-xl border border-[#E5E5EA] text-[#6E6E73] text-[11px] leading-relaxed">
            💡 或者手动接入基于 <strong>NewAPI</strong>、<strong>OneAPI</strong>、<strong>Sub2API</strong> 或自建聚合网关的中转服务。系统将自动探测连通性并拉取原始模型列表。
          </div>

          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">渠道/站点名称 (Name) *</label>
                <input
                  v-model="form.name"
                  type="text"
                  placeholder="例如: 极速云 AI 聚合 (NewAPI)"
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none transition-all"
                />
              </div>

              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">API 基础端点地址 (Base URL) *</label>
                <input
                  v-model="form.base_url"
                  type="text"
                  placeholder="https://api.my-relay.com/v1"
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none transition-all"
                />
              </div>
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">系统类型 (Site Type)</label>
                <select
                  v-model="form.site_type"
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none transition-all"
                >
                  <option value="newapi">NewAPI / OneAPI 架构</option>
                  <option value="sub2api">Sub2API 包月/额度架构</option>
                  <option value="custom">通用自建 OpenAI 兼容网关</option>
                  <option value="siliconflow">🔮 硅基流动 SiliconFlow (自动爬取官网定价)</option>
                  <option value="aliyun_bailian">🟠 阿里百炼 (Model Studio · 自动抓取官方定价)</option>
                </select>
              </div>

              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">渠道结算货币 (Currency) *</label>
                <div class="grid grid-cols-2 gap-1.5 bg-[#F2F2F7] p-1 rounded-xl border border-[#E5E5EA]">
                  <button
                    type="button"
                    @click="form.currency = 'CNY'"
                    class="py-1 rounded-lg text-xs font-bold transition-all flex items-center justify-center space-x-1"
                    :class="form.currency === 'CNY' ? 'bg-[#FFFFFF] text-[#0071E3] shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
                  >
                    <span>🇨🇳</span>
                    <span>人民币 CNY</span>
                  </button>
                  <button
                    type="button"
                    @click="form.currency = 'USD'"
                    class="py-1 rounded-lg text-xs font-bold transition-all flex items-center justify-center space-x-1"
                    :class="form.currency === 'USD' ? 'bg-[#FFFFFF] text-[#0071E3] shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
                  >
                    <span>🇺🇸</span>
                    <span>美元 USD</span>
                  </button>
                </div>
              </div>

              <div>
                <label class="block text-[#6E6E73] font-medium mb-1">充值折算汇率 (1元换多少美元额度)</label>
                <input
                  v-model.number="form.recharge_rate"
                  type="number"
                  step="0.01"
                  placeholder="1.0"
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none transition-all"
                />
              </div>
            </div>

            <div v-if="form.site_type !== 'siliconflow' && form.site_type !== 'aliyun_bailian'">
              <label class="block text-[#6E6E73] font-medium mb-1">中转站 API Key (用于鉴权、模型拉取与实时测速)</label>
              <input
                v-model="form.api_key"
                type="password"
                placeholder="sk-..."
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none transition-all"
              />
            </div>

            <!-- 硅基流动特殊提示 -->
            <div v-if="form.site_type === 'siliconflow'" class="p-3.5 bg-gradient-to-r from-[#F3F0FF] to-[#F9F7FF] rounded-xl border border-[#D8CCFF] text-xs text-[#6E29F6] leading-relaxed">
              <div class="flex items-center space-x-2 mb-1">
                <span class="text-base">🔮</span>
                <span class="font-bold">硅基流动自动爬取模式</span>
              </div>
              <p class="text-[11px] text-[#6E6E73]">
                下一步将自动访问硅基流动官网定价页 (siliconflow.cn/pricing)，通过 headless 浏览器爬取全部模型价格（包括对话、生图、语音、视频），无需手动配置 API Key。
              </p>
            </div>

            <!-- 阿里百炼特殊提示 -->
            <div v-if="form.site_type === 'aliyun_bailian'" class="p-3.5 bg-gradient-to-r from-[#FFF5ED] to-[#FFF9F5] rounded-xl border border-[#FFD8BF] text-xs text-[#FF6A00] leading-relaxed">
              <div class="flex items-center space-x-2 mb-1">
                <span class="text-base">🟠</span>
                <span class="font-bold">阿里百炼 (Model Studio) 自动抓取模式</span>
              </div>
              <p class="text-[11px] text-[#6E6E73]">
                下一步将自动抓取阿里云帮助中心百炼官方定价页（北京主力节点），自动提取通义千问全系列、第三方开源模型、多模态与语音生图全部价格，支持阶梯区间计费与限时折扣换算。
              </p>
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">备注说明 (可选)</label>
              <input
                v-model="form.notes"
                type="text"
                placeholder="例如: 支持高并发 Claude / DeepSeek 特殊渠道"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none transition-all"
              />
            </div>
          </div>
        </div>

        <!-- ==================== Step 2: 连通性探测 & 抓取 ==================== -->
        <div v-else-if="currentStep === 2" class="space-y-5 animate-fade-in flex flex-col items-center justify-center py-6">
          <div v-if="isProbing" class="flex flex-col items-center space-y-4 py-8">
            <div class="relative w-16 h-16 flex items-center justify-center">
              <div class="absolute inset-0 rounded-full border-4 animate-ping"
                :class="form.site_type === 'siliconflow' ? 'border-[#6E29F6]/20' : (form.site_type === 'aliyun_bailian' ? 'border-[#FF6A00]/20' : 'border-[#0071E3]/20')"
              ></div>
              <div class="w-12 h-12 rounded-full flex items-center justify-center text-white text-xl shadow-lg"
                :class="form.site_type === 'siliconflow' ? 'bg-[#6E29F6]' : (form.site_type === 'aliyun_bailian' ? 'bg-[#FF6A00]' : 'bg-[#0071E3]')"
              >
                {{ form.site_type === 'siliconflow' ? '🔮' : (form.site_type === 'aliyun_bailian' ? '🟠' : '📡') }}
              </div>
            </div>
            <div class="text-center">
              <div class="font-bold text-sm text-[#1D1D1F]">
                {{ form.site_type === 'siliconflow' ? '正在爬取硅基流动官网全量模型定价...' : (form.site_type === 'aliyun_bailian' ? '正在抓取阿里百炼官方全量模型定价...' : '正在探测端点连通性并抓取模型列表...') }}
              </div>
              <div class="text-[#86868B] text-xs mt-1 font-mono">
                {{ form.site_type === 'siliconflow' ? 'siliconflow.cn/pricing' : (form.site_type === 'aliyun_bailian' ? 'help.aliyun.com/zh/model-studio/model-pricing' : form.base_url) }}
              </div>
              <div v-if="form.site_type === 'siliconflow'" class="text-[10px] text-[#86868B] mt-2">
                正在自动点击展开所有隐藏模型，请稍候...
              </div>
              <div v-if="form.site_type === 'aliyun_bailian'" class="text-[10px] text-[#86868B] mt-2">
                正在解析华北2（北京）主力地域全部千问与开源模型表格，请稍候...
              </div>
            </div>
          </div>

          <!-- 硅基流动专属展示分支 (彻底与普通中转探测隔离) -->
          <template v-else-if="form.site_type === 'siliconflow'">
            <!-- 爬取成功 -->
            <div v-if="sfScrapeResult" class="w-full space-y-4">
              <div class="p-4 rounded-xl border bg-[#F3F0FF]/40 border-[#D8CCFF] flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold bg-[#6E29F6] text-white">✓</div>
                  <div>
                    <div class="font-bold text-xs text-[#4A148C]">硅基流动定价爬取完成</div>
                    <div class="text-[11px] text-[#6E6E73] mt-0.5 font-mono">耗时 {{ (sfScrapeResult.scrape_duration_ms / 1000).toFixed(1) }}s · 共发现 {{ sfScrapeResult.total_models }} 个模型</div>
                  </div>
                </div>
                <button @click="runSiliconFlowScrape" class="px-3 py-1.5 rounded-lg bg-[#FFFFFF] border border-[#D8CCFF] hover:bg-[#F3F0FF] text-[#6E29F6] font-medium transition-all cursor-pointer">
                  🔄 重新爬取
                </button>
              </div>

              <!-- 分类统计 -->
              <div class="grid grid-cols-4 gap-3">
                <div v-for="(count, cat) in sfScrapeResult.category_counts" :key="cat" class="p-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-center">
                  <div class="text-[#86868B] text-[11px]">{{ cat }}模型</div>
                  <div class="text-lg font-bold font-mono text-[#1D1D1F] mt-1">{{ count }}</div>
                </div>
              </div>

              <!-- 免费 + 分段定价统计 -->
              <div class="flex items-center space-x-4 text-[11px] text-[#6E6E73]">
                <span>🆓 免费模型: <b class="text-[#34C759] font-mono">{{ sfScrapeResult.free_models_count }}</b> 个</span>
                <span>📊 分段定价: <b class="text-[#FF9500] font-mono">{{ sfScrapeResult.tiered_models_count }}</b> 个</span>
              </div>

              <!-- 样本价格预览 -->
              <div class="bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] overflow-hidden">
                <div class="px-4 py-2 bg-[#F2F2F7] border-b border-[#E5E5EA] text-[11px] font-bold text-[#6E6E73]">
                  模型价格预览 (前 8 个)
                </div>
                <div class="divide-y divide-[#E5E5EA]">
                  <div v-for="m in sfScrapeResult.models.slice(0, 8)" :key="m.model_id" class="px-4 py-2 flex items-center justify-between text-xs">
                    <div class="flex items-center space-x-2 min-w-0">
                      <span class="text-[#86868B] text-[10px] px-1.5 py-0.5 rounded bg-[#F2F2F7] shrink-0">{{ m.category }}</span>
                      <span class="font-medium text-[#1D1D1F] truncate">{{ m.display_name }}</span>
                      <span v-if="m.is_free" class="px-1.5 py-0.5 rounded-full bg-[#E6F4EA] text-[#137333] text-[10px] font-bold shrink-0">免费</span>
                      <span v-if="m.has_tiered_pricing" class="px-1.5 py-0.5 rounded-full bg-[#FFF3CD] text-[#856404] text-[10px] font-bold shrink-0">分段</span>
                    </div>
                    <div class="flex items-center space-x-3 text-[#6E6E73] font-mono shrink-0">
                      <span>输入 ¥{{ m.input_price_cny }}</span>
                      <span>输出 ¥{{ m.output_price_cny }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 爬取失败 -->
            <div v-else-if="sfScrapeError" class="w-full space-y-4">
              <div class="p-4 rounded-xl border bg-[#FDE8E8]/40 border-[#FAD2D2]">
                <div class="font-bold text-xs text-[#C5221F] mb-1">爬取失败</div>
                <div class="text-[11px] text-[#6E6E73]">{{ sfScrapeError }}</div>
                <button @click="runSiliconFlowScrape" class="mt-2 px-3 py-1.5 rounded-lg bg-[#0071E3] text-white text-xs font-bold cursor-pointer">
                  🔄 重试
                </button>
              </div>
            </div>

            <!-- 尚未执行状态兜底 -->
            <div v-else class="w-full space-y-4 text-center py-8">
              <div class="text-xs text-[#86868B]">尚未加载爬取结果，点击下方按钮开始获取官网定价</div>
              <button @click="runSiliconFlowScrape" class="px-4 py-2 rounded-xl bg-[#6E29F6] text-white text-xs font-bold shadow-sm hover:bg-[#5d20d8] cursor-pointer">
                🔮 开始爬取官网定价
              </button>
            </div>
          </template>

          <!-- 阿里百炼专属展示分支 -->
          <template v-else-if="form.site_type === 'aliyun_bailian'">
            <!-- 爬取成功 -->
            <div v-if="bailianScrapeResult" class="w-full space-y-4">
              <div class="p-4 rounded-xl border bg-[#FFF5ED]/60 border-[#FFD8BF] flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold bg-[#FF6A00] text-white">✓</div>
                  <div>
                    <div class="font-bold text-xs text-[#CC5400]">阿里百炼官方定价抓取完成</div>
                    <div class="text-[11px] text-[#6E6E73] mt-0.5 font-mono">耗时 {{ (bailianScrapeResult.scrape_duration_ms / 1000).toFixed(1) }}s · 共发现 {{ bailianScrapeResult.total_models }} 个模型规格</div>
                  </div>
                </div>
                <button @click="runBailianScrape" class="px-3 py-1.5 rounded-lg bg-[#FFFFFF] border border-[#FFD8BF] hover:bg-[#FFF5ED] text-[#FF6A00] font-medium transition-all cursor-pointer">
                  🔄 重新抓取
                </button>
              </div>

              <!-- 分类统计 -->
              <div class="grid grid-cols-4 gap-3">
                <div v-for="(count, cat) in bailianScrapeResult.category_counts" :key="cat" class="p-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-center">
                  <div class="text-[#86868B] text-[11px] truncate">{{ cat }}</div>
                  <div class="text-lg font-bold font-mono text-[#1D1D1F] mt-1">{{ count }}</div>
                </div>
              </div>

              <!-- 免费 + 分段定价统计 -->
              <div class="flex items-center space-x-4 text-[11px] text-[#6E6E73]">
                <span>🆓 免费模型: <b class="text-[#34C759] font-mono">{{ bailianScrapeResult.free_models_count }}</b> 个</span>
                <span>📊 阶梯分段定价: <b class="text-[#FF9500] font-mono">{{ bailianScrapeResult.tiered_models_count }}</b> 个</span>
              </div>

              <!-- 样本价格预览 -->
              <div class="bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] overflow-hidden">
                <div class="px-4 py-2 bg-[#F2F2F7] border-b border-[#E5E5EA] text-[11px] font-bold text-[#6E6E73]">
                  百炼模型价格预览 (前 8 个)
                </div>
                <div class="divide-y divide-[#E5E5EA]">
                  <div v-for="m in bailianScrapeResult.models.slice(0, 8)" :key="m.model_id" class="px-4 py-2 flex items-center justify-between text-xs">
                    <div class="flex items-center space-x-2 min-w-0">
                      <span class="text-[#86868B] text-[10px] px-1.5 py-0.5 rounded bg-[#F2F2F7] shrink-0">{{ m.category }}</span>
                      <span class="font-medium text-[#1D1D1F] truncate">{{ m.display_name }}</span>
                      <span v-if="m.price_note" class="px-1.5 py-0.2 rounded text-[#FF6A00] bg-[#FFF5ED] border border-[#FFD8BF] text-[9px] font-bold shrink-0">{{ m.price_note }}</span>
                      <span v-if="m.has_tiered_pricing" class="px-1.5 py-0.2 rounded-full bg-[#FFF3CD] text-[#856404] text-[9px] font-bold shrink-0">阶梯</span>
                    </div>
                    <div class="flex items-center space-x-3 text-[#6E6E73] font-mono shrink-0">
                      <span>输入 ¥{{ m.input_price_cny }}</span>
                      <span>输出 ¥{{ m.output_price_cny }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 抓取失败 -->
            <div v-else-if="bailianScrapeError" class="w-full space-y-4">
              <div class="p-4 rounded-xl border bg-[#FDE8E8]/40 border-[#FAD2D2]">
                <div class="font-bold text-xs text-[#C5221F] mb-1">抓取失败</div>
                <div class="text-[11px] text-[#6E6E73]">{{ bailianScrapeError }}</div>
                <button @click="runBailianScrape" class="mt-2 px-3 py-1.5 rounded-lg bg-[#FF6A00] text-white text-xs font-bold cursor-pointer">
                  🔄 重试
                </button>
              </div>
            </div>

            <!-- 尚未执行状态兜底 -->
            <div v-else class="w-full space-y-4 text-center py-8">
              <div class="text-xs text-[#86868B]">尚未加载百炼抓取结果，点击下方按钮开始获取官方定价</div>
              <button @click="runBailianScrape" class="px-4 py-2 rounded-xl bg-[#FF6A00] text-white text-xs font-bold shadow-sm hover:bg-[#E65F00] cursor-pointer">
                🟠 开始抓取百炼定价
              </button>
            </div>
          </template>

          <div v-else class="w-full space-y-4">
            <!-- 探测结果状态卡片 -->
            <div
              class="p-4 rounded-xl border flex items-center justify-between"
              :class="probeResult.is_online ? 'bg-[#E6F4EA]/40 border-[#CEEAD6]' : 'bg-[#FDE8E8]/40 border-[#FAD2D2]'"
            >
              <div class="flex items-center space-x-3">
                <div
                  class="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold"
                  :class="probeResult.is_online ? 'bg-[#34C759] text-white' : 'bg-[#FF3B30] text-white'"
                >
                  {{ probeResult.is_online ? '✓' : '✕' }}
                </div>
                <div>
                  <div class="font-bold text-xs flex items-center space-x-2" :class="probeResult.is_online ? 'text-[#137333]' : 'text-[#C5221F]'">
                    <span>{{ probeResult.is_online ? '端点连接正常 (Online)' : '端点连通失败 / 鉴权错误' }}</span>
                    <span
                      v-if="probeResult.fetch_source"
                      class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]"
                    >
                      ⚡ {{ probeResult.fetch_source }}
                    </span>
                  </div>
                  <div class="text-[11px] text-[#6E6E73] mt-0.5 font-mono">
                    HTTP 状态码: {{ probeResult.status_code || 'N/A' }} | 实时延迟: {{ probeResult.latency_ms }} ms
                  </div>
                </div>
              </div>

              <button
                @click="runProbe"
                class="px-3 py-1.5 rounded-lg bg-[#FFFFFF] border border-[#E5E5EA] hover:bg-[#F2F2F7] text-[#0071E3] font-medium transition-all"
              >
                🔄 重新探测
              </button>
            </div>

            <!-- 统计指标格 -->
            <div v-if="probeResult.is_online" class="grid grid-cols-3 gap-3">
              <div class="p-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-center">
                <div class="text-[#86868B] text-[11px]">发现原始模型数</div>
                <div class="text-lg font-bold font-mono text-[#1D1D1F] mt-1">{{ probeResult.raw_count }}</div>
              </div>
              <div class="p-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-center">
                <div class="text-[#86868B] text-[11px]">已精准匹配标准模型</div>
                <div class="text-lg font-bold font-mono text-[#34C759] mt-1">{{ probeResult.matched_count }}</div>
              </div>
              <div class="p-3 bg-[#F9F9FB] rounded-xl border border-[#E5E5EA] text-center">
                <div class="text-[#86868B] text-[11px]">待确认/未匹配模型</div>
                <div class="text-lg font-bold font-mono text-[#FF9500] mt-1">{{ probeResult.unmatched_count }}</div>
              </div>
            </div>

            <!-- 目标结算分组选择器 (Group-based Pricing 支持) -->
            <div
              v-if="probeResult.available_groups && probeResult.available_groups.length > 0"
              class="p-3.5 bg-[#F2F2F7] rounded-xl border border-[#E5E5EA] space-y-2 animate-fade-in"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-1.5 text-xs font-bold text-[#1D1D1F]">
                  <span>🎯</span>
                  <span>选择目标结算分组 (Group)</span>
                </div>
                <span class="text-[11px] text-[#86868B]">共发现 {{ probeResult.available_groups.length }} 个定价分组</span>
              </div>
              <div class="flex items-center space-x-3">
                <select
                  v-model="probeResult.selected_group"
                  @change="onSelectedGroupChange"
                  class="flex-1 bg-white border border-[#E5E5EA] rounded-xl px-3 py-2 text-xs font-medium text-[#1D1D1F] focus:outline-none focus:border-[#0071E3]"
                >
                  <option
                    v-for="g in probeResult.available_groups"
                    :key="g.name"
                    :value="g.name"
                  >
                    {{ g.name }} (倍率: {{ g.ratio }}x{{ g.desc ? ` · ${g.desc}` : '' }}, 覆盖 {{ g.model_count }} 款模型)
                  </option>
                </select>
              </div>
            </div>

            <!-- Key 专属令牌特权状态卡片 -->
            <div
              v-if="probeResult.token_group || probeResult.has_special_pricing"
              class="p-3 bg-[#E8F2FD] border border-[#CCE4FB] rounded-xl flex items-center justify-between text-xs text-[#0071E3] animate-fade-in"
            >
              <div class="flex items-center space-x-2">
                <span class="font-bold">🔑 识别到令牌分组:</span>
                <span class="px-2 py-0.5 rounded bg-white font-mono font-bold text-[#0071E3] border border-[#CCE4FB] shadow-2xs">
                  {{ probeResult.token_group || '特权令牌' }}
                </span>
                <span v-if="probeResult.special_pricing_count > 0" class="text-[#137333] font-medium">
                  (已发现 {{ probeResult.special_pricing_count }} 款模型享受 Key 专属特权折扣！)
                </span>
              </div>
              <span class="text-[11px] text-[#0071E3]/80">已在第3步默认应用优惠特权价</span>
            </div>

            <!-- 站点访问限制与快捷补填 Key 提示卡片 -->
            <div
              v-if="!form.api_key && probeResult.fetch_source && probeResult.fetch_source.includes('/api/user/groups')"
              class="p-3.5 bg-[#FFF9E6] border border-[#FFE082] rounded-xl space-y-2 animate-fade-in text-xs"
            >
              <div class="flex items-start space-x-2">
                <span class="text-base leading-none">💡</span>
                <div>
                  <div class="font-bold text-[#8D6E63] text-xs">检测到该站点限制了未登录定价访问</div>
                  <div class="text-[#8D6E63]/90 text-[11px] mt-0.5 leading-relaxed">
                    当前免 Key 状态下系统已为您关联了主流基准模型。若该站点包含了商家自定义非标模型（如 <code class="bg-[#FFF3E0] px-1 py-0.5 rounded font-mono font-bold text-[#E65100]">claude-fable-5</code> 等），建议填入 API Key 即可一键拉取 100% 完整的全量真实模型列表！
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-2 pt-1">
                <input
                  v-model="form.api_key"
                  type="password"
                  placeholder="填入该站点中转 API Key (sk-...) 嗅探全量模型..."
                  class="flex-1 bg-white border border-[#E5E5EA] focus:border-[#0071E3] rounded-lg px-3 py-1.5 font-mono text-xs focus:outline-none"
                />
                <button
                  @click="runProbe"
                  class="px-3.5 py-1.5 bg-[#0071E3] hover:bg-[#0077ED] text-white font-bold rounded-lg text-xs shadow-xs transition-colors shrink-0 flex items-center space-x-1 cursor-pointer"
                >
                  <span>📡</span>
                  <span>带 Key 重新嗅探</span>
                </button>
              </div>
            </div>

            <div v-if="probeResult.error" class="p-3 bg-[#FFF3CD] border border-[#FFEEBA] text-[#856404] rounded-xl text-[11px]">
              ⚠️ 探测提示: {{ probeResult.error }}
            </div>
          </div>
        </div>

        <!-- ==================== Step 3: 智能映射与审核确认 ==================== -->
        <div v-else-if="currentStep === 3" class="space-y-3 animate-fade-in flex flex-col h-full">
          <!-- 筛选与统计工具条 (第一行: 匹配状态 + 全选/清空) -->
          <div class="flex items-center justify-between bg-[#F9F9FB] p-2.5 rounded-xl border border-[#E5E5EA]">
            <div class="flex items-center space-x-2">
              <span class="text-[#6E6E73] font-medium">状态筛选:</span>
              <button
                @click="mappingFilter = 'all'"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
                :class="mappingFilter === 'all' ? 'bg-[#0071E3] text-white font-bold' : 'text-[#6E6E73] hover:bg-[#E5E5EA]'"
              >
                当前视图 ({{ filteredMappings.length }})
              </button>
              <button
                @click="mappingFilter = 'matched'"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
                :class="mappingFilter === 'matched' ? 'bg-[#34C759] text-white font-bold' : 'text-[#6E6E73] hover:bg-[#E5E5EA]'"
              >
                已匹配 ({{ matchedMappingsCount }})
              </button>
              <button
                @click="mappingFilter = 'unmatched'"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
                :class="mappingFilter === 'unmatched' ? 'bg-[#FF9500] text-white font-bold' : 'text-[#6E6E73] hover:bg-[#E5E5EA]'"
              >
                待确认 ({{ unmatchedMappingsCount }})
              </button>

              <button
                @click="isAddingCustomModel = !isAddingCustomModel"
                class="px-2.5 py-1 rounded-lg text-[11px] font-medium border border-[#CCE4FB] bg-[#F0F7FF] text-[#0071E3] hover:bg-[#E8F2FD] transition-all flex items-center space-x-1 cursor-pointer shadow-2xs ml-1"
                title="手动添加渠道私有或非标模型 (如 claude-fable-5)"
              >
                <span>➕</span>
                <span>手动追加模型</span>
              </button>
            </div>

            <!-- 全选 / 清空当前视图模型 & 特权倍率快捷应用 -->
            <div class="flex items-center space-x-2">
              <div v-if="hasSpecialPricingInMappings" class="flex items-center space-x-1 mr-2 bg-[#E8F2FD]/50 px-2 py-0.5 rounded-lg border border-[#CCE4FB]">
                <span class="text-[10px] text-[#0071E3] font-bold">特权倍率:</span>
                <button
                  @click="batchApplyRatio('key')"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-white text-[#0071E3] border border-[#CCE4FB] hover:bg-[#0071E3] hover:text-white transition-colors"
                >
                  全部使用Key特权
                </button>
                <button
                  @click="batchApplyRatio('public')"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-white text-[#6E6E73] border border-[#E5E5EA] hover:bg-[#F2F2F7] transition-colors"
                >
                  公开倍率
                </button>
              </div>
              <span class="text-[11px] text-[#86868B]">已选收录: <b class="text-[#0071E3] font-mono">{{ selectedMappingsCount }}</b> 款</span>
              <span class="text-[#D1D1D6]">|</span>
              <button
                @click="toggleSelectAll(true)"
                class="text-[11px] text-[#0071E3] hover:underline"
              >
                全选
              </button>
              <span class="text-[#D1D1D6]">|</span>
              <button
                @click="toggleSelectAll(false)"
                class="text-[11px] text-[#86868B] hover:underline"
              >
                清空
              </button>
            </div>
          </div>

          <!-- 手动快捷追加自定义模型条目 (如 claude-fable-5) -->
          <div v-if="isAddingCustomModel" class="p-2.5 bg-[#F0F7FF] border border-[#CCE4FB] rounded-xl flex items-center space-x-2.5 text-xs animate-fade-in">
            <span class="font-bold text-[#0071E3] shrink-0 text-[11px]">➕ 追加模型:</span>
            <input
              v-model="customModelInput.name"
              type="text"
              placeholder="输入渠道原始模型名 (如 claude-fable-5)..."
              class="flex-1 bg-white border border-[#CCE4FB] focus:border-[#0071E3] rounded-lg px-2.5 py-1 font-mono text-xs text-[#1D1D1F] focus:outline-none"
              @keydown.enter.prevent="addCustomChannelModel"
            />
            <select
              v-model="customModelInput.group"
              class="bg-white border border-[#CCE4FB] focus:border-[#0071E3] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] focus:outline-none"
            >
              <option value="">-- 选择所属分组 (默认) --</option>
              <option
                v-for="g in probeResult.available_groups"
                :key="g.name"
                :value="g.name"
              >
                {{ g.name }} ({{ g.ratio }}x)
              </option>
            </select>
            <button
              @click="addCustomChannelModel"
              class="px-3 py-1 bg-[#0071E3] hover:bg-[#0077ED] text-white font-bold rounded-lg text-xs shadow-xs transition-colors shrink-0 cursor-pointer"
            >
              确认追加
            </button>
            <button
              @click="isAddingCustomModel = false"
              class="px-2.5 py-1 bg-white border border-[#E5E5EA] hover:bg-[#F2F2F7] text-[#6E6E73] rounded-lg text-xs transition-colors shrink-0 cursor-pointer"
            >
              取消
            </button>
          </div>

          <!-- 分组多选胶囊筛选栏 (第二行: 严格按选中分组过滤) -->
          <div
            v-if="probeResult.available_groups && probeResult.available_groups.length > 0"
            class="flex items-center space-x-1.5 overflow-x-auto pb-1 text-xs"
          >
            <span class="text-[#6E6E73] font-medium text-[11px] whitespace-nowrap flex items-center space-x-1">
              <span>🎯</span>
              <span>分组多选过滤:</span>
            </span>
            <button
              @click="toggleGroupFilter('all')"
              class="px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all whitespace-nowrap"
              :class="selectedGroupFilters.includes('all') ? 'bg-[#1D1D1F] text-white font-bold shadow-2xs' : 'bg-[#F2F2F7] text-[#6E6E73] hover:bg-[#E5E5EA]'"
            >
              全部 ({{ mappingsList.length }})
            </button>
            <button
              v-for="g in probeResult.available_groups"
              :key="g.name"
              @click="toggleGroupFilter(g.name)"
              class="px-2.5 py-1 rounded-lg text-[10px] font-mono transition-all whitespace-nowrap flex items-center space-x-1 border"
              :class="selectedGroupFilters.includes(g.name) ? 'bg-[#0071E3] text-white font-bold border-[#0071E3] shadow-2xs' : 'bg-[#FFFFFF] text-[#6E6E73] border-[#E5E5EA] hover:border-[#0071E3]'"
            >
              <span>{{ g.name }}</span>
              <span class="opacity-80 text-[9px]">({{ getGroupModelCount(g.name) }})</span>
            </button>
          </div>

          <!-- 映射对照数据表格 -->
          <div class="flex-1 border border-[#E5E5EA] rounded-xl overflow-x-auto overflow-y-auto max-h-[460px] min-h-[340px] custom-scrollbar shadow-2xs">
            <table class="w-full min-w-[1040px] text-left border-collapse">
              <thead class="bg-[#F2F2F7] sticky top-0 z-20 text-[11px] text-[#6E6E73] border-b border-[#E5E5EA] shadow-2xs">
                <tr>
                  <th class="py-2.5 px-3 text-center w-10">收录</th>
                  <th class="py-2.5 px-3.5 min-w-[190px]">渠道模型 & 分组</th>
                  <th class="py-2.5 px-1 text-center w-6">➔</th>
                  <th class="py-2.5 px-3 min-w-[280px]">对应 models.dev 标准模型</th>
                  <th class="py-2.5 px-3 text-center w-32 font-semibold">标准官方原价 ({{ form.currency === 'USD' ? '$' : '¥' }})</th>
                  <th class="py-2.5 px-3 text-center w-28 font-semibold">计费倍率 & 机制</th>
                  <th class="py-2.5 px-3.5 text-center w-36 font-semibold">折算实际单价 (每1M - {{ form.currency === 'USD' ? 'USD $' : 'CNY ¥' }})</th>
                  <th class="py-2.5 px-3 text-center w-16">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#E5E5EA] text-[11px]">
                <tr
                  v-for="(item, idx) in filteredMappings"
                  :key="item.item_key || idx"
                  class="hover:bg-[#F9F9FB] transition-colors"
                  :class="{'bg-[#FFF9E6]/30': !item.is_matched}"
                >
                  <!-- 1. 勾选 -->
                  <td class="py-2 px-2.5 text-center">
                    <input
                      type="checkbox"
                      v-model="item.is_selected"
                      class="rounded text-[#0071E3] focus:ring-0 cursor-pointer"
                    />
                  </td>

                  <!-- 2. 原始模型名称与所属分组徽章 -->
                  <td class="py-2 px-3">
                    <div class="font-mono font-bold text-[#1D1D1F] truncate" :title="item.channel_model_name">
                      {{ item.channel_model_name }}
                    </div>
                    <div class="mt-0.5 flex items-center space-x-1">
                      <span class="px-1.5 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-mono font-bold inline-block shadow-2xs">
                        🎯 {{ item.group_name }}
                      </span>
                      <span
                        v-if="item.match_type"
                        class="px-1.5 py-0.2 rounded border text-[9px] font-mono inline-block shadow-2xs"
                        :class="getMatchBadgeClass(item.match_type)"
                      >
                        {{ getMatchBadgeLabel(item.match_type) }}
                      </span>
                    </div>
                  </td>

                  <!-- 3. 箭头 -->
                  <td class="py-2 px-1 text-center text-[#86868B]">➔</td>

                  <!-- 4. 目标标准模型下拉选择 (支持模糊搜索与新建别名) -->
                  <td class="py-2 px-3 min-w-[240px]">
                    <ModelSearchSelect
                      v-model="item.standard_model_id"
                      :models-catalog="store.modelsCatalog"
                      :raw-model-name="item.channel_model_name"
                      :current-price-usd="item.input_price_usd"
                      :current-price-cny="item.input_price_cny"
                      :currency="form.currency"
                      @change="onStandardModelChange(item)"
                    />
                  </td>

                  <!-- 5. 【第一段】标准官方原价 (入 / 出 / 缓) -->
                  <td class="py-2 px-2.5 text-center">
                    <div v-if="item.official_input_cny > 0 || item.official_input_price > 0" class="inline-flex flex-col items-center bg-[#F9F9FB] px-2 py-0.5 rounded-lg border border-[#E5E5EA] text-[10px] font-mono text-[#6E6E73] w-full">
                      <div class="flex items-center justify-between w-full">
                        <span>入:</span>
                        <span>{{ form.currency === 'USD' ? `$${item.official_input_price.toFixed(3)}` : `¥${(item.official_input_cny || item.official_input_price * (store.usdToCnyRate || 7.25)).toFixed(2)}` }}</span>
                      </div>
                      <div class="flex items-center justify-between w-full">
                        <span>出:</span>
                        <span>{{ form.currency === 'USD' ? `$${item.official_output_price.toFixed(3)}` : `¥${(item.official_output_cny || item.official_output_price * (store.usdToCnyRate || 7.25)).toFixed(2)}` }}</span>
                      </div>
                      <div v-if="(item.official_cache_cny > 0 || item.official_cache_price > 0)" class="flex items-center justify-between w-full text-[9px] text-[#86868B]">
                        <span>缓:</span>
                        <span>{{ form.currency === 'USD' ? `$${item.official_cache_price.toFixed(3)}` : `¥${(item.official_cache_cny || item.official_cache_price * (store.usdToCnyRate || 7.25)).toFixed(2)}` }}</span>
                      </div>
                    </div>
                    <span v-else class="text-[10px] text-[#AEAEB2] font-mono">--</span>
                  </td>

                  <!-- 6. 【第二段】计费倍率 & 机制 -->
                  <td class="py-2 px-2.5 text-center">
                    <div class="flex flex-col items-center space-y-0.5">
                      <span
                        class="px-1.5 py-0.2 rounded font-mono text-[10px] font-bold border shadow-2xs"
                        :class="item.has_ratio_diff && item.applied_ratio_source === 'key' ? 'bg-[#E6F4EA] text-[#137333] border-[#CEEAD6]' : 'bg-[#F2F2F7] text-[#1D1D1F] border-[#E5E5EA]'"
                      >
                        {{ item.custom_ratio !== null ? `${item.custom_ratio}x` : '1.0x' }}
                      </span>
                      <span
                        class="text-[9px] px-1 rounded-sm"
                        :class="item.match_type === 'exact' ? 'text-[#0071E3]' : (item.match_type === 'global_alias' ? 'text-[#AF52DE]' : 'text-[#86868B]')"
                      >
                        {{ item.has_ratio_diff ? (item.applied_ratio_source === 'key' ? 'Key特权' : '公开倍率') : '分组倍率' }}
                      </span>
                    </div>
                  </td>

                  <!-- 7. 【第三段】折算实际单价 (精致高亮卡片) -->
                  <td class="py-2 px-3 text-center">
                    <div class="inline-flex flex-col items-center bg-[#F4FBF7] px-2.5 py-1 rounded-lg border border-[#CEEAD6] w-full text-[11px] font-mono">
                      <div class="flex items-center justify-between w-full space-x-2">
                        <span class="text-[#86868B]">入:</span>
                        <span class="font-bold text-[#137333]">
                          {{ form.currency === 'USD' ? `$${item.input_price_usd.toFixed(3)}` : `¥${item.input_price_cny.toFixed(2)}` }}
                        </span>
                      </div>
                      <div class="flex items-center justify-between w-full space-x-2">
                        <span class="text-[#86868B]">出:</span>
                        <span class="font-bold text-[#0071E3]">
                          {{ form.currency === 'USD' ? `$${item.output_price_usd.toFixed(3)}` : `¥${item.output_price_cny.toFixed(2)}` }}
                        </span>
                      </div>
                      <div v-if="item.cache_price_cny > 0 || item.cache_price_usd > 0" class="flex items-center justify-between w-full space-x-2 text-[10px] text-[#34C759]">
                        <span class="text-[#86868B]">缓:</span>
                        <span>{{ form.currency === 'USD' ? `$${item.cache_price_usd.toFixed(3)}` : `¥${item.cache_price_cny.toFixed(3)}` }}</span>
                      </div>
                    </div>
                  </td>

                  <!-- 8. 固化为全局规则 -->
                  <td class="py-2 px-2 text-center whitespace-nowrap">
                    <button
                      v-if="item.standard_model_id"
                      @click="promoteAlias(item)"
                      class="text-[10px] px-2 py-0.5 rounded bg-[#F2F2F7] hover:bg-[#0071E3] hover:text-white text-[#0071E3] border border-[#E5E5EA] transition-all shadow-2xs cursor-pointer"
                      title="将此映射固化为全局智能别名库规则，未来所有渠道自动生效"
                    >
                      ⭐ 固化
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ==================== Step 4: 费率倍率确认 & 最终入库 ==================== -->
        <div v-else-if="currentStep === 4" class="space-y-4 animate-fade-in">
          <div class="p-4 bg-[#E8F2FD]/50 rounded-2xl border border-[#CCE4FB] space-y-3">
            <div class="font-bold text-xs text-[#0071E3] flex items-center space-x-1.5">
              <span>✓</span>
              <span>映射审核完成，即将生成渠道与模型定价关联</span>
            </div>
            <div class="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span class="text-[#6E6E73]">渠道名称:</span>
                <span class="font-bold text-[#1D1D1F] ml-2">{{ form.name }}</span>
              </div>
              <div>
                <span class="text-[#6E6E73]">目标结算分组:</span>
                <span class="font-bold font-mono text-[#0071E3] ml-2">{{ probeResult.selected_group || '默认' }}</span>
              </div>
              <div>
                <span class="text-[#6E6E73]">确认收录模型数:</span>
                <span class="font-bold font-mono text-[#34C759] ml-2">{{ selectedMappingsCount }} 款</span>
              </div>
              <div>
                <span class="text-[#6E6E73]">充值折算汇率:</span>
                <span class="font-bold font-mono text-[#1D1D1F] ml-2">{{ form.recharge_rate }}x</span>
              </div>
              <div>
                <span class="text-[#6E6E73]">全局兜底模型倍率:</span>
                <span class="font-bold font-mono text-[#1D1D1F] ml-2">{{ form.default_ratio }}x ({{ (form.default_ratio * 10).toFixed(1) }}折)</span>
              </div>
            </div>
          </div>

          <!-- 即将入库的模型定价清单预览 (所见即所得) -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-[#1D1D1F]">📋 即将收录入库的模型清单 (共 {{ selectedMappings.length }} 款)</span>
              <span class="text-[11px] text-[#86868B]">仅选中的条目会写入数据库</span>
            </div>
            <div class="border border-[#E5E5EA] rounded-xl overflow-hidden max-h-[140px] overflow-y-auto">
              <table class="w-full text-left border-collapse text-[11px]">
                <thead class="bg-[#F2F2F7] text-[#6E6E73] sticky top-0 border-b border-[#E5E5EA]">
                  <tr>
                    <th class="py-1.5 px-3">渠道模型名</th>
                    <th class="py-1.5 px-3">归属分组</th>
                    <th class="py-1.5 px-3">映射标准模型</th>
                    <th class="py-1.5 px-3 text-right">折算实际单价</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E5E5EA]">
                  <tr v-for="item in selectedMappings" :key="item.item_key" class="hover:bg-[#F9F9FB]">
                    <td class="py-1.5 px-3 font-mono font-bold text-[#1D1D1F]">{{ item.channel_model_name }}</td>
                    <td class="py-1.5 px-3">
                      <span class="px-1.5 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-mono font-bold">
                        🎯 {{ item.group_name }}
                      </span>
                    </td>
                    <td class="py-1.5 px-3 font-mono text-[#0071E3] font-semibold">{{ item.standard_model_id }}</td>
                    <td class="py-1 px-2 text-right font-mono font-bold text-[#137333]">
                      {{ form.currency === 'USD' ? `$${item.input_price_usd.toFixed(3)}` : `¥${item.input_price_cny.toFixed(2)}` }} / 1M
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="space-y-2">
            <label class="block text-[#6E6E73] font-medium">全局默认模型倍率 (Default Model Ratio)</label>
            <div class="flex items-center space-x-3">
              <input
                v-model.number="form.default_ratio"
                type="number"
                step="0.05"
                min="0.01"
                max="5.0"
                class="w-32 bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
              />
              <span class="text-[#86868B] text-xs">
                (示例: 0.65 代表官方基准价的 65%，即 6.5 折)
              </span>
            </div>
          </div>

          <div class="p-3 bg-[#F2F2F7] rounded-xl text-[11px] text-[#6E6E73] space-y-1 border border-[#E5E5EA]">
            <div class="font-bold text-[#1D1D1F] flex items-center space-x-1">
              <span>💡</span>
              <span>倍率折算优先级规则：</span>
            </div>
            <div>• 优先采用第 3 步中从中转站公开接口（/api/pricing）提取或手动设定的「原生独立倍率」；</div>
            <div>• 未提供独立倍率的模型，将统一按照上述「全局默认模型倍率」进行价格折算入库。</div>
          </div>
        </div>

      </div>

      <!-- 4. 弹窗底部操作按钮条 -->
      <div class="px-6 py-4 border-t border-[#E5E5EA] bg-[#F9F9FB] flex items-center justify-between">
        <div>
          <button
            v-if="currentStep > 1"
            @click="currentStep--"
            class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] font-medium transition-all"
          >
            ◀ 上一步
          </button>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="emit('close')"
            class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] font-medium transition-all"
          >
            取消
          </button>

          <button
            v-if="currentStep < 4"
            @click="goNextStep"
            :disabled="isNextDisabled"
            class="px-5 py-2 rounded-xl text-white font-medium shadow-sm disabled:opacity-40 transition-all flex items-center space-x-1"
            :class="(form.site_type === 'siliconflow' && currentStep === 2)
              ? 'bg-[#6E29F6] hover:bg-[#5d20d8] active:bg-[#4A148C]'
              : ((form.site_type === 'aliyun_bailian' && currentStep === 2)
                ? 'bg-[#FF6A00] hover:bg-[#E65F00] active:bg-[#CC5400]'
                : 'bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4]')"
          >
            <span v-if="isSfImporting || isBailianImporting">⏳ 正在导入...</span>
            <span v-else-if="form.site_type === 'siliconflow' && currentStep === 2">🔮 确认导入到数据库</span>
            <span v-else-if="form.site_type === 'aliyun_bailian' && currentStep === 2">🟠 确认导入到数据库</span>
            <span v-else>下一步 ▶</span>
          </button>

          <button
            v-else
            @click="submitWizard"
            :disabled="isSubmitting"
            class="px-6 py-2 rounded-xl bg-[#34C759] hover:bg-[#2DB84D] active:bg-[#249D3F] text-white font-bold shadow-sm disabled:opacity-40 transition-all flex items-center space-x-1"
          >
            <span v-if="isSubmitting">⏳ 入库中...</span>
            <span v-else>🎉 完成并确认入库</span>
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import ModelSearchSelect from './ModelSearchSelect.vue'

const props = defineProps<{
  initialChannel?: any
  initialStep?: number
}>()

const emit = defineEmits(['close', 'success'])
const store = useDashboardStore()

const currentStep = ref(props.initialStep || 1)
const isProbing = ref(false)
const isSubmitting = ref(false)
const mappingFilter = ref<'all' | 'matched' | 'unmatched'>('all')

const steps = [
  { number: 1, title: '基础配置' },
  { number: 2, title: '连通探测' },
  { number: 3, title: '智能映射' },
  { number: 4, title: '费率入库' }
]

const form = reactive({
  name: props.initialChannel?.name || '',
  base_url: props.initialChannel?.base_url || '',
  site_type: props.initialChannel?.site_type || 'newapi',
  currency: props.initialChannel?.currency || 'CNY',
  recharge_rate: props.initialChannel?.recharge_rate ?? 1.0,
  default_ratio: 0.65,
  api_key: props.initialChannel?.api_key || '',
  notes: props.initialChannel?.notes || ''
})

onMounted(() => {
  if (props.initialStep === 2 && form.base_url) {
    if (form.site_type === 'siliconflow') {
      runSiliconFlowScrape()
    } else if (form.site_type === 'aliyun_bailian') {
      runBailianScrape()
    } else {
      runProbe()
    }
  }
})

const probeResult = reactive({
  is_online: false,
  status_code: 0,
  latency_ms: 0,
  raw_count: 0,
  matched_count: 0,
  unmatched_count: 0,
  fetch_source: '',
  token_group: '',
  has_special_pricing: false,
  special_pricing_count: 0,
  available_groups: [] as any[],
  selected_group: '',
  error: ''
})

const mappingsList = ref<any[]>([])
const selectedGroupFilters = ref<string[]>(['all'])
const isAddingCustomModel = ref(false)
const customModelInput = reactive({
  name: '',
  group: ''
})

function addCustomChannelModel() {
  if (!customModelInput.name.trim()) return
  const mName = customModelInput.name.trim()
  const grp = customModelInput.group || (probeResult.available_groups?.[0]?.name || 'default')
  const gRatio = probeResult.available_groups?.find(g => g.name === grp)?.ratio || 1.0
  const newItem = {
    channel_model_name: mName,
    group_name: grp,
    item_key: `${mName}::${grp}`,
    is_matched: false,
    match_type: 'unmapped',
    confidence: 0.0,
    standard_model_id: '',
    standard_model_name: '',
    provider: '',
    series: '',
    official_input_price: 2.0,
    official_output_price: 2.0,
    official_cache_price: 0.2,
    official_input_cny: 14.6,
    official_output_cny: 14.6,
    official_cache_cny: 1.46,
    custom_ratio: gRatio,
    public_ratio: 1.0,
    key_ratio: 1.0,
    has_ratio_diff: false,
    ratio_diff_percent: null,
    applied_ratio_source: 'public',
    is_selected: true,
    input_price_cny: roundNum(14.6 * gRatio * (form.recharge_rate || 1.0), 2),
    output_price_cny: roundNum(14.6 * gRatio * (form.recharge_rate || 1.0), 2),
    cache_price_cny: roundNum(1.46 * gRatio * (form.recharge_rate || 1.0), 3),
    input_price_usd: roundNum(2.0 * gRatio * (form.recharge_rate || 1.0), 3),
    output_price_usd: roundNum(2.0 * gRatio * (form.recharge_rate || 1.0), 3),
    cache_price_usd: roundNum(0.2 * gRatio * (form.recharge_rate || 1.0), 3),
    enable_groups: [grp],
    group_pricings: {}
  }
  mappingsList.value.unshift(newItem)
  customModelInput.name = ''
  isAddingCustomModel.value = false
}

const matchedMappingsCount = computed(() => filteredMappings.value.filter(m => m.is_matched).length)
const unmatchedMappingsCount = computed(() => filteredMappings.value.filter(m => !m.is_matched).length)
const selectedMappings = computed(() => mappingsList.value.filter(m => m.is_selected && m.standard_model_id))
const selectedMappingsCount = computed(() => selectedMappings.value.length)
const hasSpecialPricingInMappings = computed(() => mappingsList.value.some(m => m.has_ratio_diff))

function getGroupModelCount(gName: string) {
  return mappingsList.value.filter(m => m.group_name === gName).length
}

function toggleGroupFilter(gName: string) {
  if (gName === 'all') {
    selectedGroupFilters.value = ['all']
    return
  }
  if (selectedGroupFilters.value.includes('all')) {
    selectedGroupFilters.value = [gName]
    return
  }
  if (selectedGroupFilters.value.includes(gName)) {
    selectedGroupFilters.value = selectedGroupFilters.value.filter(g => g !== gName)
    if (selectedGroupFilters.value.length === 0) {
      selectedGroupFilters.value = ['all']
    }
  } else {
    selectedGroupFilters.value.push(gName)
  }
}

function onSelectedGroupChange() {
  const gName = probeResult.selected_group
  if (gName) {
    selectedGroupFilters.value = [gName]
  }
}

function batchApplyRatio(source: 'key' | 'public') {
  for (const m of mappingsList.value) {
    if (m.has_ratio_diff) {
      m.applied_ratio_source = source
      m.custom_ratio = source === 'key' ? m.key_ratio : m.public_ratio
    }
  }
}

const filteredMappings = computed(() => {
  let list = mappingsList.value

  // 1. 匹配状态过滤
  if (mappingFilter.value === 'matched') {
    list = list.filter(m => m.is_matched)
  } else if (mappingFilter.value === 'unmatched') {
    list = list.filter(m => !m.is_matched)
  }

  // 2. 分组多选过滤 (严格只显示选中分组的模型)
  if (!selectedGroupFilters.value.includes('all') && selectedGroupFilters.value.length > 0) {
    list = list.filter(m => selectedGroupFilters.value.includes(m.group_name))
  }

  return list
})

const isNextDisabled = computed(() => {
  if (currentStep.value === 1) {
    if (['siliconflow', 'aliyun_bailian'].includes(form.site_type)) {
      return false
    }
    return !form.name.trim() || !form.base_url.trim()
  }
  if (currentStep.value === 2) {
    if (form.site_type === 'siliconflow') {
      return isProbing.value || !sfScrapeResult.value?.models?.length || isSfImporting.value
    }
    if (form.site_type === 'aliyun_bailian') {
      return isProbing.value || !bailianScrapeResult.value?.models?.length || isBailianImporting.value
    }
    return isProbing.value || (!probeResult.is_online && mappingsList.value.length === 0)
  }
  if (currentStep.value === 3) {
    if (['siliconflow', 'aliyun_bailian'].includes(form.site_type)) {
      return isSfImporting.value || isBailianImporting.value
    }
    return selectedMappingsCount.value === 0
  }
  return false
})

async function runProbe() {
  isProbing.value = true
  probeResult.error = ''
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/channels/probe`, {
      base_url: form.base_url,
      api_key: form.api_key,
      site_type: form.site_type,
      target_group: probeResult.selected_group || undefined
    })
    probeResult.is_online = res.data.is_online
    probeResult.status_code = res.data.status_code
    probeResult.latency_ms = res.data.latency_ms
    probeResult.raw_count = res.data.raw_count
    probeResult.matched_count = res.data.matched_count
    probeResult.unmatched_count = res.data.unmatched_count
    probeResult.fetch_source = res.data.fetch_source || ''
    probeResult.token_group = res.data.token_group || ''
    probeResult.has_special_pricing = res.data.has_special_pricing || false
    probeResult.special_pricing_count = res.data.special_pricing_count || 0
    probeResult.available_groups = res.data.available_groups || []
    probeResult.selected_group = res.data.selected_group || (probeResult.available_groups[0]?.name || '')
    probeResult.error = res.data.error

    const rawList = res.data.mappings || []
    const defaultActiveGroup = probeResult.token_group || probeResult.selected_group || (probeResult.available_groups[0]?.name || '')
    
    // 精准收敛：仅将当前默认激活分组下的匹配模型初始设为 is_selected = true，其余分组模型全部设为 false
    rawList.forEach((m: any) => {
      if (defaultActiveGroup && m.group_name === defaultActiveGroup && m.standard_model_id) {
        m.is_selected = true
      } else if (!defaultActiveGroup && m.standard_model_id) {
        m.is_selected = true
      } else {
        m.is_selected = false
      }
    })
    mappingsList.value = rawList

    // 默认分组筛选器：优先绑定当前令牌所属分组，若无则默认选中目标分组
    if (probeResult.token_group) {
      selectedGroupFilters.value = [probeResult.token_group]
    } else if (probeResult.selected_group) {
      selectedGroupFilters.value = [probeResult.selected_group]
    } else {
      selectedGroupFilters.value = ['all']
    }
  } catch (e: any) {
    probeResult.is_online = false
    probeResult.fetch_source = ''
    probeResult.token_group = ''
    probeResult.has_special_pricing = false
    probeResult.special_pricing_count = 0
    probeResult.available_groups = []
    probeResult.selected_group = ''
    probeResult.error = e.response?.data?.detail || e.message || '网络连接超时'
  } finally {
    isProbing.value = false
  }
}

async function goNextStep() {
  if (currentStep.value === 1) {
    if (form.site_type === 'siliconflow') {
      if (!form.name) form.name = '硅基流动 SiliconFlow'
      if (!form.base_url) form.base_url = 'https://api.siliconflow.cn/v1'
      form.currency = 'CNY'
      currentStep.value = 2
      await runSiliconFlowScrape()
    } else if (form.site_type === 'aliyun_bailian') {
      if (!form.name) form.name = '阿里云百炼'
      if (!form.base_url) form.base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
      form.currency = 'CNY'
      currentStep.value = 2
      await runBailianScrape()
    } else {
      currentStep.value = 2
      await runProbe()
    }
  } else if (currentStep.value === 2) {
    if (form.site_type === 'siliconflow') {
      if (sfScrapeResult.value?.models?.length) importSiliconFlowData()
      return
    }
    if (form.site_type === 'aliyun_bailian') {
      if (bailianScrapeResult.value?.models?.length) importBailianData()
      return
    }
    currentStep.value = 3
  } else if (currentStep.value === 3) {
    currentStep.value = 4
  }
}

function toggleSelectAll(val: boolean) {
  filteredMappings.value.forEach(m => {
    if (m.standard_model_id) {
      m.is_selected = val
    }
  })
}

function roundNum(val: number, decimals: number): number {
  return Number(Math.round(Number(val + 'e' + decimals)) + 'e-' + decimals)
}

function onStandardModelChange(item: any) {
  if (item.standard_model_id) {
    item.is_matched = true
    item.is_selected = true
    item.match_type = 'channel_custom'
    const std = store.modelsCatalog.find(m => m.model_id.toLowerCase() === item.standard_model_id.toLowerCase())
    if (std) {
      item.standard_model_name = std.name
      item.provider = std.provider
      item.series = std.series
      item.official_input_price = std.official_input_price
      item.official_output_price = std.official_output_price
      item.official_cache_price = std.official_cache_price
      item.official_input_cny = roundNum(std.official_input_price * 7.25, 2)
      item.official_output_cny = roundNum(std.official_output_price * 7.25, 2)
      item.official_cache_cny = roundNum(std.official_cache_price * 7.25, 3)

      const ratio = item.custom_ratio !== null ? item.custom_ratio : (item.public_ratio || 1.0)
      const recharge = form.recharge_rate || 1.0
      item.input_price_usd = roundNum(std.official_input_price * ratio * recharge, 3)
      item.output_price_usd = roundNum(std.official_output_price * ratio * recharge, 3)
      item.cache_price_usd = roundNum(std.official_cache_price * ratio * recharge, 3)
      item.input_price_cny = roundNum(item.official_input_cny * ratio * recharge, 2)
      item.output_price_cny = roundNum(item.official_output_cny * ratio * recharge, 2)
      item.cache_price_cny = roundNum(item.official_cache_cny * ratio * recharge, 3)
    }
  } else {
    item.is_matched = false
    item.match_type = 'unmapped'
  }
}

async function promoteAlias(item: any) {
  try {
    await axios.post(`${store.apiUrl}/api/v1/channels/promote-alias`, {
      raw_pattern: item.channel_model_name,
      standard_model_id: item.standard_model_id,
      notes: `由向导固化的规则 (${form.name})`
    })
    item.match_type = 'global_alias'
    alert(`✓ 已将 "${item.channel_model_name}" ➔ "${item.standard_model_id}" 成功固化为全局别名规则！`)
  } catch (e: any) {
    alert(`固化失败: ${e.message}`)
  }
}

function getMatchBadgeClass(type: string) {
  switch (type) {
    case 'exact':
      return 'bg-[#E6F4EA] text-[#137333] border-[#CEEAD6]'
    case 'global_alias':
      return 'bg-[#E8F2FD] text-[#0071E3] border-[#CCE4FB] font-bold'
    case 'rule_normalized':
      return 'bg-[#F3E8FD] text-[#8E24AA] border-[#E1BEE7]'
    case 'channel_custom':
      return 'bg-[#E0F2FE] text-[#0369A1] border-[#BAE6FD]'
    case 'fuzzy':
      return 'bg-[#FEF3C7] text-[#92400E] border-[#FDE68A]'
    default:
      return 'bg-[#F2F2F7] text-[#86868B] border-[#E5E5EA]'
  }
}

function getMatchBadgeLabel(type: string) {
  switch (type) {
    case 'exact':
      return '精确匹配'
    case 'global_alias':
      return '全局别名'
    case 'rule_normalized':
      return '规则剥离'
    case 'channel_custom':
      return '自定义'
    case 'fuzzy':
      return '模糊推断'
    default:
      return '未识别'
  }
}

async function submitWizard() {
  isSubmitting.value = true
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/channels/wizard-create`, {
      site_id: props.initialChannel?.id || undefined,
      name: form.name,
      base_url: form.base_url,
      api_key: form.api_key,
      site_type: form.site_type,
      currency: form.currency,
      selected_group: probeResult.selected_group,
      recharge_rate: form.recharge_rate,
      default_ratio: form.default_ratio,
      notes: form.notes,
      mappings: mappingsList.value
    })
    if (res.data.status === 'success') {
      await store.fetchRelaySites()
      await store.fetchComparisonMatrix()
      emit('success', res.data)
      emit('close')
    }
  } catch (e: any) {
    alert(`创建渠道失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isSubmitting.value = false
  }
}

const isSyncingModelsDev = ref(false)

async function handleOneClickSync() {
  isSyncingModelsDev.value = true
  try {
    await store.triggerFullSync()
    emit('success')
    emit('close')
  } catch (e: any) {
    alert(`同步失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isSyncingModelsDev.value = false
  }
}

async function handleOneClickSiliconFlow() {
  // 自动填充硅基流动字段
  form.site_type = 'siliconflow'
  form.name = '硅基流动 SiliconFlow'
  form.base_url = 'https://api.siliconflow.cn/v1'
  form.currency = 'CNY'
  form.notes = '硅基流动推理平台 · 从官网定价页自动爬取'
  form.api_key = ''
  // 跳转到 Step 2 并自动开始爬取
  currentStep.value = 2
  await runSiliconFlowScrape()
}

// ==================== 硅基流动 SiliconFlow 爬取相关 ====================
const sfScrapeResult = ref<any>(null)
const sfScrapeError = ref('')
const isSfImporting = ref(false)

async function runSiliconFlowScrape() {
  isProbing.value = true
  sfScrapeResult.value = null
  sfScrapeError.value = ''
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/channels/scrape-siliconflow`)
    sfScrapeResult.value = res.data
  } catch (e: any) {
    sfScrapeError.value = e.response?.data?.detail || e.message || '爬取失败，请检查网络连接'
  } finally {
    isProbing.value = false
  }
}

async function importSiliconFlowData() {
  if (!sfScrapeResult.value?.models?.length) return
  isSfImporting.value = true
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/channels/import-siliconflow`, {
      models: sfScrapeResult.value.models,
      site_id: props.initialChannel?.id || undefined
    })
    const result = res.data
    alert(`✅ 硅基流动数据导入成功！\n\n` +
      `渠道: ${result.site_name}\n` +
      `总导入模型: ${result.total_imported} 个\n` +
      `新建模型: ${result.new_models_created} 个\n` +
      `更新价格: ${result.prices_updated} 条\n` +
      `新建价格: ${result.prices_created} 条`
    )
    emit('success')
    emit('close')
  } catch (e: any) {
    alert(`导入失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isSfImporting.value = false
  }
}

// ==================== 阿里百炼 Aliyun Model Studio 爬取相关 ====================
const bailianScrapeResult = ref<any>(null)
const bailianScrapeError = ref('')
const isBailianImporting = ref(false)

async function handleOneClickBailian() {
  form.site_type = 'aliyun_bailian'
  form.name = '阿里百炼 (Model Studio)'
  form.base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
  form.currency = 'CNY'
  form.notes = '阿里百炼大模型服务平台 · 自动抓取官方定价'
  form.api_key = ''
  currentStep.value = 2
  await runBailianScrape()
}

async function runBailianScrape() {
  isProbing.value = true
  bailianScrapeResult.value = null
  bailianScrapeError.value = ''
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/channels/scrape-bailian`)
    bailianScrapeResult.value = res.data
  } catch (e: any) {
    bailianScrapeError.value = e.response?.data?.detail || e.message || '抓取失败，请检查网络连接'
  } finally {
    isProbing.value = false
  }
}

async function importBailianData() {
  if (!bailianScrapeResult.value?.models?.length) return
  isBailianImporting.value = true
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/channels/import-bailian`, {
      models: bailianScrapeResult.value.models,
      site_id: props.initialChannel?.id || undefined
    })
    const result = res.data
    alert(`✅ 阿里百炼数据导入成功！\n\n` +
      `渠道: ${result.site_name}\n` +
      `总导入模型规格: ${result.total_imported} 个\n` +
      `新建模型: ${result.new_models_created} 个\n` +
      `更新价格: ${result.prices_updated} 条\n` +
      `新建价格: ${result.prices_created} 条`
    )
    emit('success')
    emit('close')
  } catch (e: any) {
    alert(`导入失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    isBailianImporting.value = false
  }
}

// 监听 site_type 变化，自动填充硅基流动或阿里百炼字段
watch(() => form.site_type, (newVal) => {
  if (newVal === 'siliconflow') {
    form.name = '硅基流动 SiliconFlow'
    form.base_url = 'https://api.siliconflow.cn/v1'
    form.currency = 'CNY'
    form.notes = '硅基流动推理平台 · 从官网定价页自动爬取'
    form.api_key = ''
  } else if (newVal === 'aliyun_bailian') {
    form.name = '阿里百炼 (Model Studio)'
    form.base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    form.currency = 'CNY'
    form.notes = '阿里百炼大模型服务平台 · 自动抓取官方定价'
    form.api_key = ''
  }
})
</script>

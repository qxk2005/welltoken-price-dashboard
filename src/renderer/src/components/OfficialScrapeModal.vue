<template>
  <div
    v-if="store.scrapeModalVisible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs select-none p-4"
    @click.self="store.scrapeModalVisible = false"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl border border-[#E5E5EA] w-full max-w-lg overflow-hidden animate-scale-up"
    >
      <!-- 模态框标题 -->
      <div class="px-5 py-4 border-b border-[#E5E5EA] flex items-center justify-between bg-[#FBFBFD]">
        <div class="flex items-center space-x-2">
          <div class="w-6 h-6 rounded-lg bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center font-bold">
            <SystemIcon name="refresh" custom-class="w-3.5 h-3.5" />
          </div>
          <h3 class="text-sm font-bold text-[#1D1D1F]">官网实时抓取与更新配置</h3>
        </div>
        <button
          @click="store.scrapeModalVisible = false"
          :disabled="store.isScraping"
          class="w-6 h-6 rounded-lg hover:bg-[#F2F2F7] text-[#86868B] hover:text-[#1D1D1F] flex items-center justify-center transition-all cursor-pointer disabled:opacity-30"
        >
          ✕
        </button>
      </div>

      <div class="p-5 space-y-4">
        <!-- 抓取运行提示 -->
        <div class="p-3 bg-[#F2F7FF] border border-[#0071E3]/20 rounded-xl text-xs text-[#0071E3] space-y-1">
          <div class="font-bold flex items-center space-x-1.5">
            <span>💡</span>
            <span>官方模型价格对账保障</span>
          </div>
          <div class="text-[#48484A] leading-relaxed">
            系统已内置经过权威校验的 9 大官网全部最新模型基准价与静态快照。若官网有新品发布或调价，您可在此一键发起全新实时抓取。抓取时将自动生成完整 HTML 快照文件以备对账。
          </div>
        </div>

        <!-- 代理设置 -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold text-[#48484A] flex items-center justify-between">
            <span>抓取网络代理 (HTTP / SOCKS5)</span>
            <span class="text-[11px] text-[#86868B] font-normal">访问境外官网 (OpenAI/Claude/Gemini) 建议配置</span>
          </label>
          <input
            type="text"
            v-model="store.customProxy"
            placeholder="留空自动继承系统环境变量，或填入如: http://127.0.0.1:7890"
            class="w-full px-3 py-2 bg-[#F2F2F7] border border-[#E5E5EA] rounded-xl text-xs text-[#1D1D1F] focus:bg-white focus:border-[#0071E3] focus:outline-none transition-all font-mono"
          />
        </div>

        <!-- 抓取状态展示 -->
        <div v-if="store.isScraping" class="p-3.5 bg-[#FFF9E6] border border-[#FFE082] rounded-xl text-xs text-[#8D6E00] flex items-center space-x-2 animate-pulse">
          <span class="w-2 h-2 rounded-full bg-[#FF9500] animate-ping"></span>
          <span class="font-medium">正在启动无头浏览器自动化抓取并解析... 请稍候</span>
        </div>

        <!-- 单厂商独立抓取网格 -->
        <div class="space-y-2">
          <div class="text-xs font-semibold text-[#48484A]">单个厂商独立重新抓取:</div>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="target in targets"
              :key="target.key"
              @click="handleScrapeSingle(target.key)"
              :disabled="store.isScraping"
              class="px-3 py-2 rounded-xl border border-[#E5E5EA] bg-[#F9F9FB] hover:bg-[#E8F2FD] hover:border-[#0071E3]/40 text-xs text-[#1D1D1F] flex items-center justify-between transition-all cursor-pointer disabled:opacity-50 group"
            >
              <div class="flex items-center space-x-2">
                <span class="w-1.5 h-1.5 rounded-full bg-[#0071E3]"></span>
                <span class="font-medium">{{ target.name }}</span>
              </div>
              <span class="text-[11px] text-[#86868B] group-hover:text-[#0071E3]">更新 ➔</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="px-5 py-3.5 border-t border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between">
        <span class="text-[11px] text-[#86868B]">
          当前收录: <strong class="text-[#1D1D1F] font-mono">{{ store.allModels.length }}</strong> 条官方规格
        </span>
        <div class="flex items-center space-x-2">
          <button
            @click="store.scrapeModalVisible = false"
            :disabled="store.isScraping"
            class="px-3 py-1.5 rounded-xl border border-[#E5E5EA] hover:bg-[#F2F2F7] text-[#6E6E73] text-xs font-medium transition-all cursor-pointer disabled:opacity-50"
          >
            取消
          </button>
          <button
            @click="handleScrapeAll"
            :disabled="store.isScraping"
            class="px-4 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-bold transition-all shadow-sm cursor-pointer disabled:opacity-50 flex items-center space-x-1.5"
          >
            <SystemIcon name="refresh" custom-class="w-3 h-3" :class="store.isScraping ? 'animate-spin' : ''" />
            <span>{{ store.isScraping ? '正在全网抓取...' : '一键抓取全部 10 家' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useOfficialPricingStore } from '../stores/officialPricingStore'
import SystemIcon from './SystemIcon.vue'

const store = useOfficialPricingStore()

const targets = [
  { key: 'deepseek', name: 'DeepSeek 深度求索' },
  { key: 'glm', name: '智谱 GLM' },
  { key: 'kimi', name: 'Moonshot Kimi' },
  { key: 'minimax', name: 'MiniMax 稀宇' },
  { key: 'bailian', name: '阿里百炼千问' },
  { key: 'xiaomi', name: '小米 (MiMo)' },
  { key: 'stepfun', name: '阶跃星辰 (StepFun)' },
  { key: 'openai', name: 'OpenAI' },
  { key: 'claude', name: 'Anthropic Claude' },
  { key: 'gemini', name: 'Google Gemini' }
]

async function handleScrapeAll() {
  try {
    await store.triggerScrape('all')
    store.scrapeModalVisible = false
  } catch (e: any) {
    alert(`全量抓取异常: ${e?.response?.data?.detail || e.message}`)
  }
}

async function handleScrapeSingle(key: string) {
  try {
    await store.triggerScrape(key)
    store.scrapeModalVisible = false
  } catch (e: any) {
    alert(`抓取 ${key} 异常: ${e?.response?.data?.detail || e.message}`)
  }
}
</script>

<style scoped>
@keyframes scaleUp {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
.animate-scale-up {
  animation: scaleUp 0.15s ease-out forwards;
}
</style>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import Navbar from './components/Navbar.vue'
import EssayEditor from './components/EssayEditor.vue'
import EvaluatingModal from './components/EvaluatingModal.vue'
import ScoreOverview from './components/ScoreOverview.vue'
import DimensionScores from './components/DimensionScores.vue'
import HighlightsAndDeductions from './components/HighlightsAndDeductions.vue'
import ErrorDiagnostics from './components/ErrorDiagnostics.vue'
import PolishedEssay from './components/PolishedEssay.vue'
import HistoryDrawer from './components/HistoryDrawer.vue'
import ModelSettingsModal from './components/ModelSettingsModal.vue'
import PastEssaysLibraryModal from './components/PastEssaysLibraryModal.vue'

const STORAGE_KEY = 'english_two_llm_config'

function getDefaultProviders() {
  return {
    deepseek: {
      modelName: 'deepseek-chat',
      apiKey: '',
      baseUrl: 'https://api.deepseek.com'
    },
    qwen: {
      modelName: 'qwen-plus',
      apiKey: '',
      baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    },
    moonshot: {
      modelName: 'moonshot-v1-8k',
      apiKey: '',
      baseUrl: 'https://api.moonshot.cn/v1'
    },
    zhipu: {
      modelName: 'glm-4-flash',
      apiKey: '',
      baseUrl: 'https://open.bigmodel.cn/api/paas/v4'
    },
    ollama: {
      modelName: 'qwen2.5:7b',
      apiKey: '',
      baseUrl: 'http://localhost:11434/v1'
    },
    custom: {
      modelName: '',
      apiKey: '',
      baseUrl: ''
    }
  }
}

// 加载大模型配置
function loadLlmConfig() {
  const defaultProviders = getDefaultProviders()
  try {
    const cached = localStorage.getItem(STORAGE_KEY)
    if (cached) {
      const parsed = JSON.parse(cached)
      if (parsed && typeof parsed === 'object') {
        const mergedProviders = { ...defaultProviders }
        if (parsed.providers && typeof parsed.providers === 'object') {
          for (const key of Object.keys(defaultProviders)) {
            if (parsed.providers[key]) {
              mergedProviders[key] = {
                modelName: parsed.providers[key].modelName !== undefined ? parsed.providers[key].modelName : defaultProviders[key].modelName,
                apiKey: parsed.providers[key].apiKey || '',
                baseUrl: parsed.providers[key].baseUrl !== undefined ? parsed.providers[key].baseUrl : defaultProviders[key].baseUrl
              }
            }
          }
          for (const [k, v] of Object.entries(parsed.providers)) {
            if (!mergedProviders[k] && v) {
              mergedProviders[k] = { ...v }
            }
          }
        }
        const activeProviderId = parsed.activeProviderId || 'deepseek'
        const active = mergedProviders[activeProviderId] || mergedProviders.deepseek
        return {
          activeProviderId,
          providers: mergedProviders,
          providerId: activeProviderId,
          modelName: active.modelName || 'deepseek-chat',
          apiKey: active.apiKey || '',
          baseUrl: active.baseUrl || 'https://api.deepseek.com',
          isCustom: activeProviderId !== 'deepseek' || Boolean(active.apiKey) || active.modelName !== 'deepseek-chat'
        }
      }
    }
  } catch (e) {
    console.error('Failed to load llm config:', e)
  }

  return {
    activeProviderId: 'deepseek',
    providers: defaultProviders,
    providerId: 'deepseek',
    modelName: 'deepseek-chat',
    apiKey: '',
    baseUrl: 'https://api.deepseek.com',
    isCustom: false
  }
}

// 持久化保存配置
function persistLlmConfig(activeProviderId, providers) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      activeProviderId,
      providers
    }))
  } catch (e) {
    console.error('Failed to persist llm config:', e)
  }
}

// 核心交互与弹窗显隐状态
const showModelSettings = ref(false)
const showHistory = ref(false)
const showLibraryModal = ref(false)
const activeMarkdownModal = ref(null)

// 业务数据与评卷状态
const examCategory = ref('英语一') // '英语一' | '英语二'
const systemStatus = ref({ status: 'checking', milvus: {}, models: {} })
const pastTopics = ref({ small_essays: [], big_essays: [] })
const historyReports = ref([])
const evaluationResult = ref(null)
const currentOriginalEssay = ref('')
const loading = ref(false)
const errorMessage = ref('')
const editorRef = ref(null)

function handleSwitchExamCategory(cat) {
  if (!cat || examCategory.value === cat) return
  examCategory.value = cat
  fetchTopics()
}

// 初始加载大模型配置
const llmConfig = ref(loadLlmConfig())
const targetProviderId = ref('deepseek')

const providerDisplayNames = {
  deepseek: 'DeepSeek',
  qwen: '通义千问',
  moonshot: '月之暗面',
  zhipu: '智谱清言',
  ollama: 'Ollama',
  custom: '自定义'
}

const currentProviderName = computed(() => {
  const pId = llmConfig.value.activeProviderId || llmConfig.value.providerId || 'deepseek'
  return providerDisplayNames[pId] || 'DeepSeek'
})

function openModelSettings(providerId = '') {
  targetProviderId.value = providerId || llmConfig.value.activeProviderId || 'deepseek'
  showModelSettings.value = true
}

// 快速切换当前生效的服务商
function handleQuickSwitchProvider(providerId) {
  if (!providerId) return
  const defaultProviders = getDefaultProviders()
  const providers = llmConfig.value.providers || defaultProviders
  const target = providers[providerId] || defaultProviders[providerId] || { modelName: '', apiKey: '', baseUrl: '' }

  llmConfig.value = {
    ...llmConfig.value,
    activeProviderId: providerId,
    providerId: providerId,
    modelName: target.modelName || defaultProviders[providerId]?.modelName || 'deepseek-chat',
    apiKey: target.apiKey || '',
    baseUrl: target.baseUrl || defaultProviders[providerId]?.baseUrl || 'https://api.deepseek.com',
    isCustom: providerId !== 'deepseek' || Boolean(target.apiKey)
  }

  persistLlmConfig(providerId, llmConfig.value.providers)

  const needsKey = providerId !== 'ollama' && (!target.apiKey || !target.apiKey.trim())
  if (needsKey && providerId !== 'deepseek') {
    errorMessage.value = `已切换至【${providerDisplayNames[providerId] || providerId}】。系统严格隔离密钥，检测到尚未配置该厂商的专属 API Key，请在弹窗中填入专属密钥以正常评卷。`
    openModelSettings(providerId)
  } else {
    errorMessage.value = ''
  }
}

function handleSaveLlmConfig(payload) {
  const activeProviderId = payload.activeProviderId || 'deepseek'
  const currentConfig = payload.currentConfig || {}
  const providers = payload.providers || llmConfig.value.providers || getDefaultProviders()

  llmConfig.value = {
    activeProviderId,
    providers,
    providerId: activeProviderId,
    modelName: currentConfig.modelName || 'deepseek-chat',
    apiKey: currentConfig.apiKey || '',
    baseUrl: currentConfig.baseUrl || 'https://api.deepseek.com',
    isCustom: Boolean(currentConfig.isCustom)
  }

  persistLlmConfig(activeProviderId, providers)
  showModelSettings.value = false
}

// 页面加载时拉取系统状态、真题列表与历史归档
onMounted(() => {
  fetchStatus()
  fetchTopics()
  fetchReports()
})

async function fetchStatus() {
  try {
    const res = await fetch('/api/status')
    if (res.ok) {
      systemStatus.value = await res.json()
    }
  } catch (err) {
    console.error('获取系统状态失败:', err)
  }
}

async function fetchTopics() {
  try {
    const res = await fetch(`/api/topics?exam_category=${encodeURIComponent(examCategory.value)}`)
    if (res.ok) {
      pastTopics.value = await res.json()
    }
  } catch (err) {
    console.error('获取真题列表失败:', err)
  }
}

async function fetchReports() {
  try {
    const res = await fetch('/api/reports')
    if (res.ok) {
      historyReports.value = await res.json()
    }
  } catch (err) {
    console.error('获取报告列表失败:', err)
  }
}

// 执行评卷
async function handleEvaluate({ essay_text, prompt_topic, essay_type }) {
  errorMessage.value = ''

  // 严格保护 .env 私人财产：云端大模型必须由用户显式提供 API Key，严禁默认借用服务端的 .env
  const activeBaseUrl = llmConfig.value.baseUrl || 'https://api.deepseek.com'
  const isLocal = activeBaseUrl.includes('localhost') || activeBaseUrl.includes('127.0.0.1')
  if (!isLocal && !llmConfig.value.apiKey?.trim()) {
    errorMessage.value = `评卷未启动：当前评卷模型【${llmConfig.value.modelName || 'DeepSeek'}】尚未配置 API Key！请在弹出窗口中填入您自己的专属 API Key。`
    showModelSettings.value = true
    return
  }

  loading.value = true
  currentOriginalEssay.value = essay_text

  try {
    const payload = {
      essay_text,
      prompt_topic,
      essay_type,
      exam_category: examCategory.value,
      llm_config: {
        api_key: llmConfig.value.apiKey || '',
        base_url: llmConfig.value.baseUrl || 'https://api.deepseek.com',
        model_name: llmConfig.value.modelName || 'deepseek-chat'
      }
    }

    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.error || '评卷请求失败')
    }

    const data = await res.json()
    evaluationResult.value = data

    // 重新拉取历史记录
    fetchReports()

    // 滚动至结果区域
    nextTick(() => {
      const resultsEl = document.getElementById('results-anchor')
      if (resultsEl) {
        resultsEl.scrollIntoView({ behavior: 'smooth' })
      }
    })
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    loading.value = false
  }
}

// 查阅历史报告
async function openReportDetail(filename) {
  try {
    const res = await fetch(`/api/report/${encodeURIComponent(filename)}`)
    if (res.ok) {
      const data = await res.json()
      activeMarkdownModal.value = {
        filename,
        html: marked.parse(data.content)
      }
      showHistory.value = false
    }
  } catch (err) {
    console.error('读取报告失败:', err)
  }
}

// 接收来自文库的一键填入真题与范文
function handleUseLibraryEssay({ type, topic, text, exam_category }) {
  if (exam_category && exam_category !== examCategory.value) {
    examCategory.value = exam_category
    fetchTopics()
  }
  if (editorRef.value) {
    editorRef.value.fillContent({
      type,
      topic,
      text
    })
  }
  // 平滑滚动至编辑器区域
  nextTick(() => {
    const editorEl = document.querySelector('.editor-card')
    if (editorEl) {
      editorEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}
</script>

<template>
  <div class="app-layout">
    <!-- 顶部导航 -->
    <Navbar
      :system-status="systemStatus"
      :current-model-name="llmConfig.modelName || 'deepseek-chat'"
      :current-provider-name="currentProviderName"
      :is-custom-model="Boolean(llmConfig.isCustom)"
      :exam-category="examCategory"
      @switch-exam-category="handleSwitchExamCategory"
      @open-history="showHistory = true"
      @open-model-settings="openModelSettings(llmConfig.activeProviderId)"
      @open-library="showLibraryModal = true"
    />

    <!-- 英雄区域：标语 -->
    <section class="hero-section">
      <div class="hero-inner">
        <div class="hero-eyebrow">
          考研{{ examCategory }}写作
        </div>
        <h2 class="hero-headline">
          智能作文评卷
        </h2>
        <p class="hero-body">
          {{ examCategory === '英语一' ? '大纲标准细化 · 图画大作文20分 / 应用文10分 · 逐句语病精修 · 高分示范升格' : '大纲标准细化 · 图表大作文15分 / 应用文10分 · 逐句语病精修 · 高分示范升格' }}
        </p>
      </div>
      <!-- 底部过渡曲线 -->
      <div class="hero-fade"></div>
    </section>

    <!-- 主体内容容器 -->
    <main class="main-content">
      <!-- 错误警告提示 -->
      <div v-if="errorMessage" class="error-banner animate-fade-in">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <span>{{ errorMessage }}</span>
        <button class="close-err" @click="errorMessage = ''">✕</button>
      </div>

      <!-- 作文编辑与提交区域 -->
      <EssayEditor
        ref="editorRef"
        :loading="loading"
        :past-topics="pastTopics"
        :exam-category="examCategory"
        :current-model-name="llmConfig.modelName || 'deepseek-chat'"
        :current-provider-name="currentProviderName"
        :active-provider-id="llmConfig.activeProviderId || 'deepseek'"
        :is-custom-model="Boolean(llmConfig.isCustom)"
        :providers-map="llmConfig.providers || {}"
        @evaluate="handleEvaluate"
        @switch-provider="handleQuickSwitchProvider"
        @open-model-settings="openModelSettings"
        @open-library="showLibraryModal = true"
      />

      <!-- 评卷中动效弹窗 -->
      <EvaluatingModal v-if="loading" />

      <!-- 评卷结果展示区域 -->
      <div id="results-anchor" v-if="evaluationResult" class="results-container animate-fade-in">
        <div class="results-header-divider">
          <span class="divider-line"></span>
          <span class="divider-text">评 卷 结 果 报 告</span>
          <span class="divider-line"></span>
        </div>

        <!-- 1. 得分总览卡片 -->
        <ScoreOverview :result="evaluationResult" />

        <!-- 2. 四大核心维度量化剖析 -->
        <DimensionScores :dimensions="evaluationResult.dimensions" />

        <!-- 3. 扣分规则、亮点表达与提分建议 -->
        <HighlightsAndDeductions
          :deductions="evaluationResult.deductions"
          :highlights="evaluationResult.highlights"
          :suggestions="evaluationResult.study_suggestions"
        />

        <!-- 4. 逐句语病与语法精细化诊断 -->
        <ErrorDiagnostics :errors="evaluationResult.error_diagnostics" />

        <!-- 5. 第五档高分升格示范范文 -->
        <PolishedEssay
          :original-essay="currentOriginalEssay"
          :polished-essay="evaluationResult.polished_essay"
        />
      </div>
    </main>

    <!-- 历史记录侧边抽屉 -->
    <HistoryDrawer
      :show="showHistory"
      :reports="historyReports"
      @close="showHistory = false"
      @select-report="openReportDetail"
    />

    <!-- 查看原始 Markdown 报告弹窗 -->
    <div
      v-if="activeMarkdownModal"
      class="report-modal-backdrop"
      @click.self="activeMarkdownModal = null"
    >
      <div class="report-modal-card animate-fade-in-scale">
        <div class="modal-bar">
          <h4>{{ activeMarkdownModal.filename }}</h4>
          <button class="close-modal-btn" @click="activeMarkdownModal = null">✕</button>
        </div>
        <div class="modal-html-body" v-html="activeMarkdownModal.html"></div>
      </div>
    </div>

    <!-- 大模型自定义配置弹窗 -->
    <ModelSettingsModal
      :show="showModelSettings"
      :target-provider-id="targetProviderId"
      :current-config="llmConfig"
      @close="showModelSettings = false"
      @save="handleSaveLlmConfig"
    />

    <!-- 历年真题与高分标杆范文库全屏研读弹窗 -->
    <PastEssaysLibraryModal
      :show="showLibraryModal"
      :current-exam-category="examCategory"
      @close="showLibraryModal = false"
      @use-essay="handleUseLibraryEssay"
    />
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── Hero Section ── */
.hero-section {
  background: var(--ink);
  padding: 3.5rem 1.5rem 4.5rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}

/* Subtle radial glow behind headline */
.hero-section::before {
  content: '';
  position: absolute;
  top: -60%;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(232, 168, 56, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.hero-inner {
  position: relative;
  max-width: 680px;
  margin: 0 auto;
}

.hero-eyebrow {
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--amber);
  letter-spacing: 0.06em;
  margin-bottom: 1rem;
  opacity: 0.9;
}

.hero-headline {
  font-size: 2.6rem;
  font-weight: 800;
  color: var(--paper);
  line-height: 1.15;
  letter-spacing: -0.03em;
  margin-bottom: 1rem;
}

.hero-body {
  font-size: 0.95rem;
  color: var(--text-on-dark-muted);
  line-height: 1.65;
  max-width: 520px;
  margin: 0 auto;
}

.hero-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(to bottom, transparent, var(--paper));
  pointer-events: none;
}

/* ── Main Content ── */
.main-content {
  flex: 1;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}

/* ── Error Banner ── */
.error-banner {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  background: var(--danger-light);
  border: 1px solid var(--danger-border);
  color: var(--danger);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
  font-weight: 600;
  font-size: 0.88rem;
}

.close-err {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--danger);
  cursor: pointer;
  font-weight: 700;
  font-size: 1rem;
  line-height: 1;
  padding: 0 0.25rem;
}

/* ── Results Divider ── */
.results-header-divider {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  margin: 3rem 0 2rem;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #d5d0c7, transparent);
}

.divider-text {
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: 0.15em;
  background: var(--amber-subtle);
  padding: 0.4rem 1.25rem;
  border-radius: var(--radius-full);
  border: 1px solid rgba(232, 168, 56, 0.2);
}

/* ── Report Modal ── */
.report-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(12, 18, 34, 0.65);
  backdrop-filter: blur(6px);
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.report-modal-card {
  background: var(--paper-warm);
  border-radius: var(--radius-lg);
  max-width: 900px;
  width: 100%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
  border: 1px solid rgba(12, 18, 34, 0.08);
}

.modal-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(12, 18, 34, 0.08);
}

.modal-bar h4 {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-ink);
}

.close-modal-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--text-muted);
  transition: color 0.15s;
}

.close-modal-btn:hover {
  color: var(--text-ink);
}

.modal-html-body {
  padding: 1.5rem;
  overflow-y: auto;
  font-size: 0.92rem;
  line-height: 1.7;
  color: var(--text-body);
}

.modal-html-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.modal-html-body th, .modal-html-body td {
  border: 1px solid #d5d0c7;
  padding: 0.6rem 0.8rem;
}

.modal-html-body th {
  background: var(--paper-cool);
  font-weight: 600;
}

@media (max-width: 768px) {
  .hero-headline {
    font-size: 1.85rem;
  }
  .main-content {
    padding: 1.5rem 1rem 3rem;
  }
}
</style>

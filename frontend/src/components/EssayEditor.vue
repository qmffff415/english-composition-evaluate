<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  loading: Boolean,
  pastTopics: {
    type: Object,
    default: () => ({ small_essays: [], big_essays: [] })
  },
  currentModelName: {
    type: String,
    default: 'deepseek-chat'
  },
  currentProviderName: {
    type: String,
    default: 'DeepSeek'
  },
  activeProviderId: {
    type: String,
    default: 'deepseek'
  },
  isCustomModel: {
    type: Boolean,
    default: false
  },
  providersMap: {
    type: Object,
    default: () => ({})
  },
  examCategory: {
    type: String,
    default: '英语一'
  }
})

const emit = defineEmits([
  'evaluate',
  'openModelSettings',
  'openLibrary',
  'switchProvider'
])

// 6大预设大模型服务商清单（始终常驻前端，一目了然）
const PROVIDER_LIST = [
  {
    id: 'deepseek',
    name: 'DeepSeek',
    sub: '深度求索',
    tag: '高性价比',
    iconType: 'sparkles',
    defaultModel: 'deepseek-chat'
  },
  {
    id: 'qwen',
    name: '通义千问',
    sub: '阿里云',
    tag: '中文理解',
    iconType: 'cloud',
    defaultModel: 'qwen-plus'
  },
  {
    id: 'moonshot',
    name: '月之暗面',
    sub: 'Kimi',
    tag: '长文逻辑',
    iconType: 'moon',
    defaultModel: 'moonshot-v1-8k'
  },
  {
    id: 'zhipu',
    name: '智谱清言',
    sub: 'GLM-4',
    tag: '国产基座',
    iconType: 'cpu',
    defaultModel: 'glm-4-flash'
  },
  {
    id: 'ollama',
    name: '本地部署',
    sub: 'Ollama',
    tag: '离线私有',
    iconType: 'terminal',
    defaultModel: 'qwen2.5:7b'
  },
  {
    id: 'custom',
    name: '自定义端点',
    sub: 'Custom',
    tag: '通用兼容',
    iconType: 'sliders',
    defaultModel: '自选模型'
  }
]

// 检查某个服务商是否已在本地配置专属 Key 或专属地址
function isProviderConfigured(pId) {
  const conf = props.providersMap?.[pId]
  if (!conf) return false
  if (pId === 'ollama') {
    return Boolean(conf.baseUrl && conf.baseUrl !== 'http://localhost:11434/v1') ||
           Boolean(conf.modelName && conf.modelName !== 'qwen2.5:7b')
  }
  return Boolean(conf.apiKey && conf.apiKey.trim())
}

// 获取各服务商当前设定的具体模型名称
function getProviderModelName(p) {
  const conf = props.providersMap?.[p.id]
  if (conf?.modelName && conf.modelName.trim()) {
    return conf.modelName.trim()
  }
  return p.defaultModel
}

function handleSelectProvider(providerId) {
  emit('switchProvider', providerId)
}

const essayType = ref('小作文')
const promptTopic = ref('')
const essayText = ref('')

// 计算词数（严格遵循考研大纲要求：标点符号不计算在内，连字符与缩写计为一个词）
const wordCount = computed(() => {
  if (!essayText.value.trim()) return 0
  const matches = essayText.value.match(/\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b/g)
  return matches ? matches.length : 0
})

// 小作文篇章格式与段落结构智能解析
const essayStructure = computed(() => {
  const text = essayText.value.trim()
  if (!text) {
    return {
      bodyParagraphs: [],
      bodyParagraphCount: 0,
      totalParagraphCount: 0,
      isLetter: false,
      salutation: '',
      signOff: '',
      signature: '',
      bodyWordCount: 0
    }
  }

  const rawBlocks = text.split('\n').map(p => p.trim()).filter(p => p.length > 0)
  if (essayType.value !== '小作文') {
    return {
      bodyParagraphs: rawBlocks,
      bodyParagraphCount: rawBlocks.length,
      totalParagraphCount: rawBlocks.length,
      isLetter: false,
      salutation: '',
      signOff: '',
      signature: '',
      bodyWordCount: wordCount.value
    }
  }

  const lines = [...rawBlocks]
  let salutation = ''
  let signOff = ''
  let signature = ''

  // 1. 识别称呼
  if (lines.length > 0) {
    const firstLine = lines[0]
    const salutationRegex = /^(dear\b|to\s+whom|to:\s*|hello\b|hi\b)/i
    if (salutationRegex.test(firstLine) || (firstLine.split(/\s+/).length <= 6 && /[,:]$/.test(firstLine))) {
      salutation = lines.shift()
    } else if (['NOTICE', 'ANNOUNCEMENT', 'MEMO', 'MEMORANDUM'].includes(firstLine.toUpperCase())) {
      salutation = lines.shift()
    }
  }

  // 2. 识别结尾敬辞与落款署名
  const signOffRegex = /^(yours\s+(sincerely|faithfully|truly|affectionately|warmly|respectfully)|sincerely\s+yours|sincerely|best\s+regards|warm\s+regards|with\s+(best|warm|kind)\s+wishes|yours)[,.]?$/i
  const combinedRegex = /^(yours\s+(?:sincerely|faithfully|truly|respectfully)|sincerely\s+yours|sincerely)[,\s]+(li\s*ming|[\w\s]+)$/i

  if (lines.length >= 1 && combinedRegex.test(lines[lines.length - 1])) {
    const m = lines[lines.length - 1].match(combinedRegex)
    signOff = m[1]
    signature = m[2]
    lines.pop()
  } else if (lines.length >= 2 && signOffRegex.test(lines[lines.length - 2])) {
    signature = lines.pop()
    signOff = lines.pop()
  } else if (lines.length >= 1 && signOffRegex.test(lines[lines.length - 1])) {
    signOff = lines.pop()
  } else if (lines.length >= 1 && lines[lines.length - 1].split(/\s+/).length <= 4) {
    const lastLower = lines[lines.length - 1].toLowerCase()
    if (['li ming', 'liming', 'union', 'association', 'committee', 'secretary'].some(k => lastLower.includes(k))) {
      signature = lines.pop()
    }
  }

  const bodyText = lines.join(' ')
  const bodyMatches = bodyText.match(/\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b/g)
  const bodyWordCount = bodyMatches ? bodyMatches.length : 0

  return {
    bodyParagraphs: lines,
    bodyParagraphCount: lines.length,
    totalParagraphCount: rawBlocks.length,
    isLetter: Boolean(salutation || signOff || signature),
    salutation,
    signOff,
    signature,
    bodyWordCount
  }
})

// 计算段落数（小作文书信格式自动剥离称呼与落款，仅计正文主体段落）
const paragraphCount = computed(() => {
  if (essayType.value === '小作文' && essayStructure.value.isLetter) {
    return essayStructure.value.bodyParagraphCount
  }
  return essayStructure.value.totalParagraphCount
})

// 词数达标状态判断（依据考研大纲要求，支持英语一与英语二）
const wordCountStatus = computed(() => {
  const count = wordCount.value
  const isEng1 = props.examCategory === '英语一'

  if (essayType.value === '小作文') {
    if (count === 0) return { text: '待输入 (大纲要求约100词)', color: 'muted' }
    if (count < 80) return { text: '严重不足 (<80词 扣1-2分)', color: 'danger' }
    if (count < 100) return { text: '词数偏少 (建议100-120词)', color: 'warning' }
    if (count <= 135) return { text: '区间达标 (100-130词最佳)', color: 'success' }
    return { text: '篇幅偏长 (>135词 建议精炼)', color: 'warning' }
  } else {
    if (isEng1) {
      if (count === 0) return { text: '待输入 (英语一大纲要求160-200词)', color: 'muted' }
      if (count < 120) return { text: '严重不足 (<120词 扣4-5分)', color: 'danger' }
      if (count < 160) return { text: '低于底线 (<160词 扣1-2分)', color: 'warning' }
      if (count <= 220) return { text: '区间达标 (180-220词最佳)', color: 'success' }
      return { text: '篇幅偏长 (>220词 建议精炼)', color: 'warning' }
    } else {
      if (count === 0) return { text: '待输入 (英语二大纲要求约150词)', color: 'muted' }
      if (count < 130) return { text: '严重不足 (<130词 扣2-3分)', color: 'danger' }
      if (count < 150) return { text: '低于底线 (扣0.5-1分)', color: 'warning' }
      if (count <= 190) return { text: '区间达标 (150-180词最佳)', color: 'success' }
      return { text: '篇幅偏长 (>190词 建议精炼)', color: 'warning' }
    }
  }
})

function setType(type) {
  essayType.value = type
}

function formatTopicValue(item) {
  if (!item) return ''
  const year = item.year ? `${item.year}年` : ''
  const category = item.sub_type || item.chart_type || item.type || ''
  const header = category ? `【${year}${item.type || '真题'} · ${category}】` : `【${year}${item.type || '真题'}】`
  const topicCn = item.topic_cn || item.theme || ''
  const promptEn = item.prompt_en || ''

  if (topicCn && promptEn) {
    return `${header} ${topicCn}（${promptEn}）`
  } else if (topicCn) {
    return `${header} ${topicCn}`
  } else if (promptEn) {
    return `${header} ${promptEn}`
  }
  return header
}

function formatTopicLabel(item) {
  if (!item) return ''
  const category = item.sub_type || item.chart_type || item.type || ''
  const desc = item.topic_cn || item.theme || item.prompt_en || ''
  const shortDesc = desc.length > 20 ? desc.slice(0, 20) + '...' : desc
  return `${item.year}年 ${category} - ${shortDesc}`
}

function handleSelectTopic(event) {
  const selected = event.target.value
  if (!selected) return
  promptTopic.value = selected
  event.target.value = ''
}

function loadSampleStudentEssay() {
  if (props.examCategory === '英语一') {
    if (essayType.value === '小作文') {
      promptTopic.value = '2024年英语一真题：向外国朋友写回信，推荐一位中国古代科学家并说明理由及展示建议。'
      essayText.value = `Dear friend,

I am glad to receive your email asking about ancient Chinese scientists. I want to give you some advice for your report.

I recommend you introduce Zhang Heng, who is very famous in ancient China. He invented the earthquake detector and studied astronomy. You can tell a story about his life to make the report interesting. Also, using pictures will help students understand better.

I hope my suggestions are useful for you. Good luck with your report!

Yours sincerely,
Li Ming`
    } else {
      promptTopic.value = '2019年英语一真题：图画作文《半山腰》（两人爬山，一人坐下泄气，一人鼓励前行）。'
      essayText.value = `As is shown in the picture, two men are climbing a mountain. One man sits on the ground and say he is too tired to climb. But the other man drinks water and encourages him to keep going. The caption says: "Halfway up the mountain".

This cartoon wants to tell us the importance of persistence. In our daily life, many people give up easily when they face difficulties. For example, some college students want to learn English well, but when they meet hard grammar, they stop studying. However, success needs hard work and perseverance. If we give up halfway, we can never reach our goals.

In conclusion, I think we should learn from the second man. When we face troubles in study or work, we must hold on and never quit.`
    }
  } else {
    // 英语二示例
    if (essayType.value === '小作文') {
      promptTopic.value = '外国友人想了解中国传统节日，请写一封建议信推荐一个节日并说明理由。'
      essayText.value = `Dear Tom,

I know you want to learn Chinese festival. I want to tell you about Spring Festival. It is very important festival in China.

During this festival, all families get together and have a big dinner. We eat dumplings and watch TV show. Children can get red money from old people, which makes them very happy. Furthermore, there have many interesting activities, like firework and dragon dance.

I hope you can come China to enjoy Spring Festival. Welcome to China!

Yours sincerely,
Li Ming`
    } else {
      promptTopic.value = '柱状图：某高校大学生毕业去向规划与选择（考研48.5%、就业32.2%、出国12.1%、创业7.2%）。'
      essayText.value = `The bar chart show the choices of university graduates in a Chinese college. According to the data, 48.5% of students choose to take the postgraduate entrance exam, which is the biggest part. Meanwhile, 32.2% students choose to find a job directly. In addition, studying abroad and starting business take up 12.1% and 7.2% respectively.

There are several reasons for this phenomenon. First, because the job market is very competitive now, so many students think higher degree can help them get better job and high salary. Second, university encourage students to study more. Third, some students don't want to face the society too early, so they continue to study in school.

In conclusion, more and more students choose to take postgraduate exam. I think students should make choice based on their own situation.`
    }
  }
}

function clearText() {
  essayText.value = ''
  uploadedInfo.value = null
  uploadError.value = ''
}

// 文档上传与解析状态
const fileInputRef = ref(null)
const uploading = ref(false)
const uploadError = ref('')
const uploadedInfo = ref(null)
const isDragging = ref(false)

function triggerFileInput() {
  uploadError.value = ''
  fileInputRef.value?.click()
}

async function handleFileUpload(file) {
  if (!file) return

  const allowedExtensions = ['txt', 'pdf', 'doc', 'docx', 'md', 'png', 'jpg', 'jpeg']
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!allowedExtensions.includes(ext)) {
    uploadError.value = `不支持格式 .${ext}，请上传 txt, pdf, doc, docx, md, png, jpg 文档或试卷照片`
    return
  }

  uploading.value = true
  uploadError.value = ''
  uploadedInfo.value = null

  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    })

    const data = await res.json()
    if (!res.ok || !data.success) {
      throw new Error(data.error || '文件解析识别失败，请检查文件完整性')
    }

    essayText.value = data.text
    uploadedInfo.value = {
      filename: data.filename,
      format: data.format,
      word_count: data.word_count,
      ocr_used: data.ocr_used,
      page_count: data.page_count
    }
  } catch (err) {
    console.error('文件解析错误:', err)
    uploadError.value = err.message || '文件解析识别失败'
  } finally {
    uploading.value = false
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

function onFileSelected(event) {
  const file = event.target?.files?.[0]
  if (file) {
    handleFileUpload(file)
  }
}

function onDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    handleFileUpload(file)
  }
}

function dismissUploadBanner() {
  uploadedInfo.value = null
}

function dismissUploadError() {
  uploadError.value = ''
}

function handleStartEvaluation() {
  if (!essayText.value.trim()) return
  emit('evaluate', {
    essay_text: essayText.value.trim(),
    prompt_topic: promptTopic.value.trim(),
    essay_type: essayType.value,
    exam_category: props.examCategory
  })
}

function fillContent({ topic, text, type }) {
  if (type) {
    essayType.value = type
  }
  if (topic !== undefined) {
    promptTopic.value = topic
  }
  if (text !== undefined) {
    essayText.value = text
  }
}

function resetContent() {
  promptTopic.value = ''
  essayText.value = ''
  uploadedInfo.value = null
  uploadError.value = ''
}

defineExpose({
  fillContent,
  setType,
  resetContent
})
</script>

<template>
  <div class="editor-workbench">
    <!-- 顶部工作台栏：类型切换与文件工具 -->
    <div class="workbench-bar">
      <!-- 试卷类型切换器 -->
      <div class="paper-type-tabs">
        <button
          type="button"
          class="type-tab-btn"
          :class="{ active: essayType === '小作文' }"
          @click="setType('小作文')"
        >
          <span class="part-pill">Part A</span>
          <span class="type-title">小作文</span>
          <span class="type-meta">{{ examCategory === '英语一' ? '应用文/告示 · 10分' : '应用文/书信 · 10分' }}</span>
        </button>

        <button
          type="button"
          class="type-tab-btn"
          :class="{ active: essayType === '大作文' }"
          @click="setType('大作文')"
        >
          <span class="part-pill">Part B</span>
          <span class="type-title">大作文</span>
          <span class="type-meta">{{ examCategory === '英语一' ? '图画作文 · 20分' : '图表作文 · 15分' }}</span>
        </button>
      </div>

      <!-- 右侧快捷功能 -->
      <div class="workbench-tools">
        <input
          ref="fileInputRef"
          type="file"
          accept=".txt,.pdf,.doc,.docx,.md,.png,.jpg,.jpeg"
          style="display: none"
          @change="onFileSelected"
        />

        <button
          type="button"
          class="tool-btn upload-btn"
          :disabled="uploading || loading"
          @click="triggerFileInput"
          title="支持上传 TXT, PDF, Word, Markdown 及拍照手写试卷图片"
        >
          <template v-if="uploading">
            <span class="spin-icon"></span>
            <span>识别中...</span>
          </template>
          <template v-else>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span>上传试卷/文档</span>
          </template>
        </button>

        <button
          type="button"
          class="tool-btn sample-btn"
          :disabled="uploading || loading"
          @click="loadSampleStudentEssay"
          title="载入考研真实作答样本进行体验评卷"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
          <span>载入考生样本</span>
        </button>
      </div>
    </div>

    <!-- 题目信息输入区域 -->
    <div class="topic-section">
      <div class="section-label-row">
        <label class="field-label">作文题目要求与背景</label>
      </div>

      <div class="topic-inputs-cluster">
        <div class="input-container">
          <input
            v-model="promptTopic"
            type="text"
            class="topic-text-input"
            placeholder="例如：外国友人想了解中国传统节日，请写信推荐一个节日并说明理由..."
          />
        </div>

        <div class="topic-select-wrapper">
          <select class="quick-preset-select" @change="handleSelectTopic">
            <option value="">真题题目库一键填入 ▾</option>
            <template v-if="essayType === '小作文'">
              <option
                v-for="item in (pastTopics.small_essays || [])"
                :key="item.year"
                :value="formatTopicValue(item)"
              >
                {{ formatTopicLabel(item) }}
              </option>
            </template>
            <template v-else>
              <option
                v-for="item in (pastTopics.big_essays || [])"
                :key="item.year"
                :value="formatTopicValue(item)"
              >
                {{ formatTopicLabel(item) }}
              </option>
            </template>
          </select>
        </div>

        <button
          type="button"
          class="library-nav-btn"
          title="查阅往年英语二全套真题与标杆高分范文库"
          @click="$emit('openLibrary')"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
          </svg>
          <span>真题范文库</span>
        </button>
      </div>
    </div>

    <!-- 写作输入纸张 -->
    <div class="paper-section">
      <div class="paper-header">
        <div class="paper-label-box">
          <label class="field-label">考生作答正文</label>
        </div>

        <!-- 实时大纲词数与段落监测 -->
        <div class="writing-metrics">
          <div
            class="metric-tag"
            :title="essayStructure.isLetter ? `正文 ${paragraphCount} 段（已将称呼/落款等书信格式独立，不计入正文段落）` : `全文共 ${paragraphCount} 段`"
          >
            <span class="metric-num">{{ paragraphCount }}</span>
            <span class="metric-lbl">{{ essayStructure.isLetter ? '正文段落' : '段落' }}</span>
          </div>
          <div
            class="metric-tag"
            :title="essayStructure.isLetter && essayStructure.bodyWordCount !== wordCount ? `全文 ${wordCount} 词（正文 ${essayStructure.bodyWordCount} 词，标点符号已严格剔除）` : `全文共 ${wordCount} 词（标点符号已严格剔除不计）`"
          >
            <span class="metric-num">{{ wordCount }}</span>
            <span class="metric-lbl">词数</span>
          </div>
          <div class="status-indicator" :class="wordCountStatus.color">
            <span class="dot"></span>
            <span>{{ wordCountStatus.text }}</span>
          </div>
        </div>
      </div>

      <!-- 写作区域与拖放容器 -->
      <div
        class="writing-dropzone"
        :class="{ 'is-dragging': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
      >
        <!-- 拖拽提示层 -->
        <div v-if="isDragging" class="drop-overlay">
          <div class="drop-modal-content">
            <div class="drop-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            </div>
            <p class="drop-title">释放以解析文件</p>
            <p class="drop-desc">支持 TXT · PDF · DOCX · MD · PNG · JPG</p>
          </div>
        </div>

        <!-- 识别中提示 -->
        <div v-if="uploading" class="status-banner loading-state">
          <span class="spin-icon dark"></span>
          <div class="banner-text">
            <strong>正在解析文件内容...</strong>
          </div>
        </div>

        <!-- 识别成功提示 -->
        <div v-if="uploadedInfo && !uploading" class="status-banner success-state animate-fade-in">
          <div class="banner-pill">{{ uploadedInfo.format.toUpperCase() }}</div>
          <div class="banner-text">
            <span class="file-name">{{ uploadedInfo.filename }}</span>
            <span class="bullet">·</span>
            <span class="word-stat">识别出 <strong>{{ uploadedInfo.word_count }}</strong> 词</span>
          </div>
          <button type="button" class="dismiss-btn" @click="dismissUploadBanner">✕</button>
        </div>

        <!-- 错误提示 -->
        <div v-if="uploadError" class="status-banner error-state animate-fade-in">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span class="error-msg">{{ uploadError }}</span>
          <button type="button" class="dismiss-btn" @click="dismissUploadError">✕</button>
        </div>

        <textarea
          v-model="essayText"
          class="essay-editor-canvas"
          rows="12"
          placeholder="在此输入或粘贴英文作文正文，或直接拖入文件/截图..."
          spellcheck="false"
        ></textarea>
      </div>
    </div>

    <!-- 评卷大模型服务商全量快捷卡片选择栏 -->
    <div class="provider-selector-module">
      <div class="module-title-row">
        <div class="title-left">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" class="title-icon">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          <span class="module-title">评卷大模型服务商</span>
        </div>
        <button
          type="button"
          class="all-settings-link"
          title="打开大模型多厂商独立隔离配置面板"
          @click="$emit('openModelSettings', activeProviderId)"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0 2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
          <span>配置参数</span>
        </button>
      </div>

      <div class="provider-cards-grid">
        <div
          v-for="p in PROVIDER_LIST"
          :key="p.id"
          class="provider-tile"
          :class="{
            'tile-active': activeProviderId === p.id,
            'tile-configured': isProviderConfigured(p.id)
          }"
          @click="handleSelectProvider(p.id)"
        >
          <div class="tile-header">
            <div class="tile-brand">
              <span class="tile-icon-badge" :class="p.id">
                <template v-if="p.iconType === 'sparkles'">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>
                  </svg>
                </template>
                <template v-else-if="p.iconType === 'cloud'">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
                  </svg>
                </template>
                <template v-else-if="p.iconType === 'moon'">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
                  </svg>
                </template>
                <template v-else-if="p.iconType === 'cpu'">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>
                  </svg>
                </template>
                <template v-else-if="p.iconType === 'terminal'">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>
                  </svg>
                </template>
                <template v-else>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <line x1="4" x2="20" y1="21" y2="21"/><line x1="4" x2="20" y1="3" y2="3"/><line x1="4" x2="20" y1="12" y2="12"/><line x1="8" x2="8" y1="16" y2="8"/><line x1="16" x2="16" y1="16" y2="8"/>
                  </svg>
                </template>
              </span>
              <div class="tile-name-group">
                <span class="tile-name">{{ p.name }}</span>
                <span class="tile-sub">{{ p.sub }}</span>
              </div>
            </div>

            <div class="tile-status-box">
              <span v-if="activeProviderId === p.id" class="badge-active">启用中</span>
              <span v-else-if="isProviderConfigured(p.id)" class="badge-ready">已配置</span>
              <span v-else class="badge-tag">{{ p.tag }}</span>
            </div>
          </div>

          <div class="tile-bottom">
            <span class="tile-model-name" :title="getProviderModelName(p)">
              {{ getProviderModelName(p) }}
            </span>
            <button
              type="button"
              class="tile-config-btn"
              title="设置此厂商专属 API Key 与模型"
              @click.stop="$emit('openModelSettings', p.id)"
            >
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0 2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
              <span>配置</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作与评卷激活条 -->
    <div class="editor-bottom-bar">
      <div class="bar-left">
        <button
          type="button"
          class="reset-btn"
          :disabled="loading || !essayText"
          @click="clearText"
        >
          清空正文
        </button>
      </div>

      <div class="bar-right">
        <!-- 评卷大模型切换指示牌 -->
        <div
          class="model-chip"
          :class="{ 'custom-chip': isCustomModel }"
          title="点击切换评卷大模型、API Key 或本地私有模型"
          @click="$emit('openModelSettings', activeProviderId)"
        >
          <span class="model-dot"></span>
          <span class="model-role">模型：</span>
          <span class="model-provider">{{ currentProviderName }}</span>
          <span class="model-divider">·</span>
          <span class="model-label">{{ currentModelName }}</span>
          <span v-if="isCustomModel" class="custom-badge">自选</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="gear-icon">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </div>

        <!-- 评卷主执行按钮 -->
        <button
          type="button"
          class="evaluate-submit-btn"
          :disabled="loading || !essayText.trim()"
          @click="handleStartEvaluation"
        >
          <template v-if="loading">
            <span class="spin-icon white"></span>
            <span>正在阅卷...</span>
          </template>
          <template v-else>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            <span>开始智能评卷</span>
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.editor-workbench {
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 1.5rem;
  margin-bottom: 2rem;
  transition: border-color 0.2s ease;
}

/* ── 顶部栏：类型与工具 ── */
.workbench-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--paper-border-soft);
  margin-bottom: 1.25rem;
}

.paper-type-tabs {
  display: inline-flex;
  background: var(--paper-subtle);
  padding: 3px;
  border-radius: var(--radius-md);
  border: 1px solid var(--paper-border);
}

.type-tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.95rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s var(--ease-out);
}

.type-tab-btn.active {
  background: var(--paper-card);
  color: var(--text-ink);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(12, 18, 34, 0.08);
}

.part-pill {
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: rgba(12, 18, 34, 0.06);
  color: var(--text-ink);
}

.type-tab-btn.active .part-pill {
  background: var(--ink);
  color: var(--paper);
}

.type-meta {
  font-size: 0.76rem;
  color: var(--text-muted);
}

.type-tab-btn.active .type-meta {
  color: var(--text-secondary);
}

.workbench-tools {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.85rem;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--paper-border);
  background: var(--paper-warm);
  color: var(--text-body);
  transition: all 0.18s var(--ease-out);
}

.tool-btn:hover:not(:disabled) {
  background: #ffffff;
  border-color: var(--slate-mid);
  color: var(--text-ink);
}

.tool-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tool-subtag {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  font-weight: 600;
  background: var(--paper-border);
  color: var(--text-secondary);
  padding: 0.05rem 0.35rem;
  border-radius: 3px;
}

/* ── 题目输入 ── */
.topic-section {
  margin-bottom: 1.25rem;
}

.section-label-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.45rem;
}

.field-label {
  font-family: var(--font-display);
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--text-ink);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.label-aside {
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 400;
  color: var(--text-secondary);
}

.topic-inputs-cluster {
  display: flex;
  gap: 0.6rem;
}

.input-container {
  flex: 1;
}

.topic-text-input {
  width: 100%;
  padding: 0.6rem 0.85rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--paper-border);
  background: var(--paper-warm);
  color: var(--text-ink);
  font-size: 0.88rem;
  transition: all 0.2s ease;
}

.topic-text-input:focus {
  outline: none;
  background: #ffffff;
  border-color: var(--ink);
  box-shadow: 0 0 0 3px rgba(12, 18, 34, 0.06);
}

.quick-preset-select {
  padding: 0.6rem 0.85rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--paper-border);
  background: var(--paper-warm);
  color: var(--text-body);
  font-size: 0.84rem;
  font-weight: 500;
  cursor: pointer;
  max-width: 220px;
}

.quick-preset-select:focus {
  outline: none;
  border-color: var(--ink);
}

.library-nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.6rem 0.95rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--paper-border);
  background: var(--paper-warm);
  color: var(--text-ink);
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s ease;
}

.library-nav-btn:hover {
  background: #ffffff;
  border-color: var(--amber);
  color: var(--amber-dim);
}

/* ── 正文纸张 ── */
.paper-section {
  margin-bottom: 1.25rem;
}

.paper-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.45rem;
}

.drop-hint {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-left: 0.4rem;
}

.writing-metrics {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.metric-tag {
  display: inline-flex;
  align-items: baseline;
  gap: 0.25rem;
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.metric-num {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--text-ink);
}

.metric-lbl {
  font-size: 0.76rem;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-full);
}

.status-indicator .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-indicator.muted {
  background: var(--paper-subtle);
  color: var(--text-muted);
}
.status-indicator.muted .dot { background: var(--text-muted); }

.status-indicator.success {
  background: var(--success-light);
  color: var(--success);
  border: 1px solid var(--success-border);
}
.status-indicator.success .dot { background: var(--success); }

.status-indicator.warning {
  background: var(--warning-light);
  color: var(--warning);
  border: 1px solid var(--warning-border);
}
.status-indicator.warning .dot { background: var(--warning); }

.status-indicator.danger {
  background: var(--danger-light);
  color: var(--danger);
  border: 1px solid var(--danger-border);
}
.status-indicator.danger .dot { background: var(--danger); }

/* ── 写作画布与拖放 ── */
.writing-dropzone {
  position: relative;
  border-radius: var(--radius-md);
  border: 1px solid var(--paper-border);
  background: var(--paper-warm);
  overflow: hidden;
  transition: all 0.2s ease;
}

.writing-dropzone.is-dragging {
  border-color: var(--amber);
  background: #fdfaf2;
}

.drop-overlay {
  position: absolute;
  inset: 0;
  background: rgba(250, 247, 240, 0.94);
  backdrop-filter: blur(4px);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--amber);
  border-radius: var(--radius-md);
}

.drop-modal-content {
  text-align: center;
}

.drop-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 0.75rem;
  border-radius: 50%;
  background: var(--amber-subtle);
  color: var(--amber);
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-title {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-ink);
  margin-bottom: 0.25rem;
}

.drop-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* 状态横幅 */
.status-banner {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.6rem 0.95rem;
  font-size: 0.82rem;
  border-bottom: 1px solid var(--paper-border);
}

.status-banner.loading-state {
  background: #fffbeb;
  color: #92400e;
}

.status-banner.success-state {
  background: var(--success-light);
  color: var(--success);
}

.status-banner.error-state {
  background: var(--danger-light);
  color: var(--danger);
}

.banner-pill {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: var(--success);
  color: #ffffff;
}

.ocr-tag {
  font-size: 0.72rem;
  font-weight: 700;
  background: rgba(21, 128, 61, 0.1);
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  margin-left: 0.4rem;
}

.dismiss-btn {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
  color: inherit;
  opacity: 0.7;
}
.dismiss-btn:hover { opacity: 1; }

.essay-editor-canvas {
  width: 100%;
  padding: 1.25rem 1.25rem;
  border: none;
  background: transparent;
  color: var(--text-ink);
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.85;
  letter-spacing: 0.01em;
  resize: vertical;
  min-height: 260px;
}

.essay-editor-canvas:focus {
  outline: none;
  background: #ffffff;
}

/* ── 底部控制条 ── */
.editor-bottom-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  padding-top: 0.5rem;
}

.reset-btn {
  background: none;
  border: 1px solid transparent;
  padding: 0.45rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.reset-btn:hover:not(:disabled) {
  color: var(--danger);
  background: var(--danger-light);
}

.reset-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.bar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.model-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.85rem;
  border-radius: var(--radius-full);
  border: 1px solid var(--paper-border);
  background: var(--paper-subtle);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.18s ease;
}

.model-chip:hover {
  border-color: var(--ink);
  background: #ffffff;
}

.model-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--success);
}

.model-role {
  color: var(--text-secondary);
}

.model-label {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--text-ink);
}

.custom-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.08rem 0.35rem;
  border-radius: 3px;
  background: var(--amber-subtle);
  color: var(--amber-dim);
  border: 1px solid var(--amber-border);
}

.gear-icon {
  color: var(--text-muted);
  margin-left: 2px;
}

.evaluate-submit-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.65rem 1.45rem;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  background: var(--ink);
  color: var(--paper-warm);
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(12, 18, 34, 0.15);
  transition: all 0.2s var(--ease-out);
}

.evaluate-submit-btn:hover:not(:disabled) {
  background: #18233c;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(12, 18, 34, 0.22);
}

.evaluate-submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* ── 旋转图标 ── */
.spin-icon {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(12, 18, 34, 0.2);
  border-top-color: var(--ink);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spin-icon.white {
  border-color: rgba(255, 255, 255, 0.25);
  border-top-color: #ffffff;
}

.model-provider {
  font-weight: 700;
  color: var(--text-ink);
}

.model-divider {
  color: var(--text-muted);
}

/* ── 服务商全量选择模块 ── */
.provider-selector-module {
  margin-top: 1.25rem;
  padding-top: 1.15rem;
  border-top: 1px dashed var(--paper-border);
}

.module-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.title-icon {
  color: var(--amber);
}

.module-title {
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-ink);
}

.module-tip {
  font-size: 0.74rem;
  color: var(--text-muted);
}

.all-settings-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  padding: 0.25rem 0.65rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
}

.all-settings-link:hover {
  color: var(--text-ink);
  border-color: var(--slate-mid);
  background: #ffffff;
}

.provider-cards-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.65rem;
}

@media (max-width: 1100px) {
  .provider-cards-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .provider-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.provider-tile {
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  padding: 0.65rem 0.75rem;
  cursor: pointer;
  transition: all 0.18s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 0.5rem;
  user-select: none;
}

.provider-tile:hover {
  border-color: var(--slate-mid);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(12, 18, 34, 0.05);
}

.provider-tile.tile-active {
  border-color: var(--ink);
  background: #ffffff;
  box-shadow: 0 0 0 2px var(--ink), 0 4px 14px rgba(12, 18, 34, 0.08);
}

.tile-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.3rem;
}

.tile-brand {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
}

.tile-icon-badge {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--paper-warm);
  color: var(--text-secondary);
}

.tile-icon-badge.deepseek { background: #eff6ff; color: #2563eb; }
.tile-icon-badge.qwen { background: #fff7ed; color: #ea580c; }
.tile-icon-badge.moonshot { background: #f5f3ff; color: #7c3aed; }
.tile-icon-badge.zhipu { background: #ecfdf5; color: #059669; }
.tile-icon-badge.ollama { background: #f1f5f9; color: #0f172a; }
.tile-icon-badge.custom { background: #fefce8; color: #ca8a04; }

.tile-name-group {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.tile-name {
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tile-sub {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.tile-status-box {
  flex-shrink: 0;
}

.badge-active {
  font-size: 0.62rem;
  font-weight: 700;
  color: #ffffff;
  background: var(--ink);
  padding: 0.12rem 0.4rem;
  border-radius: 4px;
}

.badge-ready {
  font-size: 0.62rem;
  font-weight: 600;
  color: #15803d;
  background: #dcfce7;
  padding: 0.12rem 0.35rem;
  border-radius: 4px;
}

.badge-tag {
  font-size: 0.62rem;
  color: var(--text-muted);
  background: var(--paper-warm);
  padding: 0.12rem 0.35rem;
  border-radius: 4px;
}

.tile-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.25rem;
  padding-top: 0.35rem;
  border-top: 1px solid var(--paper-border);
}

.tile-model-name {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
}

.tile-config-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.65rem;
  color: var(--text-muted);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 0.1rem 0.3rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tile-config-btn:hover {
  color: var(--text-ink);
  background: var(--paper-warm);
  border-color: var(--paper-border);
}

@media (max-width: 768px) {
  .topic-inputs-cluster {
    flex-direction: column;
  }
  .quick-preset-select {
    max-width: 100%;
  }
  .editor-bottom-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .bar-right {
    flex-direction: column;
    width: 100%;
  }
  .evaluate-submit-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>

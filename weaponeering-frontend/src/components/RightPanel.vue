<template>
  <div class="right-panel" :class="{ collapsed }">
    <div class="right-panel-header">
      <div class="right-panel-actions">
        <button
          type="button"
          class="right-panel-toggle"
          :title="collapsed ? 'เปิดแถบบาร์' : 'ปิดแถบบาร์'"
          :aria-label="collapsed ? 'เปิดแถบบาร์' : 'ปิดแถบบาร์'"
          @click="$emit('toggle-panel')"
        >
          <i class="bi" :class="collapsed ? 'bi-chevron-left' : 'bi-chevron-right'"></i>
        </button>
      </div>
      <div class="right-panel-brand">
        <span class="right-panel-brand-icon"><i class="bi bi-layout-sidebar-reverse"></i></span>
        <div v-show="!collapsed" class="right-panel-brand-copy">
          <strong>ผลการวิเคราะห์</strong>
          <small>Analysis Workspace</small>
        </div>
      </div>
    </div>

    <div v-show="!collapsed" class="right-panel-scroll">
      <!-- Tab Navigation -->
      <ul class="nav nav-tabs nav-fill mb-3" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" id="tab-recommend" data-bs-toggle="tab" data-bs-target="#content-recommend" type="button">
            <i class="bi bi-award"></i> Recommendation
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="tab-analysis" data-bs-toggle="tab" data-bs-target="#content-analysis" type="button">
            <i class="bi bi-graph-up"></i> Analysis
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="tab-chat" data-bs-toggle="tab" data-bs-target="#content-chat" type="button">
            <i class="bi bi-chat-dots"></i> Chat Bot
          </button>
        </li>
      </ul>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Top 5 Recommendations -->
        <div class="tab-pane fade show active" id="content-recommend" role="tabpanel">
          <div class="section-title recommendation-title mb-3">
            <span class="title-icon"><i class="bi bi-stars"></i></span>
            <span>Recommendation</span>
            <span class="top-five-badge">TOP 5</span>
          </div>
          <div class="table-responsive recommendation-card">
            <table class="table table-sm recommendation-table">
              <thead>
                <tr>
                  <th>ลำดับ</th>
                  <th>รายการ</th>
                  <th>ขนาด</th>
                  <th>จำนวน</th>
                  <th>Pd</th>
                  <th>Pk</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(rec, idx) in recommendations" :key="rec.id" @click="selectRecommendation(rec)" class="cursor-pointer">
                  <td class="rank-number">
                    <span
                      class="target-rank"
                      :class="idx === 0 ? 'rank-red' : idx === 1 ? 'rank-yellow' : idx === 2 ? 'rank-green' : 'rank-default'"
                    >{{ idx + 1 }}</span>
                  </td>
                  <td>
                    <span class="recommendation-name">{{ rec.item }}</span>
                  </td>
                  <td><span class="size-chip">{{ rec.size }}</span></td>
                  <td class="text-center"><span class="qty-badge">{{ rec.qty }}</span></td>
                  <td><span class="score-pill pd-score">{{ rec.pd.toFixed(2) }}</span></td>
                  <td><span class="score-pill pk-score">{{ rec.pk.toFixed(2) }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <button type="button" class="view-all-button" @click="showAllDetails">
            <span>ดูรายละเอียดทั้งหมด</span>
            <i class="bi bi-arrow-right"></i>
          </button>
        </div>

        <!-- AI Analysis Results -->
        <div class="tab-pane fade" id="content-analysis" role="tabpanel">
          <div class="section-title mb-3">
            <i class="bi bi-cpu"></i> AI Analysis Result (ข้อมูล Analyst วิเคราะห์ข้อมูล)
          </div>
          <div class="analysis-result">
            <pre>{{ aiAnalysisText }}</pre>
          </div>
          <div
            class="confidence-card mt-3"
            role="meter"
            aria-label="AI Confidence"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow="85"
          >
            <div class="confidence-heading">
              <i class="bi bi-shield-check"></i>
              <span>ความครบถ้วนของข้อมูล (AI Confidence)</span>
            </div>
            <div class="confidence-content">
              <div class="confidence-gauge">
                <svg viewBox="0 0 140 88" aria-hidden="true">
                  <defs>
                    <linearGradient id="confidenceGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stop-color="#2187e5" />
                      <stop offset="48%" stop-color="#20bf8a" />
                      <stop offset="72%" stop-color="#f0d044" />
                      <stop offset="100%" stop-color="#ff6c32" />
                    </linearGradient>
                  </defs>
                  <path class="gauge-track" pathLength="100" d="M15 73 A55 55 0 0 1 125 73" />
                  <path class="gauge-value" pathLength="100" d="M15 73 A55 55 0 0 1 125 73" />
                </svg>
                <div class="confidence-number">85<small>%</small></div>
              </div>
              <div class="confidence-copy">
                <span class="confidence-status"><i></i> High Confidence</span>
                <strong>ข้อมูลมีความน่าเชื่อถือสูง</strong>
                <small>พร้อมสำหรับการวิเคราะห์</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Chatbot -->
        <div class="tab-pane fade" id="content-chat" role="tabpanel">
          <div class="section-title chat-header-bar mb-2">
            <div class="chat-header-left">
              <i class="bi bi-robot"></i>
              <span>AI Assistant (Chatbot ถามตอบ)</span>
              <span
                class="chat-status-dot"
                :class="isChatConfigured ? 'connected' : 'unconfigured'"
                :title="isChatConfigured ? `เชื่อมต่อกับ: ${resolvedChatEndpoint}` : 'ยังไม่ได้ตั้งค่า POST / API (โหมดจำลอง)'"
              ></span>
            </div>
            <div class="chat-header-actions">
              <button
                type="button"
                class="chat-icon-btn"
                title="เริ่มบทสนทนาใหม่ (Clear Chat)"
                @click="resetChatConversation"
              >
                <i class="bi bi-arrow-counterclockwise"></i>
              </button>
              <button
                type="button"
                class="chat-icon-btn"
                :class="{ active: showChatSettings }"
                title="ตั้งค่า POST Endpoint & API Key"
                @click="showChatSettings = !showChatSettings"
              >
                <i class="bi bi-gear-fill"></i>
              </button>
            </div>
          </div>

          <!-- Collapsible Gear Settings Box (POST & API Key) -->
          <div v-if="showChatSettings" class="chat-settings-box mb-3">
            <div class="chat-settings-header">
              <span><i class="bi bi-sliders"></i> ตั้งค่าการเชื่อมต่อ RAG API</span>
              <span class="chat-mode-badge">{{ detectedApiModeLabel }}</span>
            </div>

            <div class="chat-field-group">
              <label class="chat-field-label">
                <i class="bi bi-hdd-network"></i> POST URL / Port
              </label>
              <input
                type="text"
                class="form-control form-control-sm chat-config-input"
                placeholder="เช่น http://localhost:1152/v1/chat/completions หรือ 1152"
                v-model="chatPostInput"
              />
              <small class="chat-field-hint">
                รองรับ URL เต็ม (<code>/v1/chat/completions</code>, <code>/chat</code>) หรือใส่เฉพาะ Port เช่น <code>1152</code>
              </small>
            </div>

            <div class="chat-field-group mt-2">
              <label class="chat-field-label">
                <i class="bi bi-key"></i> API Key <span class="text-muted">(สำหรับ /v1/chat/completions)</span>
              </label>
              <div class="input-group input-group-sm">
                <input
                  :type="showChatApiKey ? 'text' : 'password'"
                  class="form-control chat-config-input"
                  placeholder="ใส่ Platform API Key (Bearer / X-API-Key)"
                  v-model="chatApiKeyInput"
                />
                <button
                  type="button"
                  class="btn btn-outline-secondary chat-eye-btn"
                  @click="showChatApiKey = !showChatApiKey"
                  :title="showChatApiKey ? 'ซ่อน API Key' : 'แสดง API Key'"
                >
                  <i class="bi" :class="showChatApiKey ? 'bi-eye-slash' : 'bi-eye'"></i>
                </button>
              </div>
            </div>

            <div class="chat-Resolved-preview mt-2" v-if="chatPostInput.trim()">
              <span class="preview-label">POST ไปที่:</span>
              <code>{{ previewResolvedEndpoint }}</code>
            </div>

            <div v-if="chatConfigStatus.message" class="chat-config-alert mt-2" :class="chatConfigStatus.type">
              <i class="bi" :class="chatConfigStatus.type === 'success' ? 'bi-check-circle-fill' : chatConfigStatus.type === 'error' ? 'bi-exclamation-triangle-fill' : 'bi-info-circle-fill'"></i>
              <span>{{ chatConfigStatus.message }}</span>
            </div>

            <div class="chat-settings-actions mt-2">
              <button type="button" class="btn btn-primary btn-sm flex-grow-1" @click="saveChatSettings">
                <i class="bi bi-check2-circle"></i> บันทึกตั้งค่า
              </button>
              <button
                type="button"
                class="btn btn-outline-info btn-sm"
                :disabled="isTestingChatApi"
                @click="testChatConnection"
              >
                <i class="bi" :class="isTestingChatApi ? 'bi-hourglass-split' : 'bi-plug'"></i>
                {{ isTestingChatApi ? 'กำลังทดสอบ...' : 'ทดสอบ' }}
              </button>
              <button type="button" class="btn btn-outline-secondary btn-sm" title="ล้างค่า" @click="clearChatSettings">
                <i class="bi bi-trash3"></i>
              </button>
            </div>
          </div>

          <div ref="chatContainerRef" class="chatbot-messages mb-3">
            <div v-for="msg in chatMessages" :key="msg.id" class="message" :class="msg.type">
              <div class="message-content" :class="{ 'message-error': msg.isError }">
                <div class="message-text">{{ msg.text }}<span v-if="msg.streaming" class="streaming-cursor">▍</span></div>
                <div v-if="msg.citations && msg.citations.length" class="message-citations">
                  <div class="citations-title"><i class="bi bi-journal-bookmark"></i> แหล่งอ้างอิง ({{ msg.citations.length }}):</div>
                  <div
                    v-for="(cit, cIdx) in msg.citations"
                    :key="cit.id || cIdx"
                    class="citation-chip"
                    :title="cit.excerpt || ''"
                  >
                    [{{ cIdx + 1 }}] {{ cit.documentName || 'เอกสาร' }}
                    <span v-if="cit.pageNumber">(หน้า {{ cit.pageNumber }})</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="chat-input">
            <div class="input-group input-group-sm">
              <input
                type="text"
                class="form-control"
                :placeholder="isChatStreaming ? 'AI กำลังตอบคำถาม...' : 'พิมพ์คำถามของคุณ...'"
                v-model="chatInput"
                :disabled="isChatStreaming"
                @keyup.enter="sendChatMessage"
              />
              <button
                v-if="isChatStreaming"
                class="btn btn-danger btn-sm"
                type="button"
                title="หยุดการตอบ"
                @click="stopChatStreaming"
              >
                <i class="bi bi-stop-fill"></i>
              </button>
              <button
                v-else
                class="btn btn-primary btn-sm"
                type="button"
                :disabled="!chatInput.trim()"
                @click="sendChatMessage"
              >
                <i class="bi bi-send"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Simulator Section -->
      <div class="mt-4 pt-4 border-top">
        <div class="section-title mb-3">
          <i class="bi bi-play-circle"></i> Simulator Demo
        </div>
        <SimulatorDemo
          :targets="targets"
          :selected-target-id="selectedTargetId"
          :form-data="formData"
          :scenario-id="scenarioId"
        />
      </div>

      <!-- Save / Export Section -->
      <div class="mt-4 pt-4 border-top">
        <div class="section-title save-export-title mb-3">
          <i class="bi bi-download"></i>
          <span>บันทึกข้อมูล และ นำออก</span>
        </div>
        <div ref="exportMenuRef" class="action-buttons">
          <button class="btn btn-success btn-sm w-100 mb-2" @click="openSaveModal">
            <i class="bi bi-save"></i>
            <span>บันทึกข้อมูล</span>
          </button>
          <div class="export-control">
            <button class="btn btn-outline-primary btn-sm w-100 export-toggle" type="button" :aria-expanded="showExportMenu" @click.stop="showExportMenu = !showExportMenu">
              <i class="bi bi-download"></i>
              <span>นำออก</span>
              <i class="bi bi-chevron-down export-chevron" :class="{ open: showExportMenu }"></i>
            </button>
            <div v-if="showExportMenu" class="export-format-menu" role="menu">
              <div class="export-format-heading">
                <strong>รูปแบบเอกสาร</strong>
                <small>เลือกไฟล์สำหรับจัดเก็บหรือเสนอรายงาน</small>
              </div>
              <button type="button" role="menuitem" @click="exportData('pdf')">
                <span class="export-format-icon pdf"><i class="bi bi-file-earmark-pdf"></i></span>
                <span><strong>PDF</strong><small>เอกสารพร้อมพิมพ์และจัดเก็บ</small></span>
              </button>
              <button type="button" role="menuitem" @click="exportData('word')">
                <span class="export-format-icon word"><i class="bi bi-file-earmark-word"></i></span>
                <span><strong>Word</strong><small>เอกสารสำหรับแก้ไขและนำเสนอ</small></span>
              </button>
              <div class="export-format-heading">
                <strong>ภาพรวม Scenario</strong>
                <small>อาวุธที่ใช้และจำนวนรวมทุกเป้าหมาย</small>
              </div>
              <button type="button" role="menuitem" :disabled="!scenarioId" @click="exportScenario('pdf')">
                <span class="export-format-icon pdf"><i class="bi bi-clipboard-data"></i></span>
                <span><strong>ภาพรวม PDF</strong><small>สรุปการใช้อาวุธทั้ง Scenario</small></span>
              </button>
              <button type="button" role="menuitem" :disabled="!scenarioId" @click="exportScenario('word')">
                <span class="export-format-icon word"><i class="bi bi-clipboard-data"></i></span>
                <span><strong>ภาพรวม Word</strong><small>สรุปการใช้อาวุธทั้ง Scenario</small></span>
              </button>
            </div>
          </div>
        </div>
        <div class="small text-muted mt-2">
          บันทึกในระบบแล้ว: {{ savedRecordsCount }} รายการ
        </div>
      </div>

      <div v-if="showRecommendationModal" class="modal-backdrop" @click.self="closeRecommendationModal">
        <div class="modal-card recommendation-modal-card" role="dialog" aria-modal="true" aria-labelledby="recommendation-modal-title">
          <div class="modal-header recommendation-modal-header">
            <div>
              <h6 id="recommendation-modal-title" class="mb-1">
                <i class="bi bi-stars me-2"></i>Recommendation ทั้งหมด
              </h6>
              <small>รายการที่ระบบวิเคราะห์และแนะนำ</small>
            </div>
            <button type="button" class="btn-close" aria-label="ปิด" @click="closeRecommendationModal"></button>
          </div>
          <div class="modal-body recommendation-modal-body">
            <div class="table-responsive recommendation-card modal-table-card">
              <table class="table table-sm recommendation-table">
                <thead>
                  <tr>
                    <th>ลำดับ</th>
                    <th>รายการ</th>
                    <th>ขนาด</th>
                    <th>จำนวน</th>
                    <th>Pd</th>
                    <th>Pk</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(rec, idx) in recommendations" :key="`modal-${rec.id}`">
                    <td class="rank-number">
                      <span
                        class="target-rank"
                        :class="idx === 0 ? 'rank-red' : idx === 1 ? 'rank-yellow' : idx === 2 ? 'rank-green' : 'rank-default'"
                      >{{ idx + 1 }}</span>
                    </td>
                    <td><span class="recommendation-name">{{ rec.item }}</span></td>
                    <td><span class="size-chip">{{ rec.size }}</span></td>
                    <td class="text-center"><span class="qty-badge">{{ rec.qty }}</span></td>
                    <td><span class="score-pill pd-score">{{ rec.pd.toFixed(2) }}</span></td>
                    <td><span class="score-pill pk-score">{{ rec.pk.toFixed(2) }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer">
            <span class="recommendation-count">ทั้งหมด {{ recommendations.length }} รายการ</span>
            <button type="button" class="recommendation-close-button" @click="closeRecommendationModal">
              <i class="bi bi-check-lg"></i> ปิด
            </button>
          </div>
        </div>
      </div>

      <div v-if="showSaveModal" class="modal-backdrop">
        <div class="modal-card save-modal-card">
          <div class="modal-header">
            <h6 class="mb-0"><i class="bi bi-save me-2"></i>บันทึกข้อมูล</h6>
            <button type="button" class="btn-close" @click="closeSaveModal"></button>
          </div>
          <div class="modal-body save-modal-body">
            <div class="save-field-group">
              <label class="save-field-label">
                <i class="bi bi-person"></i>
                <span>ชื่อผู้บันทึก</span>
              </label>
              <input v-model="recorderName" class="form-control form-control-sm" placeholder="กรอกชื่อผู้บันทึก" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline-secondary btn-sm" @click="closeSaveModal">ยกเลิก</button>
            <button class="btn btn-success btn-sm" :disabled="!recorderName.trim()" @click="requestSaveConfirmation">บันทึก</button>
          </div>
        </div>
      </div>

      <div v-if="showSaveConfirmation" class="modal-backdrop confirmation-backdrop" @click.self="cancelSaveConfirmation">
        <div class="modal-card confirmation-card" role="alertdialog" aria-modal="true" aria-labelledby="save-confirmation-title">
          <div class="confirmation-icon" aria-hidden="true">
            <i class="bi bi-question-lg"></i>
          </div>
          <h5 id="save-confirmation-title">ต้องการบันทึกข้อมูลหรือไม่?</h5>
          <p>โปรดตรวจสอบข้อมูลก่อนยืนยันการบันทึก</p>
          <div class="confirmation-actions">
            <button type="button" class="confirmation-cancel" @click="cancelSaveConfirmation">ยกเลิก</button>
            <button type="button" class="confirmation-accept" @click="saveRecordToDatabase">
              <i class="bi bi-check-lg"></i> ต้องการ
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import mockAPI from '../services/mockAPI'
import { exportService } from '../services/exportService'
import { fetchScenarioInfo, fetchScenarioSummary, fetchTargetReportData } from '../services/reportDataService'
import { buildReportRecordFromPayload, buildTargetExportPayload } from '../utils/reportExportMapper'
import SimulatorDemo from './SimulatorDemo.vue'

const CHAT_CONFIG_STORAGE_KEY = 'weaponeering_rag_chat_config_v1'

export default {
  name: 'RightPanel',
  components: { SimulatorDemo },
  props: {
    collapsed: {
      type: Boolean,
      default: false
    },
    targetPriority: {
      type: String,
      default: ''
    },
    formData: {
      type: Object,
      default: () => ({})
    },
    recommendationsData: {
      type: Array,
      default: null
    },
    analysisText: {
      type: String,
      default: ''
    },
    scenarioId: {
      type: String,
      default: ''
    },
    targets: {
      type: Array,
      default: () => []
    },
    selectedTargetId: {
      type: String,
      default: ''
    }
  },
  emits: ['save-data', 'toggle-panel'],
  setup(props, { emit }) {
    const recommendations = ref(mockAPI.recommendations)
    const aiAnalysisText = ref('')
    const chatMessages = ref([
      {
        id: 1,
        type: 'assistant',
        text: 'สวัสดีครับ ฉันเป็น AI Assistant ของระบบ Weaponeering พร้อมช่วยวิเคราะห์และตอบคำถามจากฐานข้อมูล (คลิกปุ่มฟันเฟือง ⚙️ มุมขวาบนเพื่อตั้งค่า POST URL และ API Key)'
      }
    ])
    const chatInput = ref('')
    const chatContainerRef = ref(null)

    // Chatbot RAG API configuration state
    const showChatSettings = ref(false)
    const showChatApiKey = ref(false)
    const chatPostInput = ref('')
    const chatApiKeyInput = ref('')
    const savedChatPost = ref('')
    const savedChatApiKey = ref('')
    const chatConfigStatus = ref({ type: '', message: '' })
    const isTestingChatApi = ref(false)
    const isChatStreaming = ref(false)
    const ragConversationId = ref(null)
    let activeChatAbortController = null

    /**
     * Resolve raw POST URL / Host:Port / Port into { endpoint, baseUrl, mode }
     * Supports both:
     * - External OpenAI-compatible API: POST /v1/chat/completions (with Bearer / X-API-Key)
     * - Native Internal Chat API: POST /chat (SSE event: delta / event: done)
     */
    const resolveRagConfig = (rawPost, rawApiKey) => {
      const trimmed = String(rawPost || '').trim()
      const apiKey = String(rawApiKey || '').trim()
      if (!trimmed) {
        return { endpoint: '', baseUrl: '', mode: 'unconfigured', apiKey }
      }

      let normalized = trimmed
      // If user entered only port digits like "1152" or "8000"
      if (/^\d{2,5}$/.test(normalized)) {
        normalized = `http://localhost:${normalized}`
      } else if (!/^https?:\/\//i.test(normalized)) {
        // If user entered "/v1/chat/completions" or "localhost:1152" or "192.168.1.10:1152"
        if (normalized.startsWith('/')) {
          normalized = `http://localhost:1152${normalized}`
        } else {
          normalized = `http://${normalized}`
        }
      }

      // Remove trailing slash
      normalized = normalized.replace(/\/+$/, '')

      try {
        const urlObj = new URL(normalized)
        const baseUrl = `${urlObj.protocol}//${urlObj.host}`
        const path = urlObj.pathname.replace(/\/+$/, '')

        if (path.endsWith('/v1/chat/completions')) {
          return { endpoint: normalized, baseUrl, mode: 'openai', apiKey }
        }
        if (path.endsWith('/chat')) {
          return { endpoint: normalized, baseUrl, mode: 'native', apiKey }
        }
        if (path === '' || path === '/') {
          // Auto-select endpoint based on whether API Key is provided (per api-manual.md)
          if (apiKey) {
            return { endpoint: `${baseUrl}/v1/chat/completions`, baseUrl, mode: 'openai', apiKey }
          }
          return { endpoint: `${baseUrl}/chat`, baseUrl, mode: 'native', apiKey }
        }
        if (path === '/v1') {
          return { endpoint: `${baseUrl}/v1/chat/completions`, baseUrl, mode: 'openai', apiKey }
        }
        // Custom path entered explicitly
        const mode = path.includes('/v1/') || Boolean(apiKey) ? 'openai' : 'native'
        return { endpoint: normalized, baseUrl, mode, apiKey }
      } catch {
        return { endpoint: normalized, baseUrl: normalized, mode: apiKey ? 'openai' : 'native', apiKey }
      }
    }

    const activeRagConfig = computed(() =>
      resolveRagConfig(savedChatPost.value || chatPostInput.value, savedChatApiKey.value || chatApiKeyInput.value)
    )

    const previewRagConfig = computed(() =>
      resolveRagConfig(chatPostInput.value, chatApiKeyInput.value)
    )

    const isChatConfigured = computed(() => Boolean(activeRagConfig.value.endpoint))
    const resolvedChatEndpoint = computed(() => activeRagConfig.value.endpoint)
    const previewResolvedEndpoint = computed(() => previewRagConfig.value.endpoint)

    const detectedApiModeLabel = computed(() => {
      const cfg = previewRagConfig.value
      if (!cfg.endpoint) return 'ยังไม่ได้ตั้งค่า'
      return cfg.mode === 'openai' ? 'POST /v1/chat/completions' : 'POST /chat (SSE)'
    })

    const loadChatConfig = () => {
      try {
        const raw = window.localStorage.getItem(CHAT_CONFIG_STORAGE_KEY)
        if (raw) {
          const parsed = JSON.parse(raw)
          chatPostInput.value = parsed.postUrl || ''
          chatApiKeyInput.value = parsed.apiKey || ''
          savedChatPost.value = parsed.postUrl || ''
          savedChatApiKey.value = parsed.apiKey || ''
        }
      } catch (err) {
        console.warn('Unable to load RAG chat config:', err)
      }
    }

    const saveChatSettings = () => {
      savedChatPost.value = chatPostInput.value.trim()
      savedChatApiKey.value = chatApiKeyInput.value.trim()
      try {
        window.localStorage.setItem(
          CHAT_CONFIG_STORAGE_KEY,
          JSON.stringify({
            postUrl: savedChatPost.value,
            apiKey: savedChatApiKey.value
          })
        )
        const cfg = resolveRagConfig(savedChatPost.value, savedChatApiKey.value)
        if (cfg.endpoint) {
          chatConfigStatus.value = {
            type: 'success',
            message: `บันทึกแล้ว: ${cfg.endpoint}`
          }
        } else {
          chatConfigStatus.value = {
            type: 'info',
            message: 'ล้างการตั้งค่าแล้ว (ทำงานในโหมดจำลอง)'
          }
        }
      } catch (err) {
        chatConfigStatus.value = {
          type: 'error',
          message: `บันทึกไม่สำเร็จ: ${err.message}`
        }
      }
    }

    const clearChatSettings = () => {
      chatPostInput.value = ''
      chatApiKeyInput.value = ''
      savedChatPost.value = ''
      savedChatApiKey.value = ''
      ragConversationId.value = null
      window.localStorage.removeItem(CHAT_CONFIG_STORAGE_KEY)
      chatConfigStatus.value = {
        type: 'info',
        message: 'ล้างค่า POST และ API Key เรียบร้อยแล้ว'
      }
    }

    const buildAuthHeaders = (apiKey) => {
      const headers = {
        'Content-Type': 'application/json'
      }
      if (apiKey) {
        const cleanKey = apiKey.replace(/^Bearer\s+/i, '').trim()
        headers['Authorization'] = `Bearer ${cleanKey}`
        headers['X-API-Key'] = cleanKey
      }
      return headers
    }

    const testChatConnection = async () => {
      const cfg = resolveRagConfig(chatPostInput.value, chatApiKeyInput.value)
      if (!cfg.endpoint) {
        chatConfigStatus.value = {
          type: 'error',
          message: 'กรุณากรอก POST URL หรือ Port ก่อนทดสอบ (เช่น http://localhost:1152)'
        }
        return
      }

      isTestingChatApi.value = true
      chatConfigStatus.value = { type: 'info', message: `กำลังทดสอบการเชื่อมต่อไปยัง ${cfg.baseUrl} ...` }

      try {
        const headers = buildAuthHeaders(cfg.apiKey)
        // If OpenAI mode or API key provided, test /v1/models first, fallback to /system/health
        let testUrl = cfg.mode === 'openai' && cfg.apiKey ? `${cfg.baseUrl}/v1/models` : `${cfg.baseUrl}/system/health`
        let res = await fetch(testUrl, { method: 'GET', headers }).catch(() => null)

        if (!res || (!res.ok && testUrl.endsWith('/v1/models'))) {
          const healthRes = await fetch(`${cfg.baseUrl}/system/health`, { method: 'GET' }).catch(() => null)
          if (healthRes && healthRes.ok) {
            res = healthRes
          }
        }

        if (!res) {
          throw new Error(`ไม่สามารถเชื่อมต่อ ${cfg.baseUrl} ได้ (ตรวจสอบว่าเปิด Server หรือ Port ถูกต้อง และเปิด CORS แล้ว)`)
        }

        if (res.status === 401 || res.status === 403) {
          throw new Error(`เชื่อมต่อเซิร์ฟเวอร์ได้ แต่ API Key ไม่ถูกต้องหรือไม่มีสิทธิ์ (HTTP ${res.status})`)
        }

        if (!res.ok) {
          throw new Error(`เซิร์ฟเวอร์ตอบกลับด้วยสถานะ HTTP ${res.status}`)
        }

        // Auto-save on successful test
        saveChatSettings()
        chatConfigStatus.value = {
          type: 'success',
          message: `เชื่อมต่อสำเร็จ! พร้อมส่งคำถามไปยัง ${cfg.endpoint}`
        }
      } catch (err) {
        chatConfigStatus.value = {
          type: 'error',
          message: err.message || 'ไม่สามารถเชื่อมต่อกับ API ได้'
        }
      } finally {
        isTestingChatApi.value = false
      }
    }

    const scrollToBottom = () => {
      nextTick(() => {
        const container = chatContainerRef.value || document.querySelector('.chatbot-messages')
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    }

    const stopChatStreaming = () => {
      if (activeChatAbortController) {
        activeChatAbortController.abort()
        activeChatAbortController = null
      }
      isChatStreaming.value = false
    }

    const resetChatConversation = () => {
      stopChatStreaming()
      ragConversationId.value = null
      chatMessages.value = [
        {
          id: Date.now(),
          type: 'assistant',
          text: isChatConfigured.value
            ? `เริ่มบทสนทนาใหม่แล้ว (เชื่อมต่อไปยัง ${resolvedChatEndpoint.value})`
            : 'สวัสดีครับ ฉันเป็น AI Assistant ของระบบ Weaponeering พร้อมช่วยวิเคราะห์และตอบคำถามจากฐานข้อมูล'
        }
      ]
    }

    /**
     * Stream or parse response from OpenAI-compatible POST /v1/chat/completions (api-manual.md §7)
     * OR Native POST /chat (api-manual.md §5 & §10)
     */
    const sendChatMessage = async () => {
      const question = chatInput.value.trim()
      if (!question || isChatStreaming.value) return

      // Ensure any unsaved inputs in the gear box are also used if user typed them and hit Enter directly
      if (chatPostInput.value.trim() && !savedChatPost.value) {
        saveChatSettings()
      }

      const cfg = activeRagConfig.value
      chatInput.value = ''

      // Build conversation history before pushing the new messages
      const historyMessages = chatMessages.value
        .filter((m) => !m.isError && m.id !== 1 && (m.type === 'user' || m.type === 'assistant') && m.text.trim())
        .map((m) => ({
          role: m.type === 'user' ? 'user' : 'assistant',
          content: m.text
        }))

      const userMsgId = Date.now()
      chatMessages.value.push({
        id: userMsgId,
        type: 'user',
        text: question
      })
      scrollToBottom()

      // Fallback to mock response if user hasn't configured POST URL yet
      if (!cfg.endpoint) {
        setTimeout(() => {
          chatMessages.value.push({
            id: Date.now() + 1,
            type: 'assistant',
            text: `${mockAPI.getChatbotResponse(question)}\n\n💡 (ขณะนี้อยู่ในโหมดจำลอง — กดปุ่มรูปฟันเฟือง ⚙️ มุมขวาบนเพื่อใส่ POST URL และ API Key สำหรับเชื่อมต่อ RAG Server จริง)`
          })
          scrollToBottom()
        }, 350)
        return
      }

      // Create placeholder assistant message for live streaming
      const botMsg = ref({
        id: Date.now() + 1,
        type: 'assistant',
        text: '',
        citations: [],
        streaming: true,
        isError: false
      })
      chatMessages.value.push(botMsg.value)
      scrollToBottom()

      isChatStreaming.value = true
      activeChatAbortController = new AbortController()

      try {
        const headers = buildAuthHeaders(cfg.apiKey)
        let requestBody

        if (cfg.mode === 'openai') {
          // OpenAI-compatible format per api-manual.md §7.3
          requestBody = {
            model: 'rag-grounded',
            messages: [...historyMessages, { role: 'user', content: question }],
            stream: true,
            grounding_footer: true
          }
        } else {
          // Native RAG format per api-manual.md §5.1 / §10.2
          requestBody = {
            question,
            scope: { mode: 'all', documentIds: [] },
            conversationId: ragConversationId.value || null
          }
        }

        const response = await fetch(cfg.endpoint, {
          method: 'POST',
          headers,
          body: JSON.stringify(requestBody),
          signal: activeChatAbortController.signal
        })

        if (!response.ok) {
          let errDetail = `HTTP ${response.status}`
          try {
            const errJson = await response.json()
            errDetail = errJson?.error?.message || errJson?.detail || errDetail
          } catch {
            // ignore json parse error
          }
          throw new Error(`การเชื่อมต่อล้มเหลว (${errDetail})`)
        }

        const contentType = (response.headers.get('content-type') || '').toLowerCase()

        // Case 1: Standard JSON response (non-streaming)
        if (contentType.includes('application/json')) {
          const data = await response.json()
          if (data?.choices?.[0]?.message?.content != null) {
            botMsg.value.text = data.choices[0].message.content
          } else if (typeof data?.answer === 'string') {
            botMsg.value.text = data.answer
          } else if (typeof data?.text === 'string') {
            botMsg.value.text = data.text
          } else {
            botMsg.value.text = JSON.stringify(data, null, 2)
          }
          if (Array.isArray(data?.citations)) {
            botMsg.value.citations = data.citations
          }
          if (data?.conversationId) {
            ragConversationId.value = data.conversationId
          }
          return
        }

        // Case 2: SSE Streaming response (text/event-stream) for both /v1/chat/completions and /chat
        const reader = response.body?.getReader()
        if (!reader) {
          const textFallback = await response.text()
          botMsg.value.text = textFallback || 'ไม่ได้รับข้อความตอบกลับ'
          return
        }

        const decoder = new TextDecoder('utf-8')
        let buffer = ''
        let currentEventName = null

        const processLine = (rawLine) => {
          const line = rawLine.trimEnd()
          if (!line) {
            currentEventName = null
            return
          }
          if (line.startsWith('event:')) {
            currentEventName = line.slice(6).trim()
            return
          }
          if (!line.startsWith('data:')) return

          const dataStr = line.slice(5).trim()
          if (!dataStr || dataStr === '[DONE]') return

          try {
            const payload = JSON.parse(dataStr)

            // Format A: OpenAI-compatible SSE chunk (choices[0].delta.content)
            if (Array.isArray(payload.choices)) {
              const deltaContent = payload.choices[0]?.delta?.content
              if (deltaContent) {
                botMsg.value.text += deltaContent
                scrollToBottom()
              }
              if (Array.isArray(payload.citations) && payload.citations.length) {
                botMsg.value.citations = payload.citations
              }
              return
            }

            // Format B: Native /chat SSE events (event: delta -> {text}, event: done -> {citations, conversationId})
            if (currentEventName === 'delta' || typeof payload.text === 'string') {
              botMsg.value.text += payload.text || ''
              scrollToBottom()
              return
            }

            if (currentEventName === 'done' || payload.conversationId || Array.isArray(payload.citations)) {
              if (Array.isArray(payload.citations)) {
                botMsg.value.citations = payload.citations
              }
              if (payload.conversationId) {
                ragConversationId.value = payload.conversationId
              }
            }
          } catch {
            // Ignore malformed partial JSON chunk
          }
        }

        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          for (const line of lines) {
            processLine(line)
          }
        }
        if (buffer.trim()) {
          for (const line of buffer.split('\n')) {
            processLine(line)
          }
        }

        if (!botMsg.value.text.trim()) {
          botMsg.value.text = 'ระบบได้รับคำขอแล้วแต่ไม่มีข้อความตอบกลับ'
        }
      } catch (err) {
        if (err.name === 'AbortError') {
          if (!botMsg.value.text) {
            botMsg.value.text = '(ยกเลิกการตอบคำถาม)'
          }
        } else {
          botMsg.value.isError = true
          botMsg.value.text = `⚠️ ${err.message || 'ไม่สามารถเชื่อมต่อกับ RAG API ได้ กรุณาตรวจสอบ POST URL และ API Key ที่ปุ่มฟันเฟือง ⚙️'}`
        }
      } finally {
        botMsg.value.streaming = false
        isChatStreaming.value = false
        activeChatAbortController = null
        scrollToBottom()
      }
    }

    const showSaveModal = ref(false)
    const showSaveConfirmation = ref(false)
    const showRecommendationModal = ref(false)
    const showExportMenu = ref(false)
    const exportMenuRef = ref(null)
    const recorderName = ref('')
    const savedRecordsCount = ref(0)
    const DB_KEY = 'weaponeering_records'

    watch(
      () => props.recommendationsData,
      (rows) => {
        if (rows == null) {
          recommendations.value = mockAPI.recommendations
        } else if (Array.isArray(rows)) {
          recommendations.value = rows
        }
      },
      { immediate: true, deep: true },
    )

    watch(
      () => props.analysisText,
      (text) => {
        if (text) aiAnalysisText.value = text
        else if (text === '') aiAnalysisText.value = ''
      },
      { immediate: true },
    )

    const selectRecommendation = () => {
      showRecommendationModal.value = true
    }

    const showAllDetails = () => {
      showRecommendationModal.value = true
    }

    const closeRecommendationModal = () => {
      showRecommendationModal.value = false
    }

    const loadSavedRecords = () => {
      try {
        const stored = window.localStorage.getItem(DB_KEY)
        if (stored) {
          const parsed = JSON.parse(stored)
          savedRecordsCount.value = Array.isArray(parsed) ? parsed.length : 0
        }
      } catch (error) {
        console.error('Unable to load saved records', error)
      }
    }

    const openSaveModal = () => {
      showSaveModal.value = true
      recorderName.value = ''
    }

    const closeSaveModal = () => {
      showSaveModal.value = false
      showSaveConfirmation.value = false
      recorderName.value = ''
    }

    const requestSaveConfirmation = () => {
      if (!recorderName.value.trim()) {
        alert('กรุณากรอกชื่อผู้บันทึก')
        return
      }
      showSaveConfirmation.value = true
    }

    const cancelSaveConfirmation = () => {
      showSaveConfirmation.value = false
    }

    const saveRecordToDatabase = () => {
      const name = recorderName.value.trim()
      if (!name) {
        alert('กรุณากรอกชื่อผู้บันทึก')
        return
      }

      try {
        showSaveConfirmation.value = false
        const existing = JSON.parse(window.localStorage.getItem(DB_KEY) || '[]')
        const exportSnapshot = buildExportData()
        const record = buildReportRecordFromPayload(exportSnapshot, name)
        record.summary = {
          recommendations: recommendations.value.slice(0, 5),
          analysis: aiAnalysisText.value,
        }

        existing.push(record)
        window.localStorage.setItem(DB_KEY, JSON.stringify(existing))
        savedRecordsCount.value = existing.length
        emit('save-data', record)
        showSaveModal.value = false
        recorderName.value = ''
      } catch (error) {
        console.error('Unable to save record', error)
        alert('ไม่สามารถบันทึกข้อมูลได้ในขณะนี้')
      }
    }

    const buildExportData = (extra = {}) => buildTargetExportPayload({
      formData: props.formData || {},
      recommendations: recommendations.value,
      analysisText: props.analysisText || aiAnalysisText.value || '',
      priority: props.targetPriority || props.formData?.targetPriority || '',
      ...extra,
    })

    const buildFullExportData = async () => {
      const targetId = props.formData?.id
      if (!targetId) return buildExportData()
      const [{ card, jmem }, scenario] = await Promise.all([
        fetchTargetReportData(targetId).catch(() => ({ card: null, jmem: null })),
        props.scenarioId ? fetchScenarioInfo(props.scenarioId) : null,
      ])
      return buildExportData({ card, jmem, scenarioName: scenario?.name || '' })
    }

    const exportScenario = async (format) => {
      showExportMenu.value = false
      if (!props.scenarioId) return
      try {
        const summary = await fetchScenarioSummary(props.scenarioId)
        const date = new Date().toISOString().split('T')[0]
        const safeName = String(summary.scenarioName).trim().replace(/[\\/:*?"<>|]+/g, '').replace(/\s+/g, '_')
        const filename = `scenario_summary_${safeName}_${date}`
        if (format === 'pdf') await exportService.exportScenarioToPDF(summary, `${filename}.pdf`)
        else await exportService.exportScenarioToWord(summary, `${filename}.docx`)
      } catch (error) {
        console.error('Scenario Export Error:', error)
        alert(`เกิดข้อผิดพลาดในการส่งออกภาพรวม: ${error.message}`)
      }
    }

    const exportData = async (format) => {
      showExportMenu.value = false
      const date = new Date().toISOString().split('T')[0]
      const exportData = await buildFullExportData()
      const targetName = exportData?.mainRow?.name || exportData?.targetInfo?.name || 'เป้าหมาย'
      const safeName = String(targetName).trim().replace(/[\\/:*?"<>|]+/g, '').replace(/\s+/g, '_')
      const filename = `report_${safeName}_${date}`

      try {
        if (format === 'pdf') {
          await exportService.exportToPDF(exportData, `${filename}.pdf`)
          alert('ส่งออก PDF สำเร็จ')
          return
        }

        if (format === 'word') {
          await exportService.exportToWord(exportData, `${filename}.docx`)
          alert('ส่งออก Word สำเร็จ')
          return
        }

        alert('ไม่พบรูปแบบไฟล์ที่รองรับ')
      } catch (error) {
        console.error('Export Error:', error)
        alert(`เกิดข้อผิดพลาดในการส่งออก: ${error.message}`)
      }
    }

    const closeExportMenuOnOutsideClick = (event) => {
      if (exportMenuRef.value && !exportMenuRef.value.contains(event.target)) {
        showExportMenu.value = false
      }
    }

    onMounted(() => {
      loadSavedRecords()
      loadChatConfig()
      document.addEventListener('click', closeExportMenuOnOutsideClick)
    })

    onBeforeUnmount(() => {
      stopChatStreaming()
      document.removeEventListener('click', closeExportMenuOnOutsideClick)
    })

    return {
      recommendations,
      aiAnalysisText,
      chatMessages,
      chatInput,
      chatContainerRef,
      showChatSettings,
      showChatApiKey,
      chatPostInput,
      chatApiKeyInput,
      chatConfigStatus,
      isTestingChatApi,
      isChatStreaming,
      isChatConfigured,
      resolvedChatEndpoint,
      previewResolvedEndpoint,
      detectedApiModeLabel,
      saveChatSettings,
      clearChatSettings,
      testChatConnection,
      stopChatStreaming,
      resetChatConversation,
      showSaveModal,
      showSaveConfirmation,
      showRecommendationModal,
      showExportMenu,
      exportMenuRef,
      recorderName,
      savedRecordsCount,
      selectRecommendation,
      showAllDetails,
      closeRecommendationModal,
      sendChatMessage,
      openSaveModal,
      closeSaveModal,
      requestSaveConfirmation,
      cancelSaveConfirmation,
      saveRecordToDatabase,
      exportData,
      exportScenario
    }
  }
}
</script>

<style scoped>
.right-panel {
  background: var(--panel-bg);
  border-left: 2px solid var(--border);
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 4px;
}

.right-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 62px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(225deg, rgba(13, 110, 253, 0.16), rgba(96, 70, 200, 0.08));
}

.right-panel-brand {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 9px;
}

.right-panel-brand-icon {
  display: inline-flex;
  flex: 0 0 36px;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid #5b92e8;
  border-radius: 9px;
  background: #0d6efd;
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.28);
  color: #ffffff;
  font-size: 1.05rem;
}

.right-panel-brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.right-panel-brand-copy strong {
  overflow: hidden;
  color: var(--text);
  font-size: 0.9rem;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.right-panel-brand-copy small {
  color: var(--muted);
  font-size: 0.66rem;
  white-space: nowrap;
}

.right-panel-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.right-panel-toggle {
  display: inline-flex;
  flex: 0 0 30px;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--control-bg);
  color: #6ea8fe;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.right-panel-toggle:hover {
  border-color: #0d6efd;
  background: #0d6efd;
  color: #ffffff;
  transform: scale(1.04);
}

.right-panel.collapsed .right-panel-header {
  flex-direction: column;
  justify-content: flex-start;
  padding: 10px 7px;
}

.right-panel.collapsed .right-panel-brand {
  order: 1;
  justify-content: center;
}

.right-panel.collapsed .right-panel-actions {
  order: 2;
  flex-direction: column;
}

.right-panel-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.section-title {
  font-weight: 600;
  color: #0d6efd;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-tabs {
  gap: 5px;
  padding: 5px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.18);
}

.nav-tabs .nav-link {
  width: 100%;
  min-height: 38px;
  padding: 7px 8px;
  border: 0 !important;
  border-radius: 7px;
  color: var(--text);
  font-size: 0.78rem;
  font-weight: 500;
  background: transparent;
  transition: background-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.nav-tabs .nav-link:hover:not(.active) {
  border: 0;
  background: rgba(13, 110, 253, 0.1);
  color: #6ea8fe;
}

.nav-tabs .nav-link.active {
  border: 0 !important;
  background: #0d6efd;
  box-shadow: 0 4px 10px rgba(13, 110, 253, 0.3);
  color: #ffffff;
  transform: translateY(-1px);
}

.nav-tabs .nav-link.active i {
  color: #ffffff;
}

:global(body.dark-theme .nav-tabs .nav-link.active),
:global(body.light-theme .nav-tabs .nav-link.active) {
  border-color: transparent !important;
  background-color: #0d6efd !important;
  background-image: none !important;
  color: #ffffff !important;
}

:global(body.dark-theme .nav-tabs .nav-link.active i),
:global(body.light-theme .nav-tabs .nav-link.active i) {
  color: #ffffff !important;
}

.recommendation-title {
  padding: 2px 3px;
}

.title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(145deg, #2f73d9, #173f8d);
  box-shadow: 0 3px 8px rgba(13, 110, 253, 0.3);
  color: #ffffff;
}

.top-five-badge {
  margin-left: auto;
  padding: 3px 8px;
  border: 1px solid rgba(255, 193, 7, 0.45);
  border-radius: 999px;
  background: rgba(255, 193, 7, 0.12);
  color: #e4ad08;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.recommendation-card {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
}

.recommendation-table {
  --bs-table-bg: transparent;
  --bs-table-color: var(--text);
  width: 100%;
  min-width: 100%;
  table-layout: fixed;
  margin-bottom: 0;
  border: 0;
  color: var(--text);
  font-size: 0.7rem;
}

.recommendation-table thead {
  --bs-table-bg: #12376f;
  --bs-table-color: #ffffff;
  background: linear-gradient(90deg, #12376f, #16529b);
  color: #ffffff;
}

.recommendation-table thead th {
  padding: 8px 3px;
  border: 0;
  color: #dbe9ff;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-align: center;
  white-space: nowrap;
}

.recommendation-table th:nth-child(1),
.recommendation-table td:nth-child(1) { width: 12%; }
.recommendation-table th:nth-child(2),
.recommendation-table td:nth-child(2) { width: 20%; }
.recommendation-table th:nth-child(3),
.recommendation-table td:nth-child(3) { width: 26%; }
.recommendation-table th:nth-child(4),
.recommendation-table td:nth-child(4) { width: 14%; }
.recommendation-table th:nth-child(5),
.recommendation-table td:nth-child(5),
.recommendation-table th:nth-child(6),
.recommendation-table td:nth-child(6) { width: 14%; }

.recommendation-table thead th:nth-child(2) {
  text-align: left;
}

.recommendation-table tbody tr {
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background-color 0.18s ease, box-shadow 0.18s ease;
}

.recommendation-table tbody tr:last-child {
  border-bottom: 0;
}

.recommendation-table tbody tr:nth-child(even) {
  background: rgba(13, 110, 253, 0.035);
}

.recommendation-table tbody tr:hover {
  background: rgba(13, 110, 253, 0.13);
  box-shadow: inset 3px 0 #0d6efd;
}

.recommendation-table tbody td {
  padding: 7px 3px;
  border: 0;
  color: var(--text);
  vertical-align: middle;
  white-space: nowrap;
}

.rank-number {
  text-align: center;
}

.target-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 1px solid rgba(255, 255, 255, 0.38);
  border-radius: 50%;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.34), 0 3px 7px rgba(0, 0, 0, 0.24);
  font-size: 0.72rem;
  font-weight: 700;
}

.rank-red {
  background: linear-gradient(145deg, #ff646d, #bd2531);
  color: #ffffff;
}

.rank-yellow {
  border-color: #ffe78b;
  background: linear-gradient(145deg, #ffe26b, #d5a911);
  color: #2a2100;
}

.rank-green {
  background: linear-gradient(145deg, #4bd790, #168451);
  color: #ffffff;
}

.rank-default {
  border-color: #58728d;
  background: #263b50;
  color: #c9d8e8;
}

.recommendation-name {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  overflow: hidden;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.size-chip {
  padding: 2px 4px;
  border: 1px solid var(--border);
  border-radius: 5px;
  background: rgba(108, 117, 125, 0.1);
  color: var(--text);
  font-size: 0.61rem;
  white-space: nowrap;
}

.qty-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  border-radius: 6px;
  background: rgba(111, 66, 193, 0.16);
  color: #9b7fe4;
  font-weight: 700;
}

.score-pill {
  display: inline-block;
  min-width: 33px;
  padding: 3px 4px;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
  text-align: center;
}

.pd-score {
  background: rgba(13, 110, 253, 0.14);
  color: #6ea8fe;
}

.pk-score {
  background: rgba(25, 135, 84, 0.16);
  color: #42ca82;
}

.recommendation-card::-webkit-scrollbar {
  height: 6px;
}

.recommendation-card::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: #3869a7;
}

.view-all-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 38px;
  margin-top: 10px;
  border: 1px solid rgba(13, 110, 253, 0.5);
  border-radius: 8px;
  background: rgba(13, 110, 253, 0.08);
  color: #4b91f7;
  font-family: inherit;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.view-all-button:hover {
  background: #0d6efd;
  color: #ffffff;
  transform: translateY(-1px);
}

.view-all-button i {
  transition: transform 0.18s ease;
}

.view-all-button:hover i {
  transform: translateX(3px);
}

.analysis-result {
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: 4px;
  padding: 12px;
  font-size: 0.85rem;
  max-height: 250px;
  overflow-y: auto;
  color: var(--text);
}

.analysis-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 0.8rem;
  line-height: 1.4;
  color: var(--text);
}

.confidence-card {
  overflow: hidden;
  border: 1px solid #294968;
  border-radius: 10px;
  background: radial-gradient(circle at 22% 85%, rgba(13, 110, 253, 0.12), transparent 44%), #07131f;
  box-shadow: 0 7px 20px rgba(0, 0, 0, 0.26);
}

.confidence-heading {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 11px;
  border-bottom: 1px solid #213a52;
  color: #c8d9e9;
  font-size: 0.72rem;
  font-weight: 500;
}

.confidence-heading i {
  color: #63a6ed;
}

.confidence-content {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 120px;
  padding: 10px 12px 12px;
}

:global(body.light-theme .confidence-card) { border-color: #bfd0df; background: radial-gradient(circle at 22% 85%, rgba(13, 110, 253, 0.08), transparent 44%), #ffffff; box-shadow: 0 7px 18px rgba(31, 65, 98, 0.12); }
:global(body.light-theme .confidence-heading) { border-bottom-color: #d2dee9; color: #28465f; }

.confidence-gauge {
  position: relative;
  flex: 0 0 132px;
  width: 132px;
  height: 84px;
}

.confidence-gauge svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.gauge-track,
.gauge-value {
  fill: none;
  stroke-width: 10;
  stroke-linecap: round;
}

.gauge-track {
  stroke: #172c3f;
}

.gauge-value {
  stroke: url(#confidenceGradient);
  stroke-dasharray: 85 100;
  filter: drop-shadow(0 0 4px rgba(59, 188, 188, 0.45));
  animation: confidenceFill 0.8s ease-out both;
}

.confidence-number {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  color: #ffffff;
  font: 500 1.9rem/1 'Segoe UI', sans-serif;
  text-align: center;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.7);
}

.confidence-number small {
  margin-left: 2px;
  color: #b9c9d7;
  font-size: 0.72rem;
}

.confidence-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.confidence-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #ff9c4c;
  font-size: 0.74rem;
  font-weight: 600;
  white-space: nowrap;
}

.confidence-status i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ff8b39;
  box-shadow: 0 0 7px rgba(255, 139, 57, 0.8);
}

.confidence-copy strong {
  color: #d9e6f2;
  font-size: 0.7rem;
  font-weight: 500;
}

.confidence-copy small {
  color: #778da3;
  font-size: 0.62rem;
}

@keyframes confidenceFill {
  from { stroke-dasharray: 0 100; }
  to { stroke-dasharray: 85 100; }
}

@media (max-width: 340px) {
  .confidence-content { gap: 6px; padding-right: 7px; padding-left: 7px; }
  .confidence-gauge { flex-basis: 118px; width: 118px; }
  .confidence-status { font-size: 0.68rem; }
}

.chat-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
}

.chat-header-left span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  display: inline-block;
}

.chat-status-dot.connected {
  background: #20c997;
  box-shadow: 0 0 6px rgba(32, 201, 151, 0.8);
}

.chat-status-dot.unconfigured {
  background: #6c757d;
}

.chat-header-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.chat-icon-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.82rem;
}

.chat-icon-btn:hover {
  border-color: #0d6efd;
  color: #4da3ff;
  background: rgba(13, 110, 253, 0.12);
}

.chat-icon-btn.active {
  border-color: #0d6efd;
  background: #0d6efd;
  color: #ffffff;
}

.chat-settings-box {
  background: var(--surface);
  border: 1px solid #2b4c6f;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 0.78rem;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.22);
  animation: slideIn 0.2s ease-out;
}

.chat-settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-weight: 600;
  color: #cfe2ff;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

:global(body.light-theme .chat-settings-header) {
  color: #1e3a5f;
  border-bottom-color: rgba(0, 0, 0, 0.1);
}

.chat-mode-badge {
  font-size: 0.66rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(13, 110, 253, 0.18);
  color: #7abaff;
  border: 1px solid rgba(13, 110, 253, 0.35);
  font-family: monospace;
}

:global(body.light-theme .chat-mode-badge) {
  color: #0a58ca;
  background: rgba(13, 110, 253, 0.1);
}

.chat-field-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-field-label {
  font-size: 0.73rem;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 5px;
}

.chat-config-input {
  font-size: 0.76rem;
  background: rgba(0, 0, 0, 0.2);
  color: var(--text);
  border-color: var(--border);
}

:global(body.light-theme .chat-config-input) {
  background: #ffffff;
}

.chat-field-hint {
  font-size: 0.66rem;
  color: #8aa0b6;
  line-height: 1.3;
}

.chat-eye-btn {
  font-size: 0.75rem;
  padding: 0 8px;
}

.chat-Resolved-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding: 5px 8px;
  border-radius: 4px;
  background: rgba(13, 110, 253, 0.08);
  border: 1px dashed rgba(13, 110, 253, 0.3);
  font-size: 0.7rem;
}

.chat-Resolved-preview .preview-label {
  color: #8aa0b6;
  font-weight: 600;
}

.chat-Resolved-preview code {
  word-break: break-all;
  color: #6ea8fe;
}

:global(body.light-theme .chat-Resolved-preview code) {
  color: #0a58ca;
}

.chat-config-alert {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 5px;
  font-size: 0.72rem;
  line-height: 1.35;
}

.chat-config-alert.success {
  background: rgba(25, 135, 84, 0.16);
  border: 1px solid rgba(25, 135, 84, 0.4);
  color: #75b798;
}

.chat-config-alert.error {
  background: rgba(220, 53, 69, 0.16);
  border: 1px solid rgba(220, 53, 69, 0.4);
  color: #ea868f;
}

.chat-config-alert.info {
  background: rgba(13, 202, 240, 0.14);
  border: 1px solid rgba(13, 202, 240, 0.35);
  color: #6edff6;
}

:global(body.light-theme .chat-config-alert.success) { color: #0f5132; }
:global(body.light-theme .chat-config-alert.error) { color: #842029; }
:global(body.light-theme .chat-config-alert.info) { color: #055160; }

.chat-settings-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.chatbot-messages {
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: 4px;
  padding: 12px;
  height: 220px;
  overflow-y: auto;
  margin-bottom: 10px;
}

.message {
  margin-bottom: 10px;
  display: flex;
  animation: slideIn 0.3s ease-in-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 85%;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.83rem;
  word-wrap: break-word;
}

.message-text {
  white-space: pre-wrap;
  line-height: 1.45;
}

.message.user .message-content {
  background: #0d6efd;
  color: white;
}

.message.assistant .message-content {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border);
  color: var(--text);
}

:global(body.light-theme .message.assistant .message-content) {
  background: rgba(0, 0, 0, 0.04);
}

.message-content.message-error {
  border-color: rgba(220, 53, 69, 0.5);
  background: rgba(220, 53, 69, 0.12);
}

.streaming-cursor {
  display: inline-block;
  margin-left: 2px;
  color: #0d6efd;
  animation: blinkCursor 0.8s infinite;
}

@keyframes blinkCursor {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.message-citations {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px dashed rgba(255, 255, 255, 0.15);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

:global(body.light-theme .message-citations) {
  border-top-color: rgba(0, 0, 0, 0.15);
}

.citations-title {
  font-size: 0.7rem;
  font-weight: 600;
  color: #8bb9fe;
}

:global(body.light-theme .citations-title) {
  color: #0a58ca;
}

.citation-chip {
  font-size: 0.69rem;
  padding: 3px 7px;
  border-radius: 4px;
  background: rgba(13, 110, 253, 0.12);
  border: 1px solid rgba(13, 110, 253, 0.25);
  color: var(--text);
}

.chat-input {
  display: flex;
  gap: 8px;
}

.ratio ratio-16x9 {
  margin-bottom: 15px;
  border: 2px solid #444444;
  border-radius: 4px;
  overflow: hidden;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.export-control {
  position: relative;
}

.save-export-title,
.action-buttons .btn {
  align-items: center;
  justify-content: center;
  text-align: center;
}

.action-buttons .btn {
  display: inline-flex;
  gap: 7px;
}

.export-toggle {
  position: relative;
  padding-right: 34px;
}

.export-chevron {
  position: absolute;
  right: 12px;
  font-size: 0.68rem;
  transition: transform 0.2s ease;
}

.export-chevron.open {
  transform: rotate(180deg);
}

.export-format-menu {
  position: absolute;
  right: 0;
  bottom: calc(100% + 7px);
  left: 0;
  z-index: 30;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--panel-bg);
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.48);
}

.export-format-heading {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 8px 8px;
  margin-bottom: 4px;
  border-bottom: 1px solid var(--border);
}

.export-format-heading strong {
  color: var(--text);
  font-size: 0.82rem;
}

.export-format-heading small {
  color: var(--muted);
  font-size: 0.65rem;
  line-height: 1.2;
}

.export-format-menu button {
  display: flex;
  min-height: 50px;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  text-align: left;
  transition: background 0.16s ease, transform 0.16s ease;
}

.export-format-menu button:hover:not(:disabled) {
  background: rgba(13, 110, 253, 0.12);
  transform: translateX(2px);
}

.export-format-menu button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.export-format-menu button + .export-format-heading {
  margin-top: 6px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.export-format-menu button > span:last-child {
  display: flex;
  flex-direction: column;
  line-height: 1.18;
}

.export-format-menu strong {
  font-size: 0.8rem;
}

.export-format-menu small {
  margin-top: 3px;
  color: var(--muted);
  font-size: 0.64rem;
}

.export-format-icon {
  display: inline-flex;
  flex: 0 0 32px;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  font-size: 1rem;
}

.export-format-icon.word {
  background: rgba(47, 109, 179, 0.18);
  color: #5aa4f2;
}

.export-format-icon.pdf {
  background: rgba(220, 53, 69, 0.18);
  color: #ff6575;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

.modal-card {
  width: min(90vw, 360px);
  background: #111111;
  border: 2px solid #444444;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
}

.save-modal-card {
  width: min(92vw, 430px);
  border-color: #315f9d;
  border-radius: 12px;
  background: var(--panel-bg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.62);
}

.save-modal-card .modal-header {
  background: linear-gradient(90deg, rgba(13, 110, 253, 0.2), rgba(111, 66, 193, 0.1));
}

.save-modal-card .modal-header h6 {
  color: #8bb9ff;
  font-weight: 600;
}

.save-modal-card .btn-close {
  filter: invert(1) grayscale(1);
}

.save-modal-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 17px !important;
}

.save-field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.save-field-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: #d6e3ef;
  font-size: 0.8rem;
  font-weight: 600;
}

.save-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 23px;
  height: 23px;
  border: 1px solid #6da4f5;
  border-radius: 50%;
  background: #174f9d;
  color: #ffffff;
  font-size: 0.68rem;
}

.priority-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.priority-option {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 5px;
  min-height: 86px;
  padding: 9px 6px;
  border: 1px solid #34495e;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.025);
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, transform 0.18s ease;
}

.priority-option:hover,
.priority-option.selected {
  transform: translateY(-1px);
}

.priority-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.priority-option > .bi {
  position: absolute;
  top: 6px;
  right: 7px;
  font-size: 0.72rem;
}

.priority-color {
  width: 23px;
  height: 23px;
  border: 2px solid rgba(255, 255, 255, 0.46);
  border-radius: 50%;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
}

.priority-copy {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.priority-copy strong {
  color: #e1ebf4;
  font-size: 0.7rem;
}

.priority-copy small {
  color: #7f94a8;
  font-size: 0.6rem;
}

.priority-red .priority-color { background: #e33c49; }
.priority-orange .priority-color { background: #f28b2c; }
.priority-green .priority-color { background: #29a968; }
.priority-red.selected { border-color: #e33c49; background: rgba(227, 60, 73, 0.12); }
.priority-orange.selected { border-color: #f28b2c; background: rgba(242, 139, 44, 0.12); }
.priority-green.selected { border-color: #29a968; background: rgba(41, 169, 104, 0.12); }
.priority-red.selected > .bi { color: #ff7079; }
.priority-orange.selected > .bi { color: #ffad63; }
.priority-green.selected > .bi { color: #59d799; }

.confirmation-backdrop {
  z-index: 1080;
}

.confirmation-card {
  width: min(90vw, 370px);
  padding: 27px 23px 22px;
  border-color: #315f9d;
  border-radius: 14px;
  background: var(--panel-bg);
  color: var(--text);
  text-align: center;
  box-shadow: 0 22px 65px rgba(0, 0, 0, 0.68);
  animation: confirmationPop 0.2s ease-out;
}

.confirmation-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  margin-bottom: 15px;
  border: 1px solid #63a6ed;
  border-radius: 50%;
  background: rgba(13, 110, 253, 0.14);
  box-shadow: 0 0 0 8px rgba(13, 110, 253, 0.06);
  color: #79b4ff;
  font-size: 1.45rem;
}

.confirmation-card h5 {
  margin: 0 0 7px;
  color: var(--text);
  font-size: 1rem;
  font-weight: 700;
}

.confirmation-card p {
  margin: 0 0 20px;
  color: var(--muted);
  font-size: 0.76rem;
}

.confirmation-actions {
  display: flex;
  justify-content: center;
  gap: 9px;
}

.confirmation-cancel,
.confirmation-accept {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 108px;
  min-height: 38px;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.confirmation-cancel {
  border: 1px solid var(--border);
  background: var(--control-bg);
  color: var(--text);
}

.confirmation-cancel:hover {
  border-color: #6c7e90;
  background: #253342;
  color: #ffffff;
}

.confirmation-accept {
  border: 1px solid #4ba97a;
  background: #198754;
  box-shadow: 0 5px 14px rgba(25, 135, 84, 0.3);
  color: #ffffff;
}

.confirmation-accept:hover {
  background: #24a064;
  transform: translateY(-1px);
}

@keyframes confirmationPop {
  from { opacity: 0; transform: translateY(10px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.recommendation-modal-card {
  width: min(92vw, 780px);
  max-height: 88vh;
  border-color: #315f9d;
  border-radius: 12px;
  background: var(--panel-bg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.65);
}

.recommendation-modal-header {
  background: linear-gradient(90deg, rgba(13, 110, 253, 0.2), rgba(111, 66, 193, 0.12));
}

.recommendation-modal-header h6 {
  color: #8bb9ff;
  font-weight: 600;
}

.recommendation-modal-header small {
  color: var(--muted);
}

.recommendation-modal-header .btn-close {
  filter: invert(1) grayscale(1);
}

.recommendation-modal-body {
  overflow-y: auto;
  padding: 16px;
}

.modal-table-card {
  box-shadow: none;
}

.modal-table-card .recommendation-table {
  min-width: 600px;
}

.modal-table-card .recommendation-table tbody tr {
  cursor: default;
}

.recommendation-count {
  margin-right: auto;
  color: var(--muted);
  font-size: 0.78rem;
}

.recommendation-close-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 120px;
  min-height: 38px;
  border: 0;
  border-radius: 8px;
  background: #0d6efd;
  box-shadow: 0 5px 14px rgba(13, 110, 253, 0.3);
  color: #ffffff;
  font-family: inherit;
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.18s ease, transform 0.18s ease;
}

.recommendation-close-button:hover {
  background: #2b7bf0;
  color: #ffffff;
  transform: translateY(-1px);
}

.modal-header,
.modal-body,
.modal-footer {
  padding: 12px 15px;
  border-color: #444444;
  color: #ffffff;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2px solid #444444;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  border-top: 2px solid #444444;
}

.btn-sm {
  font-size: 0.85rem;
}

/* Scrollbar styling */
.right-panel-scroll::-webkit-scrollbar,
.chatbot-messages::-webkit-scrollbar,
.analysis-result::-webkit-scrollbar {
  width: 6px;
}

.right-panel-scroll::-webkit-scrollbar-track,
.chatbot-messages::-webkit-scrollbar-track,
.analysis-result::-webkit-scrollbar-track {
  background: #111111;
}

.right-panel-scroll::-webkit-scrollbar-thumb,
.chatbot-messages::-webkit-scrollbar-thumb,
.analysis-result::-webkit-scrollbar-thumb {
  background: #555555;
  border-radius: 3px;
}

.right-panel-scroll::-webkit-scrollbar-thumb:hover,
.chatbot-messages::-webkit-scrollbar-thumb:hover,
.analysis-result::-webkit-scrollbar-thumb:hover {
  background: #777777;
}

@media (max-width: 992px) {
  .right-panel { height: 100%; border-left: 0; }
  .right-panel-toggle { flex-basis: 38px; width: 38px; height: 38px; }
  .right-panel-scroll { padding: 12px; }
  .recommendation-table { min-width: 560px; }
}

@media (max-width: 600px) {
  .right-panel-header { min-height: 58px; padding: 8px 10px; }
  .right-panel-brand-icon { flex-basis: 32px; width: 32px; height: 32px; }
  .right-panel-brand-copy small { display: none; }
  .right-panel-scroll { padding: 8px; }
  .nav-tabs { position: sticky; top: 0; z-index: 12; gap: 3px; }
  .nav-tabs .nav-link { min-height: 44px; padding: 7px 4px; font-size: 0.72rem; }
  .modal-backdrop { padding: 8px; }
  .modal-card, .save-modal-card, .recommendation-modal-card, .confirmation-card { width: 100%; max-width: 100%; max-height: calc(100dvh - 16px); }
  .modal-header, .modal-body, .modal-footer, .recommendation-modal-body { padding: 10px; }
  .modal-footer { flex-wrap: wrap; }
  .recommendation-count { width: 100%; }
  .recommendation-close-button { width: 100%; }
  .export-format-menu button { min-height: 48px; }
}
</style>

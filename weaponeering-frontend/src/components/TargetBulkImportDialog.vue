<template>
  <Teleport to="body">
    <div v-if="open" class="import-backdrop" @click.self="$emit('close')">
      <div class="import-dialog" role="dialog" aria-modal="true" aria-label="นำเข้าเป้าหมายหลายรายการ">
        <header class="dialog-head">
          <div>
            <span class="kicker">IMPORT</span>
            <h3><i class="bi bi-file-earmark-arrow-up"></i> นำเข้าเป้าหมายหลายรายการ</h3>
            <p>วางข้อมูลจากตารางเป้าหมาย (Excel / Google Sheets) หรืออัปโหลดไฟล์ CSV / TSV</p>
          </div>
          <button type="button" class="icon-btn" title="ปิด" @click="$emit('close')">
            <i class="bi bi-x-lg"></i>
          </button>
        </header>

        <div class="import-actions">
          <label class="file-btn">
            <i class="bi bi-upload"></i>
            เลือกไฟล์
            <input type="file" accept=".csv,.tsv,.txt,.xlsx,.xls,text/csv,text/tab-separated-values,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel" @change="onFileChange" />
          </label>
          <button type="button" class="ghost-btn" @click="loadSample">ตัวอย่างจากตารางเป้าหมาย</button>
          <button type="button" class="ghost-btn" @click="clearAll">ล้าง</button>
        </div>

        <label class="paste-field">
          <span>วางข้อมูลตาราง</span>
          <textarea
            v-model="rawText"
            rows="7"
            spellcheck="false"
            placeholder="TGT	ชื่อเป้าหมาย	Pri	DMPI : พิกัด (Lat/Long)	ความสูง (MSL)(ft.)	..."
          ></textarea>
        </label>

        <div v-if="parsed.rows.length" class="preview-wrap">
          <div class="preview-head">
            <strong>ตัวอย่างก่อนนำเข้า</strong>
            <small>
              {{ validCount }} รายการพร้อมนำเข้า
              <template v-if="invalidCount"> · {{ invalidCount }} มีข้อผิดพลาด</template>
            </small>
          </div>
          <div class="preview-table-wrap">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>TGT</th>
                  <th>ชื่อเป้าหมาย</th>
                  <th>Pri</th>
                  <th>พิกัด</th>
                  <th>ประเภท</th>
                  <th>ขนาด ก×ย×ส (ม.)</th>
                  <th>ผลกระทบ</th>
                  <th>สถานะ</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in parsed.rows" :key="row.rowNumber" :class="{ invalid: !row.valid }">
                  <td>{{ row.rowNumber }}</td>
                  <td>{{ row.tgt || '—' }}</td>
                  <td :title="row.displayName">{{ truncate(row.displayName, 42) }}</td>
                  <td>{{ row.pri || '—' }}</td>
                  <td>
                    <template v-if="row.coords">
                      {{ row.coords.lat.toFixed(5) }}, {{ row.coords.lng.toFixed(5) }}
                    </template>
                    <template v-else>{{ truncate(row.coordinatesRaw, 28) || '—' }}</template>
                  </td>
                  <td :title="row.targetSubtype">{{ row.targetType || '—' }}</td>
                  <td>{{ sizeText(row) }}</td>
                  <td>{{ truncate(row.desiredEffect, 24) || '—' }}</td>
                  <td>
                    <span v-if="row.valid" class="status ok">พร้อม</span>
                    <span v-else class="status bad" :title="row.errors.join(', ')">{{ row.errors[0] }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <p v-else class="hint">ยังไม่มีข้อมูล — วางแถวจากตารางเป้าหมายที่มีคอลัมน์ TGT, ชื่อ, พิกัด DMPI เป็นต้น</p>

        <p v-if="importMessage" class="import-message" :class="{ error: importFailed }">{{ importMessage }}</p>

        <footer class="dialog-foot">
          <small v-if="!scenarioId" class="warn">เลือก scenario ก่อนนำเข้า</small>
          <small v-else>{{ validCount }} รายการจะถูกสร้างใน scenario นี้</small>
          <div class="foot-actions">
            <button type="button" class="ghost-btn" :disabled="importing" @click="$emit('close')">ยกเลิก</button>
            <button
              type="button"
              class="primary-btn"
              :disabled="!canImport"
              @click="runImport"
            >
              <i v-if="importing" class="bi bi-arrow-repeat spin"></i>
              <i v-else class="bi bi-check2-circle"></i>
              {{ importing ? 'กำลังนำเข้า…' : `นำเข้า ${validCount} รายการ` }}
            </button>
          </div>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { computed, ref, watch } from 'vue'
import { createResource } from '../services/api'
import {
  TARGET_IMPORT_SAMPLE,
  importTargetsFromRows,
  parseTargetImportText,
  workbookToImportText,
} from '../utils/targetImportMapper'

export default {
  name: 'TargetBulkImportDialog',
  props: {
    open: { type: Boolean, default: false },
    scenarioId: { type: String, default: '' },
  },
  emits: ['close', 'imported', 'error'],
  setup(props, { emit }) {
    const rawText = ref('')
    const importing = ref(false)
    const importMessage = ref('')
    const importFailed = ref(false)

    const parsed = computed(() => parseTargetImportText(rawText.value))
    const validCount = computed(() => parsed.value.rows.filter((row) => row.valid).length)
    const invalidCount = computed(() => parsed.value.rows.filter((row) => !row.valid).length)
    const canImport = computed(
      () => !!props.scenarioId && validCount.value > 0 && !importing.value,
    )

    function truncate(value, max) {
      const text = String(value || '')
      if (text.length <= max) return text
      return `${text.slice(0, max - 1)}…`
    }

    function sizeText(row) {
      const dims = [row.widthM, row.lengthM, row.heightM]
      if (dims.every((v) => v == null)) return '—'
      return dims.map((v) => (v == null ? '?' : v)).join('×')
    }

    function clearAll() {
      rawText.value = ''
      importMessage.value = ''
      importFailed.value = false
    }

    function loadSample() {
      rawText.value = TARGET_IMPORT_SAMPLE
      importMessage.value = ''
      importFailed.value = false
    }

    async function onFileChange(event) {
      const file = event.target.files?.[0]
      event.target.value = ''
      if (!file) return
      try {
        const name = file.name.toLowerCase()
        if (name.endsWith('.xlsx') || name.endsWith('.xls')) {
          rawText.value = await workbookToImportText(await file.arrayBuffer())
        } else {
          rawText.value = await file.text()
        }
        importMessage.value = `โหลดไฟล์ ${file.name} แล้ว`
        importFailed.value = false
      } catch (err) {
        importMessage.value = err?.message || 'อ่านไฟล์ไม่สำเร็จ'
        importFailed.value = true
      }
    }

    async function runImport() {
      if (!canImport.value) return
      importing.value = true
      importMessage.value = ''
      importFailed.value = false
      try {
        const { results, successCount, failCount } = await importTargetsFromRows(
          parsed.value.rows,
          props.scenarioId,
          createResource,
        )
        if (successCount > 0 && failCount === 0) {
          importMessage.value = `นำเข้าสำเร็จ ${successCount} รายการ`
          emit('imported', { successCount, results })
          emit('close')
        } else if (successCount > 0) {
          importMessage.value = `นำเข้าสำเร็จ ${successCount} รายการ, ล้มเหลว ${failCount} รายการ`
          importFailed.value = true
          emit('imported', { successCount, failCount, results })
        } else {
          importMessage.value = results[0]?.error || 'นำเข้าไม่สำเร็จ'
          importFailed.value = true
          emit('error', importMessage.value)
        }
      } catch (err) {
        importMessage.value = err?.message || 'นำเข้าไม่สำเร็จ'
        importFailed.value = true
        emit('error', importMessage.value)
      } finally {
        importing.value = false
      }
    }

    watch(
      () => props.open,
      (isOpen) => {
        if (!isOpen) return
        importMessage.value = ''
        importFailed.value = false
      },
    )

    return {
      rawText,
      importing,
      importMessage,
      importFailed,
      parsed,
      validCount,
      invalidCount,
      canImport,
      truncate,
      sizeText,
      clearAll,
      loadSample,
      onFileChange,
      runImport,
    }
  },
}
</script>

<style scoped>
.import-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1650;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(2, 8, 16, 0.68);
}

.import-dialog {
  display: flex;
  flex-direction: column;
  width: min(920px, 100%);
  max-height: min(88vh, 900px);
  overflow: hidden;
  border: 1px solid #355574;
  border-radius: 14px;
  background: #0b1a2b;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);
  color: #e8f1fa;
}

.dialog-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 16px 10px;
  border-bottom: 1px solid #27405a;
}

.kicker {
  display: block;
  color: #6ea8fe;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.dialog-head h3 {
  margin: 2px 0 0;
  font-size: 0.98rem;
}

.dialog-head p {
  margin: 6px 0 0;
  color: #8fb4d8;
  font-size: 0.74rem;
}

.icon-btn,
.ghost-btn,
.primary-btn,
.file-btn {
  border: 1px solid #355574;
  border-radius: 8px;
  background: #102336;
  color: #c8ddf3;
  font-family: inherit;
}

.icon-btn {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
}

.ghost-btn,
.primary-btn,
.file-btn {
  min-height: 34px;
  padding: 0 12px;
  font-size: 0.75rem;
  font-weight: 700;
}

.file-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.file-btn input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.primary-btn {
  border-color: #0d6efd;
  background: #0d6efd;
  color: #fff;
}

.primary-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.import-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px 0;
}

.paste-field {
  display: grid;
  gap: 6px;
  padding: 12px 16px 0;
}

.paste-field span {
  color: #8fb4d8;
  font-size: 0.72rem;
  font-weight: 700;
}

.paste-field textarea {
  width: 100%;
  min-height: 140px;
  padding: 10px 12px;
  border: 1px solid #355574;
  border-radius: 10px;
  background: #0f2236;
  color: #e8f1fa;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.72rem;
  line-height: 1.45;
  resize: vertical;
}

.preview-wrap {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  margin-top: 12px;
  padding: 0 16px;
}

.preview-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.preview-head strong {
  font-size: 0.8rem;
}

.preview-head small {
  color: #8fb4d8;
  font-size: 0.7rem;
}

.preview-table-wrap {
  flex: 1;
  overflow: auto;
  border: 1px solid #27405a;
  border-radius: 10px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.72rem;
}

.preview-table th,
.preview-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #22384f;
  text-align: left;
  vertical-align: top;
}

.preview-table th {
  position: sticky;
  top: 0;
  background: #102336;
  color: #8fb4d8;
  font-weight: 700;
}

.preview-table tr.invalid {
  background: rgba(239, 68, 68, 0.08);
}

.status.ok {
  color: #81d9aa;
  font-weight: 700;
}

.status.bad {
  color: #fca5a5;
  font-weight: 700;
}

.hint,
.import-message {
  margin: 12px 16px 0;
  font-size: 0.74rem;
}

.hint {
  color: #8fb4d8;
}

.import-message {
  color: #81d9aa;
}

.import-message.error {
  color: #fca5a5;
}

.dialog-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 16px;
  margin-top: 12px;
  border-top: 1px solid #27405a;
}

.dialog-foot small {
  color: #8fb4d8;
  font-size: 0.72rem;
}

.dialog-foot small.warn {
  color: #fcd34d;
}

.foot-actions {
  display: flex;
  gap: 8px;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>

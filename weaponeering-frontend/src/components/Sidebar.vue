<template>
  <div class="sidebar-container" :class="{ collapsed }">
    <div class="sidebar-header">
      <div class="sidebar-brand">
        <span class="sidebar-brand-icon"><i class="bi bi-sliders2-vertical"></i></span>
        <div v-show="!collapsed" class="sidebar-brand-copy">
          <strong>ข้อมูลเป้าหมาย</strong>
          <small>Target Configuration</small>
        </div>
      </div>
      <div class="sidebar-actions">
        <button
          type="button"
          class="sidebar-toggle"
          :title="collapsed ? 'เปิดแถบบาร์' : 'ปิดแถบบาร์'"
          :aria-label="collapsed ? 'เปิดแถบบาร์' : 'ปิดแถบบาร์'"
          @click="$emit('toggle-sidebar')"
        >
          <i class="bi" :class="collapsed ? 'bi-chevron-right' : 'bi-chevron-left'"></i>
        </button>
        <button
          type="button"
          class="sidebar-reset"
          title="ล้างค่าและเริ่มต้นใหม่เฉพาะข้อมูลเป้าหมาย"
          aria-label="ล้างค่าและเริ่มต้นใหม่เฉพาะข้อมูลเป้าหมาย"
          :disabled="collapsed"
          @click="$emit('reset-target')"
        >
          <i class="bi bi-eraser"></i>
        </button>
        <button
          type="button"
          class="sidebar-reset-all"
          title="ล้างค่าและเริ่มต้นใหม่ทั้งหมด"
          aria-label="ล้างค่าและเริ่มต้นใหม่ทั้งหมด"
          :disabled="collapsed"
          @click="$emit('reset-all')"
        >
          <i class="bi bi-arrow-repeat"></i>
        </button>
      </div>
    </div>

    <div v-show="!collapsed" class="sidebar-scroll">
      <!-- 1. Target Source Selection -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">1</span><i class="bi bi-target"></i> เลือกแหล่งที่มาของเป้าหมาย
        </label>
        <details ref="targetSourceDropdown" class="target-source-dropdown">
          <summary class="target-source-trigger">
            <i
              class="source-icon bi"
              :class="selectedTargetSourceData?.icon || 'bi-bullseye'"
              aria-hidden="true"
            ></i>
            <span>{{ selectedTargetSourceData?.name || '-- เลือกแหล่งที่มา --' }}</span>
            <i class="dropdown-chevron bi bi-chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="target-source-list" role="radiogroup" aria-label="แหล่งที่มาของเป้าหมาย">
            <button
              v-for="source in formData.targetSources"
              :key="source.id"
              type="button"
              class="target-source-option"
              :class="{ active: formData.selectedTargetSource === source.name }"
              role="radio"
              :aria-checked="formData.selectedTargetSource === source.name"
              @click="selectTargetSource(source)"
            >
              <i class="source-icon bi" :class="source.icon" aria-hidden="true"></i>
              <span>{{ source.name }}</span>
              <i
                v-if="formData.selectedTargetSource === source.name"
                class="selection-check bi bi-check-lg"
                aria-hidden="true"
              ></i>
            </button>
          </div>
        </details>

        <div class="target-priority-field">
          <div class="target-priority-label">
            <i class="bi bi-flag-fill"></i>
            <span>ความสำคัญของเป้าหมาย</span>
          </div>
          <div class="target-priority-options" role="radiogroup" aria-label="ความสำคัญของเป้าหมาย">
            <label class="target-priority-option priority-red" :class="{ selected: formData.targetPriority === 'red' }">
              <input v-model="formData.targetPriority" type="radio" value="red" @change="$emit('priority-change', formData.targetPriority)" />
              <span class="priority-dot"></span>
              <span>สำคัญสูง</span>
              <i v-if="formData.targetPriority === 'red'" class="bi bi-check-lg"></i>
            </label>
            <label class="target-priority-option priority-orange" :class="{ selected: formData.targetPriority === 'orange' }">
              <input v-model="formData.targetPriority" type="radio" value="orange" @change="$emit('priority-change', formData.targetPriority)" />
              <span class="priority-dot"></span>
              <span>ปานกลาง</span>
              <i v-if="formData.targetPriority === 'orange'" class="bi bi-check-lg"></i>
            </label>
            <label class="target-priority-option priority-green" :class="{ selected: formData.targetPriority === 'green' }">
              <input v-model="formData.targetPriority" type="radio" value="green" @change="$emit('priority-change', formData.targetPriority)" />
              <span class="priority-dot"></span>
              <span>ทั่วไป</span>
              <i v-if="formData.targetPriority === 'green'" class="bi bi-check-lg"></i>
            </label>
          </div>
        </div>
      </div>

      <!-- 2. Target Type (Dropdown) -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">2</span><i class="bi bi-list"></i> ประเภทเป้าหมาย
        </label>
        <details ref="targetTypeDropdown" class="target-source-dropdown">
          <summary class="target-source-trigger">
            <svg v-if="selectedTargetTypeData?.name === 'สะพาน'" class="source-icon bridge-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M2 7.5h20M4 7.5v11M20 7.5v11M6 7.5c0 5.4 2.7 8 6 8s6-2.6 6-8M2 18.5h20" />
            </svg>
            <i v-else class="source-icon bi" :class="selectedTargetTypeData?.icon || 'bi-crosshair'" aria-hidden="true"></i>
            <span>{{ selectedTargetTypeData?.name || '-- เลือกประเภทเป้าหมาย --' }}</span>
            <i class="dropdown-chevron bi bi-chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="target-source-list target-type-list" role="radiogroup" aria-label="ประเภทเป้าหมาย">
            <button
              v-for="type in targetTypes"
              :key="type.name"
              type="button"
              class="target-source-option"
              :class="{ active: formData.targetType === type.name }"
              role="radio"
              :aria-checked="formData.targetType === type.name"
              @click="selectTargetType(type)"
            >
              <svg v-if="type.name === 'สะพาน'" class="source-icon bridge-icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M2 7.5h20M4 7.5v11M20 7.5v11M6 7.5c0 5.4 2.7 8 6 8s6-2.6 6-8M2 18.5h20" />
              </svg>
              <i v-else class="source-icon bi" :class="type.icon" aria-hidden="true"></i>
              <span>{{ type.name }}</span>
              <i
                v-if="formData.targetType === type.name"
                class="selection-check bi bi-check-lg"
                aria-hidden="true"
              ></i>
            </button>
          </div>
        </details>
        <div v-if="targetRcInfo" class="info-card">
          <div class="info-card-head">
            <span>ค่า RC ทั่วไป (f'c)</span>
            <strong>{{ targetRcRange }}</strong>
          </div>
          <div class="info-card-row">
            <span>ระบบโครงสร้าง</span>
            <span>{{ targetRcInfo.system }}</span>
          </div>
          <div class="info-card-row">
            <span>พารามิเตอร์สำคัญ</span>
            <span>{{ targetRcInfo.keyParams }}</span>
          </div>
        </div>
      </div>

      <!-- 3. Structure Type (Dropdown) -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">3</span><i class="bi bi-boxes"></i> ชนิดโครงสร้าง
        </label>
        <details ref="structureDropdown" class="target-source-dropdown">
          <summary class="target-source-trigger">
            <i class="source-icon bi" :class="selectedStructureData?.icon || 'bi-boxes'" aria-hidden="true"></i>
            <span>{{ selectedStructureData?.name || '-- เลือกชนิดโครงสร้าง --' }}</span>
            <i class="dropdown-chevron bi bi-chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="target-source-list themed-option-list" role="radiogroup" aria-label="ชนิดโครงสร้าง">
            <button
              v-for="type in structureTypes"
              :key="type.name"
              type="button"
              class="target-source-option"
              :class="{ active: formData.structureType === type.name }"
              role="radio"
              :aria-checked="formData.structureType === type.name"
              @click="selectStructure(type)"
            >
              <i class="source-icon bi" :class="type.icon" aria-hidden="true"></i>
              <span>{{ type.name }}</span>
              <i v-if="formData.structureType === type.name" class="selection-check bi bi-check-lg" aria-hidden="true"></i>
            </button>
          </div>
        </details>
      </div>

      <!-- 4. Material Strength -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">4</span><i class="bi bi-shield"></i> ค่าความแข็งแรงของวัสดุ
        </label>
        <p v-if="!materialSpec" class="field-hint">เลือกชนิดโครงสร้างก่อน เพื่อกรอกค่าความแข็งแรงของวัสดุ</p>
        <template v-else>
          <div class="material-meta">
            <span class="material-badge" :class="{ rc: materialSpec.isRc }">
              {{ materialSpec.isRc ? 'RC' : 'ไม่ใช่ RC' }}
            </span>
            <small>ตัวอย่าง: {{ materialSpec.example }}</small>
          </div>
          <div v-if="fcChoices.length" class="chip-row">
            <small>f'c ตามประเภทเป้าหมาย</small>
            <button
              v-for="value in fcChoices"
              :key="value"
              type="button"
              class="value-chip"
              :class="{ active: Number(formData.materialStrength.fc_mpa) === value }"
              @click="formData.materialStrength.fc_mpa = value"
            >
              {{ value }} MPa
            </button>
          </div>
          <div class="material-grid">
            <div
              v-for="param in materialSpec.params"
              :key="param.key"
              class="material-param-card"
              :class="{ 'full-width': isFullWidthParam(param) }"
            >
              <div class="material-param-label">
                <span class="label-text">{{ param.label }}</span>
                <span v-if="param.unit" class="unit-text">{{ param.unit }}</span>
              </div>
              <input
                v-if="param.type === 'number'"
                v-model.number="formData.materialStrength[param.key]"
                type="number"
                min="0"
                step="any"
                class="material-param-input"
                :placeholder="param.defaultValue != null ? String(param.defaultValue) : '-'"
              />
              <input
                v-else
                v-model="formData.materialStrength[param.key]"
                type="text"
                class="material-param-input"
                placeholder="-"
              />
            </div>
          </div>
          <div class="material-summary">
            <i class="bi bi-info-circle"></i>
            <span>การแสดงผล: <strong>{{ materialSummary }}</strong></span>
          </div>
        </template>
      </div>

      <!-- 5. Coordinates -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">5</span><i class="bi bi-geo"></i> พิกัดตำแหน่ง
        </label>
        <div class="field-shell coordinate-field" :class="{ invalid: coordinateStatus === 'invalid' }">
          <i class="bi bi-compass"></i>
          <input
            type="text"
            :value="coordinateText"
            placeholder="WGS84 / DMS / UTM / MGRS"
            spellcheck="false"
            autocomplete="off"
            @input="handleCoordinateInput"
          />
          <span v-if="detectedCoordinateFormat">{{ detectedCoordinateFormat }}</span>
        </div>
        <p v-if="coordinateStatus === 'invalid'" class="field-hint error">
          อ่านพิกัดไม่ได้ — ตัวอย่าง: 14.317383, 105.177066 · 14°19'02.6"N 105°10'37.4"E · 48P 519095 1582835 · 48P WA 19095 82834
        </p>
        <dl v-if="coordinateFormats" class="coordinate-formats">
          <template v-for="(value, key) in coordinateFormats" :key="key">
            <dt>{{ key === 'DD' ? 'WGS84' : key }}</dt>
            <dd>{{ value }}</dd>
          </template>
        </dl>
      </div>

      <!-- 5b. Size / ERR for JMEM -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">5b</span><i class="bi bi-rulers"></i> ขนาดเป้าหมาย / ERR (สำหรับ JMEM)
        </label>
        <div class="coordinate-inputs">
          <div class="field-shell coordinate-field">
            <i class="bi bi-arrows-expand"></i>
            <input type="number" placeholder="กว้าง (ม.)" v-model.number="formData.width_m" step="0.1" min="0" />
          </div>
          <div class="field-shell coordinate-field">
            <i class="bi bi-arrows-expand"></i>
            <input type="number" placeholder="ยาว (ม.)" v-model.number="formData.length_m" step="0.1" min="0" />
          </div>
        </div>
        <div class="coordinate-inputs" style="margin-top: 8px">
          <div class="field-shell coordinate-field">
            <i class="bi bi-arrow-up"></i>
            <input type="number" placeholder="สูง (ม.)" v-model.number="formData.height_m" step="0.1" min="0" />
          </div>
          <div class="field-shell coordinate-field">
            <i class="bi bi-exclamation-triangle"></i>
            <input type="number" placeholder="ERR (ม.)" v-model.number="formData.coordinate_error_m" step="0.1" min="0" />
          </div>
        </div>
        <div class="coordinate-inputs" style="margin-top: 8px">
          <div class="field-shell coordinate-field" title="ทิศของแกนยาว วัดตามเข็มนาฬิกาจากทิศเหนือ (0–359°)">
            <i class="bi bi-compass"></i>
            <input type="number" placeholder="ทิศแกนยาว (°)" v-model.number="formData.heading_deg" step="1" min="0" max="359" />
          </div>
        </div>
      </div>

      <!-- 6. Image Upload -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">6</span><i class="bi bi-image"></i> นำเข้ารูปภาพ
        </label>
        <div class="upload-panel" :class="{ 'has-image': formData.imagePreview }">
          <img v-if="formData.imagePreview" :src="formData.imagePreview" alt="ตัวอย่างรูปเป้าหมาย" class="upload-preview" />
          <i v-else class="bi bi-cloud-arrow-up upload-icon" aria-hidden="true"></i>
          <div class="upload-copy">
            <strong>{{ formData.imageName || 'เลือกรูปภาพเป้าหมาย' }}</strong>
            <small v-if="formData.imageName">อัปโหลดเรียบร้อย</small>
          </div>
          <div class="file-actions">
            <button type="button" class="btn btn-outline-primary btn-sm" @click="triggerFileInput">
              <i class="bi bi-folder2-open me-1"></i> เลือกไฟล์
            </button>
            <button type="button" class="btn btn-outline-danger btn-sm" @click="clearImage" :disabled="!formData.imageName">
              <i class="bi bi-trash me-1"></i> ลบ
            </button>
          </div>
        </div>
        <input
          ref="fileInput"
          type="file"
          class="d-none"
          accept="image/*"
          @change="handleImageUpload"
        />
      </div>

      <!-- 7. Target Details -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">7</span><i class="bi bi-file-text"></i> กรอกรายละเอียดเป้าหมาย
        </label>
        <div class="textarea-shell">
          <textarea rows="4" placeholder="กรอกรายละเอียดเป้าหมาย..." v-model="formData.targetDetails"></textarea>
        </div>
      </div>

      <!-- 8. Desired Effect & Pk -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">8</span><i class="bi bi-bullseye"></i> Desired Effect &amp; Pk
        </label>
        <details ref="desiredEffectDropdown" class="target-source-dropdown">
          <summary class="target-source-trigger">
            <i class="source-icon bi" :class="selectedDesiredEffectData?.icon || 'bi-stars'" aria-hidden="true"></i>
            <span>{{ selectedDesiredEffectData?.name || 'เลือกผลที่ต้องการ' }}</span>
            <i class="dropdown-chevron bi bi-chevron-down" aria-hidden="true"></i>
          </summary>
          <div class="target-source-list themed-option-list" role="radiogroup" aria-label="Desired Effect">
            <button
              v-for="effect in desiredEffects"
              :key="effect.name"
              type="button"
              class="target-source-option"
              :class="{ active: formData.desiredEffect === effect.name }"
              role="radio"
              :aria-checked="formData.desiredEffect === effect.name"
              @click="selectDesiredEffect(effect)"
            >
              <i class="source-icon bi" :class="effect.icon" aria-hidden="true"></i>
              <span>{{ effect.name }}</span>
              <i v-if="formData.desiredEffect === effect.name" class="selection-check bi bi-check-lg" aria-hidden="true"></i>
            </button>
          </div>
        </details>
        <div class="field-shell numeric-field pk-field">
          <i class="bi bi-speedometer2"></i>
          <input
            type="number"
            placeholder="Pk ที่ต้องการ"
            :value="pkPercent"
            min="0"
            max="100"
            step="1"
            @input="handlePkPercentInput"
          />
          <span>%</span>
        </div>
        <div class="chip-row">
          <button
            v-for="value in pkPresets"
            :key="value"
            type="button"
            class="value-chip"
            :class="{ active: pkPercent === value }"
            @click="setPkPercent(value)"
          >
            {{ value }}%
          </button>
        </div>
      </div>

      <!-- 9. CEP Value -->
      <div class="form-section">
        <label class="form-label">
          <span class="step-number">9</span> CEP (ft)
        </label>
        <div class="field-shell numeric-field">
          <i class="bi bi-bullseye"></i>
          <input
            type="text"
            placeholder="กรอกค่า CEP (ft)"
            :value="formData.cep"
            inputmode="numeric"
            pattern="[0-9]*"
            @keydown="allowNumericInput($event, false)"
            @input="handleCepInput"
            @blur="handleCepBlur"
          />
        </div>
      </div>

      <!-- Save + AI Analysis -->
      <div class="form-section action-section">
        <button
          type="button"
          class="btn btn-outline-light btn-sm w-100 save-button mb-2"
          :disabled="saving || !canSave"
          @click="saveTarget"
        >
          <i class="bi" :class="saving ? 'bi-hourglass-split' : 'bi-save'"></i>
          {{ saving ? 'กำลังบันทึก…' : 'บันทึกข้อมูลเป้าหมาย' }}
        </button>
        <button
          class="btn btn-primary btn-sm w-100 analysis-button"
          :disabled="analyzing"
          @click="runAIAnalysis"
        >
          <i class="bi" :class="analyzing ? 'bi-hourglass-split' : 'bi-cpu'"></i>
          {{ analyzing ? 'กำลังคำนวณ JMEM / AI…' : 'คำนวณ JMEM + AI วิเคราะห์สินค้า' }}
        </button>
        <small class="action-hint">บันทึกค่าในฟอร์มก่อน แล้วระบบจะจัดอันดับสินค้าแบบโปรแกรมเดิม</small>
      </div>

    </div>

    <div v-if="showValidationModal" class="validation-backdrop" @click.self="closeValidationModal">
      <div class="validation-modal" role="alertdialog" aria-modal="true" aria-labelledby="validation-title">
        <div class="validation-icon" aria-hidden="true">
          <i class="bi bi-exclamation-lg"></i>
        </div>
        <h5 id="validation-title">กรุณาเลือกเป้าหมายและกรอกค่าสำคัญ</h5>
        <p>เลือกเป้าหมายบนแผนที่ แล้วกรอกพิกัด / Pk / CEP ก่อนบันทึกหรือวิเคราะห์</p>
        <button type="button" class="validation-button" @click="closeValidationModal">
          <i class="bi bi-check-lg"></i> ตกลง
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, watch } from 'vue'
import mockAPI from '../services/mockAPI'
import {
  MATERIAL_STRENGTH,
  TARGET_TYPE_RC,
  defaultMaterialStrength,
  materialStrengthSummary,
  targetRcChoices,
  targetRcRangeText,
} from '../config/materialStrength'
import { formatAllCoordinates, formatDecimal, parseCoordinateText } from '../utils/coordinateParser'

const PK_PRESETS = [50, 70, 80, 90, 95]

export default {
  name: 'Sidebar',
  props: {
    collapsed: {
      type: Boolean,
      default: false
    },
    /** When set (e.g. user picked a map target), fill the form for readability. */
    targetDraft: {
      type: Object,
      default: null
    }
  },
  emits: [
    'ai-analysis',
    'toggle-sidebar',
    'reset-target',
    'reset-all',
    'priority-change',
    'form-change',
    'save-target',
  ],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const targetSourceDropdown = ref(null)
    const targetTypeDropdown = ref(null)
    const structureDropdown = ref(null)
    const desiredEffectDropdown = ref(null)
    const showValidationModal = ref(false)
    const saving = ref(false)
    const analyzing = ref(false)

    const formData = ref({
      targetSources: mockAPI.targetSources.map((source, index) => ({
        ...source,
        icon: ['bi-people', 'bi-airplane', 'bi-shield-plus', 'bi-shield-check', 'bi-three-dots'][index]
      })),
      selectedTargetSource: '',
      targetPriority: '',
      targetType: '',
      structureType: '',
      materialStrength: {},
      latitude: null,
      longitude: null,
      imagePreview: null,
      imageName: '',
      targetDetails: '',
      desiredEffect: '',
      pk: null,
      cep: null,
      width_m: null,
      length_m: null,
      height_m: null,
      heading_deg: null,
      coordinate_error_m: null,
      label: '',
      id: '',
    })

    const canSave = computed(() => Boolean(formData.value.id || props.targetDraft?.id))

    const applyDraft = (draft) => {
      if (!draft) return
      const keys = [
        'selectedTargetSource',
        'targetPriority',
        'targetType',
        'structureType',
        'latitude',
        'longitude',
        'targetDetails',
        'desiredEffect',
        'pk',
        'cep',
        'width_m',
        'length_m',
        'height_m',
        'heading_deg',
        'coordinate_error_m',
        'label',
        'id',
        'target_type_api',
        'material_class_api',
      ]
      keys.forEach((key) => {
        if (draft[key] !== undefined) {
          formData.value[key] = draft[key]
        }
      })
      if (draft.materialStrength !== undefined) {
        formData.value.materialStrength = { ...(draft.materialStrength || {}) }
      }
      if (draft.targetPriority) {
        emit('priority-change', draft.targetPriority)
      }
      emit('form-change', {
        ...snapshotForm(),
        label: draft.label || formData.value.label || '',
        id: draft.id || formData.value.id || '',
      })
    }

    const snapshotForm = () => ({
      selectedTargetSource: formData.value.selectedTargetSource,
      targetType: formData.value.targetType,
      targetPriority: formData.value.targetPriority,
      structureType: formData.value.structureType,
      materialStrength: { ...formData.value.materialStrength },
      targetDetails: formData.value.targetDetails,
      imageName: formData.value.imageName,
      imagePreview: formData.value.imagePreview,
      desiredEffect: formData.value.desiredEffect,
      latitude: formData.value.latitude,
      longitude: formData.value.longitude,
      pk: formData.value.pk,
      cep: formData.value.cep,
      width_m: formData.value.width_m,
      length_m: formData.value.length_m,
      height_m: formData.value.height_m,
      heading_deg: formData.value.heading_deg,
      coordinate_error_m: formData.value.coordinate_error_m,
      label: formData.value.label,
      id: formData.value.id,
      target_type_api: formData.value.target_type_api,
      material_class_api: formData.value.material_class_api,
    })

    watch(
      () => props.targetDraft,
      (draft) => {
        if (draft) applyDraft(draft)
      },
      { deep: true, immediate: true },
    )

    const targetTypes = ref(mockAPI.targetTypes.map((name, index) => ({
      name,
      icon: [
        'bi-building',
        'bi-signpost-split',
        'bi-bricks',
        'bi-arrows-expand',
        'bi-airplane-engines',
        'bi-houses',
        'bi-water',
        'bi-broadcast-pin',
        'bi-box-seam',
        'bi-fuel-pump'
      ][index]
    })))
    const structureTypes = ref(mockAPI.structureTypes.map((name, index) => ({
      name,
      icon: ['bi-bricks', 'bi-box', 'bi-grid-3x3-gap', 'bi-tree', 'bi-globe2', 'bi-three-dots'][index]
    })))
    const desiredEffects = ref(mockAPI.desiredEffects.map((name, index) => ({
      name,
      icon: ['bi-x-octagon', 'bi-slash-circle', 'bi-building-down', 'bi-exclamation-triangle'][index]
    })))
    const selectedTargetSourceData = computed(() =>
      formData.value.targetSources.find(source => source.name === formData.value.selectedTargetSource)
    )
    const selectedTargetTypeData = computed(() =>
      targetTypes.value.find(type => type.name === formData.value.targetType)
    )
    const selectedStructureData = computed(() =>
      structureTypes.value.find(type => type.name === formData.value.structureType)
    )
    const selectedDesiredEffectData = computed(() =>
      desiredEffects.value.find(effect => effect.name === formData.value.desiredEffect)
    )

    const targetRcInfo = computed(() => TARGET_TYPE_RC[formData.value.targetType] || null)
    const targetRcRange = computed(() => targetRcRangeText(targetRcInfo.value))
    const materialSpec = computed(() => MATERIAL_STRENGTH[formData.value.structureType] || null)
    const fcChoices = computed(() =>
      materialSpec.value?.params.some((p) => p.key === 'fc_mpa') ? targetRcChoices(targetRcInfo.value) : []
    )
    const materialSummary = computed(() =>
      materialStrengthSummary(formData.value.structureType, formData.value.materialStrength)
    )

    const selectTargetSource = (source) => {
      formData.value.selectedTargetSource = source.name
      targetSourceDropdown.value?.removeAttribute('open')
    }

    const setStructure = (structureType) => {
      if (formData.value.structureType === structureType) return
      formData.value.structureType = structureType
      formData.value.materialStrength = defaultMaterialStrength(structureType, formData.value.targetType)
    }

    const selectTargetType = (type) => {
      formData.value.targetType = type.name
      targetTypeDropdown.value?.removeAttribute('open')
      const rc = TARGET_TYPE_RC[type.name]
      if (!rc) return
      if (!formData.value.structureType) {
        setStructure(rc.material)
      } else if (fcChoices.value.length && !fcChoices.value.includes(Number(formData.value.materialStrength.fc_mpa))) {
        formData.value.materialStrength.fc_mpa = fcChoices.value[1] ?? fcChoices.value[0]
      }
    }

    const isFullWidthParam = (param) => {
      return param.type === 'text' || (param.label && param.label.length > 4)
    }

    const selectStructure = (type) => {
      setStructure(type.name)
      structureDropdown.value?.removeAttribute('open')
    }

    const coordinateText = ref('')
    const coordinateStatus = ref('')
    const detectedCoordinateFormat = ref('')

    const handleCoordinateInput = (event) => {
      coordinateText.value = event.target.value
      if (!coordinateText.value.trim()) {
        coordinateStatus.value = ''
        detectedCoordinateFormat.value = ''
        formData.value.latitude = null
        formData.value.longitude = null
        return
      }
      const parsed = parseCoordinateText(coordinateText.value)
      if (!parsed) {
        coordinateStatus.value = 'invalid'
        detectedCoordinateFormat.value = ''
        return
      }
      coordinateStatus.value = 'ok'
      detectedCoordinateFormat.value = parsed.format === 'DD' ? 'WGS84' : parsed.format
      formData.value.latitude = Number(parsed.lat.toFixed(8))
      formData.value.longitude = Number(parsed.lng.toFixed(8))
    }

    const coordinateFormats = computed(() => {
      const { latitude, longitude } = formData.value
      if (latitude === null || longitude === null || latitude === '' || longitude === '') return null
      return formatAllCoordinates(latitude, longitude)
    })

    watch(
      () => [formData.value.latitude, formData.value.longitude],
      ([lat, lng]) => {
        if (lat === null || lng === null || lat === '' || lng === '') {
          coordinateText.value = ''
          coordinateStatus.value = ''
          detectedCoordinateFormat.value = ''
          return
        }
        const parsed = parseCoordinateText(coordinateText.value)
        if (parsed && Math.abs(parsed.lat - lat) < 1e-6 && Math.abs(parsed.lng - lng) < 1e-6) return
        coordinateText.value = formatDecimal(Number(lat), Number(lng))
        coordinateStatus.value = 'ok'
        detectedCoordinateFormat.value = 'WGS84'
      },
      { immediate: true },
    )

    const pkPercent = computed(() => {
      const pk = formData.value.pk
      if (pk === null || pk === '' || !Number.isFinite(Number(pk))) return ''
      return Math.round(Number(pk) * 1000) / 10
    })

    const setPkPercent = (value) => {
      if (value === '' || value === null || !Number.isFinite(Number(value))) {
        formData.value.pk = null
        return
      }
      const pct = Math.min(100, Math.max(0, Number(value)))
      formData.value.pk = Math.round(pct * 10) / 1000
    }

    const handlePkPercentInput = (event) => setPkPercent(event.target.value)

    const selectDesiredEffect = (effect) => {
      formData.value.desiredEffect = effect.name
      desiredEffectDropdown.value?.removeAttribute('open')
    }

    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    const clearImage = () => {
      formData.value.imagePreview = null
      formData.value.imageName = ''
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const handleImageUpload = (event) => {
      const file = event.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          formData.value.imagePreview = e.target.result
          formData.value.imageName = file.name
        }
        reader.readAsDataURL(file)
      }
    }

    const allowNumericInput = (event, allowDecimal = false) => {
      const allowedKeys = ['Backspace', 'Delete', 'Tab', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'Enter']
      if (allowDecimal && event.key === '.') {
        return
      }
      if (allowedKeys.includes(event.key)) {
        return
      }
      if (event.key === ' ' || /[^0-9]/.test(event.key)) {
        event.preventDefault()
      }
    }

    const handleCepInput = (event) => {
      const rawValue = event.target.value.replace(/\D/g, '')
      formData.value.cep = rawValue === '' ? 0 : Number(rawValue)
    }

    const handleCepBlur = () => {
      if (formData.value.cep === null || formData.value.cep === '' || Number.isNaN(formData.value.cep)) {
        formData.value.cep = 0
      }
    }

    const validateForm = () => {
      if (
        !formData.value.id &&
        !props.targetDraft?.id
      ) {
        showValidationModal.value = true
        return false
      }
      if (
        formData.value.latitude === null ||
        formData.value.longitude === null ||
        formData.value.pk === null ||
        formData.value.cep === null
      ) {
        showValidationModal.value = true
        return false
      }
      return true
    }

    const closeValidationModal = () => {
      showValidationModal.value = false
    }

    const runAIAnalysis = async () => {
      if (!validateForm()) {
        return
      }
      analyzing.value = true
      try {
        await new Promise((resolve, reject) => {
          emit('ai-analysis', {
            ...snapshotForm(),
            done: resolve,
            fail: reject,
          })
        })
      } catch {
        /* parent shows error */
      } finally {
        analyzing.value = false
      }
    }

    const saveTarget = async () => {
      if (!canSave.value) {
        showValidationModal.value = true
        return
      }
      saving.value = true
      try {
        await new Promise((resolve, reject) => {
          emit('save-target', {
            ...snapshotForm(),
            done: resolve,
            fail: reject,
          })
        })
      } catch {
        /* parent shows error */
      } finally {
        saving.value = false
      }
    }

    return {
      formData,
      fileInput,
      targetSourceDropdown,
      targetTypeDropdown,
      structureDropdown,
      desiredEffectDropdown,
      showValidationModal,
      saving,
      analyzing,
      canSave,
      selectedTargetSourceData,
      selectedTargetTypeData,
      selectedStructureData,
      selectedDesiredEffectData,
      targetTypes,
      structureTypes,
      desiredEffects,
      targetRcInfo,
      targetRcRange,
      materialSpec,
      fcChoices,
      materialSummary,
      isFullWidthParam,
      coordinateText,
      coordinateStatus,
      detectedCoordinateFormat,
      coordinateFormats,
      handleCoordinateInput,
      pkPercent,
      pkPresets: PK_PRESETS,
      setPkPercent,
      handlePkPercentInput,
      selectTargetSource,
      selectTargetType,
      selectStructure,
      selectDesiredEffect,
      triggerFileInput,
      clearImage,
      handleImageUpload,
      allowNumericInput,
      handleCepInput,
      handleCepBlur,
      closeValidationModal,
      runAIAnalysis,
      saveTarget,
    }
  }
}
</script>

<style scoped>
.sidebar-container {
  display: flex;
  flex-direction: column;
  background: var(--panel-bg);
  border-right: 2px solid var(--border);
  height: 100%;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 62px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.16), rgba(96, 70, 200, 0.08));
}

.sidebar-brand {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 9px;
}

.sidebar-brand-icon {
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

.sidebar-brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.sidebar-brand-copy strong {
  overflow: hidden;
  color: var(--text);
  font-size: 0.9rem;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-brand-copy small {
  color: var(--muted);
  font-size: 0.66rem;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.sidebar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sidebar-reset { order: 1; }
.sidebar-reset-all { order: 2; }
.sidebar-toggle { order: 3; }

.sidebar-toggle,
.sidebar-reset,
.sidebar-reset-all {
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

.sidebar-toggle:hover,
.sidebar-reset:hover:not(:disabled),
.sidebar-reset-all:hover:not(:disabled) {
  border-color: #0d6efd;
  background: #0d6efd;
  color: #ffffff;
  transform: scale(1.04);
}

.sidebar-reset {
  border-color: rgba(25, 135, 84, 0.58);
  color: #56c98d;
}

.sidebar-reset:hover:not(:disabled) {
  border-color: #198754;
  background: #198754;
}

.sidebar-reset-all {
  border-color: rgba(242, 139, 44, 0.62);
  color: #f2a04e;
}

.sidebar-reset-all:hover:not(:disabled) {
  border-color: #d8751d;
  background: #d8751d;
}

.sidebar-reset:disabled,
.sidebar-reset-all:disabled {
  cursor: not-allowed;
  opacity: 0.38;
  pointer-events: none;
}

.sidebar-container.collapsed .sidebar-header {
  flex-direction: column;
  justify-content: flex-start;
  padding: 10px 7px;
}

.sidebar-container.collapsed .sidebar-brand {
  justify-content: center;
}

.sidebar-container.collapsed .sidebar-actions {
  flex-direction: column;
}

.sidebar-container.collapsed .sidebar-toggle { order: 1; }
.sidebar-container.collapsed .sidebar-reset { order: 2; }
.sidebar-container.collapsed .sidebar-reset-all { order: 3; }

.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.form-section {
  margin-bottom: 15px;
  padding: 12px;
  background: var(--surface);
  border-radius: 8px;
  border: 1px solid var(--border);
  border-left: 4px solid #0d6efd;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.form-section:focus-within {
  border-color: rgba(13, 110, 253, 0.75);
  box-shadow: 0 4px 14px rgba(13, 110, 253, 0.14);
}

.section-title {
  margin: 0 0 10px 0;
  font-weight: 600;
  color: #0d6efd;
  font-size: 0.95rem;
}

.form-label {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #ffffff;
}

.form-label > .bi {
  color: #73a7ff;
  font-size: 1rem;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 22px;
  width: 22px;
  height: 22px;
  border: 1px solid #75a7ff;
  border-radius: 50%;
  background: linear-gradient(145deg, #2f73d9 0%, #123f91 100%);
  box-shadow:
    inset 0 1px 1px rgba(255, 255, 255, 0.4),
    0 1px 3px rgba(0, 0, 0, 0.45);
  color: #ffffff;
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1;
}

.target-sources {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.target-source-dropdown {
  overflow: hidden;
  border: 1px solid var(--control-border);
  border-radius: 4px;
  background: var(--control-bg);
}

.target-source-trigger {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) 18px;
  align-items: center;
  min-height: 34px;
  padding: 6px 10px;
  color: var(--text);
  font-size: 0.875rem;
  cursor: pointer;
  list-style: none;
  user-select: none;
}

.target-source-trigger::-webkit-details-marker {
  display: none;
}

.target-source-trigger:focus-visible {
  outline: 2px solid #0d6efd;
  outline-offset: -2px;
}

.dropdown-chevron {
  justify-self: end;
  font-size: 0.75rem;
  transition: transform 0.18s ease;
}

.target-source-dropdown[open] .dropdown-chevron {
  transform: rotate(180deg);
}

.target-source-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 4px;
  border-top: 1px solid var(--border);
}

.target-source-option {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) 20px;
  align-items: center;
  width: 100%;
  min-height: 38px;
  padding: 7px 10px;
  border: 1px solid transparent;
  border-bottom-color: var(--border);
  border-radius: 4px;
  background: transparent;
  color: var(--text);
  font-family: inherit;
  font-size: 0.9rem;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease;
}

.target-source-option:hover {
  background: rgba(13, 110, 253, 0.12);
  border-color: rgba(13, 110, 253, 0.35);
}

.target-source-option.active {
  background: rgba(173, 122, 24, 0.28);
  border-color: rgba(218, 170, 70, 0.42);
}

.source-icon {
  color: currentColor;
  font-size: 1.15rem;
}

.bridge-icon {
  width: 1.15rem;
  height: 1.15rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.selection-check {
  color: #f0c764;
  font-size: 1.15rem;
  justify-self: end;
}

:global(body.light-theme .target-source-option.active) {
  background: #fff2cc;
  border-color: #d9b44a;
}

.target-type-list {
  max-height: 300px;
  overflow-y: auto;
}

.target-type-list .target-source-option.active,
:global(body.light-theme .target-type-list .target-source-option.active) {
  background: #0d6efd;
  border-color: #4b91f7;
  color: #ffffff;
}

.target-type-list .target-source-option.active .selection-check {
  color: #ffffff;
}

.themed-option-list .target-source-option.active,
:global(body.light-theme .themed-option-list .target-source-option.active) {
  background: #0d6efd;
  border-color: #4b91f7;
  color: #ffffff;
}

.themed-option-list .target-source-option.active .selection-check {
  color: #ffffff;
}

.target-priority-field {
  margin-top: 11px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.target-priority-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 7px;
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 500;
}

.target-priority-label i {
  color: #6ea8fe;
}

.target-priority-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 5px;
}

.target-priority-option {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 0;
  min-height: 34px;
  padding: 5px 4px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--control-bg);
  color: var(--text);
  font-size: 0.62rem;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease;
}

.target-priority-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.target-priority-option > .bi {
  font-size: 0.62rem;
}

.priority-dot {
  flex: 0 0 9px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 5px currentColor;
}

.target-priority-option.priority-red .priority-dot { background: #e33c49; color: #e33c49; }
.target-priority-option.priority-orange .priority-dot { background: #f28b2c; color: #f28b2c; }
.target-priority-option.priority-green .priority-dot { background: #29a968; color: #29a968; }
.target-priority-option.priority-red.selected { border-color: #e33c49; background: rgba(227, 60, 73, 0.12); }
.target-priority-option.priority-orange.selected { border-color: #f28b2c; background: rgba(242, 139, 44, 0.12); }
.target-priority-option.priority-green.selected { border-color: #29a968; background: rgba(41, 169, 104, 0.12); }

.form-check {
  display: flex;
  align-items: center;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.form-check:hover {
  background-color: #222222;
}

.form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.form-check-label {
  margin: 0;
  cursor: pointer;
  user-select: none;
  color: var(--text);
}

.coordinate-inputs {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.coordinate-field {
  grid-template-columns: 36px minmax(0, 1fr) auto;
  min-height: 42px;
}

.numeric-field {
  grid-template-columns: 36px minmax(0, 1fr) auto;
  min-height: 42px;
}

.coordinate-field.invalid {
  border-color: #e33c49;
}

.field-hint {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 0.7rem;
  line-height: 1.45;
}

.field-hint.error {
  color: #f0848c;
}

.info-card {
  margin-top: 8px;
  padding: 8px 10px;
  border: 1px solid rgba(13, 110, 253, 0.35);
  border-radius: 6px;
  background: rgba(13, 110, 253, 0.08);
  font-size: 0.72rem;
}

.info-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  color: var(--muted);
}

.info-card-head strong {
  color: #6ea8fe;
  font-size: 0.86rem;
}

.info-card-row {
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr);
  gap: 6px;
  padding-top: 3px;
  color: var(--text);
}

.info-card-row span:first-child {
  color: var(--muted);
}

.material-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 0.7rem;
}

.material-badge {
  padding: 2px 8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--muted);
  font-size: 0.68rem;
  font-weight: 700;
  white-space: nowrap;
}

.material-badge.rc {
  border-color: #4b91f7;
  background: rgba(13, 110, 253, 0.16);
  color: #6ea8fe;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  margin: 8px 0;
}

.chip-row small {
  width: 100%;
  color: var(--muted);
  font-size: 0.68rem;
}

.value-chip {
  padding: 3px 9px;
  border: 1px solid var(--control-border);
  border-radius: 999px;
  background: var(--control-bg);
  color: var(--text);
  font-family: inherit;
  font-size: 0.72rem;
  cursor: pointer;
}

.value-chip:hover {
  border-color: #4b91f7;
}

.value-chip.active {
  border-color: #4b91f7;
  background: #0d6efd;
  color: #ffffff;
}

.material-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 6px;
}

.material-param-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.material-param-card.full-width {
  grid-column: 1 / -1;
}

.material-param-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  min-width: 0;
  line-height: 1.2;
}

.material-param-label .label-text {
  font-size: 0.73rem;
  font-weight: 600;
  color: #6ea8fe;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.material-param-label .unit-text {
  font-size: 0.65rem;
  font-weight: 500;
  color: #94a3b8;
  background: rgba(148, 163, 184, 0.12);
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  flex-shrink: 0;
}

.material-param-input {
  width: 100% !important;
  height: 36px !important;
  min-height: 36px !important;
  padding: 6px 10px !important;
  background: var(--control-bg, #0d1b2a) !important;
  border: 1px solid var(--control-border, #1e293b) !important;
  border-radius: 6px !important;
  outline: none !important;
  color: var(--text, #f8fafc) !important;
  font-size: 0.82rem !important;
  font-family: inherit !important;
  box-shadow: none !important;
  transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}

.material-param-input:focus {
  border-color: #0d6efd !important;
  box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.25) !important;
}

.material-param-input::-webkit-inner-spin-button,
.material-param-input::-webkit-outer-spin-button {
  display: none;
  margin: 0;
  appearance: none;
}

.material-param-input[type='number'] {
  appearance: textfield;
  -moz-appearance: textfield;
}

:global(body.light-theme .material-param-input) {
  background: #ffffff !important;
  border-color: #cbd5e1 !important;
  color: #0f172a !important;
}

.material-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  color: var(--muted);
  font-size: 0.72rem;
}

.material-summary i {
  color: #6ea8fe;
}

.material-summary strong {
  color: var(--text);
}

.coordinate-formats {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  gap: 3px 8px;
  margin: 8px 0 0;
  padding: 7px 9px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.72rem;
}

.coordinate-formats dt {
  color: var(--muted);
  font-weight: 600;
}

.coordinate-formats dd {
  margin: 0;
  color: var(--text);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  user-select: all;
  word-break: break-word;
}

.pk-field {
  margin-top: 8px;
}

.coordinate-field input,
.numeric-field input {
  padding: 9px 10px 9px 2px;
  font-size: 0.9rem;
}

.coordinate-field input::-webkit-inner-spin-button,
.coordinate-field input::-webkit-outer-spin-button,
.numeric-field input::-webkit-inner-spin-button,
.numeric-field input::-webkit-outer-spin-button {
  display: none;
  margin: 0;
  appearance: none;
}

.coordinate-field input[type='number'],
.numeric-field input[type='number'] {
  appearance: textfield;
  -moz-appearance: textfield;
}

.field-shell {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) auto;
  align-items: center;
  min-height: 38px;
  overflow: hidden;
  border: 1px solid var(--control-border);
  border-radius: 6px;
  background: var(--control-bg);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.field-shell:focus-within,
.textarea-shell:focus-within {
  border-color: #0d6efd;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.16);
}

.field-shell > i {
  justify-self: center;
  color: #6ea8fe;
}

.field-shell input {
  width: 100%;
  min-width: 0;
  padding: 7px 5px;
  border: 0 !important;
  outline: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  color: var(--text);
  font-family: inherit;
  font-size: 0.875rem;
}

.field-shell > span {
  align-self: stretch;
  display: inline-flex;
  align-items: center;
  padding: 0 9px;
  border-left: 1px solid var(--control-border);
  color: var(--muted);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.textarea-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  overflow: hidden;
  border: 1px solid var(--control-border);
  border-radius: 6px;
  background: var(--control-bg);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.textarea-shell > i {
  justify-self: center;
  margin-top: 10px;
  color: #6ea8fe;
}

.textarea-shell textarea {
  width: 100%;
  padding: 9px 10px;
  border: 0 !important;
  outline: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  color: var(--text);
  font-family: inherit;
  font-size: 0.875rem;
  resize: vertical;
}

.upload-panel {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px dashed #4b91f7;
  border-radius: 8px;
  background: rgba(13, 110, 253, 0.07);
}

.upload-icon,
.upload-preview {
  width: 46px;
  height: 46px;
  border-radius: 7px;
}

.upload-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(13, 110, 253, 0.14);
  color: #6ea8fe;
  font-size: 1.5rem;
}

.upload-preview {
  object-fit: cover;
  border: 1px solid var(--border);
}

.upload-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.upload-copy strong {
  overflow: hidden;
  color: var(--text);
  font-size: 0.82rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-copy small {
  color: var(--muted);
  font-size: 0.7rem;
}

.file-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
  grid-column: 1 / -1;
}

.btn-sm {
  font-size: 0.85rem;
}

.action-section {
  padding: 8px;
  border-left-color: #6f42c1;
}

.analysis-button {
  min-height: 40px;
  border: 1px solid #78a9ff;
  border-radius: 7px;
  background: linear-gradient(135deg, #0d6efd, #6046c8);
  box-shadow: 0 5px 14px rgba(13, 110, 253, 0.3);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.analysis-button:hover {
  background: linear-gradient(135deg, #247cf1, #7258d6);
  transform: translateY(-1px);
}

.save-button {
  min-height: 38px;
  border-radius: 7px;
  font-weight: 600;
}

.action-hint {
  display: block;
  margin-top: 8px;
  color: var(--muted);
  font-size: 0.68rem;
  line-height: 1.35;
}

.mb-2 {
  margin-bottom: 0.5rem !important;
}

.validation-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(3px);
}

.validation-modal {
  width: min(90vw, 380px);
  padding: 28px 24px 22px;
  border: 1px solid #315f9d;
  border-radius: 14px;
  background: var(--panel-bg);
  box-shadow: 0 22px 65px rgba(0, 0, 0, 0.58);
  color: var(--text);
  text-align: center;
  animation: validationPop 0.2s ease-out;
}

.validation-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  margin-bottom: 16px;
  border: 1px solid #f3c14b;
  border-radius: 50%;
  background: rgba(255, 193, 7, 0.14);
  box-shadow: 0 0 0 8px rgba(255, 193, 7, 0.06);
  color: #f3c14b;
  font-size: 1.55rem;
}

.validation-modal h5 {
  margin: 0 0 8px;
  color: var(--text);
  font-size: 1.08rem;
  font-weight: 700;
  text-align: center;
}

.validation-modal p {
  margin: 0 0 20px;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.55;
  text-align: center;
}

.validation-button {
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
}

.validation-button:hover {
  background: #2b7bf0;
  transform: translateY(-1px);
}

@keyframes validationPop {
  from { opacity: 0; transform: translateY(10px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Scrollbar styling */
.sidebar-scroll::-webkit-scrollbar {
  width: 6px;
}

.sidebar-scroll::-webkit-scrollbar-track {
  background: #111111;
}

.sidebar-scroll::-webkit-scrollbar-thumb {
  background: #555555;
  border-radius: 3px;
}

.sidebar-scroll::-webkit-scrollbar-thumb:hover {
  background: #777777;
}

@media (max-width: 992px) {
  .sidebar-container { height: 100%; border-right: 0; }
  .sidebar-toggle, .sidebar-reset, .sidebar-reset-all { flex-basis: 38px; width: 38px; height: 38px; }
  .sidebar-scroll { padding: 12px; }
}

@media (max-width: 600px) {
  .sidebar-header { min-height: 58px; padding: 8px; }
  .sidebar-brand-icon { flex-basis: 32px; width: 32px; height: 32px; }
  .sidebar-brand-copy small { display: none; }
  .sidebar-actions { gap: 4px; }
  .sidebar-toggle, .sidebar-reset, .sidebar-reset-all { flex-basis: 36px; width: 36px; height: 36px; }
  .sidebar-scroll { padding: 8px; }
  .form-section { margin-bottom: 10px; padding: 10px; }
  input, select, textarea, button { touch-action: manipulation; }
}
</style>

<template>
  <div class="database-page">
    <Header />

    <div class="database-shell">
      <aside class="db-nav">
        <div class="db-nav-heading">
          <span class="kicker">DATA MANAGEMENT</span>
          <h2><i class="bi bi-database-gear"></i> ฐานข้อมูล</h2>
          <p>จัดการข้อมูลทุกโมดูลของระบบ</p>
        </div>

        <div
          v-for="group in databaseGroups"
          :key="group.id"
          class="db-group"
        >
          <button
            type="button"
            class="db-group-toggle"
            @click="toggleGroup(group.id)"
          >
            <i :class="group.icon"></i>
            <span>{{ group.label }}</span>
            <i
              class="bi chevron"
              :class="openGroups[group.id] ? 'bi-chevron-up' : 'bi-chevron-down'"
            ></i>
          </button>
          <div v-show="openGroups[group.id]" class="db-entity-list">
            <button
              v-for="entity in group.entities"
              :key="entity.id"
              type="button"
              class="db-entity-link"
              :class="{ active: activeEntityId === entity.id }"
              @click="selectEntity(entity.id)"
            >
              {{ entity.label }}
            </button>
          </div>
        </div>
      </aside>

      <main class="db-main">
        <header class="db-toolbar">
          <div>
            <span class="kicker">{{ activeGroup?.label || 'เลือกตาราง' }}</span>
            <h3>{{ activeEntity?.label || 'ยังไม่ได้เลือก' }}</h3>
            <p v-if="activeEntity">
              API <code>{{ activeEntity.path }}</code>
              <span v-if="activeEntity.readOnly" class="badge-readonly">อ่านอย่างเดียว</span>
            </p>
          </div>

          <div class="toolbar-actions">
            <div class="scenario-picker" v-if="activeEntity?.scenarioScoped">
              <label for="scenario-select">Scenario</label>
              <select
                id="scenario-select"
                v-model="selectedScenarioId"
                @change="loadRows"
              >
                <option value="">ทั้งหมด / ไม่กรอง</option>
                <option
                  v-for="s in scenarios"
                  :key="s.id"
                  :value="s.id"
                >
                  {{ s.name }}
                </option>
              </select>
            </div>

            <button
              type="button"
              class="btn-ghost"
              :disabled="loading"
              @click="loadRows"
            >
              <i class="bi bi-arrow-clockwise"></i> รีเฟรช
            </button>
            <button
              v-if="activeEntity && !activeEntity.readOnly"
              type="button"
              class="btn-primary"
              :disabled="!canCreate"
              @click="openCreate"
            >
              <i class="bi bi-plus-lg"></i> เพิ่มรายการ
            </button>
          </div>
        </header>

        <div v-if="error" class="alert-error">
          <i class="bi bi-exclamation-triangle"></i> {{ error }}
        </div>

        <div v-if="!activeEntity" class="empty-state">
          <i class="bi bi-database"></i>
          <h4>เลือกตารางจากเมนูด้านซ้าย</h4>
          <p>ครอบคลุม Scenarios, Targets, Logistics, Wing, Weaponeering และ Map</p>
        </div>

        <div v-else class="table-panel">
          <div class="table-meta">
            <span>{{ rows.length }} รายการ</span>
            <span v-if="loading" class="loading-dot"><i class="bi bi-hourglass-split"></i> กำลังโหลด…</span>
          </div>

          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th v-for="col in listColumns" :key="col.key">{{ col.label }}</th>
                  <th class="actions-col">จัดการ</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!loading && rows.length === 0">
                  <td :colspan="listColumns.length + 1" class="empty-row">ไม่มีข้อมูล</td>
                </tr>
                <tr v-for="row in rows" :key="row[activeEntity.idField || 'id']">
                  <td v-for="col in listColumns" :key="col.key">
                    <span class="cell" :title="String(row[col.key] ?? '')">{{ formatCell(row[col.key], col.key) }}</span>
                  </td>
                  <td class="actions-col">
                    <button
                      v-if="!activeEntity.readOnly && !activeEntity.createOnly"
                      type="button"
                      class="icon-btn"
                      title="แก้ไข"
                      @click="openEdit(row)"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button
                      v-if="!activeEntity.readOnly"
                      type="button"
                      class="icon-btn danger"
                      title="ลบ / archive"
                      @click="confirmDelete(row)"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                    <button
                      v-if="activeEntity.readOnly"
                      type="button"
                      class="icon-btn"
                      title="ดูรายละเอียด"
                      @click="openView(row)"
                    >
                      <i class="bi bi-eye"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>

    <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
      <div class="modal-card">
        <header>
          <h4>
            <i class="bi" :class="modalMode === 'create' ? 'bi-plus-circle' : modalMode === 'edit' ? 'bi-pencil-square' : 'bi-eye'"></i>
            {{ modalTitle }}
          </h4>
          <button type="button" class="icon-btn" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </header>

        <form class="modal-form" @submit.prevent="saveForm">
          <div
            v-if="activeEntity?.scenarioScoped && modalMode === 'create'"
            class="form-field"
          >
            <label>Scenario <em>*</em></label>
            <select v-model="form.scenario_id" required :disabled="modalMode === 'view'">
              <option disabled value="">เลือก scenario</option>
              <option v-for="s in scenarios" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>

          <div
            v-if="activeEntity?.catalogPath && modalMode !== 'view'"
            class="form-field"
          >
            <label>คลังมาตรฐาน</label>
            <select v-model="catalogSelection" @change="applyCatalogSelection">
              <option value="">— กรอกเอง —</option>
              <option v-for="item in catalogItems" :key="item.key" :value="item.key">
                {{ item.category_label }} · {{ item.product_name }}
              </option>
            </select>
            <small v-if="catalogHint" class="catalog-hint">{{ catalogHint }}</small>
          </div>

          <div
            v-for="field in formFields"
            :key="field.key"
            class="form-field"
          >
            <label>
              {{ field.label }}
              <em v-if="field.required">*</em>
            </label>

            <select
              v-if="field.type === 'select'"
              v-model="form[field.key]"
              :required="field.required"
              :disabled="modalMode === 'view'"
            >
              <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
            </select>

            <select
              v-else-if="field.type === 'relation'"
              v-model="form[field.key]"
              :required="field.required"
              :disabled="modalMode === 'view' || relationLoading[field.key]"
            >
              <option v-if="field.allowEmpty !== false" value="">
                {{ relationLoading[field.key] ? 'กำลังโหลด…' : (field.emptyLabel || '— เลือก —') }}
              </option>
              <option
                v-for="opt in relationOptions[field.key] || []"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </option>
            </select>

            <textarea
              v-else-if="field.type === 'textarea'"
              v-model="form[field.key]"
              rows="3"
              :required="field.required"
              :disabled="modalMode === 'view'"
              :placeholder="field.placeholder"
            />

            <input
              v-else-if="field.type === 'number'"
              v-model.number="form[field.key]"
              type="number"
              :min="field.min"
              :max="field.max"
              :step="field.step"
              :required="field.required"
              :disabled="modalMode === 'view'"
            />

            <input
              v-else
              v-model="form[field.key]"
              type="text"
              :required="field.required"
              :disabled="modalMode === 'view'"
              :placeholder="field.placeholder"
            />
          </div>

          <footer v-if="modalMode !== 'view'" class="modal-actions">
            <button type="button" class="btn-ghost" @click="closeModal">ยกเลิก</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'กำลังบันทึก…' : 'บันทึก' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import Header from '../components/Header.vue'
import { databaseGroups, findEntity } from '../config/databaseCatalog'
import { createResource, deleteResource, listResource, updateResource } from '../services/api'

export default {
  name: 'Database',
  components: { Header },
  setup() {
    const openGroups = reactive(
      Object.fromEntries(databaseGroups.map((g) => [g.id, true])),
    )
    const activeEntityId = ref(databaseGroups[0]?.entities[0]?.id || '')
    const scenarios = ref([])
    const selectedScenarioId = ref('')
    const rows = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const error = ref('')

    const modalOpen = ref(false)
    const modalMode = ref('create')
    const form = reactive({})
    const editingId = ref(null)
    const relationOptions = reactive({})
    const relationLoading = reactive({})
    const relationLabelMaps = reactive({})
    const catalogItems = ref([])
    const catalogSelection = ref('')
    const catalogHint = computed(() => {
      const item = catalogItems.value.find((row) => row.key === catalogSelection.value)
      return item?.description || ''
    })

    const activeMatch = computed(() => findEntity(activeEntityId.value))
    const activeEntity = computed(() => activeMatch.value?.entity || null)
    const activeGroup = computed(() => activeMatch.value?.group || null)

    const listColumns = computed(() => {
      const entity = activeEntity.value
      if (!entity) return []
      if (entity.listFields?.length) {
        return entity.listFields.map((key) => ({
          key,
          label: entity.fields.find((f) => f.key === key)?.label || key,
        }))
      }
      return entity.fields
        .filter((f) => f.list !== false)
        .slice(0, 6)
        .map((f) => ({ key: f.key, label: f.label }))
    })

    const formFields = computed(() => activeEntity.value?.fields || [])

    const canCreate = computed(() => {
      const entity = activeEntity.value
      if (!entity || entity.readOnly) return false
      if (entity.scenarioScoped && !selectedScenarioId.value && scenarios.value.length === 0) {
        return false
      }
      return true
    })

    const modalTitle = computed(() => {
      const name = activeEntity.value?.label || ''
      if (modalMode.value === 'create') return `เพิ่ม ${name}`
      if (modalMode.value === 'edit') return `แก้ไข ${name}`
      return `รายละเอียด ${name}`
    })

    function relationScenarioId() {
      return form.scenario_id || selectedScenarioId.value || ''
    }

    function formatRelationOption(row, field) {
      const value = row?.[field.relationValueKey]
      if (value == null || value === '') return null
      const labelRaw = row?.[field.relationLabelKey]
      const label = labelRaw ? String(labelRaw) : String(value).slice(0, 8)
      return { value: String(value), label }
    }

    function relationFieldQuery(field) {
      const query = {}
      if (field.scenarioScoped !== false) {
        const sid = relationScenarioId()
        if (sid) query.scenario_id = sid
      }
      if (field.filterKey && field.filterSourceKey) {
        const filterValue = form[field.filterSourceKey]
        if (filterValue) query[field.filterKey] = filterValue
      }
      return query
    }

    async function loadRelationOptionsForFields(fields) {
      const relationFields = (fields || []).filter((f) => f.type === 'relation' && f.relationPath)
      await Promise.all(
        relationFields.map(async (field) => {
          relationLoading[field.key] = true
          try {
            const query = relationFieldQuery(field)
            const data = await listResource(field.relationPath, query)
            const dataRows = Array.isArray(data) ? data : data?.items || []
            const options = dataRows
              .map((row) => formatRelationOption(row, field))
              .filter(Boolean)
            relationOptions[field.key] = options
            relationLabelMaps[field.key] = Object.fromEntries(
              options.map((opt) => [opt.value, opt.label]),
            )
          } catch {
            relationOptions[field.key] = []
            relationLabelMaps[field.key] = {}
          } finally {
            relationLoading[field.key] = false
          }
        }),
      )
    }

    async function prepareModalRelations() {
      const entity = activeEntity.value
      if (!entity) return
      await loadRelationOptionsForFields(entity.fields)
    }

    function toggleGroup(id) {
      openGroups[id] = !openGroups[id]
    }

    function selectEntity(id) {
      activeEntityId.value = id
      error.value = ''
      loadRows()
    }

    function formatCell(value, columnKey) {
      if (value == null || value === '') return '—'
      if (typeof value === 'boolean') return value ? 'true' : 'false'
      if (typeof value === 'object') return JSON.stringify(value)
      const field = activeEntity.value?.fields?.find((f) => f.key === columnKey)
      if (field?.type === 'relation') {
        const mapped = relationLabelMaps[field.key]?.[String(value)]
        if (mapped) return mapped
      }
      const text = String(value)
      return text.length > 48 ? `${text.slice(0, 45)}…` : text
    }

    function resetForm(seed = {}) {
      Object.keys(form).forEach((key) => delete form[key])
      Object.assign(form, seed)
    }

    function sanitizePayload(payload, fields) {
      const fieldByKey = Object.fromEntries((fields || []).map((f) => [f.key, f]))
      const out = {}
      Object.entries(payload).forEach(([key, value]) => {
        const field = fieldByKey[key]
        if (value === '' || value === undefined) {
          if (field?.type === 'number') {
            if (field.required) out[key] = null
            return
          }
          if (field?.type === 'relation') {
            out[key] = null
            return
          }
          if (field?.type === 'text' || field?.type === 'textarea' || field?.type === 'select') {
            out[key] = ''
            return
          }
          out[key] = null
          return
        }
        out[key] = value
      })
      return out
    }

    async function loadScenarios() {
      try {
        scenarios.value = (await listResource('/scenarios')) || []
        if (!selectedScenarioId.value && scenarios.value.length === 1) {
          selectedScenarioId.value = scenarios.value[0].id
        }
      } catch (err) {
        scenarios.value = []
        error.value = err.message || 'โหลด scenarios ไม่สำเร็จ'
      }
    }

    async function loadRows() {
      const entity = activeEntity.value
      if (!entity) return
      loading.value = true
      error.value = ''
      try {
        const query = {}
        if (entity.scenarioScoped && selectedScenarioId.value) {
          query.scenario_id = selectedScenarioId.value
        }
        const data = await listResource(entity.path, query)
        rows.value = Array.isArray(data) ? data : data?.items || []
        await loadRelationOptionsForFields(
          (entity.fields || []).filter((f) => f.type === 'relation'),
        )
      } catch (err) {
        rows.value = []
        error.value = err.message || 'โหลดข้อมูลไม่สำเร็จ'
      } finally {
        loading.value = false
      }
    }

    async function loadProductCatalog() {
      const entity = activeEntity.value
      catalogItems.value = []
      catalogSelection.value = ''
      if (!entity?.catalogPath) return
      try {
        catalogItems.value = (await listResource(entity.catalogPath)) || []
      } catch {
        catalogItems.value = []
      }
    }

    function applyCatalogSelection() {
      const item = catalogItems.value.find((row) => row.key === catalogSelection.value)
      if (!item) return
      form.product_name = item.product_name
      form.weight_pounds = item.weight_pounds
      form.unit_cost = item.unit_cost
      form.description = item.description || ''
    }

    async function openCreate() {
      const entity = activeEntity.value
      if (!entity) return
      modalMode.value = 'create'
      editingId.value = null
      resetForm({
        ...structuredClone(entity.defaults || {}),
        ...(entity.scenarioScoped
          ? { scenario_id: selectedScenarioId.value || '' }
          : {}),
      })
      modalOpen.value = true
      await Promise.all([prepareModalRelations(), loadProductCatalog()])
    }

    function normalizeRelationSeed(row) {
      const seed = { ...row }
      ;(activeEntity.value?.fields || [])
        .filter((f) => f.type === 'relation')
        .forEach((f) => {
          if (seed[f.key] != null && seed[f.key] !== '') {
            seed[f.key] = String(seed[f.key])
          } else {
            seed[f.key] = ''
          }
        })
      return seed
    }

    async function openEdit(row) {
      modalMode.value = 'edit'
      editingId.value = row[activeEntity.value.idField || 'id']
      resetForm(normalizeRelationSeed(row))
      modalOpen.value = true
      await Promise.all([prepareModalRelations(), loadProductCatalog()])
    }

    async function openView(row) {
      modalMode.value = 'view'
      editingId.value = row[activeEntity.value.idField || 'id']
      resetForm(normalizeRelationSeed(row))
      modalOpen.value = true
      await prepareModalRelations()
    }

    function closeModal() {
      modalOpen.value = false
    }

    async function saveForm() {
      const entity = activeEntity.value
      if (!entity || modalMode.value === 'view') return
      saving.value = true
      error.value = ''
      try {
        const allowedKeys = new Set(entity.fields.map((f) => f.key))
        if (entity.scenarioScoped) allowedKeys.add('scenario_id')
        const raw = {}
        allowedKeys.forEach((key) => {
          if (Object.prototype.hasOwnProperty.call(form, key)) {
            raw[key] = form[key]
          }
        })
        const payload = sanitizePayload(raw, entity.fields)

        if (modalMode.value === 'create') {
          if (entity.scenarioScoped && !payload.scenario_id) {
            throw new Error('กรุณาเลือก scenario')
          }
          await createResource(entity.path, payload)
        } else {
          delete payload.scenario_id
          await updateResource(entity.path, editingId.value, payload)
        }
        modalOpen.value = false
        await loadRows()
      } catch (err) {
        error.value = err.message || 'บันทึกไม่สำเร็จ'
      } finally {
        saving.value = false
      }
    }

    async function confirmDelete(row) {
      const entity = activeEntity.value
      if (!entity) return
      const id = row[entity.idField || 'id']
      if (!confirm(`ต้องการลบ/archive รายการนี้หรือไม่?\nID: ${id}`)) return
      error.value = ''
      try {
        await deleteResource(entity.path, id)
        await loadRows()
      } catch (err) {
        error.value = err.message || 'ลบไม่สำเร็จ'
      }
    }

    watch(activeEntityId, () => {
      // keep groups expanded for active entity
      const match = findEntity(activeEntityId.value)
      if (match) openGroups[match.group.id] = true
    })

    watch(
      () => form.scenario_id,
      async () => {
        if (modalOpen.value) await prepareModalRelations()
      },
    )

    watch(
      () => form.wing_id,
      async (nextWing, prevWing) => {
        if (!modalOpen.value) return
        const flyingUnitField = (activeEntity.value?.fields || []).find(
          (f) => f.key === 'flying_unit_id' && f.type === 'relation',
        )
        if (!flyingUnitField) return
        await loadRelationOptionsForFields([flyingUnitField])
        if (nextWing !== prevWing && form.flying_unit_id) {
          const valid = (relationOptions.flying_unit_id || []).some(
            (opt) => opt.value === String(form.flying_unit_id),
          )
          if (!valid) form.flying_unit_id = ''
        }
      },
    )

    onMounted(async () => {
      await loadScenarios()
      await loadRows()
    })

    return {
      databaseGroups,
      openGroups,
      activeEntityId,
      activeEntity,
      activeGroup,
      scenarios,
      selectedScenarioId,
      rows,
      loading,
      saving,
      error,
      modalOpen,
      modalMode,
      modalTitle,
      form,
      listColumns,
      formFields,
      canCreate,
      relationOptions,
      relationLoading,
      catalogItems,
      catalogSelection,
      catalogHint,
      applyCatalogSelection,
      toggleGroup,
      selectEntity,
      formatCell,
      loadRows,
      openCreate,
      openEdit,
      openView,
      closeModal,
      saveForm,
      confirmDelete,
    }
  },
}
</script>

<style scoped>
.database-page {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}

.database-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 0;
  min-height: calc(100vh - 74px);
}

.db-nav {
  border-right: 1px solid var(--border);
  background: var(--panel-bg);
  padding: 18px 14px 28px;
  overflow-y: auto;
}

.db-nav-heading .kicker,
.db-toolbar .kicker {
  display: block;
  color: #6ea8fe;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.db-nav-heading h2,
.db-toolbar h3 {
  margin: 4px 0;
  font-size: 1.15rem;
}

.db-nav-heading p,
.db-toolbar p {
  margin: 0;
  color: var(--muted);
  font-size: 0.78rem;
}

.db-group {
  margin-top: 14px;
}

.db-group-toggle {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: rgba(13, 110, 253, 0.06);
  color: var(--text);
  font-size: 0.82rem;
  font-weight: 600;
}

.db-group-toggle .chevron {
  margin-left: auto;
  opacity: 0.7;
}

.db-entity-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
  padding-left: 6px;
}

.db-entity-link {
  text-align: left;
  padding: 8px 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  font-size: 0.78rem;
}

.db-entity-link:hover {
  background: rgba(13, 110, 253, 0.1);
  color: #6ea8fe;
}

.db-entity-link.active {
  background: #0d6efd;
  color: #fff;
  font-weight: 600;
}

.db-main {
  padding: 18px 20px 32px;
  overflow: auto;
}

.db-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.db-toolbar code {
  color: #ffd84d;
  font-size: 0.75rem;
}

.badge-readonly {
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 193, 7, 0.15);
  color: #ffc107;
  font-size: 0.68rem;
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: end;
}

.scenario-picker {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 220px;
}

.scenario-picker label {
  color: var(--muted);
  font-size: 0.68rem;
}

.scenario-picker select,
.form-field input,
.form-field select,
.form-field textarea {
  width: 100%;
  min-height: 38px;
  padding: 7px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--control-bg);
  color: var(--text);
}

.btn-primary,
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 38px;
  padding: 7px 12px;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 600;
}

.btn-primary {
  border: 0;
  background: #0d6efd;
  color: #fff;
}

.btn-primary:disabled {
  opacity: 0.5;
}

.btn-ghost {
  border: 1px solid var(--border);
  background: var(--control-bg);
  color: var(--text);
}

.alert-error {
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(220, 53, 69, 0.45);
  border-radius: 8px;
  background: rgba(220, 53, 69, 0.12);
  color: #ff8a95;
  font-size: 0.82rem;
}

.empty-state {
  display: grid;
  place-items: center;
  gap: 6px;
  min-height: 280px;
  border: 1px dashed var(--border);
  border-radius: 12px;
  color: var(--muted);
}

.empty-state i {
  font-size: 2rem;
  color: #6ea8fe;
}

.table-panel {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--panel-bg);
  overflow: hidden;
}

.table-meta {
  display: flex;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.75rem;
}

.table-scroll {
  overflow: auto;
  max-height: calc(100vh - 240px);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

th,
td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: middle;
}

th {
  position: sticky;
  top: 0;
  background: rgba(13, 110, 253, 0.08);
  color: #9ec1ff;
  font-weight: 600;
  white-space: nowrap;
}

.cell {
  display: inline-block;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-row {
  text-align: center;
  color: var(--muted);
  padding: 28px 12px;
}

.actions-col {
  width: 100px;
  white-space: nowrap;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-right: 4px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--control-bg);
  color: var(--text);
}

.icon-btn.danger {
  border-color: rgba(220, 53, 69, 0.45);
  color: #ef6b78;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.55);
}

.modal-card {
  width: min(560px, 100%);
  max-height: 90vh;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--panel-bg);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
}

.modal-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}

.modal-card h4 {
  margin: 0;
  font-size: 1rem;
}

.modal-form {
  display: grid;
  gap: 12px;
  padding: 16px;
}

.form-field label {
  display: block;
  margin-bottom: 4px;
  color: var(--muted);
  font-size: 0.72rem;
}

.form-field em {
  color: #ef6b78;
  font-style: normal;
}

.catalog-hint {
  display: block;
  margin-top: 6px;
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.35;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 6px;
}

@media (max-width: 960px) {
  .database-shell {
    grid-template-columns: 1fr;
  }

  .db-nav {
    border-right: 0;
    border-bottom: 1px solid var(--border);
    max-height: 280px;
  }

  .db-toolbar {
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
  }

  .scenario-picker {
    flex: 1;
    min-width: 0;
  }
}
</style>

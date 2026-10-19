/**
 * Catalog of database entities managed in the Database hub.
 * Each entity maps to a backend REST collection under /api.
 */

const text = (key, label, opts = {}) => ({
  key,
  label,
  type: 'text',
  required: !!opts.required,
  placeholder: opts.placeholder || '',
  list: opts.list !== false,
})

const number = (key, label, opts = {}) => ({
  key,
  label,
  type: 'number',
  required: !!opts.required,
  min: opts.min,
  max: opts.max,
  step: opts.step ?? 'any',
  list: opts.list !== false,
})

const select = (key, label, options, opts = {}) => ({
  key,
  label,
  type: 'select',
  options,
  required: !!opts.required,
  list: opts.list !== false,
})

/** Dropdown loaded from another API collection (e.g. wings). */
const relation = (key, label, opts = {}) => ({
  key,
  label,
  type: 'relation',
  required: !!opts.required,
  list: opts.list !== false,
  relationPath: opts.path,
  relationValueKey: opts.valueKey || 'id',
  relationLabelKey: opts.labelKey || 'name',
  filterKey: opts.filterKey || '',
  filterSourceKey: opts.filterSourceKey || '',
  scenarioScoped: opts.scenarioScoped !== false,
  allowEmpty: opts.allowEmpty !== false,
  emptyLabel: opts.emptyLabel || '— เลือก —',
})

const wingRelation = (key, label, opts = {}) =>
  relation(key, label, {
    path: '/wings',
    valueKey: 'id',
    labelKey: 'wing_name',
    ...opts,
  })

const flyingUnitRelation = (key, label, opts = {}) =>
  relation(key, label, {
    path: '/flying-units',
    valueKey: 'id',
    labelKey: 'unit_name',
    filterKey: 'wing_id',
    filterSourceKey: 'wing_id',
    ...opts,
  })

const textarea = (key, label, opts = {}) => ({
  key,
  label,
  type: 'textarea',
  required: !!opts.required,
  list: false,
})

export const databaseGroups = [
  {
    id: 'foundation',
    label: 'Foundation',
    icon: 'bi-layers',
    entities: [
      {
        id: 'scenarios',
        label: 'Scenarios',
        path: '/scenarios',
        idField: 'id',
        scenarioScoped: false,
        fields: [
          text('name', 'ชื่อ Scenario', { required: true }),
          textarea('description', 'รายละเอียด'),
          select('status', 'สถานะ', ['draft', 'active', 'archived'], { required: true }),
        ],
        defaults: { name: '', description: '', status: 'draft' },
      },
    ],
  },
  {
    id: 'targets',
    label: 'Targets',
    icon: 'bi-bullseye',
    entities: [
      {
        id: 'targets',
        label: 'Target Cards',
        path: '/targets',
        idField: 'id',
        scenarioScoped: true,
        fields: [
          text('label', 'ชื่อเป้าหมาย', { required: true }),
          text('target_type', 'ประเภท'),
          text('target_subtype', 'ประเภทย่อย'),
          number('priority_score', 'Priority', { min: 1, max: 5 }),
          number('complexity_score', 'Complexity', { min: 1, max: 5 }),
          select('status', 'สถานะ', ['active', 'archived']),
          select('review_status', 'Review', ['draft', 'requires_review', 'approved']),
        ],
        defaults: {
          label: '',
          target_type: 'BUILDING',
          target_subtype: 'UNKNOWN',
          priority_score: 3,
          complexity_score: 3,
          status: 'active',
          review_status: 'draft',
        },
      },
    ],
  },
  {
    id: 'logistics',
    label: 'Assets / Logistics',
    icon: 'bi-box-seam',
    entities: [
      {
        id: 'organizations',
        label: 'Organizations',
        path: '/organizations',
        scenarioScoped: true,
        fields: [
          text('name', 'ชื่อหน่วย', { required: true }),
          text('organization_type', 'ประเภท'),
          text('location_label', 'สถานที่'),
          number('map_lat', 'Lat'),
          number('map_lng', 'Lng'),
          select('status', 'สถานะ', ['active', 'archived']),
        ],
        defaults: {
          name: '',
          organization_type: 'unit',
          location_label: '',
          map_lat: null,
          map_lng: null,
          status: 'active',
        },
      },
      {
        id: 'platform-types',
        label: 'Platform Types',
        path: '/platform-types',
        scenarioScoped: true,
        fields: [
          text('label', 'ชื่อประเภท', { required: true }),
          select('capability_band', 'Capability', ['low', 'medium', 'high']),
          number('resource_cost_score', 'Resource cost', { min: 0, max: 100 }),
          number('support_need_score', 'Support need', { min: 0, max: 100 }),
        ],
        defaults: {
          label: '',
          capability_band: 'medium',
          resource_cost_score: 50,
          support_need_score: 50,
          status: 'active',
        },
      },
      {
        id: 'platforms',
        label: 'Simulated Platforms',
        path: '/platforms',
        scenarioScoped: true,
        fields: [
          text('label', 'ชื่อแพลตฟอร์ม', { required: true }),
          text('organization_id', 'Organization ID'),
          text('platform_type_id', 'Platform Type ID'),
          select('capability_band', 'Capability', ['low', 'medium', 'high']),
          number('availability_score', 'Availability', { min: 1, max: 5 }),
          select('readiness_status', 'Readiness', ['unknown', 'ready', 'not_ready', 'limited']),
        ],
        defaults: {
          label: '',
          organization_id: null,
          platform_type_id: null,
          capability_band: 'medium',
          availability_score: 3,
          readiness_status: 'unknown',
          status: 'active',
        },
      },
      {
        id: 'depots',
        label: 'Depots',
        path: '/depots',
        scenarioScoped: true,
        fields: [
          text('name', 'ชื่อคลัง', { required: true }),
          text('depot_type', 'ประเภท'),
          number('capacity_score', 'Capacity', { min: 0, max: 100 }),
          number('map_lat', 'Lat'),
          number('map_lng', 'Lng'),
          select('availability_status', 'Availability', ['available', 'limited', 'unavailable']),
        ],
        defaults: {
          name: '',
          depot_type: 'abstract_store',
          capacity_score: 50,
          map_lat: null,
          map_lng: null,
          availability_status: 'available',
          status: 'active',
        },
      },
      {
        id: 'resource-tokens',
        label: 'Resource Tokens',
        path: '/resource-tokens',
        scenarioScoped: true,
        fields: [
          text('token_type', 'Token type', { required: true }),
          number('quantity', 'Quantity', { min: 0 }),
          text('availability_window', 'Availability window'),
        ],
        defaults: {
          token_type: '',
          quantity: 0,
          availability_window: '',
          status: 'active',
        },
      },
      {
        id: 'transport-assets',
        label: 'Transport Assets',
        path: '/transport-assets',
        scenarioScoped: true,
        fields: [
          text('label', 'ชื่อ', { required: true }),
          select('transport_type', 'ประเภท', ['ground', 'air', 'sea']),
          number('capacity_score', 'Capacity', { min: 0, max: 100 }),
          select('readiness_status', 'Readiness', ['unknown', 'ready', 'not_ready']),
        ],
        defaults: {
          label: '',
          transport_type: 'ground',
          capacity_score: 50,
          readiness_status: 'unknown',
          status: 'active',
        },
      },
      {
        id: 'route-segments',
        label: 'Route Segments',
        path: '/route-segments',
        scenarioScoped: true,
        fields: [
          text('origin_entity_type', 'Origin type', { required: true }),
          text('origin_entity_id', 'Origin ID', { required: true }),
          text('destination_entity_type', 'Destination type', { required: true }),
          text('destination_entity_id', 'Destination ID', { required: true }),
          number('distance_score', 'Distance score', { min: 0, max: 100 }),
          number('route_friction_score', 'Friction', { min: 0, max: 100 }),
        ],
        defaults: {
          origin_entity_type: 'organization',
          origin_entity_id: '',
          destination_entity_type: 'depot',
          destination_entity_id: '',
          distance_score: 50,
          route_friction_score: 50,
          status: 'active',
        },
      },
    ],
  },
  {
    id: 'wing',
    label: 'Wing Database',
    icon: 'bi-airplane',
    entities: [
      {
        id: 'wings',
        label: 'Air Wings',
        path: '/wings',
        scenarioScoped: true,
        fields: [
          text('wing_name', 'ชื่อกองบิน', { required: true }),
          number('map_lat', 'Lat'),
          number('map_lng', 'Lng'),
          select('status', 'สถานะ', ['active', 'archived']),
        ],
        defaults: { wing_name: '', map_lat: null, map_lng: null, status: 'active' },
      },
      {
        id: 'flying-units',
        label: 'Flying Units',
        path: '/flying-units',
        scenarioScoped: true,
        fields: [
          wingRelation('wing_id', 'กองบิน', { required: true }),
          text('unit_name', 'ชื่อหน่วยบิน', { required: true }),
          select('status', 'สถานะ', ['active', 'archived']),
        ],
        defaults: { wing_id: '', unit_name: '', status: 'active' },
      },
      {
        id: 'aircraft',
        label: 'Aircraft',
        path: '/aircraft',
        scenarioScoped: true,
        fields: [
          wingRelation('wing_id', 'กองบิน', { required: true }),
          flyingUnitRelation('flying_unit_id', 'หน่วยบิน'),
          text('aircraft_type', 'Aircraft type', { required: true }),
          select('mission_ready', 'Mission ready', ['ready', 'not_ready']),
        ],
        defaults: {
          wing_id: '',
          flying_unit_id: null,
          aircraft_type: 'F-16',
          mission_ready: 'not_ready',
          status: 'active',
        },
      },
      {
        id: 'pilots',
        label: 'Pilots',
        path: '/pilots',
        scenarioScoped: true,
        fields: [
          text('pilot_name', 'ชื่อนักบิน', { required: true }),
          text('callsign', 'Callsign'),
          number('cep_value', 'CEP'),
          wingRelation('wing_id', 'กองบิน', { required: false }),
          flyingUnitRelation('flying_unit_id', 'หน่วยบิน'),
        ],
        defaults: {
          pilot_name: '',
          callsign: '',
          cep_value: 0,
          wing_id: null,
          flying_unit_id: null,
          status: 'active',
        },
      },
      {
        id: 'wing-depots',
        label: 'Wing Depots',
        path: '/wing-depots',
        scenarioScoped: true,
        fields: [
          wingRelation('wing_id', 'กองบิน', { required: true }),
          text('depot_name', 'ชื่อคลัง', { required: true }),
          number('map_lat', 'Lat'),
          number('map_lng', 'Lng'),
        ],
        defaults: { wing_id: '', depot_name: '', map_lat: null, map_lng: null, status: 'active' },
      },
      {
        id: 'wing-products',
        label: 'Wing Products',
        path: '/wing-products',
        scenarioScoped: true,
        catalogPath: '/wing-products/catalog',
        fields: [
          text('product_name', 'ชื่อสินค้า', { required: true }),
          number('weight_pounds', 'Weight (lb)', { min: 0 }),
          number('unit_cost', 'Unit cost', { min: 0 }),
          textarea('description', 'รายละเอียด'),
        ],
        defaults: {
          product_name: '',
          weight_pounds: 0,
          unit_cost: 0,
          description: '',
          status: 'active',
        },
      },
      {
        id: 'wing-vehicles',
        label: 'Logistics Vehicles',
        path: '/wing-vehicles',
        scenarioScoped: true,
        fields: [
          wingRelation('wing_id', 'กองบิน', { required: true }),
          text('vehicle_name', 'ชื่อยาน', { required: true }),
          number('fuel_consumption_rate', 'Fuel rate', { min: 0 }),
          select('mission_ready', 'Mission ready', ['ready', 'not_ready']),
        ],
        defaults: {
          wing_id: '',
          vehicle_name: '',
          fuel_consumption_rate: 0,
          mission_ready: 'not_ready',
          status: 'active',
        },
      },
    ],
  },
  {
    id: 'weaponeering',
    label: 'Weaponeering / Ranking',
    icon: 'bi-crosshair',
    entities: [
      {
        id: 'weaponeering-options',
        label: 'Weaponeering Options',
        path: '/weaponeering-options',
        scenarioScoped: true,
        fields: [
          text('option_label', 'ชื่อตัวเลือก', { required: true }),
          select('effect_category', 'Effect', [
            'abstract_support',
            'abstract_disrupt',
            'abstract_delay',
            'abstract_deny',
          ]),
          number('estimated_effect_score', 'Effect score', { min: 0, max: 100 }),
          number('risk_score', 'Risk', { min: 0, max: 100 }),
          number('logistics_demand_score', 'Logistics demand', { min: 0, max: 100 }),
        ],
        defaults: {
          option_label: '',
          effect_category: 'abstract_support',
          estimated_effect_score: 50,
          risk_score: 50,
          logistics_demand_score: 50,
          status: 'active',
        },
      },
      {
        id: 'scoring-profiles',
        label: 'Scoring Profiles',
        path: '/scoring-profiles',
        scenarioScoped: true,
        fields: [
          text('name', 'ชื่อโปรไฟล์', { required: true }),
          number('priority_weight', 'Priority wt', { min: 0, max: 100 }),
          number('weaponeering_weight', 'Weaponeering wt', { min: 0, max: 100 }),
          number('logistics_weight', 'Logistics wt', { min: 0, max: 100 }),
          number('readiness_weight', 'Readiness wt', { min: 0, max: 100 }),
          number('risk_weight', 'Risk wt', { min: 0, max: 100 }),
        ],
        defaults: {
          name: '',
          priority_weight: 20,
          weaponeering_weight: 20,
          logistics_weight: 20,
          readiness_weight: 15,
          risk_weight: 15,
          resource_balance_weight: 10,
          is_active: false,
        },
      },
      {
        id: 'ranking-runs',
        label: 'Ranking Runs',
        path: '/ranking-runs',
        scenarioScoped: true,
        createOnly: true,
        fields: [
          text('scoring_profile_id', 'Scoring profile ID'),
          text('ruleset_version', 'Ruleset'),
        ],
        defaults: { scoring_profile_id: null, ruleset_version: 'phase-1-baseline' },
        listFields: ['id', 'run_status', 'generated_by', 'ruleset_version', 'created_at'],
      },
      {
        id: 'plan-options',
        label: 'Plan Options',
        path: '/plan-options',
        scenarioScoped: true,
        fields: [
          text('title', 'ชื่อแผน', { required: true }),
          text('planning_horizon', 'Horizon'),
          select('review_status', 'Review', ['draft', 'requires_review', 'approved']),
          number('rank_order', 'Rank'),
        ],
        defaults: {
          title: '',
          planning_horizon: '',
          review_status: 'draft',
          rank_order: null,
        },
      },
    ],
  },
  {
    id: 'map',
    label: 'Detection / Map',
    icon: 'bi-map',
    entities: [
      {
        id: 'team-markers',
        label: 'Team Markers',
        path: '/team-markers',
        scenarioScoped: true,
        fields: [
          select('side', 'ฝ่าย', ['blue', 'red'], { required: true }),
          select(
            'unit_type',
            'Unit type',
            ['generic', 'radar', 'tank', 'small_arms', 'artillery', 'anti_air'],
          ),
          text('label', 'ป้ายชื่อ', { required: true }),
          number('map_lat', 'Lat', { required: true }),
          number('map_lng', 'Lng', { required: true }),
          number('radius_m', 'Radius (m)', { min: 0 }),
        ],
        defaults: {
          side: 'blue',
          unit_type: 'generic',
          label: '',
          map_lat: 14.0,
          map_lng: 100.5,
          radius_m: null,
        },
      },
      {
        id: 'ground-transports',
        label: 'Ground Transports',
        path: '/ground-transports',
        scenarioScoped: true,
        fields: [
          wingRelation('origin_wing_id', 'กองบินต้นทาง', { required: true }),
          wingRelation('destination_wing_id', 'กองบินปลายทาง', { required: true }),
          number('distance_m', 'Distance (m)', { required: true, min: 0 }),
          number('duration_min', 'Duration (min)', { required: true, min: 0 }),
          number('quantity', 'Quantity', { min: 1 }),
          text('label', 'ป้ายชื่อ'),
          select('route_mode', 'Route mode', ['direct', 'road']),
        ],
        defaults: {
          origin_wing_id: '',
          destination_wing_id: '',
          distance_m: 0,
          duration_min: 0,
          quantity: 1,
          label: '',
          route_mode: 'direct',
          status: 'active',
        },
      },
      {
        id: 'detection-runs',
        label: 'Detection Runs',
        path: '/detection-runs',
        scenarioScoped: true,
        readOnly: true,
        fields: [
          text('target_card_id', 'Target ID'),
          text('model_name', 'Model'),
          number('object_count', 'Objects'),
          number('radius_m', 'Radius'),
        ],
        defaults: {},
        listFields: [
          'id',
          'target_card_id',
          'model_name',
          'object_count',
          'radius_m',
          'updated_at',
        ],
      },
    ],
  },
]

export function findEntity(entityId) {
  for (const group of databaseGroups) {
    const found = group.entities.find((e) => e.id === entityId)
    if (found) return { group, entity: found }
  }
  return null
}

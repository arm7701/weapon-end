from uuid import UUID

from pydantic import BaseModel, Field


class JmemProductRankOut(BaseModel):
    rank: int
    product_id: str
    product_name: str
    weight_pounds: float
    unit_cost: float = 0.0
    pd_base: float
    pk_single: float
    n_jmem: int
    n_required: int
    pk_n: float
    quantity_overridden: bool = False
    mae_building_ft2: float
    impact_angle_deg: float | None = None
    description: str = ""
    guidance: str = "unguided"
    requires_laser_designation: bool = False
    range_red_ft: float
    range_orange_min_ft: float
    range_orange_max_ft: float
    range_yellow_dark_ft: float
    range_yellow_light_ft: float
    range_red_m: float
    range_orange_m: float
    range_yellow_dark_m: float
    range_yellow_light_m: float
    selected: bool = False


class JmemCatalogItemOut(BaseModel):
    id: str
    name: str
    weight_pounds: float = 0.0
    unit_cost: float = 0.0
    description: str = ""
    guidance: str = "unguided"
    requires_laser_designation: bool = False


class LaserDesignationWorkflowOut(BaseModel):
    key: str
    label_en: str
    label_th: str
    summary: str


class LaserDesignationOut(BaseModel):
    required: bool
    title: str
    intro: str
    weather_limitation: str = ""
    guidance: str = "unguided"
    workflows: list[LaserDesignationWorkflowOut] = Field(default_factory=list)


class WeaponEffectOut(BaseModel):
    key: str
    label_en: str
    label_th: str
    summary: str


class WeaponEffectsOut(BaseModel):
    title: str
    intro: str
    effects: list[WeaponEffectOut] = Field(default_factory=list)


class CircularErrorMetricOut(BaseModel):
    key: str
    label_en: str
    label_th: str
    summary: str


class CircularErrorOut(BaseModel):
    title: str
    intro: str
    application: str = ""
    metrics: list[CircularErrorMetricOut] = Field(default_factory=list)
    ce50_ft: float | None = None
    ce90_ft: float | None = None
    cep_source: str = ""


class JmemMissionOut(BaseModel):
    cep_ft: float
    tle_ft: float
    impact_angle_deg: float
    burial_pct: float
    target_length_ft: float
    target_width_ft: float
    p_rel: float
    p_wpn: float
    pk_desired: float


class JmemEffectZoneOut(BaseModel):
    zone: str
    color: str
    label_th: str
    radius_ft: float
    radius_m: float
    n_required: int = 1


class JmemCoordinateProductOut(BaseModel):
    coordinate_id: str
    label: str
    is_primary: bool
    selected_product_id: str | None = None
    weapon_quantity: int | None = None
    products: list[JmemProductRankOut] = Field(default_factory=list)


class JmemTargetProductsOut(BaseModel):
    target_id: UUID
    label: str
    target_element: str
    selected_product_id: str | None = None
    weapon_quantity: int | None = None
    product_hint: str = "จัดอันดับจาก Product ใน Database ด้วยสูตร JMEM เดียวกับโปรแกรมเดิม"
    warnings: list[str] = Field(default_factory=list)
    mission: JmemMissionOut
    product_catalog: list[JmemCatalogItemOut] = Field(default_factory=list)
    products: list[JmemProductRankOut] = Field(default_factory=list)
    coordinate_products: list[JmemCoordinateProductOut] = Field(default_factory=list)
    effect_zones: list[JmemEffectZoneOut] = Field(default_factory=list)
    laser_designation: LaserDesignationOut | None = None
    weapon_effects: WeaponEffectsOut | None = None
    circular_error: CircularErrorOut | None = None


class JmemSelectProductIn(BaseModel):
    product_id: str | None = None
    coordinate_id: UUID | None = None


class JmemWeaponQuantityIn(BaseModel):
    quantity: int | None = Field(
        default=None,
        ge=1,
        le=999,
        description="จำนวนลูกที่ใช้ (null = กลับไปใช้ค่า JMEM)",
    )
    coordinate_id: UUID | None = None


class JmemAiAdviceOut(BaseModel):
    recommendation: dict
    analysis_text: str
    prompt: str
    jmem: JmemTargetProductsOut
    applied_product_id: str | None = None

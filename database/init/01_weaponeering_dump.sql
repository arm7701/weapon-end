--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2 (Debian 17.2-1.pgdg120+1)
-- Dumped by pg_dump version 17.2 (Debian 17.2-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.wing_products DROP CONSTRAINT IF EXISTS wing_products_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_pilots DROP CONSTRAINT IF EXISTS wing_pilots_wing_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_pilots DROP CONSTRAINT IF EXISTS wing_pilots_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_pilots DROP CONSTRAINT IF EXISTS wing_pilots_flying_unit_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_logistics_vehicles DROP CONSTRAINT IF EXISTS wing_logistics_vehicles_wing_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_logistics_vehicles DROP CONSTRAINT IF EXISTS wing_logistics_vehicles_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_flying_units DROP CONSTRAINT IF EXISTS wing_flying_units_wing_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_flying_units DROP CONSTRAINT IF EXISTS wing_flying_units_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depots DROP CONSTRAINT IF EXISTS wing_depots_wing_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depots DROP CONSTRAINT IF EXISTS wing_depots_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_transfers DROP CONSTRAINT IF EXISTS wing_depot_transfers_to_depot_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_transfers DROP CONSTRAINT IF EXISTS wing_depot_transfers_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_transfers DROP CONSTRAINT IF EXISTS wing_depot_transfers_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_transfers DROP CONSTRAINT IF EXISTS wing_depot_transfers_from_depot_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_inventory DROP CONSTRAINT IF EXISTS wing_depot_inventory_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_inventory DROP CONSTRAINT IF EXISTS wing_depot_inventory_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_inventory DROP CONSTRAINT IF EXISTS wing_depot_inventory_depot_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_aircraft DROP CONSTRAINT IF EXISTS wing_aircraft_wing_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_aircraft DROP CONSTRAINT IF EXISTS wing_aircraft_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.wing_aircraft DROP CONSTRAINT IF EXISTS wing_aircraft_flying_unit_id_fkey;
ALTER TABLE IF EXISTS ONLY public.weaponeering_import_batches DROP CONSTRAINT IF EXISTS weaponeering_import_batches_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.transport_assets DROP CONSTRAINT IF EXISTS transport_assets_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.transport_assets DROP CONSTRAINT IF EXISTS transport_assets_organization_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_waypoints DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_waypoints_plan_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_plans DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_plans_wing_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_plans DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_plans_target_card_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_plans DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_plans_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_plans DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_plans_flying_unit_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_aircraft DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_aircraft_plan_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_aircraft DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_aircraft_aircraft_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_assessments DROP CONSTRAINT IF EXISTS target_weaponeering_assessments_target_card_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_assessments DROP CONSTRAINT IF EXISTS target_weaponeering_assessmen_abstract_weaponeering_option_fkey;
ALTER TABLE IF EXISTS ONLY public.target_recognition_results DROP CONSTRAINT IF EXISTS target_recognition_results_target_card_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_map_detection_runs DROP CONSTRAINT IF EXISTS target_map_detection_runs_target_coordinate_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_map_detection_runs DROP CONSTRAINT IF EXISTS target_map_detection_runs_target_card_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_map_detection_runs DROP CONSTRAINT IF EXISTS target_map_detection_runs_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_map_detection_objects DROP CONSTRAINT IF EXISTS target_map_detection_objects_target_card_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_map_detection_objects DROP CONSTRAINT IF EXISTS target_map_detection_objects_run_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_coordinates DROP CONSTRAINT IF EXISTS target_coordinates_target_card_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_cards DROP CONSTRAINT IF EXISTS target_cards_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.target_cards DROP CONSTRAINT IF EXISTS target_cards_map_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.simulated_platforms DROP CONSTRAINT IF EXISTS simulated_platforms_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.simulated_platforms DROP CONSTRAINT IF EXISTS simulated_platforms_platform_type_id_fkey;
ALTER TABLE IF EXISTS ONLY public.simulated_platforms DROP CONSTRAINT IF EXISTS simulated_platforms_organization_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scoring_profiles DROP CONSTRAINT IF EXISTS scoring_profiles_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scenarios DROP CONSTRAINT IF EXISTS scenarios_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.scenario_team_markers DROP CONSTRAINT IF EXISTS scenario_team_markers_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scenario_ground_transports DROP CONSTRAINT IF EXISTS scenario_ground_transports_vehicle_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scenario_ground_transports DROP CONSTRAINT IF EXISTS scenario_ground_transports_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scenario_ground_transports DROP CONSTRAINT IF EXISTS scenario_ground_transports_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scenario_ground_transports DROP CONSTRAINT IF EXISTS scenario_ground_transports_origin_wing_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scenario_ground_transports DROP CONSTRAINT IF EXISTS scenario_ground_transports_destination_wing_id_fkey;
ALTER TABLE IF EXISTS ONLY public.route_segments DROP CONSTRAINT IF EXISTS route_segments_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.resource_tokens DROP CONSTRAINT IF EXISTS resource_tokens_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ranking_runs DROP CONSTRAINT IF EXISTS ranking_runs_scoring_profile_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ranking_runs DROP CONSTRAINT IF EXISTS ranking_runs_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ranking_items DROP CONSTRAINT IF EXISTS ranking_items_ranking_run_id_fkey;
ALTER TABLE IF EXISTS ONLY public.platform_types DROP CONSTRAINT IF EXISTS platform_types_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.platform_readiness_events DROP CONSTRAINT IF EXISTS platform_readiness_events_simulated_platform_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plan_scores DROP CONSTRAINT IF EXISTS plan_scores_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plan_scores DROP CONSTRAINT IF EXISTS plan_scores_route_segment_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plan_options DROP CONSTRAINT IF EXISTS plan_options_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plan_assignments DROP CONSTRAINT IF EXISTS plan_assignments_target_card_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plan_assignments DROP CONSTRAINT IF EXISTS plan_assignments_plan_option_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plan_assignments DROP CONSTRAINT IF EXISTS plan_assignments_abstract_weaponeering_option_id_fkey;
ALTER TABLE IF EXISTS ONLY public.organizations DROP CONSTRAINT IF EXISTS organizations_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.map_nodes DROP CONSTRAINT IF EXISTS map_nodes_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.learning_objectives DROP CONSTRAINT IF EXISTS learning_objectives_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.human_review_records DROP CONSTRAINT IF EXISTS human_review_records_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.depots DROP CONSTRAINT IF EXISTS depots_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.depots DROP CONSTRAINT IF EXISTS depots_organization_id_fkey;
ALTER TABLE IF EXISTS ONLY public.depot_inventory DROP CONSTRAINT IF EXISTS depot_inventory_resource_token_id_fkey;
ALTER TABLE IF EXISTS ONLY public.depot_inventory DROP CONSTRAINT IF EXISTS depot_inventory_depot_id_fkey;
ALTER TABLE IF EXISTS ONLY public.auth_sessions DROP CONSTRAINT IF EXISTS auth_sessions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.air_wings DROP CONSTRAINT IF EXISTS air_wings_scenario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.abstract_weaponeering_options DROP CONSTRAINT IF EXISTS abstract_weaponeering_options_scenario_id_fkey;
DROP INDEX IF EXISTS public.ix_wing_products_scenario_id;
DROP INDEX IF EXISTS public.ix_wing_pilots_wing_id;
DROP INDEX IF EXISTS public.ix_wing_pilots_scenario_id;
DROP INDEX IF EXISTS public.ix_wing_logistics_vehicles_wing_id;
DROP INDEX IF EXISTS public.ix_wing_logistics_vehicles_scenario_id;
DROP INDEX IF EXISTS public.ix_wing_flying_units_wing_id;
DROP INDEX IF EXISTS public.ix_wing_flying_units_scenario_id;
DROP INDEX IF EXISTS public.ix_wing_depots_wing_id;
DROP INDEX IF EXISTS public.ix_wing_depots_scenario_id;
DROP INDEX IF EXISTS public.ix_wing_depot_transfers_scenario_id;
DROP INDEX IF EXISTS public.ix_wing_depot_inventory_scenario_id;
DROP INDEX IF EXISTS public.ix_wing_depot_inventory_product_id;
DROP INDEX IF EXISTS public.ix_wing_depot_inventory_depot_id;
DROP INDEX IF EXISTS public.ix_wing_aircraft_wing_id;
DROP INDEX IF EXISTS public.ix_wing_aircraft_scenario_id;
DROP INDEX IF EXISTS public.ix_weaponeering_import_batches_scenario_id;
DROP INDEX IF EXISTS public.ix_users_username;
DROP INDEX IF EXISTS public.ix_transport_assets_scenario_id;
DROP INDEX IF EXISTS public.ix_target_weaponeering_assessments_target;
DROP INDEX IF EXISTS public.ix_target_weaponeering_assessments_option;
DROP INDEX IF EXISTS public.ix_target_recognition_results_target_card_id;
DROP INDEX IF EXISTS public.ix_target_map_detection_runs_target_card_id;
DROP INDEX IF EXISTS public.ix_target_map_detection_runs_scenario_id;
DROP INDEX IF EXISTS public.ix_target_map_detection_objects_target_card_id;
DROP INDEX IF EXISTS public.ix_target_map_detection_objects_run_id;
DROP INDEX IF EXISTS public.ix_target_coordinates_target_card_id;
DROP INDEX IF EXISTS public.ix_target_coordinates_card_sort;
DROP INDEX IF EXISTS public.ix_target_cards_scenario_id;
DROP INDEX IF EXISTS public.ix_simulated_platforms_scenario_id;
DROP INDEX IF EXISTS public.ix_scoring_profiles_scenario_id;
DROP INDEX IF EXISTS public.ix_scenario_team_markers_scenario_id;
DROP INDEX IF EXISTS public.ix_scenario_ground_transports_scenario_id;
DROP INDEX IF EXISTS public.ix_route_segments_scenario_id;
DROP INDEX IF EXISTS public.ix_resource_tokens_scenario_id;
DROP INDEX IF EXISTS public.ix_ranking_runs_scenario_id;
DROP INDEX IF EXISTS public.ix_ranking_items_run_id;
DROP INDEX IF EXISTS public.ix_platform_types_scenario_id;
DROP INDEX IF EXISTS public.ix_platform_readiness_events_platform_id;
DROP INDEX IF EXISTS public.ix_plan_scores_scenario_id;
DROP INDEX IF EXISTS public.ix_plan_options_scenario_id;
DROP INDEX IF EXISTS public.ix_plan_assignments_plan_option_id;
DROP INDEX IF EXISTS public.ix_organizations_scenario_id;
DROP INDEX IF EXISTS public.ix_map_nodes_scenario_id;
DROP INDEX IF EXISTS public.ix_learning_objectives_scenario_id;
DROP INDEX IF EXISTS public.ix_human_review_records_scenario_id;
DROP INDEX IF EXISTS public.ix_depots_scenario_id;
DROP INDEX IF EXISTS public.ix_depot_inventory_depot_id;
DROP INDEX IF EXISTS public.ix_deployment_waypoints_plan_id;
DROP INDEX IF EXISTS public.ix_deployment_plans_scenario_id;
DROP INDEX IF EXISTS public.ix_deployment_aircraft_plan_id;
DROP INDEX IF EXISTS public.ix_auth_sessions_user_id;
DROP INDEX IF EXISTS public.ix_audit_events_event_type;
DROP INDEX IF EXISTS public.ix_air_wings_scenario_id;
DROP INDEX IF EXISTS public.ix_abstract_weaponeering_options_scenario_id;
ALTER TABLE IF EXISTS ONLY public.wing_products DROP CONSTRAINT IF EXISTS wing_products_pkey;
ALTER TABLE IF EXISTS ONLY public.wing_pilots DROP CONSTRAINT IF EXISTS wing_pilots_pkey;
ALTER TABLE IF EXISTS ONLY public.wing_logistics_vehicles DROP CONSTRAINT IF EXISTS wing_logistics_vehicles_pkey;
ALTER TABLE IF EXISTS ONLY public.wing_flying_units DROP CONSTRAINT IF EXISTS wing_flying_units_pkey;
ALTER TABLE IF EXISTS ONLY public.wing_depots DROP CONSTRAINT IF EXISTS wing_depots_pkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_transfers DROP CONSTRAINT IF EXISTS wing_depot_transfers_pkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_inventory DROP CONSTRAINT IF EXISTS wing_depot_inventory_pkey;
ALTER TABLE IF EXISTS ONLY public.wing_aircraft DROP CONSTRAINT IF EXISTS wing_aircraft_pkey;
ALTER TABLE IF EXISTS ONLY public.weaponeering_import_batches DROP CONSTRAINT IF EXISTS weaponeering_import_batches_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_username_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.wing_depot_inventory DROP CONSTRAINT IF EXISTS uq_wing_depot_product;
ALTER TABLE IF EXISTS ONLY public.target_map_detection_runs DROP CONSTRAINT IF EXISTS uq_detection_run_target_coord;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_aircraft DROP CONSTRAINT IF EXISTS uq_deployment_plan_aircraft;
ALTER TABLE IF EXISTS ONLY public.transport_assets DROP CONSTRAINT IF EXISTS transport_assets_pkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_waypoints DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_waypoints_pkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_plans DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_plans_target_card_id_key;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_plans DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_plans_pkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_deployment_aircraft DROP CONSTRAINT IF EXISTS target_weaponeering_deployment_aircraft_pkey;
ALTER TABLE IF EXISTS ONLY public.target_weaponeering_assessments DROP CONSTRAINT IF EXISTS target_weaponeering_assessments_pkey;
ALTER TABLE IF EXISTS ONLY public.target_recognition_results DROP CONSTRAINT IF EXISTS target_recognition_results_pkey;
ALTER TABLE IF EXISTS ONLY public.target_map_detection_runs DROP CONSTRAINT IF EXISTS target_map_detection_runs_pkey;
ALTER TABLE IF EXISTS ONLY public.target_map_detection_objects DROP CONSTRAINT IF EXISTS target_map_detection_objects_pkey;
ALTER TABLE IF EXISTS ONLY public.target_coordinates DROP CONSTRAINT IF EXISTS target_coordinates_pkey;
ALTER TABLE IF EXISTS ONLY public.target_cards DROP CONSTRAINT IF EXISTS target_cards_pkey;
ALTER TABLE IF EXISTS ONLY public.simulated_platforms DROP CONSTRAINT IF EXISTS simulated_platforms_pkey;
ALTER TABLE IF EXISTS ONLY public.scoring_profiles DROP CONSTRAINT IF EXISTS scoring_profiles_pkey;
ALTER TABLE IF EXISTS ONLY public.scenarios DROP CONSTRAINT IF EXISTS scenarios_pkey;
ALTER TABLE IF EXISTS ONLY public.scenario_team_markers DROP CONSTRAINT IF EXISTS scenario_team_markers_pkey;
ALTER TABLE IF EXISTS ONLY public.scenario_ground_transports DROP CONSTRAINT IF EXISTS scenario_ground_transports_pkey;
ALTER TABLE IF EXISTS ONLY public.route_segments DROP CONSTRAINT IF EXISTS route_segments_pkey;
ALTER TABLE IF EXISTS ONLY public.resource_tokens DROP CONSTRAINT IF EXISTS resource_tokens_pkey;
ALTER TABLE IF EXISTS ONLY public.ranking_runs DROP CONSTRAINT IF EXISTS ranking_runs_pkey;
ALTER TABLE IF EXISTS ONLY public.ranking_items DROP CONSTRAINT IF EXISTS ranking_items_pkey;
ALTER TABLE IF EXISTS ONLY public.platform_types DROP CONSTRAINT IF EXISTS platform_types_pkey;
ALTER TABLE IF EXISTS ONLY public.platform_readiness_events DROP CONSTRAINT IF EXISTS platform_readiness_events_pkey;
ALTER TABLE IF EXISTS ONLY public.plan_scores DROP CONSTRAINT IF EXISTS plan_scores_pkey;
ALTER TABLE IF EXISTS ONLY public.plan_options DROP CONSTRAINT IF EXISTS plan_options_pkey;
ALTER TABLE IF EXISTS ONLY public.plan_assignments DROP CONSTRAINT IF EXISTS plan_assignments_pkey;
ALTER TABLE IF EXISTS ONLY public.organizations DROP CONSTRAINT IF EXISTS organizations_pkey;
ALTER TABLE IF EXISTS ONLY public.map_nodes DROP CONSTRAINT IF EXISTS map_nodes_pkey;
ALTER TABLE IF EXISTS ONLY public.learning_objectives DROP CONSTRAINT IF EXISTS learning_objectives_pkey;
ALTER TABLE IF EXISTS ONLY public.human_review_records DROP CONSTRAINT IF EXISTS human_review_records_pkey;
ALTER TABLE IF EXISTS ONLY public.guardrail_events DROP CONSTRAINT IF EXISTS guardrail_events_pkey;
ALTER TABLE IF EXISTS ONLY public.depots DROP CONSTRAINT IF EXISTS depots_pkey;
ALTER TABLE IF EXISTS ONLY public.depot_inventory DROP CONSTRAINT IF EXISTS depot_inventory_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_sessions DROP CONSTRAINT IF EXISTS auth_sessions_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_sessions DROP CONSTRAINT IF EXISTS auth_sessions_access_token_key;
ALTER TABLE IF EXISTS ONLY public.audit_events DROP CONSTRAINT IF EXISTS audit_events_pkey;
ALTER TABLE IF EXISTS ONLY public.app_settings DROP CONSTRAINT IF EXISTS app_settings_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS ONLY public.air_wings DROP CONSTRAINT IF EXISTS air_wings_pkey;
ALTER TABLE IF EXISTS ONLY public.abstract_weaponeering_options DROP CONSTRAINT IF EXISTS abstract_weaponeering_options_pkey;
DROP TABLE IF EXISTS public.wing_products;
DROP TABLE IF EXISTS public.wing_pilots;
DROP TABLE IF EXISTS public.wing_logistics_vehicles;
DROP TABLE IF EXISTS public.wing_flying_units;
DROP TABLE IF EXISTS public.wing_depots;
DROP TABLE IF EXISTS public.wing_depot_transfers;
DROP TABLE IF EXISTS public.wing_depot_inventory;
DROP TABLE IF EXISTS public.wing_aircraft;
DROP TABLE IF EXISTS public.weaponeering_import_batches;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.transport_assets;
DROP TABLE IF EXISTS public.target_weaponeering_deployment_waypoints;
DROP TABLE IF EXISTS public.target_weaponeering_deployment_plans;
DROP TABLE IF EXISTS public.target_weaponeering_deployment_aircraft;
DROP TABLE IF EXISTS public.target_weaponeering_assessments;
DROP TABLE IF EXISTS public.target_recognition_results;
DROP TABLE IF EXISTS public.target_map_detection_runs;
DROP TABLE IF EXISTS public.target_map_detection_objects;
DROP TABLE IF EXISTS public.target_coordinates;
DROP TABLE IF EXISTS public.target_cards;
DROP TABLE IF EXISTS public.simulated_platforms;
DROP TABLE IF EXISTS public.scoring_profiles;
DROP TABLE IF EXISTS public.scenarios;
DROP TABLE IF EXISTS public.scenario_team_markers;
DROP TABLE IF EXISTS public.scenario_ground_transports;
DROP TABLE IF EXISTS public.route_segments;
DROP TABLE IF EXISTS public.resource_tokens;
DROP TABLE IF EXISTS public.ranking_runs;
DROP TABLE IF EXISTS public.ranking_items;
DROP TABLE IF EXISTS public.platform_types;
DROP TABLE IF EXISTS public.platform_readiness_events;
DROP TABLE IF EXISTS public.plan_scores;
DROP TABLE IF EXISTS public.plan_options;
DROP TABLE IF EXISTS public.plan_assignments;
DROP TABLE IF EXISTS public.organizations;
DROP TABLE IF EXISTS public.map_nodes;
DROP TABLE IF EXISTS public.learning_objectives;
DROP TABLE IF EXISTS public.human_review_records;
DROP TABLE IF EXISTS public.guardrail_events;
DROP TABLE IF EXISTS public.depots;
DROP TABLE IF EXISTS public.depot_inventory;
DROP TABLE IF EXISTS public.auth_sessions;
DROP TABLE IF EXISTS public.audit_events;
DROP TABLE IF EXISTS public.app_settings;
DROP TABLE IF EXISTS public.alembic_version;
DROP TABLE IF EXISTS public.air_wings;
DROP TABLE IF EXISTS public.abstract_weaponeering_options;
-- *not* dropping schema, since initdb creates it
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: abstract_weaponeering_options; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.abstract_weaponeering_options (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    option_label character varying(255) NOT NULL,
    effect_category character varying(64) DEFAULT 'abstract_support'::character varying NOT NULL,
    required_capability_band character varying(64) DEFAULT 'medium'::character varying NOT NULL,
    resource_token_type character varying(128) DEFAULT ''::character varying NOT NULL,
    estimated_effect_score integer DEFAULT 50 NOT NULL,
    risk_score integer DEFAULT 50 NOT NULL,
    logistics_demand_score integer DEFAULT 50 NOT NULL,
    source_module character varying(64) DEFAULT 'manual'::character varying NOT NULL,
    review_status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: air_wings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.air_wings (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    wing_name character varying(255) NOT NULL,
    map_lat double precision,
    map_lng double precision,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: app_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_settings (
    key character varying(128) NOT NULL,
    value text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: audit_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_events (
    id uuid NOT NULL,
    actor character varying(128) NOT NULL,
    event_type character varying(64) NOT NULL,
    entity_type character varying(64) NOT NULL,
    entity_id character varying(64) NOT NULL,
    details_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: auth_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    access_token text NOT NULL,
    challenge character varying(255),
    login_mode character varying(64),
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone
);


--
-- Name: depot_inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.depot_inventory (
    id uuid NOT NULL,
    depot_id uuid NOT NULL,
    resource_token_id uuid,
    inventory_category character varying(64) DEFAULT 'support_token'::character varying NOT NULL,
    option_label character varying(255) NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    availability_status character varying(64) DEFAULT 'available'::character varying NOT NULL,
    notes text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: depots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.depots (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    organization_id uuid,
    name character varying(255) NOT NULL,
    depot_type character varying(64) DEFAULT 'abstract_store'::character varying NOT NULL,
    map_lat double precision,
    map_lng double precision,
    capacity_score integer DEFAULT 50 NOT NULL,
    availability_status character varying(64) DEFAULT 'available'::character varying NOT NULL,
    review_status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: guardrail_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.guardrail_events (
    id uuid NOT NULL,
    event_type character varying(64) NOT NULL,
    entity_type character varying(64) NOT NULL,
    entity_id character varying(64) NOT NULL,
    decision character varying(64) NOT NULL,
    sanitized_summary text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: human_review_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.human_review_records (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    entity_type character varying(64) NOT NULL,
    entity_id character varying(64) NOT NULL,
    reviewer character varying(128) NOT NULL,
    decision character varying(64) NOT NULL,
    notes text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: learning_objectives; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_objectives (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    label character varying(255) NOT NULL,
    priority integer DEFAULT 50 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: map_nodes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.map_nodes (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    label character varying(255) NOT NULL,
    node_type character varying(64) DEFAULT 'synthetic_node'::character varying NOT NULL,
    map_lat double precision NOT NULL,
    map_lng double precision NOT NULL,
    review_status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    linked_entity_type character varying(64),
    linked_entity_id character varying(64),
    is_synthetic_location boolean DEFAULT true NOT NULL
);


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    organization_type character varying(64) DEFAULT 'unit'::character varying NOT NULL,
    map_lat double precision,
    map_lng double precision,
    location_label character varying(255) DEFAULT ''::character varying NOT NULL,
    is_synthetic_location boolean DEFAULT true NOT NULL,
    readiness_summary character varying(64) DEFAULT 'unknown'::character varying NOT NULL,
    review_status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: plan_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plan_assignments (
    id uuid NOT NULL,
    plan_option_id uuid NOT NULL,
    target_card_id uuid,
    simulated_platform_id uuid,
    abstract_weaponeering_option_id uuid,
    depot_id uuid,
    route_segment_id uuid,
    assigned_resource_quantity integer DEFAULT 0 NOT NULL,
    assignment_score integer DEFAULT 50 NOT NULL,
    review_status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: plan_options; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plan_options (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    planning_horizon character varying(64) DEFAULT ''::character varying NOT NULL,
    title character varying(255) NOT NULL,
    generated_by character varying(64) DEFAULT 'user'::character varying NOT NULL,
    review_status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    rank_order integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: plan_scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plan_scores (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    route_segment_id uuid,
    plan_option_id character varying(64),
    priority_alignment integer,
    logistics_feasibility integer NOT NULL,
    resource_balance integer,
    risk_indicator integer,
    rationale text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: platform_readiness_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.platform_readiness_events (
    id uuid NOT NULL,
    simulated_platform_id uuid NOT NULL,
    status character varying(64) NOT NULL,
    readiness_score integer DEFAULT 50 NOT NULL,
    reason text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: platform_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.platform_types (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    label character varying(255) NOT NULL,
    capability_band character varying(64) DEFAULT 'medium'::character varying NOT NULL,
    resource_cost_score integer DEFAULT 50 NOT NULL,
    support_need_score integer DEFAULT 50 NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: ranking_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ranking_items (
    id uuid NOT NULL,
    ranking_run_id uuid NOT NULL,
    entity_type character varying(64) DEFAULT 'target_card'::character varying NOT NULL,
    entity_id character varying(64) NOT NULL,
    rank_order integer NOT NULL,
    total_score integer NOT NULL,
    confidence_score integer DEFAULT 50 NOT NULL,
    rationale text DEFAULT ''::text NOT NULL,
    breakdown_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    review_status character varying(32) DEFAULT 'requires_review'::character varying NOT NULL,
    override_rank_order integer,
    override_notes text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: ranking_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ranking_runs (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    ruleset_version character varying(64) DEFAULT 'phase-1-baseline'::character varying NOT NULL,
    scoring_profile_id uuid,
    generated_by character varying(128) DEFAULT 'local_user'::character varying NOT NULL,
    run_status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    summary text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: resource_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_tokens (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    token_type character varying(128) NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    availability_window character varying(255) DEFAULT ''::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: route_segments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.route_segments (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    origin_entity_type character varying(64) NOT NULL,
    origin_entity_id character varying(64) NOT NULL,
    destination_entity_type character varying(64) NOT NULL,
    destination_entity_id character varying(64) NOT NULL,
    origin_lat double precision,
    origin_lng double precision,
    destination_lat double precision,
    destination_lng double precision,
    distance_score integer DEFAULT 50 NOT NULL,
    fuel_stop_score integer DEFAULT 50 NOT NULL,
    route_friction_score integer DEFAULT 50 NOT NULL,
    availability_status character varying(64) DEFAULT 'available'::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: scenario_ground_transports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scenario_ground_transports (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    origin_wing_id uuid NOT NULL,
    destination_wing_id uuid NOT NULL,
    product_id uuid,
    vehicle_id uuid,
    quantity integer DEFAULT 1 NOT NULL,
    distance_m double precision NOT NULL,
    duration_min double precision NOT NULL,
    route_mode character varying(32) DEFAULT 'direct'::character varying NOT NULL,
    route_geometry_json jsonb,
    label character varying(255) DEFAULT ''::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: scenario_team_markers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scenario_team_markers (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    side character varying(16) NOT NULL,
    unit_type character varying(32) DEFAULT 'generic'::character varying NOT NULL,
    label character varying(255) NOT NULL,
    map_lat double precision NOT NULL,
    map_lng double precision NOT NULL,
    radius_m double precision,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_team_marker_side CHECK (((side)::text = ANY ((ARRAY['blue'::character varying, 'red'::character varying])::text[]))),
    CONSTRAINT ck_team_marker_unit_type CHECK (((unit_type)::text = ANY ((ARRAY['generic'::character varying, 'radar'::character varying, 'tank'::character varying, 'small_arms'::character varying, 'artillery'::character varying, 'anti_air'::character varying])::text[])))
);


--
-- Name: scenarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scenarios (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text DEFAULT ''::text NOT NULL,
    status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    ruleset_version character varying(64) DEFAULT 'phase-0-web'::character varying NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: scoring_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scoring_profiles (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    ruleset_version character varying(64) DEFAULT 'phase-1-baseline'::character varying NOT NULL,
    priority_weight integer DEFAULT 20 NOT NULL,
    weaponeering_weight integer DEFAULT 20 NOT NULL,
    logistics_weight integer DEFAULT 20 NOT NULL,
    readiness_weight integer DEFAULT 15 NOT NULL,
    risk_weight integer DEFAULT 15 NOT NULL,
    resource_balance_weight integer DEFAULT 10 NOT NULL,
    is_active boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: simulated_platforms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.simulated_platforms (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    organization_id uuid,
    platform_type_id uuid,
    label character varying(255) NOT NULL,
    capability_band character varying(64) DEFAULT 'medium'::character varying NOT NULL,
    availability_score integer DEFAULT 3 NOT NULL,
    readiness_status character varying(64) DEFAULT 'unknown'::character varying NOT NULL,
    readiness_note text DEFAULT ''::text NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: target_cards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_cards (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    label character varying(255) NOT NULL,
    priority_score integer DEFAULT 3 NOT NULL,
    complexity_score integer DEFAULT 3 NOT NULL,
    map_node_id uuid,
    review_status character varying(32) DEFAULT 'draft'::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    target_type character varying(64) DEFAULT 'BUILDING'::character varying NOT NULL,
    target_subtype character varying(128) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    material_class character varying(64) DEFAULT 'UNKNOWN'::character varying NOT NULL,
    target_description text DEFAULT ''::text NOT NULL,
    floor_count character varying(32) DEFAULT ''::character varying NOT NULL,
    width_m double precision,
    length_m double precision,
    height_m double precision,
    desired_model_result character varying(128) DEFAULT 'STRUCTURAL FAILURE'::character varying NOT NULL,
    coordinate_error_m double precision,
    data_source character varying(64) DEFAULT 'manual'::character varying NOT NULL,
    cep double precision,
    target_pk double precision,
    reference_pk double precision,
    resistance character varying(128) DEFAULT ''::character varying NOT NULL,
    capacity character varying(128) DEFAULT ''::character varying NOT NULL,
    damage_fit character varying(128) DEFAULT ''::character varying NOT NULL,
    model_version character varying(64) DEFAULT ''::character varying NOT NULL,
    selected_product_id character varying(64),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    weapon_quantity integer,
    heading_deg double precision,
    material_strength jsonb DEFAULT '{}'::jsonb NOT NULL
);


--
-- Name: target_coordinates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_coordinates (
    id uuid NOT NULL,
    target_card_id uuid NOT NULL,
    label character varying(255) DEFAULT ''::character varying NOT NULL,
    map_lat double precision NOT NULL,
    map_lng double precision NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    selected_product_id character varying(64),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    weapon_quantity integer
);


--
-- Name: target_map_detection_objects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_map_detection_objects (
    id uuid NOT NULL,
    run_id uuid NOT NULL,
    target_card_id uuid NOT NULL,
    map_object_id character varying(128) NOT NULL,
    object_label character varying(255) NOT NULL,
    object_type character varying(64) NOT NULL,
    risk_level character varying(32) NOT NULL,
    confidence double precision NOT NULL,
    center_lat double precision NOT NULL,
    center_lng double precision NOT NULL,
    polygon_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL
);


--
-- Name: target_map_detection_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_map_detection_runs (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    target_card_id uuid NOT NULL,
    target_coordinate_id uuid NOT NULL,
    model_name character varying(255) NOT NULL,
    model_file_name character varying(255),
    radius_m integer NOT NULL,
    capture_radius_m integer NOT NULL,
    source_image_name character varying(255),
    object_count integer DEFAULT 0 NOT NULL,
    detection_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: target_recognition_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_recognition_results (
    id uuid NOT NULL,
    target_card_id uuid NOT NULL,
    source_type character varying(64) DEFAULT 'manual'::character varying NOT NULL,
    recognition_summary text DEFAULT ''::text NOT NULL,
    recognition_confidence_score integer DEFAULT 50 NOT NULL,
    missing_data_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    generated_by character varying(64) DEFAULT 'user'::character varying NOT NULL,
    review_status character varying(32) DEFAULT 'requires_review'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: target_weaponeering_assessments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_weaponeering_assessments (
    id uuid NOT NULL,
    target_card_id uuid NOT NULL,
    abstract_weaponeering_option_id uuid NOT NULL,
    suitability_score integer DEFAULT 50 NOT NULL,
    feasibility_score integer DEFAULT 50 NOT NULL,
    risk_score integer DEFAULT 50 NOT NULL,
    rationale text DEFAULT ''::text NOT NULL,
    generated_by character varying(64) DEFAULT 'user'::character varying NOT NULL,
    review_status character varying(32) DEFAULT 'requires_review'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: target_weaponeering_deployment_aircraft; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_weaponeering_deployment_aircraft (
    id uuid NOT NULL,
    plan_id uuid NOT NULL,
    aircraft_id uuid NOT NULL,
    aircraft_count integer DEFAULT 1 NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: target_weaponeering_deployment_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_weaponeering_deployment_plans (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    target_card_id uuid NOT NULL,
    wing_id uuid NOT NULL,
    flying_unit_id uuid NOT NULL,
    takeoff_lat double precision,
    takeoff_lng double precision,
    ingress_bearing_deg double precision,
    ingress_offset_m integer DEFAULT 30000 NOT NULL,
    cruise_altitude_ft integer DEFAULT 25000 NOT NULL,
    ingress_altitude_ft integer DEFAULT 2000 NOT NULL,
    target_altitude_ft integer DEFAULT 2000 NOT NULL,
    climb_rate_ft_min integer DEFAULT 3000 NOT NULL,
    descent_rate_ft_min integer DEFAULT 2000 NOT NULL,
    return_enabled boolean DEFAULT true NOT NULL,
    cruise_speed_kt double precision DEFAULT '420'::double precision NOT NULL,
    climb_speed_kt double precision DEFAULT '250'::double precision NOT NULL,
    descent_speed_kt double precision DEFAULT '300'::double precision NOT NULL,
    ingress_speed_kt double precision DEFAULT '250'::double precision NOT NULL,
    bank_angle_deg double precision DEFAULT '20'::double precision NOT NULL,
    turn_mode character varying(32) DEFAULT 'fly_by'::character varying NOT NULL,
    auto_toc_tod boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: target_weaponeering_deployment_waypoints; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_weaponeering_deployment_waypoints (
    id uuid NOT NULL,
    plan_id uuid NOT NULL,
    waypoint_type character varying(32) DEFAULT 'fly_through'::character varying NOT NULL,
    label character varying(128),
    lat double precision NOT NULL,
    lng double precision NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    altitude_ft integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: transport_assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transport_assets (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    organization_id uuid,
    label character varying(255) NOT NULL,
    transport_type character varying(64) DEFAULT 'ground'::character varying NOT NULL,
    capacity_score integer DEFAULT 50 NOT NULL,
    readiness_status character varying(64) DEFAULT 'unknown'::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    username character varying(80) NOT NULL,
    user_name character varying(255),
    rank character varying(64),
    rank_id character varying(32),
    fname character varying(128),
    lname character varying(128),
    user_position character varying(512),
    user_orgname character varying(255),
    user_orgname_code character varying(64),
    user_role character varying(64),
    profile_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: weaponeering_import_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weaponeering_import_batches (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    source_reference character varying(255) DEFAULT ''::character varying NOT NULL,
    import_status character varying(32) DEFAULT 'pending'::character varying NOT NULL,
    validation_summary text DEFAULT ''::text NOT NULL,
    imported_count integer DEFAULT 0 NOT NULL,
    rejected_count integer DEFAULT 0 NOT NULL,
    created_by character varying(128) DEFAULT 'local_user'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: wing_aircraft; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wing_aircraft (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    wing_id uuid NOT NULL,
    flying_unit_id uuid,
    aircraft_type character varying(128) DEFAULT 'F-16'::character varying NOT NULL,
    mission_ready character varying(32) DEFAULT 'not_ready'::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: wing_depot_inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wing_depot_inventory (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    depot_id uuid NOT NULL,
    product_id uuid NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: wing_depot_transfers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wing_depot_transfers (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    product_id uuid NOT NULL,
    from_depot_id uuid NOT NULL,
    to_depot_id uuid NOT NULL,
    quantity integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: wing_depots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wing_depots (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    wing_id uuid NOT NULL,
    depot_name character varying(255) NOT NULL,
    map_lat double precision,
    map_lng double precision,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: wing_flying_units; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wing_flying_units (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    wing_id uuid NOT NULL,
    unit_name character varying(255) NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    map_lat double precision,
    map_lng double precision
);


--
-- Name: wing_logistics_vehicles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wing_logistics_vehicles (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    wing_id uuid NOT NULL,
    vehicle_name character varying(255) NOT NULL,
    fuel_consumption_rate double precision DEFAULT '0'::double precision NOT NULL,
    mission_ready character varying(32) DEFAULT 'not_ready'::character varying NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: wing_pilots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wing_pilots (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    wing_id uuid,
    flying_unit_id uuid,
    pilot_name character varying(255) NOT NULL,
    callsign character varying(128) DEFAULT ''::character varying NOT NULL,
    cep_value double precision DEFAULT '0'::double precision NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: wing_products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wing_products (
    id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    product_name character varying(255) NOT NULL,
    weight_pounds double precision DEFAULT '0'::double precision NOT NULL,
    unit_cost double precision DEFAULT '0'::double precision NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    description text DEFAULT ''::text NOT NULL
);


--
-- Data for Name: abstract_weaponeering_options; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.abstract_weaponeering_options (id, scenario_id, option_label, effect_category, required_capability_band, resource_token_type, estimated_effect_score, risk_score, logistics_demand_score, source_module, review_status, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: air_wings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.air_wings (id, scenario_id, wing_name, map_lat, map_lng, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
0012_target_material_strength
\.


--
-- Data for Name: app_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.app_settings (key, value, updated_at) FROM stdin;
offline_mode	false	2026-10-16 10:00:10.720792+00
ruleset_version	phase-0-web	2026-10-16 10:00:10.720792+00
\.


--
-- Data for Name: audit_events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_events (id, actor, event_type, entity_type, entity_id, details_json, created_at) FROM stdin;
21f753e5-02f5-4393-b148-83d8a6bb6543	admin	auth.login	user	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	{"login_mode": "dev-bypass"}	2026-10-16 10:11:16.25985+00
f078d94a-2fbb-4792-a42f-03a6f5d17e20	admin	auth.login	user	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	{"login_mode": "dev-bypass"}	2026-10-16 12:53:06.840403+00
5e2f4639-0101-441c-b0a4-611e5045c118	admin	auth.login	user	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	{"login_mode": "dev-bypass"}	2026-10-16 13:52:54.096368+00
c2d5c9ae-9a24-4379-9fdf-3e97347941bb	admin	scenario.create	scenario	c150bb44-8766-46a6-bb83-c7a429d60624	{"name": "ภารกิจทดสอบยุทธการ (Scenario ตัวอย่าง)"}	2026-10-16 13:52:54.172985+00
8a32b589-c06d-4242-9ddd-1f9ae93194b3	admin	auth.login	user	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	{"login_mode": "dev-bypass"}	2026-10-16 13:53:22.844249+00
09a99061-0553-4963-a921-6937d8ca721e	admin	target.create	target_card	64ddee5e-53d6-4301-91ac-523fdd96faef	{"label": "เป้าหมายที่ 1: ศูนย์บัญชาการและควบคุม (C2)", "scenario_id": "c150bb44-8766-46a6-bb83-c7a429d60624"}	2026-10-16 13:53:22.88151+00
33063f7b-2958-42ae-880c-530ec6fd724b	admin	target_card.selected_product	target_card	64ddee5e-53d6-4301-91ac-523fdd96faef	{"product_id": "7f478bef-d749-4fa2-aabe-8547f3538836"}	2026-10-16 13:53:23.002554+00
e3921679-b6e1-49ee-975b-e7192ca75911	admin	target.create	target_card	39d2c1a7-8919-4d23-b52d-b3ed2e3eef39	{"label": "เป้าหมายที่ 2: คลังเชื้อเพลิงและยุทโธปกรณ์", "scenario_id": "c150bb44-8766-46a6-bb83-c7a429d60624"}	2026-10-16 13:53:23.044107+00
4e8f0d60-b539-464a-a3f9-94c543506ec5	admin	target_card.selected_product	target_card	39d2c1a7-8919-4d23-b52d-b3ed2e3eef39	{"product_id": "ce7dd8e9-b494-45f5-b1db-f9724f914d8c"}	2026-10-16 13:53:23.109516+00
0d8ac15e-e289-4608-b0e9-dc9096bff02f	admin	target.create	target_card	b625ca78-cf8b-44c1-81a9-b4ccd7266b2c	{"label": "เป้าหมายที่ 3: สถานีเรดาร์ตรวจการณ์ระยะไกล", "scenario_id": "c150bb44-8766-46a6-bb83-c7a429d60624"}	2026-10-16 13:53:23.151673+00
be242866-f2c0-4372-b716-8749c7edb9e2	admin	target_card.selected_product	target_card	b625ca78-cf8b-44c1-81a9-b4ccd7266b2c	{"product_id": "3d4762fe-0d7a-4f85-9673-a61bf024f33f"}	2026-10-16 13:53:23.209648+00
601f3271-82a4-4f6b-9c42-d14ccf0559ae	admin	target.create	target_card	ea226511-f406-4e4c-9eaa-f887100085b0	{"label": "เป้าหมายที่ 4: สะพานส่งกำลังบำรุงยุทธศาสตร์", "scenario_id": "c150bb44-8766-46a6-bb83-c7a429d60624"}	2026-10-16 13:53:23.247819+00
80a60817-5fae-4860-b02b-cf25e648b8b8	admin	target_card.selected_product	target_card	ea226511-f406-4e4c-9eaa-f887100085b0	{"product_id": "ce7dd8e9-b494-45f5-b1db-f9724f914d8c"}	2026-10-16 13:53:23.304198+00
b05845b8-4264-49f9-8dae-17c33ab0bde4	admin	auth.login	user	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	{"login_mode": "dev-bypass"}	2026-10-16 13:54:12.310266+00
42bee3a1-1a6c-4cc0-ae19-d205d60c8baf	admin	auth.login	user	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	{"login_mode": "dev-bypass"}	2026-10-19 12:00:10.318368+00
a8a10753-d5ec-44d7-a43c-5d40b6e58e9c	admin	target.create	target_card	f714beea-285a-4197-85b0-9718d29a0814	{"label": "เป้าหมาย 5", "scenario_id": "c150bb44-8766-46a6-bb83-c7a429d60624"}	2026-10-19 12:00:44.719382+00
83356ab8-709d-4f31-a010-6f8a7f703780	admin	target.delete	target_card	f714beea-285a-4197-85b0-9718d29a0814	{}	2026-10-19 12:05:41.174479+00
\.


--
-- Data for Name: auth_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_sessions (id, user_id, access_token, challenge, login_mode, expires_at, created_at, revoked_at) FROM stdin;
244dfab1-b987-4dfa-b85f-362757999aca	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	dev-token-ab336cf25eb643e890b3fd502c2ad54d	dev-otp-bypass	dev-bypass	\N	2026-10-16 10:11:16.25985+00	\N
a8dce024-3622-4fea-89ea-4fb8468bd62b	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	dev-token-17087d39db314e3da37b3461994bc121	dev-otp-bypass	dev-bypass	\N	2026-10-16 12:53:06.840403+00	\N
82c422d9-f306-44c0-82d6-fcb7c4488c5a	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	dev-token-77d5a28c06b7475580698e2d4c8746bf	dev-otp-bypass	dev-bypass	\N	2026-10-16 13:52:54.096368+00	\N
56106f4d-d4e0-40a3-8f3e-98fff92d7a10	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	dev-token-7b7eb5549ae54e83843a2443fb9324b1	dev-otp-bypass	dev-bypass	\N	2026-10-16 13:53:22.844249+00	\N
255b1cab-2637-43ea-a5e8-35f0c876ce6d	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	dev-token-88ac94670a8b41f4913e8ec03de42223	dev-otp-bypass	dev-bypass	\N	2026-10-16 13:54:12.310266+00	\N
d5eaa938-0eef-4a59-b025-213c08002375	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	dev-token-9827b8e80d33466da09ba0935917d536	dev-otp-bypass	dev-bypass	\N	2026-10-19 12:00:10.318368+00	\N
\.


--
-- Data for Name: depot_inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.depot_inventory (id, depot_id, resource_token_id, inventory_category, option_label, quantity, availability_status, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: depots; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.depots (id, scenario_id, organization_id, name, depot_type, map_lat, map_lng, capacity_score, availability_status, review_status, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: guardrail_events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.guardrail_events (id, event_type, entity_type, entity_id, decision, sanitized_summary, created_at) FROM stdin;
\.


--
-- Data for Name: human_review_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.human_review_records (id, scenario_id, entity_type, entity_id, reviewer, decision, notes, created_at) FROM stdin;
\.


--
-- Data for Name: learning_objectives; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.learning_objectives (id, scenario_id, label, priority, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: map_nodes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.map_nodes (id, scenario_id, label, node_type, map_lat, map_lng, review_status, created_at, updated_at, linked_entity_type, linked_entity_id, is_synthetic_location) FROM stdin;
23b94533-661b-47ee-85a0-d3b549e1ca54	c150bb44-8766-46a6-bb83-c7a429d60624	P1	target	14.8825	100.6512	draft	2026-10-16 13:53:22.88151+00	2026-10-16 13:53:22.88151+00	target_card	64ddee5e-53d6-4301-91ac-523fdd96faef	t
205bfaa9-e551-4019-87f0-11db7065c471	c150bb44-8766-46a6-bb83-c7a429d60624	P1	target	14.896	100.6745	draft	2026-10-16 13:53:23.044107+00	2026-10-16 13:53:23.044107+00	target_card	39d2c1a7-8919-4d23-b52d-b3ed2e3eef39	t
ba57295d-12ee-4429-9078-5ec5433c0ffb	c150bb44-8766-46a6-bb83-c7a429d60624	P1	target	14.869	100.632	draft	2026-10-16 13:53:23.151673+00	2026-10-16 13:53:23.151673+00	target_card	b625ca78-cf8b-44c1-81a9-b4ccd7266b2c	t
c5abae66-0aa3-4cbe-a753-170b5b22a868	c150bb44-8766-46a6-bb83-c7a429d60624	P1	target	14.911	100.641	draft	2026-10-16 13:53:23.247819+00	2026-10-16 13:53:23.247819+00	target_card	ea226511-f406-4e4c-9eaa-f887100085b0	t
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.organizations (id, scenario_id, name, organization_type, map_lat, map_lng, location_label, is_synthetic_location, readiness_summary, review_status, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: plan_assignments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plan_assignments (id, plan_option_id, target_card_id, simulated_platform_id, abstract_weaponeering_option_id, depot_id, route_segment_id, assigned_resource_quantity, assignment_score, review_status, created_at) FROM stdin;
\.


--
-- Data for Name: plan_options; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plan_options (id, scenario_id, planning_horizon, title, generated_by, review_status, rank_order, created_at) FROM stdin;
\.


--
-- Data for Name: plan_scores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plan_scores (id, scenario_id, route_segment_id, plan_option_id, priority_alignment, logistics_feasibility, resource_balance, risk_indicator, rationale, created_at) FROM stdin;
\.


--
-- Data for Name: platform_readiness_events; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.platform_readiness_events (id, simulated_platform_id, status, readiness_score, reason, created_at) FROM stdin;
\.


--
-- Data for Name: platform_types; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.platform_types (id, scenario_id, label, capability_band, resource_cost_score, support_need_score, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ranking_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ranking_items (id, ranking_run_id, entity_type, entity_id, rank_order, total_score, confidence_score, rationale, breakdown_json, review_status, override_rank_order, override_notes, created_at) FROM stdin;
\.


--
-- Data for Name: ranking_runs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ranking_runs (id, scenario_id, ruleset_version, scoring_profile_id, generated_by, run_status, summary, created_at) FROM stdin;
\.


--
-- Data for Name: resource_tokens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resource_tokens (id, scenario_id, token_type, quantity, availability_window, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: route_segments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.route_segments (id, scenario_id, origin_entity_type, origin_entity_id, destination_entity_type, destination_entity_id, origin_lat, origin_lng, destination_lat, destination_lng, distance_score, fuel_stop_score, route_friction_score, availability_status, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: scenario_ground_transports; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scenario_ground_transports (id, scenario_id, origin_wing_id, destination_wing_id, product_id, vehicle_id, quantity, distance_m, duration_min, route_mode, route_geometry_json, label, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: scenario_team_markers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scenario_team_markers (id, scenario_id, side, unit_type, label, map_lat, map_lng, radius_m, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: scenarios; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scenarios (id, name, description, status, ruleset_version, created_by, created_at, updated_at) FROM stdin;
c150bb44-8766-46a6-bb83-c7a429d60624	ภารกิจทดสอบยุทธการ (Scenario ตัวอย่าง)	สถานการณ์ตัวอย่างพร้อมจุดเป้าหมาย 3D จำนวน 4 จุด	active	1.0	74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00
\.


--
-- Data for Name: scoring_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scoring_profiles (id, scenario_id, name, ruleset_version, priority_weight, weaponeering_weight, logistics_weight, readiness_weight, risk_weight, resource_balance_weight, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: simulated_platforms; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.simulated_platforms (id, scenario_id, organization_id, platform_type_id, label, capability_band, availability_score, readiness_status, readiness_note, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: target_cards; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_cards (id, scenario_id, label, priority_score, complexity_score, map_node_id, review_status, status, target_type, target_subtype, material_class, target_description, floor_count, width_m, length_m, height_m, desired_model_result, coordinate_error_m, data_source, cep, target_pk, reference_pk, resistance, capacity, damage_fit, model_version, selected_product_id, created_at, updated_at, weapon_quantity, heading_deg, material_strength) FROM stdin;
64ddee5e-53d6-4301-91ac-523fdd96faef	c150bb44-8766-46a6-bb83-c7a429d60624	เป้าหมายที่ 1: ศูนย์บัญชาการและควบคุม (C2)	5	3	23b94533-661b-47ee-85a0-d3b549e1ca54	draft	active	BUILDING	COMMAND_POST	REINFORCED_CONCRETE			22	35	12	STRUCTURAL FAILURE	8	manual	5	0.85	\N					7f478bef-d749-4fa2-aabe-8547f3538836	2026-10-16 13:53:22.88151+00	2026-10-16 13:53:23.002554+00	\N	30	{}
39d2c1a7-8919-4d23-b52d-b3ed2e3eef39	c150bb44-8766-46a6-bb83-c7a429d60624	เป้าหมายที่ 2: คลังเชื้อเพลิงและยุทโธปกรณ์	4	3	205bfaa9-e551-4019-87f0-11db7065c471	draft	active	STORAGE	FUEL_DEPOT	STEEL			28	50	10	STRUCTURAL FAILURE	10	manual	8	0.8	\N					ce7dd8e9-b494-45f5-b1db-f9724f914d8c	2026-10-16 13:53:23.044107+00	2026-10-16 13:53:23.109516+00	\N	115	{}
b625ca78-cf8b-44c1-81a9-b4ccd7266b2c	c150bb44-8766-46a6-bb83-c7a429d60624	เป้าหมายที่ 3: สถานีเรดาร์ตรวจการณ์ระยะไกล	5	3	ba57295d-12ee-4429-9078-5ec5433c0ffb	draft	active	DEFENSE	RADAR_SITE	REINFORCED_CONCRETE			18	24	16	STRUCTURAL FAILURE	6	manual	5	0.85	\N					3d4762fe-0d7a-4f85-9673-a61bf024f33f	2026-10-16 13:53:23.151673+00	2026-10-16 13:53:23.209648+00	\N	65	{}
ea226511-f406-4e4c-9eaa-f887100085b0	c150bb44-8766-46a6-bb83-c7a429d60624	เป้าหมายที่ 4: สะพานส่งกำลังบำรุงยุทธศาสตร์	3	3	c5abae66-0aa3-4cbe-a753-170b5b22a868	draft	active	BRIDGE	CONCRETE_BRIDGE	REINFORCED_CONCRETE			16	60	9	STRUCTURAL FAILURE	8	manual	6	0.75	\N					ce7dd8e9-b494-45f5-b1db-f9724f914d8c	2026-10-16 13:53:23.247819+00	2026-10-16 13:53:23.304198+00	\N	150	{}
\.


--
-- Data for Name: target_coordinates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_coordinates (id, target_card_id, label, map_lat, map_lng, sort_order, is_primary, selected_product_id, created_at, weapon_quantity) FROM stdin;
e56eb22a-0351-4d67-a46f-15f67171403c	64ddee5e-53d6-4301-91ac-523fdd96faef	P1	14.8825	100.6512	0	t	\N	2026-10-16 13:53:22.88151+00	\N
ac4c0a83-622d-431a-b69f-00079e4cbcf1	39d2c1a7-8919-4d23-b52d-b3ed2e3eef39	P1	14.896	100.6745	0	t	\N	2026-10-16 13:53:23.044107+00	\N
9e7826b7-201d-4e90-a881-4324eb0a6c66	b625ca78-cf8b-44c1-81a9-b4ccd7266b2c	P1	14.869	100.632	0	t	\N	2026-10-16 13:53:23.151673+00	\N
412b65fc-e6f7-48a6-ab84-fda9302809ac	ea226511-f406-4e4c-9eaa-f887100085b0	P1	14.911	100.641	0	t	\N	2026-10-16 13:53:23.247819+00	\N
\.


--
-- Data for Name: target_map_detection_objects; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_map_detection_objects (id, run_id, target_card_id, map_object_id, object_label, object_type, risk_level, confidence, center_lat, center_lng, polygon_json, sort_order) FROM stdin;
\.


--
-- Data for Name: target_map_detection_runs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_map_detection_runs (id, scenario_id, target_card_id, target_coordinate_id, model_name, model_file_name, radius_m, capture_radius_m, source_image_name, object_count, detection_message, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: target_recognition_results; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_recognition_results (id, target_card_id, source_type, recognition_summary, recognition_confidence_score, missing_data_json, generated_by, review_status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: target_weaponeering_assessments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_weaponeering_assessments (id, target_card_id, abstract_weaponeering_option_id, suitability_score, feasibility_score, risk_score, rationale, generated_by, review_status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: target_weaponeering_deployment_aircraft; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_weaponeering_deployment_aircraft (id, plan_id, aircraft_id, aircraft_count, sort_order, created_at) FROM stdin;
\.


--
-- Data for Name: target_weaponeering_deployment_plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_weaponeering_deployment_plans (id, scenario_id, target_card_id, wing_id, flying_unit_id, takeoff_lat, takeoff_lng, ingress_bearing_deg, ingress_offset_m, cruise_altitude_ft, ingress_altitude_ft, target_altitude_ft, climb_rate_ft_min, descent_rate_ft_min, return_enabled, cruise_speed_kt, climb_speed_kt, descent_speed_kt, ingress_speed_kt, bank_angle_deg, turn_mode, auto_toc_tod, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: target_weaponeering_deployment_waypoints; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.target_weaponeering_deployment_waypoints (id, plan_id, waypoint_type, label, lat, lng, sort_order, altitude_ft, created_at) FROM stdin;
\.


--
-- Data for Name: transport_assets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transport_assets (id, scenario_id, organization_id, label, transport_type, capacity_score, readiness_status, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, user_name, rank, rank_id, fname, lname, user_position, user_orgname, user_orgname_code, user_role, profile_json, created_at, updated_at) FROM stdin;
74c19933-5b2e-4b9d-b91d-d5ab4ab54eac	admin	น.อ. admin (Dev Mode)	น.อ.	10	admin	RTAF	นายทหารวางแผนยุทธการ	ศูนย์ซอฟต์แวร์กองทัพอากาศ	SWC	admin	{"rank": "น.อ.", "user": "admin", "fname": "admin", "lname": "RTAF", "token": "dev-token-9827b8e80d33466da09ba0935917d536", "rankID": "10", "result": "Process-Complete", "challenge": "dev-otp-bypass", "user_name": "น.อ. admin (Dev Mode)", "user_role": "admin", "login_mode": "dev-bypass", "user_orgname": "ศูนย์ซอฟต์แวร์กองทัพอากาศ", "user_position": "นายทหารวางแผนยุทธการ", "user_orgname_code": "SWC"}	2026-10-16 10:11:16.25985+00	2026-10-19 12:00:10.318368+00
\.


--
-- Data for Name: weaponeering_import_batches; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.weaponeering_import_batches (id, scenario_id, source_reference, import_status, validation_summary, imported_count, rejected_count, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: wing_aircraft; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wing_aircraft (id, scenario_id, wing_id, flying_unit_id, aircraft_type, mission_ready, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: wing_depot_inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wing_depot_inventory (id, scenario_id, depot_id, product_id, quantity, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: wing_depot_transfers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wing_depot_transfers (id, scenario_id, product_id, from_depot_id, to_depot_id, quantity, created_at) FROM stdin;
\.


--
-- Data for Name: wing_depots; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wing_depots (id, scenario_id, wing_id, depot_name, map_lat, map_lng, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: wing_flying_units; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wing_flying_units (id, scenario_id, wing_id, unit_name, status, created_at, updated_at, map_lat, map_lng) FROM stdin;
\.


--
-- Data for Name: wing_logistics_vehicles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wing_logistics_vehicles (id, scenario_id, wing_id, vehicle_name, fuel_consumption_rate, mission_ready, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: wing_pilots; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wing_pilots (id, scenario_id, wing_id, flying_unit_id, pilot_name, callsign, cep_value, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: wing_products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.wing_products (id, scenario_id, product_name, weight_pounds, unit_cost, status, created_at, updated_at, description) FROM stdin;
d6689272-c1d2-44cc-b130-a7804c1494c8	c150bb44-8766-46a6-bb83-c7a429d60624	MK 81 (250 lb)	250	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 250 ปอนด์
8d497776-c054-44c0-94c6-1b7cc71a94fc	c150bb44-8766-46a6-bb83-c7a429d60624	MK 82 (500 lb)	500	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 500 ปอนด์ นิยมใช้งานมากที่สุด
f82f260e-bf80-40a3-8460-fea6b1bd9d19	c150bb44-8766-46a6-bb83-c7a429d60624	MK 83 (1,000 lb)	1000	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 1,000 ปอนด์ นิยมใช้งานมากที่สุด
ce7dd8e9-b494-45f5-b1db-f9724f914d8c	c150bb44-8766-46a6-bb83-c7a429d60624	MK 84 (2,000 lb)	2000	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 2,000 ปอนด์
00bebb05-3700-43ea-8f9d-5efe30a1d682	c150bb44-8766-46a6-bb83-c7a429d60624	MK 15 (High-Drag Bomb)	500	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดติดตั้งหางหน่วงแรงกังหัน (หางเตะ) สำหรับการทิ้งระเบิดในระยะต่ำ เพื่อให้เครื่องบินรบสามารถบินพ้นรัศมีแรงระเบิด โดยระเบิดจะตกทำมุมชันเกือบ 90 องศา
f5cb3ecc-d7e5-44ef-9a0a-b34ffc78e66d	c150bb44-8766-46a6-bb83-c7a429d60624	CBU-49 / CBU-71 (Cluster Bomb)	800	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดพวง/ระเบิดลูกปู บรรจุลูกระเบิดขนาดเล็ก (ลูกน้อยหน่า/ลูกเกลี้ยง) ประมาณ 300 ลูกอยู่ภายใน เมื่อปล่อยจากเครื่องบิน ปลอกนอกจะแยกออกเพื่อกระจายลูกระเบิดเล็กครอบคลุมพื้นที่กว้างเกือบ 2 กิโลเมตร ใช้สำหรับจำกัดการเข้าถึงของข้าศึก (Area Denial) หมายเหตุสำคัญ: ปัจจุบันประเทศไทยได้ลงนามในสนธิสัญญาห้ามใช้ระเบิดพวง (Convention on Cluster Munitions) แล้ว จึงไม่มีการนำมาใช้งานในภารกิจหลัก
7f478bef-d749-4fa2-aabe-8547f3538836	c150bb44-8766-46a6-bb83-c7a429d60624	GBU-12 (Laser-Guided, MK 82)	500	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดนำวิถีเลเซอร์ (Laser-Guided Bomb) ฐานจาก MK 82 ควบคุมการตกด้วยระบบเซ็นเซอร์ตรวจจับลำแสงเลเซอร์ จำเป็นต้องมีแหล่งชี้เป้าเลเซอร์จากอากาศ (Targeting Pod เช่น Litening/Sniper บน F-16) หรือจากภาคพื้น (JTAC/CCT) และมีข้อจำกัดเมื่อสภาพอากาศปิด
3d4762fe-0d7a-4f85-9673-a61bf024f33f	c150bb44-8766-46a6-bb83-c7a429d60624	GBU-10 / GBU-16 (Laser-Guided, MK 84)	2000	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดนำวิถีเลเซอร์ (Laser-Guided Bomb) ฐานจาก MK 84 เช่น GBU-10 และ GBU-16 ควบคุมการตกด้วยระบบเซ็นเซอร์ตรวจจับลำแสงเลเซอร์ จำเป็นต้องมีแหล่งชี้เป้าเลเซอร์จากอากาศ (Targeting Pod เช่น Litening/Sniper บน F-16) หรือจากภาคพื้น (JTAC/CCT) และมีข้อจำกัดเมื่อสภาพอากาศปิด
7da74e76-0beb-457f-82e8-0be3efcbd717	c150bb44-8766-46a6-bb83-c7a429d60624	JDAM (Stand-off Weapon)	2000	0	active	2026-10-16 13:52:54.172985+00	2026-10-16 13:52:54.172985+00	ระเบิดติดตั้งชุดหางนำวิถีด้วย GPS / อาวุธปล่อยร่อน (Stand-off Weapon) สามารถร่อนไปทำลายเป้าหมายได้เองจากระยะไกลสูงสุดถึง 100 กิโลเมตร ช่วยให้เครื่องบินปล่อยอาวุธนอกระยะต่อต้านของข้าศึก มีความสามารถเลี้ยวอ้อมสันเขาได้ถึง 180 องศา
\.


--
-- Name: abstract_weaponeering_options abstract_weaponeering_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abstract_weaponeering_options
    ADD CONSTRAINT abstract_weaponeering_options_pkey PRIMARY KEY (id);


--
-- Name: air_wings air_wings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.air_wings
    ADD CONSTRAINT air_wings_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: app_settings app_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_settings
    ADD CONSTRAINT app_settings_pkey PRIMARY KEY (key);


--
-- Name: audit_events audit_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_pkey PRIMARY KEY (id);


--
-- Name: auth_sessions auth_sessions_access_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_access_token_key UNIQUE (access_token);


--
-- Name: auth_sessions auth_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_pkey PRIMARY KEY (id);


--
-- Name: depot_inventory depot_inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.depot_inventory
    ADD CONSTRAINT depot_inventory_pkey PRIMARY KEY (id);


--
-- Name: depots depots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.depots
    ADD CONSTRAINT depots_pkey PRIMARY KEY (id);


--
-- Name: guardrail_events guardrail_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardrail_events
    ADD CONSTRAINT guardrail_events_pkey PRIMARY KEY (id);


--
-- Name: human_review_records human_review_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.human_review_records
    ADD CONSTRAINT human_review_records_pkey PRIMARY KEY (id);


--
-- Name: learning_objectives learning_objectives_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_objectives
    ADD CONSTRAINT learning_objectives_pkey PRIMARY KEY (id);


--
-- Name: map_nodes map_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.map_nodes
    ADD CONSTRAINT map_nodes_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: plan_assignments plan_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_assignments
    ADD CONSTRAINT plan_assignments_pkey PRIMARY KEY (id);


--
-- Name: plan_options plan_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_options
    ADD CONSTRAINT plan_options_pkey PRIMARY KEY (id);


--
-- Name: plan_scores plan_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_scores
    ADD CONSTRAINT plan_scores_pkey PRIMARY KEY (id);


--
-- Name: platform_readiness_events platform_readiness_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_readiness_events
    ADD CONSTRAINT platform_readiness_events_pkey PRIMARY KEY (id);


--
-- Name: platform_types platform_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_types
    ADD CONSTRAINT platform_types_pkey PRIMARY KEY (id);


--
-- Name: ranking_items ranking_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ranking_items
    ADD CONSTRAINT ranking_items_pkey PRIMARY KEY (id);


--
-- Name: ranking_runs ranking_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ranking_runs
    ADD CONSTRAINT ranking_runs_pkey PRIMARY KEY (id);


--
-- Name: resource_tokens resource_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_tokens
    ADD CONSTRAINT resource_tokens_pkey PRIMARY KEY (id);


--
-- Name: route_segments route_segments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_segments
    ADD CONSTRAINT route_segments_pkey PRIMARY KEY (id);


--
-- Name: scenario_ground_transports scenario_ground_transports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_ground_transports
    ADD CONSTRAINT scenario_ground_transports_pkey PRIMARY KEY (id);


--
-- Name: scenario_team_markers scenario_team_markers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_team_markers
    ADD CONSTRAINT scenario_team_markers_pkey PRIMARY KEY (id);


--
-- Name: scenarios scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenarios
    ADD CONSTRAINT scenarios_pkey PRIMARY KEY (id);


--
-- Name: scoring_profiles scoring_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scoring_profiles
    ADD CONSTRAINT scoring_profiles_pkey PRIMARY KEY (id);


--
-- Name: simulated_platforms simulated_platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulated_platforms
    ADD CONSTRAINT simulated_platforms_pkey PRIMARY KEY (id);


--
-- Name: target_cards target_cards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_cards
    ADD CONSTRAINT target_cards_pkey PRIMARY KEY (id);


--
-- Name: target_coordinates target_coordinates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_coordinates
    ADD CONSTRAINT target_coordinates_pkey PRIMARY KEY (id);


--
-- Name: target_map_detection_objects target_map_detection_objects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_map_detection_objects
    ADD CONSTRAINT target_map_detection_objects_pkey PRIMARY KEY (id);


--
-- Name: target_map_detection_runs target_map_detection_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_map_detection_runs
    ADD CONSTRAINT target_map_detection_runs_pkey PRIMARY KEY (id);


--
-- Name: target_recognition_results target_recognition_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_recognition_results
    ADD CONSTRAINT target_recognition_results_pkey PRIMARY KEY (id);


--
-- Name: target_weaponeering_assessments target_weaponeering_assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_assessments
    ADD CONSTRAINT target_weaponeering_assessments_pkey PRIMARY KEY (id);


--
-- Name: target_weaponeering_deployment_aircraft target_weaponeering_deployment_aircraft_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_aircraft
    ADD CONSTRAINT target_weaponeering_deployment_aircraft_pkey PRIMARY KEY (id);


--
-- Name: target_weaponeering_deployment_plans target_weaponeering_deployment_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_plans
    ADD CONSTRAINT target_weaponeering_deployment_plans_pkey PRIMARY KEY (id);


--
-- Name: target_weaponeering_deployment_plans target_weaponeering_deployment_plans_target_card_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_plans
    ADD CONSTRAINT target_weaponeering_deployment_plans_target_card_id_key UNIQUE (target_card_id);


--
-- Name: target_weaponeering_deployment_waypoints target_weaponeering_deployment_waypoints_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_waypoints
    ADD CONSTRAINT target_weaponeering_deployment_waypoints_pkey PRIMARY KEY (id);


--
-- Name: transport_assets transport_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_assets
    ADD CONSTRAINT transport_assets_pkey PRIMARY KEY (id);


--
-- Name: target_weaponeering_deployment_aircraft uq_deployment_plan_aircraft; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_aircraft
    ADD CONSTRAINT uq_deployment_plan_aircraft UNIQUE (plan_id, aircraft_id);


--
-- Name: target_map_detection_runs uq_detection_run_target_coord; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_map_detection_runs
    ADD CONSTRAINT uq_detection_run_target_coord UNIQUE (target_card_id, target_coordinate_id);


--
-- Name: wing_depot_inventory uq_wing_depot_product; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_inventory
    ADD CONSTRAINT uq_wing_depot_product UNIQUE (depot_id, product_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: weaponeering_import_batches weaponeering_import_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weaponeering_import_batches
    ADD CONSTRAINT weaponeering_import_batches_pkey PRIMARY KEY (id);


--
-- Name: wing_aircraft wing_aircraft_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_aircraft
    ADD CONSTRAINT wing_aircraft_pkey PRIMARY KEY (id);


--
-- Name: wing_depot_inventory wing_depot_inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_inventory
    ADD CONSTRAINT wing_depot_inventory_pkey PRIMARY KEY (id);


--
-- Name: wing_depot_transfers wing_depot_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_transfers
    ADD CONSTRAINT wing_depot_transfers_pkey PRIMARY KEY (id);


--
-- Name: wing_depots wing_depots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depots
    ADD CONSTRAINT wing_depots_pkey PRIMARY KEY (id);


--
-- Name: wing_flying_units wing_flying_units_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_flying_units
    ADD CONSTRAINT wing_flying_units_pkey PRIMARY KEY (id);


--
-- Name: wing_logistics_vehicles wing_logistics_vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_logistics_vehicles
    ADD CONSTRAINT wing_logistics_vehicles_pkey PRIMARY KEY (id);


--
-- Name: wing_pilots wing_pilots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_pilots
    ADD CONSTRAINT wing_pilots_pkey PRIMARY KEY (id);


--
-- Name: wing_products wing_products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_products
    ADD CONSTRAINT wing_products_pkey PRIMARY KEY (id);


--
-- Name: ix_abstract_weaponeering_options_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_abstract_weaponeering_options_scenario_id ON public.abstract_weaponeering_options USING btree (scenario_id);


--
-- Name: ix_air_wings_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_air_wings_scenario_id ON public.air_wings USING btree (scenario_id);


--
-- Name: ix_audit_events_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_events_event_type ON public.audit_events USING btree (event_type);


--
-- Name: ix_auth_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_auth_sessions_user_id ON public.auth_sessions USING btree (user_id);


--
-- Name: ix_deployment_aircraft_plan_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_aircraft_plan_id ON public.target_weaponeering_deployment_aircraft USING btree (plan_id);


--
-- Name: ix_deployment_plans_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_plans_scenario_id ON public.target_weaponeering_deployment_plans USING btree (scenario_id);


--
-- Name: ix_deployment_waypoints_plan_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_waypoints_plan_id ON public.target_weaponeering_deployment_waypoints USING btree (plan_id);


--
-- Name: ix_depot_inventory_depot_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_depot_inventory_depot_id ON public.depot_inventory USING btree (depot_id);


--
-- Name: ix_depots_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_depots_scenario_id ON public.depots USING btree (scenario_id);


--
-- Name: ix_human_review_records_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_human_review_records_scenario_id ON public.human_review_records USING btree (scenario_id);


--
-- Name: ix_learning_objectives_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_objectives_scenario_id ON public.learning_objectives USING btree (scenario_id);


--
-- Name: ix_map_nodes_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_map_nodes_scenario_id ON public.map_nodes USING btree (scenario_id);


--
-- Name: ix_organizations_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organizations_scenario_id ON public.organizations USING btree (scenario_id);


--
-- Name: ix_plan_assignments_plan_option_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plan_assignments_plan_option_id ON public.plan_assignments USING btree (plan_option_id);


--
-- Name: ix_plan_options_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plan_options_scenario_id ON public.plan_options USING btree (scenario_id);


--
-- Name: ix_plan_scores_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plan_scores_scenario_id ON public.plan_scores USING btree (scenario_id);


--
-- Name: ix_platform_readiness_events_platform_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_platform_readiness_events_platform_id ON public.platform_readiness_events USING btree (simulated_platform_id);


--
-- Name: ix_platform_types_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_platform_types_scenario_id ON public.platform_types USING btree (scenario_id);


--
-- Name: ix_ranking_items_run_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ranking_items_run_id ON public.ranking_items USING btree (ranking_run_id);


--
-- Name: ix_ranking_runs_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ranking_runs_scenario_id ON public.ranking_runs USING btree (scenario_id);


--
-- Name: ix_resource_tokens_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_tokens_scenario_id ON public.resource_tokens USING btree (scenario_id);


--
-- Name: ix_route_segments_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_route_segments_scenario_id ON public.route_segments USING btree (scenario_id);


--
-- Name: ix_scenario_ground_transports_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scenario_ground_transports_scenario_id ON public.scenario_ground_transports USING btree (scenario_id);


--
-- Name: ix_scenario_team_markers_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scenario_team_markers_scenario_id ON public.scenario_team_markers USING btree (scenario_id);


--
-- Name: ix_scoring_profiles_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scoring_profiles_scenario_id ON public.scoring_profiles USING btree (scenario_id);


--
-- Name: ix_simulated_platforms_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_simulated_platforms_scenario_id ON public.simulated_platforms USING btree (scenario_id);


--
-- Name: ix_target_cards_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_cards_scenario_id ON public.target_cards USING btree (scenario_id);


--
-- Name: ix_target_coordinates_card_sort; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_coordinates_card_sort ON public.target_coordinates USING btree (target_card_id, sort_order);


--
-- Name: ix_target_coordinates_target_card_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_coordinates_target_card_id ON public.target_coordinates USING btree (target_card_id);


--
-- Name: ix_target_map_detection_objects_run_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_map_detection_objects_run_id ON public.target_map_detection_objects USING btree (run_id);


--
-- Name: ix_target_map_detection_objects_target_card_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_map_detection_objects_target_card_id ON public.target_map_detection_objects USING btree (target_card_id);


--
-- Name: ix_target_map_detection_runs_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_map_detection_runs_scenario_id ON public.target_map_detection_runs USING btree (scenario_id);


--
-- Name: ix_target_map_detection_runs_target_card_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_map_detection_runs_target_card_id ON public.target_map_detection_runs USING btree (target_card_id);


--
-- Name: ix_target_recognition_results_target_card_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_recognition_results_target_card_id ON public.target_recognition_results USING btree (target_card_id);


--
-- Name: ix_target_weaponeering_assessments_option; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_weaponeering_assessments_option ON public.target_weaponeering_assessments USING btree (abstract_weaponeering_option_id);


--
-- Name: ix_target_weaponeering_assessments_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_weaponeering_assessments_target ON public.target_weaponeering_assessments USING btree (target_card_id);


--
-- Name: ix_transport_assets_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transport_assets_scenario_id ON public.transport_assets USING btree (scenario_id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_weaponeering_import_batches_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_weaponeering_import_batches_scenario_id ON public.weaponeering_import_batches USING btree (scenario_id);


--
-- Name: ix_wing_aircraft_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_aircraft_scenario_id ON public.wing_aircraft USING btree (scenario_id);


--
-- Name: ix_wing_aircraft_wing_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_aircraft_wing_id ON public.wing_aircraft USING btree (wing_id);


--
-- Name: ix_wing_depot_inventory_depot_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_depot_inventory_depot_id ON public.wing_depot_inventory USING btree (depot_id);


--
-- Name: ix_wing_depot_inventory_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_depot_inventory_product_id ON public.wing_depot_inventory USING btree (product_id);


--
-- Name: ix_wing_depot_inventory_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_depot_inventory_scenario_id ON public.wing_depot_inventory USING btree (scenario_id);


--
-- Name: ix_wing_depot_transfers_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_depot_transfers_scenario_id ON public.wing_depot_transfers USING btree (scenario_id);


--
-- Name: ix_wing_depots_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_depots_scenario_id ON public.wing_depots USING btree (scenario_id);


--
-- Name: ix_wing_depots_wing_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_depots_wing_id ON public.wing_depots USING btree (wing_id);


--
-- Name: ix_wing_flying_units_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_flying_units_scenario_id ON public.wing_flying_units USING btree (scenario_id);


--
-- Name: ix_wing_flying_units_wing_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_flying_units_wing_id ON public.wing_flying_units USING btree (wing_id);


--
-- Name: ix_wing_logistics_vehicles_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_logistics_vehicles_scenario_id ON public.wing_logistics_vehicles USING btree (scenario_id);


--
-- Name: ix_wing_logistics_vehicles_wing_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_logistics_vehicles_wing_id ON public.wing_logistics_vehicles USING btree (wing_id);


--
-- Name: ix_wing_pilots_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_pilots_scenario_id ON public.wing_pilots USING btree (scenario_id);


--
-- Name: ix_wing_pilots_wing_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_pilots_wing_id ON public.wing_pilots USING btree (wing_id);


--
-- Name: ix_wing_products_scenario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_wing_products_scenario_id ON public.wing_products USING btree (scenario_id);


--
-- Name: abstract_weaponeering_options abstract_weaponeering_options_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abstract_weaponeering_options
    ADD CONSTRAINT abstract_weaponeering_options_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: air_wings air_wings_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.air_wings
    ADD CONSTRAINT air_wings_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: auth_sessions auth_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: depot_inventory depot_inventory_depot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.depot_inventory
    ADD CONSTRAINT depot_inventory_depot_id_fkey FOREIGN KEY (depot_id) REFERENCES public.depots(id) ON DELETE CASCADE;


--
-- Name: depot_inventory depot_inventory_resource_token_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.depot_inventory
    ADD CONSTRAINT depot_inventory_resource_token_id_fkey FOREIGN KEY (resource_token_id) REFERENCES public.resource_tokens(id) ON DELETE SET NULL;


--
-- Name: depots depots_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.depots
    ADD CONSTRAINT depots_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;


--
-- Name: depots depots_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.depots
    ADD CONSTRAINT depots_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: human_review_records human_review_records_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.human_review_records
    ADD CONSTRAINT human_review_records_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: learning_objectives learning_objectives_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_objectives
    ADD CONSTRAINT learning_objectives_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: map_nodes map_nodes_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.map_nodes
    ADD CONSTRAINT map_nodes_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: organizations organizations_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: plan_assignments plan_assignments_abstract_weaponeering_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_assignments
    ADD CONSTRAINT plan_assignments_abstract_weaponeering_option_id_fkey FOREIGN KEY (abstract_weaponeering_option_id) REFERENCES public.abstract_weaponeering_options(id) ON DELETE SET NULL;


--
-- Name: plan_assignments plan_assignments_plan_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_assignments
    ADD CONSTRAINT plan_assignments_plan_option_id_fkey FOREIGN KEY (plan_option_id) REFERENCES public.plan_options(id) ON DELETE CASCADE;


--
-- Name: plan_assignments plan_assignments_target_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_assignments
    ADD CONSTRAINT plan_assignments_target_card_id_fkey FOREIGN KEY (target_card_id) REFERENCES public.target_cards(id) ON DELETE SET NULL;


--
-- Name: plan_options plan_options_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_options
    ADD CONSTRAINT plan_options_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: plan_scores plan_scores_route_segment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_scores
    ADD CONSTRAINT plan_scores_route_segment_id_fkey FOREIGN KEY (route_segment_id) REFERENCES public.route_segments(id) ON DELETE SET NULL;


--
-- Name: plan_scores plan_scores_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_scores
    ADD CONSTRAINT plan_scores_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: platform_readiness_events platform_readiness_events_simulated_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_readiness_events
    ADD CONSTRAINT platform_readiness_events_simulated_platform_id_fkey FOREIGN KEY (simulated_platform_id) REFERENCES public.simulated_platforms(id) ON DELETE CASCADE;


--
-- Name: platform_types platform_types_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_types
    ADD CONSTRAINT platform_types_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: ranking_items ranking_items_ranking_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ranking_items
    ADD CONSTRAINT ranking_items_ranking_run_id_fkey FOREIGN KEY (ranking_run_id) REFERENCES public.ranking_runs(id) ON DELETE CASCADE;


--
-- Name: ranking_runs ranking_runs_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ranking_runs
    ADD CONSTRAINT ranking_runs_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: ranking_runs ranking_runs_scoring_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ranking_runs
    ADD CONSTRAINT ranking_runs_scoring_profile_id_fkey FOREIGN KEY (scoring_profile_id) REFERENCES public.scoring_profiles(id) ON DELETE SET NULL;


--
-- Name: resource_tokens resource_tokens_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_tokens
    ADD CONSTRAINT resource_tokens_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: route_segments route_segments_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_segments
    ADD CONSTRAINT route_segments_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: scenario_ground_transports scenario_ground_transports_destination_wing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_ground_transports
    ADD CONSTRAINT scenario_ground_transports_destination_wing_id_fkey FOREIGN KEY (destination_wing_id) REFERENCES public.air_wings(id) ON DELETE CASCADE;


--
-- Name: scenario_ground_transports scenario_ground_transports_origin_wing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_ground_transports
    ADD CONSTRAINT scenario_ground_transports_origin_wing_id_fkey FOREIGN KEY (origin_wing_id) REFERENCES public.air_wings(id) ON DELETE CASCADE;


--
-- Name: scenario_ground_transports scenario_ground_transports_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_ground_transports
    ADD CONSTRAINT scenario_ground_transports_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.wing_products(id) ON DELETE SET NULL;


--
-- Name: scenario_ground_transports scenario_ground_transports_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_ground_transports
    ADD CONSTRAINT scenario_ground_transports_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: scenario_ground_transports scenario_ground_transports_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_ground_transports
    ADD CONSTRAINT scenario_ground_transports_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.wing_logistics_vehicles(id) ON DELETE SET NULL;


--
-- Name: scenario_team_markers scenario_team_markers_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenario_team_markers
    ADD CONSTRAINT scenario_team_markers_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: scenarios scenarios_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenarios
    ADD CONSTRAINT scenarios_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: scoring_profiles scoring_profiles_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scoring_profiles
    ADD CONSTRAINT scoring_profiles_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: simulated_platforms simulated_platforms_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulated_platforms
    ADD CONSTRAINT simulated_platforms_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;


--
-- Name: simulated_platforms simulated_platforms_platform_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulated_platforms
    ADD CONSTRAINT simulated_platforms_platform_type_id_fkey FOREIGN KEY (platform_type_id) REFERENCES public.platform_types(id) ON DELETE SET NULL;


--
-- Name: simulated_platforms simulated_platforms_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulated_platforms
    ADD CONSTRAINT simulated_platforms_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: target_cards target_cards_map_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_cards
    ADD CONSTRAINT target_cards_map_node_id_fkey FOREIGN KEY (map_node_id) REFERENCES public.map_nodes(id) ON DELETE SET NULL;


--
-- Name: target_cards target_cards_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_cards
    ADD CONSTRAINT target_cards_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: target_coordinates target_coordinates_target_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_coordinates
    ADD CONSTRAINT target_coordinates_target_card_id_fkey FOREIGN KEY (target_card_id) REFERENCES public.target_cards(id) ON DELETE CASCADE;


--
-- Name: target_map_detection_objects target_map_detection_objects_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_map_detection_objects
    ADD CONSTRAINT target_map_detection_objects_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.target_map_detection_runs(id) ON DELETE CASCADE;


--
-- Name: target_map_detection_objects target_map_detection_objects_target_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_map_detection_objects
    ADD CONSTRAINT target_map_detection_objects_target_card_id_fkey FOREIGN KEY (target_card_id) REFERENCES public.target_cards(id) ON DELETE CASCADE;


--
-- Name: target_map_detection_runs target_map_detection_runs_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_map_detection_runs
    ADD CONSTRAINT target_map_detection_runs_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: target_map_detection_runs target_map_detection_runs_target_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_map_detection_runs
    ADD CONSTRAINT target_map_detection_runs_target_card_id_fkey FOREIGN KEY (target_card_id) REFERENCES public.target_cards(id) ON DELETE CASCADE;


--
-- Name: target_map_detection_runs target_map_detection_runs_target_coordinate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_map_detection_runs
    ADD CONSTRAINT target_map_detection_runs_target_coordinate_id_fkey FOREIGN KEY (target_coordinate_id) REFERENCES public.target_coordinates(id) ON DELETE CASCADE;


--
-- Name: target_recognition_results target_recognition_results_target_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_recognition_results
    ADD CONSTRAINT target_recognition_results_target_card_id_fkey FOREIGN KEY (target_card_id) REFERENCES public.target_cards(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_assessments target_weaponeering_assessmen_abstract_weaponeering_option_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_assessments
    ADD CONSTRAINT target_weaponeering_assessmen_abstract_weaponeering_option_fkey FOREIGN KEY (abstract_weaponeering_option_id) REFERENCES public.abstract_weaponeering_options(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_assessments target_weaponeering_assessments_target_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_assessments
    ADD CONSTRAINT target_weaponeering_assessments_target_card_id_fkey FOREIGN KEY (target_card_id) REFERENCES public.target_cards(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_deployment_aircraft target_weaponeering_deployment_aircraft_aircraft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_aircraft
    ADD CONSTRAINT target_weaponeering_deployment_aircraft_aircraft_id_fkey FOREIGN KEY (aircraft_id) REFERENCES public.wing_aircraft(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_deployment_aircraft target_weaponeering_deployment_aircraft_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_aircraft
    ADD CONSTRAINT target_weaponeering_deployment_aircraft_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.target_weaponeering_deployment_plans(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_deployment_plans target_weaponeering_deployment_plans_flying_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_plans
    ADD CONSTRAINT target_weaponeering_deployment_plans_flying_unit_id_fkey FOREIGN KEY (flying_unit_id) REFERENCES public.wing_flying_units(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_deployment_plans target_weaponeering_deployment_plans_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_plans
    ADD CONSTRAINT target_weaponeering_deployment_plans_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_deployment_plans target_weaponeering_deployment_plans_target_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_plans
    ADD CONSTRAINT target_weaponeering_deployment_plans_target_card_id_fkey FOREIGN KEY (target_card_id) REFERENCES public.target_cards(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_deployment_plans target_weaponeering_deployment_plans_wing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_plans
    ADD CONSTRAINT target_weaponeering_deployment_plans_wing_id_fkey FOREIGN KEY (wing_id) REFERENCES public.air_wings(id) ON DELETE CASCADE;


--
-- Name: target_weaponeering_deployment_waypoints target_weaponeering_deployment_waypoints_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_weaponeering_deployment_waypoints
    ADD CONSTRAINT target_weaponeering_deployment_waypoints_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.target_weaponeering_deployment_plans(id) ON DELETE CASCADE;


--
-- Name: transport_assets transport_assets_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_assets
    ADD CONSTRAINT transport_assets_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;


--
-- Name: transport_assets transport_assets_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_assets
    ADD CONSTRAINT transport_assets_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: weaponeering_import_batches weaponeering_import_batches_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weaponeering_import_batches
    ADD CONSTRAINT weaponeering_import_batches_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: wing_aircraft wing_aircraft_flying_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_aircraft
    ADD CONSTRAINT wing_aircraft_flying_unit_id_fkey FOREIGN KEY (flying_unit_id) REFERENCES public.wing_flying_units(id) ON DELETE SET NULL;


--
-- Name: wing_aircraft wing_aircraft_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_aircraft
    ADD CONSTRAINT wing_aircraft_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: wing_aircraft wing_aircraft_wing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_aircraft
    ADD CONSTRAINT wing_aircraft_wing_id_fkey FOREIGN KEY (wing_id) REFERENCES public.air_wings(id) ON DELETE CASCADE;


--
-- Name: wing_depot_inventory wing_depot_inventory_depot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_inventory
    ADD CONSTRAINT wing_depot_inventory_depot_id_fkey FOREIGN KEY (depot_id) REFERENCES public.wing_depots(id) ON DELETE CASCADE;


--
-- Name: wing_depot_inventory wing_depot_inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_inventory
    ADD CONSTRAINT wing_depot_inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.wing_products(id) ON DELETE CASCADE;


--
-- Name: wing_depot_inventory wing_depot_inventory_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_inventory
    ADD CONSTRAINT wing_depot_inventory_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: wing_depot_transfers wing_depot_transfers_from_depot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_transfers
    ADD CONSTRAINT wing_depot_transfers_from_depot_id_fkey FOREIGN KEY (from_depot_id) REFERENCES public.wing_depots(id) ON DELETE CASCADE;


--
-- Name: wing_depot_transfers wing_depot_transfers_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_transfers
    ADD CONSTRAINT wing_depot_transfers_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.wing_products(id) ON DELETE CASCADE;


--
-- Name: wing_depot_transfers wing_depot_transfers_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_transfers
    ADD CONSTRAINT wing_depot_transfers_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: wing_depot_transfers wing_depot_transfers_to_depot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depot_transfers
    ADD CONSTRAINT wing_depot_transfers_to_depot_id_fkey FOREIGN KEY (to_depot_id) REFERENCES public.wing_depots(id) ON DELETE CASCADE;


--
-- Name: wing_depots wing_depots_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depots
    ADD CONSTRAINT wing_depots_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: wing_depots wing_depots_wing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_depots
    ADD CONSTRAINT wing_depots_wing_id_fkey FOREIGN KEY (wing_id) REFERENCES public.air_wings(id) ON DELETE CASCADE;


--
-- Name: wing_flying_units wing_flying_units_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_flying_units
    ADD CONSTRAINT wing_flying_units_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: wing_flying_units wing_flying_units_wing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_flying_units
    ADD CONSTRAINT wing_flying_units_wing_id_fkey FOREIGN KEY (wing_id) REFERENCES public.air_wings(id) ON DELETE CASCADE;


--
-- Name: wing_logistics_vehicles wing_logistics_vehicles_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_logistics_vehicles
    ADD CONSTRAINT wing_logistics_vehicles_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: wing_logistics_vehicles wing_logistics_vehicles_wing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_logistics_vehicles
    ADD CONSTRAINT wing_logistics_vehicles_wing_id_fkey FOREIGN KEY (wing_id) REFERENCES public.air_wings(id) ON DELETE CASCADE;


--
-- Name: wing_pilots wing_pilots_flying_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_pilots
    ADD CONSTRAINT wing_pilots_flying_unit_id_fkey FOREIGN KEY (flying_unit_id) REFERENCES public.wing_flying_units(id) ON DELETE SET NULL;


--
-- Name: wing_pilots wing_pilots_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_pilots
    ADD CONSTRAINT wing_pilots_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- Name: wing_pilots wing_pilots_wing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_pilots
    ADD CONSTRAINT wing_pilots_wing_id_fkey FOREIGN KEY (wing_id) REFERENCES public.air_wings(id) ON DELETE SET NULL;


--
-- Name: wing_products wing_products_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wing_products
    ADD CONSTRAINT wing_products_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.scenarios(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--


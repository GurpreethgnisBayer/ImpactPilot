export type ValueSource = 'evidence' | 'user' | 'llm_suggested' | 'default' | 'config';
export type Direction = 'up' | 'down' | 'flat';
export type MaturityTier = 'exploratory' | 'emerging_local' | 'mature';
export type SignoffStatus = 'pending' | 'confirmed' | 'rejected';
export type EvidenceKind = 'pubmed' | 'literature' | 'internal_proof_point' | 'benchmark' | 'expert_input';
export type Confidence = 'low' | 'medium' | 'high';
export type Cadence = 'monthly' | 'quarterly' | 'semiannual';

export interface RangeValue {
  low: number;
  base: number;
  high: number;
  unit?: string;
  source?: ValueSource;
  confirmed?: boolean;
  evidence_ids?: string[];
  rationale?: string;
}

export interface Roles {
  project_lead_name?: string;
  business_owner_name?: string;
  product_owner_name?: string;
  reviewer_name?: string;
  business_owner_signoff_status?: SignoffStatus;
}

export interface Scope {
  phase_id?: string;
  process_step?: string;
  process_step_free_text?: string;
}

export interface BaselineMetric {
  id?: string;
  metric: string;
  value?: RangeValue | null;
  unit?: string;
  source?: string;
  as_of?: string | null;
  unknown?: boolean;
}

export interface DimensionEstimate {
  dimension_id: string;
  direction?: Direction;
  estimate?: RangeValue | null;
  confidence?: Confidence;
  mechanism?: string;
  linked_evidence_ids?: string[];
}

export interface EvidenceItem {
  id?: string;
  kind: EvidenceKind;
  title?: string;
  source_or_link?: string;
  summary?: string;
  pmid?: string | null;
  supports_assumption_ids?: string[];
  quotes?: string[];
}

export interface CostLine {
  category_id: string;
  amount: RangeValue;
  notes?: string;
}

export interface MonetizationResult {
  dimension_id: string;
  formula?: string;
  inputs_trace?: string[];
  amount_eur: RangeValue;
  label?: 'indicative' | 'confirmed';
}

export interface KpiPlan {
  id?: string;
  name: string;
  definition?: string;
  baseline?: RangeValue | null;
  target?: RangeValue | null;
  data_source?: string;
  owner?: string;
  cadence?: Cadence;
}

export interface RealizationRecord {
  id?: string;
  kpi_id: string;
  period: string;
  actual?: RangeValue | null;
  notes?: string;
  recorded_by?: string;
  recorded_at?: string;
}

export interface SuccessStory {
  situation?: string;
  action?: string;
  result?: string;
}

export interface ScorecardEntry {
  dimension_id: string;
  direction: Direction;
  range?: RangeValue | null;
  unit?: string;
  confidence?: Confidence;
  evidence_count?: number;
}

export interface ImpactScore {
  score: number;
  label?: string;
  rationale?: string;
  override?: boolean;
  override_reason?: string;
}

export interface DoubleCountingFlag {
  flagged?: boolean;
  note?: string;
}

export interface Initiative {
  title?: string;
  description?: string;
  focus_area_code?: string;
  big_bet_type?: string;
  big_bet_link?: string;
  lifecycle_stage?: string;
  roles?: Roles;
}

export interface ChangeLever {
  what_changes?: string;
  lever_type?: string;
  affected_dimension_ids?: string[];
}

export interface MaturityAssessment {
  tier?: MaturityTier;
  questionnaire_answers?: Record<string, string>;
  rationale?: string;
}

export interface TcoSummary {
  horizon_years?: number;
  lines?: CostLine[];
  total?: RangeValue | null;
  trace?: string[];
}

export interface InitiativeRecord {
  schema_version?: string;
  id?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
  initiative: Initiative;
  scope?: Scope;
  baselines?: BaselineMetric[];
  change?: ChangeLever;
  maturity?: MaturityAssessment;
  evidence?: EvidenceItem[];
  estimates?: DimensionEstimate[];
  tco?: TcoSummary;
  monetization?: MonetizationResult[];
  measurement_plan?: KpiPlan[];
  realizations?: RealizationRecord[];
  success_story?: SuccessStory;
  compendium?: Compendium | null;
  impact_statement?: string;
  quality_warnings?: QualityWarning[];
  scorecard?: ScorecardEntry[];
  impact_score?: ImpactScore | null;
  double_counting?: DoubleCountingFlag;
}

export interface CompendiumSource {
  source_id: string;
  /** Registry key of the source that returned this hit, e.g. "pubmed", "guidance", "isrctn". */
  database: string;
  title: string;
  year?: string | number | null;
  venue?: string | null;
  url?: string | null;
  type?: string | null;
  abstract?: string;
  relevance?: 'high' | 'medium' | 'low';
}

export type RelevanceRank = 0 | 1 | 2 | 3;

/** Row shape returned by `GET /initiatives` (not the full record). */
export interface InitiativeSummary {
  id: string;
  title: string;
  focus_area_code?: string;
  phase_id?: string;
  maturity_tier?: MaturityTier | string;
  impact_score?: number | null;
  status?: string;
  signoff?: string;
  updated_at?: string;
  dimensions?: string[];
}

export interface CandidateSource extends CompendiumSource {
  recommended?: boolean;
  note?: string;
}

export interface LiteratureSearchResult {
  sources: CandidateSource[];
  queries: Record<string, string>;
  interpretation: string;
  llm_used: boolean;
  warnings: string[];
}

export interface CompendiumDimension {
  dimension_id: string;
  direction: Direction;
  low: number | null;
  base: number | null;
  high: number | null;
  unit: string;
  confidence: Confidence;
  rationale: string;
  citations: string[];
  quotes: string[];
  evidence_backed: boolean;
  /** True when low/high actually matches a number reported in a cited source, not just a
   * band the model invented around it. Only meaningful when evidence_backed is true. */
  grounded?: boolean;
}

export interface Compendium {
  generated_at: string;
  llm_used: boolean;
  queries: Record<string, string>;
  sources: CompendiumSource[];
  executive_summary: string;
  value_chain_phase: string;
  process_step: string;
  mechanism: string;
  key_findings: { finding: string; citations: string[] }[];
  dimensions: CompendiumDimension[];
  suggested_maturity: MaturityTier;
  maturity_rationale: string;
  suggested_kpis: { name: string; definition?: string; cadence?: string }[];
  risks_and_caveats: string[];
  open_questions: string[];
  numeric_snippets: { pmid: string; raw: string; context: string; type: string }[];
  warnings: string[];
}

export interface QualityWarning {
  code?: string;
  message?: string;
  severity?: string;
}

export interface PortfolioAggregations {
  count: number;
  by_tier: Record<string, number>;
  by_focus_area: Record<string, number>;
  by_impact_score: Record<string, number>;
  note?: string;
}

export interface AppConfig {
  focus_areas?: { code: string; label: string }[];
  dimensions?: { id: string; label: string }[];
  value_chain?: { phases?: { id: string; label: string }[] };
  maturity?: { questions?: { id: string; text: string; options?: { value: string; label: string }[] }[] };
  [key: string]: unknown;
}

export interface LlmSettings {
  provider: 'openai_compatible' | 'azure_openai';
  openai_base_url?: string;
  openai_api_key?: string;
  openai_model?: string;
  azure_openai_endpoint?: string;
  azure_openai_api_key?: string;
  azure_openai_deployment?: string;
  azure_openai_api_version?: string;
}

export const emptyRange = (unit = ''): RangeValue => ({
  low: 0,
  base: 0,
  high: 0,
  unit,
  source: 'user',
  confirmed: true,
});

export function emptyInitiativeRecord(): InitiativeRecord {
  return {
    initiative: { title: '', focus_area_code: 'UN', roles: {} },
    scope: {},
    baselines: [],
    change: { affected_dimension_ids: [] },
    maturity: { tier: 'exploratory', questionnaire_answers: {} },
    evidence: [],
    estimates: [],
    tco: { horizon_years: 3, lines: [] },
    monetization: [],
    measurement_plan: [],
    realizations: [],
    success_story: {},
  };
}

export function eurosPermitted(tier?: MaturityTier): boolean {
  return tier === 'emerging_local' || tier === 'mature';
}

// Typed client for the Insight2Listing backend. All requests use relative
// `/api/v1` paths and are proxied by Next (see next.config.ts rewrites), so
// the browser never talks to the API cross-origin.
const BASE = "/api/v1";

export interface Workspace {
  id: string;
  name: string;
  created_at: string;
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  marketplace: string;
  target_locale: string;
  interface_locale: string;
  currency: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Freshness {
  value?: string | null;
  source?: string;
  observed_at?: string | null;
  freshness_status?: string;
  license_ref?: string | null;
  [key: string]: unknown;
}

export interface Product {
  id: string;
  project_id: string;
  external_id: string | null;
  category: string | null;
  title: string;
  brand: string | null;
  currency: string;
  rating: number | null;
  review_count: number | null;
  observed_at: string | null;
  freshness: Freshness | null;
}

export interface Review {
  id: string;
  project_id: string;
  product_id: string | null;
  external_review_id: string | null;
  rating: number | null;
  title: string | null;
  body: string;
  language: string | null;
  verified_purchase: boolean | null;
  reviewed_at: string | null;
}

export interface PreviewColumn {
  source_field: string;
  detected_target: string | null;
  sample_values: string[];
}

export interface ImportPreview {
  target: "products" | "reviews";
  row_count: number;
  columns: PreviewColumn[];
  warnings: string[];
  errors: string[];
}

export interface ImportReport {
  target: string;
  rows_total: number;
  rows_valid: number;
  rows_invalid: number;
  imported: number;
  skipped_duplicates: number;
  errors: string[];
  warnings: string[];
}

export interface ImportBatch {
  id: string;
  project_id: string;
  source_id: string | null;
  target: string;
  source_file_name: string | null;
  status: "processing" | "completed" | "failed" | "pending";
  report: ImportReport | null;
  finished_at: string | null;
  created_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function getWorkspace(): Promise<Workspace> {
  return request<Workspace>("/workspaces");
}

export function listProjects(): Promise<{ items: Project[]; total: number }> {
  return request<{ items: Project[]; total: number }>("/projects");
}

export function getProject(id: string): Promise<Project> {
  return request<Project>(`/projects/${id}`);
}

export function createProject(
  workspaceId: string,
  name: string
): Promise<Project> {
  return request<Project>("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_id: workspaceId, name }),
  });
}

export function listProducts(
  projectId: string
): Promise<{ items: Product[]; total: number }> {
  return request<{ items: Product[]; total: number }>(
    `/projects/${projectId}/products`
  );
}

export function listReviews(
  projectId: string,
  q?: string
): Promise<{ items: Review[]; total: number }> {
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  return request<{ items: Review[]; total: number }>(
    `/projects/${projectId}/reviews${query}`
  );
}

export function previewImport(
  projectId: string,
  file: File,
  target: string
): Promise<ImportPreview> {
  const form = new FormData();
  form.append("file", file);
  form.append("target", target);
  return request<ImportPreview>(`/projects/${projectId}/imports/preview`, {
    method: "POST",
    body: form,
  });
}

export function importFile(
  projectId: string,
  file: File,
  target: string
): Promise<ImportBatch> {
  const form = new FormData();
  form.append("file", file);
  form.append("target", target);
  return request<ImportBatch>(`/projects/${projectId}/imports`, {
    method: "POST",
    body: form,
  });
}

// ---- Phase C: insights & opportunity cards ----

export interface Evidence {
  id: string;
  insight_id: string;
  evidence_type: string;
  source_entity_id: string | null;
  excerpt: string;
  support_strength: number | null;
  observed_at: string | null;
}

export interface Insight {
  id: string;
  project_id: string;
  product_id: string | null;
  topic: string;
  summary: string | null;
  sentiment: "positive" | "negative" | "neutral";
  frequency: number;
  severity: "low" | "medium" | "high";
  rating_impact: number | null;
  recency_score: number | null;
  cross_competitor_score: number | null;
  confidence: number | null;
  status: "generated" | "accepted" | "edited" | "rejected" | "superseded";
  created_at: string;
}

export interface InsightDetail extends Insight {
  evidence: Evidence[];
}

export interface OpportunityCard {
  id: string;
  project_id: string;
  product_id: string;
  title: string;
  target_audience: string | null;
  use_cases: string[] | null;
  competitor_gaps: string[] | null;
  differentiation_ideas: string[] | null;
  keywords: string[] | null;
  opportunity_score: number | null;
  dimension_scores: Record<string, number | null> | null;
  score_version: string | null;
  confidence: number | null;
  missing_dimensions: string[] | null;
  risk_flags: string[] | null;
  status: string;
  created_at: string;
}

export interface GenerateResult {
  insights: number;
  cards: number;
  reviews_attributed: number;
  reviews_skipped: number;
}

export function generateInsights(projectId: string): Promise<GenerateResult> {
  return request<GenerateResult>(`/projects/${projectId}/insights/generate`, {
    method: "POST",
  });
}

export function listInsights(
  projectId: string,
  insightStatus?: string
): Promise<{ items: Insight[]; total: number }> {
  const q = insightStatus ? `?insight_status=${encodeURIComponent(insightStatus)}` : "";
  return request<{ items: Insight[]; total: number }>(
    `/projects/${projectId}/insights${q}`
  );
}

export function getInsight(projectId: string, id: string): Promise<InsightDetail> {
  return request<InsightDetail>(`/projects/${projectId}/insights/${id}`);
}

export function setInsightStatus(
  projectId: string,
  id: string,
  status: string
): Promise<Insight> {
  return request<Insight>(`/projects/${projectId}/insights/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export function listOpportunityCards(
  projectId: string
): Promise<{ items: OpportunityCard[]; total: number }> {
  return request<{ items: OpportunityCard[]; total: number }>(
    `/projects/${projectId}/opportunity-cards`
  );
}
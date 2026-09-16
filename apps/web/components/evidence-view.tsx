"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { LoaderIcon, ChevronDownIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useWorkspaceData } from "@/hooks/use-workspace-data";
import * as api from "@/lib/api";

export function EvidenceView() {
  const t = useTranslations("evidence");
  const tCommon = useTranslations("common");
  const data = useWorkspaceData();

  const [projectId, setProjectId] = useState("");
  const [insights, setInsights] = useState<api.Insight[]>([]);
  const [cards, setCards] = useState<api.OpportunityCard[]>([]);
  const [evidenceMap, setEvidenceMap] = useState<Record<string, api.Evidence[]>>({});
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const projects = data.projects;

  useEffect(() => {
    if (projects.length > 0 && !projectId) setProjectId(projects[0].id);
  }, [projects, projectId]);

  const load = useCallback(
    async (id: string) => {
      setLoading(true);
      setError(null);
      try {
        const [ins, cardsRes] = await Promise.all([
          api.listInsights(id),
          api.listOpportunityCards(id),
        ]);
        setInsights(ins.items);
        setCards(cardsRes.items);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (projectId) void load(projectId);
  }, [projectId, load]);

  const generate = useCallback(async () => {
    if (!projectId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.generateInsights(projectId);
      await load(projectId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setGenerating(false);
    }
  }, [projectId, load]);

  const toggleExpand = useCallback(
    async (id: string) => {
      if (expandedId === id) {
        setExpandedId(null);
        return;
      }
      setExpandedId(id);
      if (!evidenceMap[id] && projectId) {
        try {
          const detail = await api.getInsight(projectId, id);
          setEvidenceMap((m) => ({ ...m, [id]: detail.evidence }));
        } catch {
          /* ignore expand errors */
        }
      }
    },
    [expandedId, evidenceMap, projectId]
  );

  const review = useCallback(
    async (id: string, status: "accepted" | "rejected") => {
      if (!projectId) return;
      setBusyId(id);
      setError(null);
      try {
        await api.setInsightStatus(projectId, id, status);
        await load(projectId);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setBusyId(null);
      }
    },
    [projectId, load]
  );

  return (
    <div className="grid grid-cols-1 gap-4 px-4 lg:px-6 xl:grid-cols-2">
      {/* Insights column */}
      <div className="space-y-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base">{t("insightsTitle")}</CardTitle>
              <CardDescription>{t("desc")}</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={generate} disabled={!projectId || generating}>
              {generating ? <LoaderIcon className="size-4 animate-spin" /> : null}
              {t("generate")}
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">{t("project")}</label>
              <Select value={projectId} onValueChange={(v) => v != null && setProjectId(v)}>
                <SelectTrigger>
                  <SelectValue placeholder={t("selectProject")} />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            {loading ? <p className="text-sm text-muted-foreground">{tCommon("loading")}</p> : null}

            {!loading && !error && insights.length === 0 && (
              <p className="text-sm text-muted-foreground">{t("notGenerated")}</p>
            )}

            <div className="space-y-2">
              {insights.map((ins) => (
                <div key={ins.id} className="rounded-lg border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => toggleExpand(ins.id)}
                      className="flex min-w-0 items-center gap-2 text-left"
                    >
                      <ChevronDownIcon className={`size-4 shrink-0 transition-transform ${expandedId === ins.id ? "rotate-180" : ""}`} />
                      <span className="truncate text-sm font-medium">{ins.topic}</span>
                    </button>
                    <div className="flex shrink-0 items-center gap-1.5">
                      <Badge variant={ins.sentiment === "negative" ? "destructive" : "outline"}>
                        {ins.sentiment}
                      </Badge>
                      <Badge variant="secondary">{ins.severity}</Badge>
                      <span className="text-xs tabular-nums text-muted-foreground">{ins.frequency}</span>
                    </div>
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {ins.summary} · {t("confidence")} {ins.confidence != null ? `${Math.round(ins.confidence * 100)}%` : "—"}
                  </div>
                  {expandedId === ins.id ? (
                    <div className="mt-2 space-y-1.5 border-t pt-2">
                      {(evidenceMap[ins.id] ?? []).length === 0 ? (
                        <p className="text-xs text-muted-foreground">{t("evidence")}: —</p>
                      ) : (
                        (evidenceMap[ins.id] ?? []).map((ev) => (
                          <div key={ev.id} className="rounded bg-muted/40 p-2 text-xs">
                            <div className="text-muted-foreground">
                              {t("evidence")} · {ev.evidence_type}
                            </div>
                            <div className="mt-1 line-clamp-2 text-foreground/80">{ev.excerpt}</div>
                          </div>
                        ))
                      )}
                    </div>
                  ) : null}
                  {["generated", "edited"].includes(ins.status) ? (
                    <div className="mt-2 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => review(ins.id, "accepted")}
                        disabled={busyId === ins.id}
                      >
                        {t("accept")}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => review(ins.id, "rejected")}
                        disabled={busyId === ins.id}
                      >
                        {t("reject")}
                      </Button>
                    </div>
                  ) : (
                    <div className="mt-2 text-xs text-muted-foreground">{ins.status}</div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Opportunity cards column */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("cards")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {cards.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                {loading ? tCommon("loading") : t("cardsEmpty")}
              </p>
            ) : (
              cards.map((card) => (
                <div key={card.id} className="rounded-lg border p-3">
                  <div className="flex items-center justify-between">
                    <span className="truncate text-sm font-medium">{card.title}</span>
                    <Badge variant="outline">{card.status}</Badge>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <div className="text-muted-foreground">{t("cardScore")}</div>
                      <div className="text-base font-semibold tabular-nums">
                        {card.opportunity_score ?? "—"}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">{t("cardConfidence")}</div>
                      <div className="text-sm font-semibold tabular-nums">
                        {card.confidence != null ? `${Math.round(card.confidence * 100)}%` : "—"}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">{t("keywords")}</div>
                      <div className="line-clamp-2 text-foreground/80">
                        {(card.keywords ?? []).slice(0, 5).join(", ") || "—"}
                      </div>
                    </div>
                  </div>
                  {card.missing_dimensions && card.missing_dimensions.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(card.missing_dimensions ?? []).map((m) => (
                        <Badge key={m} variant="outline">
                          {m}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                  {card.risk_flags && card.risk_flags.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(card.risk_flags ?? []).map((r) => (
                        <Badge key={r} variant="secondary">
                          {r}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
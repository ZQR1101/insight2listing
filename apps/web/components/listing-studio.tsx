"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { CheckIcon, LoaderIcon, SparklesIcon, TrashIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useWorkspaceData } from "@/hooks/use-workspace-data";
import * as api from "@/lib/api";

const FACT_TYPES = [
  "material",
  "size",
  "weight",
  "capacity",
  "accessory",
  "color",
  "usage_limitation",
  "certification",
] as const;

function download(file: api.ExportedFile) {
  const blob = new Blob([file.content], { type: file.mediaType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = file.filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ListingStudio() {
  const t = useTranslations("studio");
  const tCommon = useTranslations("common");
  const data = useWorkspaceData();

  const [projectId, setProjectId] = useState("");
  const [products, setProducts] = useState<api.Product[]>([]);
  const [productId, setProductId] = useState("");
  const [facts, setFacts] = useState<api.ProductFact[]>([]);
  const [listings, setListings] = useState<api.ListingVersion[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [factType, setFactType] = useState<string>("material");
  const [factValue, setFactValue] = useState("");
  const [factUnit, setFactUnit] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loading = data.loading;
  const projects = data.projects;

  useEffect(() => {
    if (projects.length > 0 && !projectId) setProjectId(projects[0].id);
  }, [projects, projectId]);

  useEffect(() => {
    let cancelled = false;
    if (!projectId) return;
    setProducts([]);
    setProductId("");
    api
      .listProducts(projectId)
      .then((res) => {
        if (cancelled) return;
        setProducts(res.items);
        if (res.items.length > 0) setProductId(res.items[0].id);
      })
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : "Unknown error"));
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const reloadFacts = useCallback(
    async (id: string) => {
      const res = await api.listFacts(id);
      setFacts(res.items);
    },
    []
  );

  const reloadListings = useCallback(
    async (id: string, selectFirst = false) => {
      const res = await api.listListings(id);
      setListings(res.items);
      if (selectFirst && res.items.length > 0) setSelectedId(res.items[0].id);
    },
    []
  );

  useEffect(() => {
    if (!productId) {
      setFacts([]);
      setListings([]);
      return;
    }
    setError(null);
    void reloadFacts(projectId).catch((e) => setError(e instanceof Error ? e.message : "Unknown error"));
    void reloadListings(projectId).catch((e) => setError(e instanceof Error ? e.message : "Unknown error"));
  }, [productId, projectId, reloadFacts, reloadListings]);

  const addFact = useCallback(async () => {
    if (!projectId || !productId || !factValue.trim()) return;
    setBusy("addFact");
    setError(null);
    try {
      await api.createFact(projectId, productId, {
        fact_type: factType,
        value: factValue.trim(),
        unit: factUnit.trim() || undefined,
      });
      setFactValue("");
      setFactUnit("");
      await reloadFacts(projectId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setBusy(null);
    }
  }, [projectId, productId, factType, factValue, factUnit, reloadFacts]);

  const act = useCallback(
    async (key: string, action: () => Promise<void>, onDone?: () => void) => {
      setBusy(key);
      setError(null);
      setNotice(null);
      try {
        await action();
        onDone?.();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setBusy(null);
      }
    },
    []
  );

  const selected = useMemo(
    () => listings.find((l) => l.id === selectedId) ?? null,
    [listings, selectedId]
  );

  if (loading) {
    return <p className="px-6 py-8 text-sm text-muted-foreground">{tCommon("loading")}</p>;
  }

  return (
    <div className="space-y-4 px-4 lg:px-6">
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {notice ? <p className="text-sm text-muted-foreground">{notice}</p> : null}

      <Card>
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
          <CardDescription>{t("desc")}</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="space-y-2">
            <Label>{t("project")}</Label>
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
          <div className="space-y-2">
            <Label>{t("product")}</Label>
            <Select value={productId} onValueChange={(v) => v != null && setProductId(v)}>
              <SelectTrigger>
                <SelectValue placeholder={t("selectProduct")} />
              </SelectTrigger>
              <SelectContent>
                {products.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {/* Facts centre */}
        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-3">
            <div>
              <CardTitle className="text-base">{t("factsTitle")}</CardTitle>
              <CardDescription>{t("confirmGateHint")}</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={!projectId || busy === "confirmGate"}
              onClick={() =>
                act(
                  "confirmGate",
                  async () => {
                    const res = await api.confirmFacts(projectId);
                    setNotice(`${t("confirmGate")}: ${res.status} (${res.confirmed_facts})`);
                    data.reload();
                  },
                  () => reloadFacts(projectId)
                )
              }
            >
              {busy === "confirmGate" ? <LoaderIcon className="size-4 animate-spin" /> : <CheckIcon className="size-4" />}
              {t("confirmGate")}
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {facts.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("noFacts")}</p>
            ) : (
              <ul className="divide-y">
                {facts.map((fact) => (
                  <li key={fact.id} className="flex items-center justify-between gap-2 py-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{t(`fact_${fact.fact_type}`)}</Badge>
                        <span className="truncate text-sm">
                          {fact.value}
                          {fact.unit ? ` ${fact.unit}` : ""}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {fact.verification_status}
                        {fact.verified_by ? ` · ${fact.verified_by}` : ""}
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-1">
                      {fact.verification_status === "unverified" ? (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busy === `fact-${fact.id}`}
                            onClick={() =>
                              act(`fact-${fact.id}`, async () => {
                                await api.setFactStatus(projectId, fact.id, "user_confirmed");
                                await reloadFacts(projectId);
                              })
                            }
                          >
                            {t("confirm")}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={busy === `fact-${fact.id}`}
                            onClick={() =>
                              act(`fact-${fact.id}`, async () => {
                                await api.setFactStatus(projectId, fact.id, "rejected");
                                await reloadFacts(projectId);
                              })
                            }
                          >
                            {t("rejectFact")}
                          </Button>
                        </>
                      ) : null}
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label={t("delete")}
                        disabled={busy === `fact-${fact.id}`}
                        onClick={() =>
                          act(`fact-${fact.id}`, async () => {
                            await api.deleteFact(projectId, fact.id);
                            await reloadFacts(projectId);
                          })
                        }
                      >
                        <TrashIcon className="size-4" />
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <div className="space-y-2 rounded-lg border p-3">
              <Label>{t("addFact")}</Label>
              <div className="grid grid-cols-2 gap-2">
                <Select value={factType} onValueChange={(v) => v != null && setFactType(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FACT_TYPES.map((ft) => (
                      <SelectItem key={ft} value={ft}>
                        {t(`fact_${ft}`)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder={t("unit")}
                  value={factUnit}
                  onChange={(e) => setFactUnit(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder={t("value")}
                  value={factValue}
                  onChange={(e) => setFactValue(e.target.value)}
                />
                <Button onClick={addFact} disabled={busy === "addFact" || !factValue.trim()}>
                  {busy === "addFact" ? <LoaderIcon className="size-4 animate-spin" /> : null}
                  {t("create")}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Listing versions */}
        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-3">
            <div>
              <CardTitle className="text-base">{t("listingsTitle")}</CardTitle>
              <CardDescription>{t("generateHint")}</CardDescription>
            </div>
            <Button
              size="sm"
              disabled={!projectId || !productId || busy === "generate"}
              onClick={() =>
                act("generate", async () => {
                  const created = await api.generateListing(projectId, productId);
                  setNotice(`${t("generate")}: ${created.title}`);
                  await reloadListings(projectId, true);
                })
              }
            >
              {busy === "generate" ? <LoaderIcon className="size-4 animate-spin" /> : <SparklesIcon className="size-4" />}
              {t("generate")}
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {listings.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("noListings")}</p>
            ) : (
              <ul className="space-y-2">
                {listings.map((listing) => {
                  const factPassed = listing.fact_check?.passed === true;
                  const rulePassed = listing.rule_check?.passed === true;
                  const isSelected = listing.id === selectedId;
                  return (
                    <li
                      key={listing.id}
                      className={`cursor-pointer rounded-lg border p-3 ${isSelected ? "border-foreground/40" : ""}`}
                      onClick={() => setSelectedId(listing.id)}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm font-medium">{listing.title}</span>
                        <Badge variant={listing.status === "approved" ? "secondary" : "outline"}>
                          {listing.status === "approved" ? t("approved") : t("draft")}
                        </Badge>
                      </div>
                      <div className="mt-1 flex items-center gap-2 text-xs">
                        <span className={factPassed && rulePassed ? "text-emerald-600" : "text-amber-600"}>
                          {factPassed && rulePassed ? t("checksPassed") : t("checksFailed")}
                        </span>
                        <span className="text-muted-foreground">{listing.model}</span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}

            {selected ? (
              <div className="space-y-3 rounded-lg border p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-semibold">{selected.title}</span>
                  <div className="flex shrink-0 gap-1">
                    {(["json", "markdown", "csv"] as const).map((fmt) => (
                      <Button
                        key={fmt}
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          void exportListingSafe(projectId, selected.id, fmt, download, setError)
                        }
                      >
                        {fmt}
                      </Button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-xs font-medium text-muted-foreground">{t("bullets")}</div>
                  <ul className="mt-1 space-y-1">
                    {(selected.bullet_points ?? []).map((b, idx) => (
                      <li key={idx} className="rounded bg-muted/40 p-2 text-xs">
                        {b.text}
                        <span className="ml-1 text-muted-foreground">
                          ({b.fact_ids.length + b.insight_ids.length} {t("refs")})
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
                {selected.description ? (
                  <div>
                    <div className="text-xs font-medium text-muted-foreground">{t("description")}</div>
                    <p className="mt-1 text-xs">{selected.description}</p>
                  </div>
                ) : null}
                {selected.search_terms ? (
                  <div>
                    <div className="text-xs font-medium text-muted-foreground">{t("searchTerms")}</div>
                    <p className="mt-1 text-xs">{selected.search_terms}</p>
                  </div>
                ) : null}
                <Button
                  size="sm"
                  disabled={busy === "approve" || selected.status === "approved"}
                  onClick={() =>
                    act(
                      "approve",
                      async () => {
                        await api.approveListing(projectId, selected.id);
                        await reloadListings(projectId);
                      },
                      () => data.reload()
                    )
                  }
                >
                  {busy === "approve" ? <LoaderIcon className="size-4 animate-spin" /> : null}
                  {t("approve")}
                </Button>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

async function exportListingSafe(
  projectId: string,
  listingId: string,
  format: "json" | "markdown" | "csv",
  download: (file: api.ExportedFile) => void,
  setError: (message: string) => void
) {
  try {
    download(await api.exportListing(projectId, listingId, format));
  } catch (e) {
    setError(e instanceof Error ? e.message : "Unknown error");
  }
}
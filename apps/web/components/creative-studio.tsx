"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { DownloadIcon, ImagePlusIcon, LoaderIcon, SparklesIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useWorkspaceData } from "@/hooks/use-workspace-data";
import * as api from "@/lib/api";

const ASSET_TYPES = [
  "main_image_edit",
  "lifestyle_image",
  "feature_image",
  "comparison_image",
  "size_image",
  "detail_page_section",
] as const;

function downloadBlob(file: api.BinaryFile) {
  const url = URL.createObjectURL(file.blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = file.filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function CreativeStudio() {
  const t = useTranslations("creatives");
  const tNav = useTranslations("nav");
  const tCommon = useTranslations("common");
  const data = useWorkspaceData();
  const projects = data.projects;

  const [projectId, setProjectId] = useState("");
  const [products, setProducts] = useState<api.Product[]>([]);
  const [productId, setProductId] = useState("");
  const [images, setImages] = useState<api.ProductImage[]>([]);
  const [creatives, setCreatives] = useState<api.CreativeAsset[]>([]);
  const [assetType, setAssetType] = useState<string>("main_image_edit");
  const [sourceIds, setSourceIds] = useState<string[]>([]);
  const [overlayText, setOverlayText] = useState("");
  const [rightsAttested, setRightsAttested] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const productIdRef = useRef("");

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

  const reloadImages = useCallback(async () => {
    if (!productIdRef.current) return;
    const res = await api.listImages(projectId, productIdRef.current);
    setImages(res.items);
  }, []);

  const reloadCreatives = useCallback(async () => {
    if (!productIdRef.current) return;
    const res = await api.listCreatives(projectId, productIdRef.current);
    setCreatives(res.items);
  }, []);

  useEffect(() => {
    productIdRef.current = productId;
    if (!productId) {
      setImages([]);
      setCreatives([]);
      return;
    }
    setError(null);
    api
      .listImages(projectId, productId)
      .then((res) => setImages(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Unknown error"));
    api
      .listCreatives(projectId, productId)
      .then((res) => setCreatives(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Unknown error"));
  }, [projectId, productId]);

  const upload = useCallback(async () => {
    if (!projectId || !productId || !file) return;
    setBusy("upload");
    setError(null);
    try {
      await api.uploadImage(projectId, productId, file, rightsAttested);
      setFile(null);
      await reloadImages();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setBusy(null);
    }
  }, [projectId, productId, file, rightsAttested, reloadImages]);

  const generate = useCallback(async () => {
    if (!projectId || !productId) return;
    setBusy("generate");
    setError(null);
    try {
      await api.generateCreative(projectId, productId, {
        asset_type: assetType,
        source_image_ids: sourceIds,
        overlay_lines: overlayText
          .split(",")
          .map((line) => line.trim())
          .filter(Boolean),
      });
      await reloadCreatives();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setBusy(null);
    }
  }, [projectId, productId, assetType, sourceIds, overlayText, reloadCreatives]);

  const review = useCallback(
    async (creativeId: string, decision: "approved" | "rejected") => {
      if (!projectId) return;
      setBusy(creativeId);
      setError(null);
      try {
        await api.reviewCreative(projectId, creativeId, decision);
        await reloadCreatives();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setBusy(null);
      }
    },
    [projectId, reloadCreatives]
  );

  const download = useCallback(
    async (creativeId: string) => {
      if (!projectId) return;
      setBusy(creativeId);
      setError(null);
      try {
        downloadBlob(await api.downloadCreative(projectId, creativeId));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setBusy(null);
      }
    },
    [projectId]
  );

  const isMain = assetType === "main_image_edit";

  if (data.loading) {
    return <p className="px-6 py-8 text-sm text-muted-foreground">{tCommon("loading")}</p>;
  }

  return (
    <div className="space-y-4 px-4 lg:px-6">
      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <Card>
        <CardHeader>
          <CardTitle>{tNav("creatives")}</CardTitle>
          <CardDescription>{t("desc")}</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="space-y-2">
            <Label>{t("project")}</Label>
            <Select value={projectId} onValueChange={(v) => v != null && setProjectId(v)}>
              <SelectTrigger>
                <SelectValue />
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
        {/* Product photos */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("imagesTitle")}</CardTitle>
            <CardDescription>{t("noImages")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {images.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {images.map((image) => (
                  <div key={image.id} className="space-y-1">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={api.imageUrl(projectId, image.id)}
                      alt={image.filename}
                      className="h-24 w-full rounded border object-cover"
                    />
                    <div className="text-xs text-muted-foreground">
                      {image.width}×{image.height}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}

            <div className="space-y-2 rounded-lg border p-3">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="rights"
                  checked={rightsAttested}
                  onCheckedChange={(checked) => setRightsAttested(checked === true)}
                />
                <Label htmlFor="rights" className="text-xs font-normal">
                  {t("rightsHint")}
                </Label>
              </div>
              <div className="flex gap-2">
                <Input
                  type="file"
                  accept="image/png,image/jpeg"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
                <Button onClick={upload} disabled={!file || busy === "upload"}>
                  {busy === "upload" ? (
                    <LoaderIcon className="size-4 animate-spin" />
                  ) : (
                    <ImagePlusIcon className="size-4" />
                  )}
                  {t("upload")}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Creatives */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("creativesTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2 rounded-lg border p-3">
              <Label>{t("assetType")}</Label>
              <Select value={assetType} onValueChange={(v) => v != null && setAssetType(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ASSET_TYPES.map((at) => (
                    <SelectItem key={at} value={at}>
                      {t(`type_${at}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {images.length > 0 ? (
                <div className="space-y-1">
                  <Label className="text-xs">{t("sourceImages")}</Label>
                  {images.map((image) => (
                    <div key={image.id} className="flex items-center gap-2">
                      <Checkbox
                        id={`src-${image.id}`}
                        checked={sourceIds.includes(image.id)}
                        onCheckedChange={(checked) =>
                          setSourceIds((prev) =>
                            checked === true
                              ? [...prev, image.id]
                              : prev.filter((id) => id !== image.id)
                          )
                        }
                      />
                      <label htmlFor={`src-${image.id}`} className="text-xs">
                        {image.filename} ({image.width}×{image.height})
                      </label>
                    </div>
                  ))}
                </div>
              ) : null}

              {!isMain ? (
                <div className="space-y-1">
                  <Label className="text-xs">{t("overlayLines")}</Label>
                  <Input value={overlayText} onChange={(e) => setOverlayText(e.target.value)} />
                </div>
              ) : null}

              <Button onClick={generate} disabled={busy === "generate"}>
                {busy === "generate" ? (
                  <LoaderIcon className="size-4 animate-spin" />
                ) : (
                  <SparklesIcon className="size-4" />
                )}
                {t("generate")}
              </Button>
            </div>

            {creatives.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("noCreatives")}</p>
            ) : (
              <ul className="space-y-2">
                {creatives.map((creative) => (
                  <li key={creative.id} className="flex items-start gap-3 rounded-lg border p-3">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={api.creativeUrl(projectId, creative.id)}
                      alt={creative.asset_type}
                      className="h-20 w-20 shrink-0 rounded border object-cover"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{t(`type_${creative.asset_type}`)}</Badge>
                        <Badge
                          variant={creative.human_review_status === "approved" ? "secondary" : "outline"}
                        >
                          {creative.human_review_status}
                        </Badge>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-1 text-xs text-muted-foreground">
                        <span>
                          {t("consistency")}: {creative.consistency_status}
                        </span>
                        <span>·</span>
                        <span>
                          {t("compliance")}: {creative.compliance_status}
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {creative.human_review_status === "pending" ? (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={busy === creative.id}
                              onClick={() => review(creative.id, "approved")}
                            >
                              {t("approve")}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              disabled={busy === creative.id}
                              onClick={() => review(creative.id, "rejected")}
                            >
                              {t("reject")}
                            </Button>
                          </>
                        ) : null}
                        {creative.human_review_status === "approved" ? (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busy === creative.id}
                            onClick={() => download(creative.id)}
                          >
                            {busy === creative.id ? (
                              <LoaderIcon className="size-4 animate-spin" />
                            ) : (
                              <DownloadIcon className="size-4" />
                            )}
                            {t("download")}
                          </Button>
                        ) : null}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
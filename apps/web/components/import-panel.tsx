"use client";

import { useCallback, useEffect, useMemo, useState, useTransition } from "react";
import { useTranslations } from "next-intl";
import { FileUpIcon, LoaderIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import * as api from "@/lib/api";

export function ImportPanel() {
  const t = useTranslations("import");
  const tCommon = useTranslations("common");

  const [projects, setProjects] = useState<api.Project[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [newProjectName, setNewProjectName] = useState("");
  const [creating, setCreating] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [target, setTarget] = useState("products");
  const [preview, setPreview] = useState<api.ImportPreview | null>(null);
  const [report, setReport] = useState<api.ImportBatch | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getWorkspace(), api.listProjects()])
      .then(([ws, list]) => {
        if (cancelled) return;
        setWorkspaceId(ws.id);
        setProjects(list.items);
        if (list.items.length > 0) setProjectId(list.items[0].id);
      })
      .catch((e) => cancelled || setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, []);

  const createProject = useCallback(async () => {
    const name = newProjectName.trim();
    if (!name || !workspaceId) return;
    setCreating(true);
    setError(null);
    try {
      const created = await api.createProject(workspaceId, name);
      setProjects((prev) => [...prev, created]);
      setProjectId(created.id);
      setNewProjectName("");
    } catch (e) {
      setError(String(e));
    } finally {
      setCreating(false);
    }
  }, [newProjectName, workspaceId]);

  const runPreview = useCallback(() => {
    if (!projectId || !file) return;
    setError(null);
    setReport(null);
    startTransition(async () => {
      try {
        setPreview(await api.previewImport(projectId, file as File, target));
      } catch (e) {
        setError(String(e));
      }
    });
  }, [projectId, file, target]);

  const runImport = useCallback(() => {
    if (!projectId || !file) return;
    setError(null);
    startTransition(async () => {
      try {
        setReport(await api.importFile(projectId, file as File, target));
        setPreview(null);
      } catch (e) {
        setError(String(e));
      }
    });
  }, [projectId, file, target]);

  const mappedColumns = useMemo(
    () => preview?.columns.filter((c) => c.detected_target) ?? [],
    [preview]
  );

  return (
    <div className="grid grid-cols-1 gap-4 px-4 lg:px-6 xl:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
          <CardDescription>{t("desc")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>{t("project")}</Label>
            <div className="flex gap-2">
              <Select value={projectId} onValueChange={(v) => v != null && setProjectId(v)}>
                <SelectTrigger className="flex-1">
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
          </div>

          <div className="space-y-2">
            <Label>{t("createProject")}</Label>
            <div className="flex gap-2">
              <Input
                value={newProjectName}
                placeholder={t("projectNamePlaceholder")}
                onChange={(e) => setNewProjectName(e.target.value)}
              />
              <Button variant="outline" onClick={createProject} disabled={creating || !newProjectName.trim()}>
                {creating ? <LoaderIcon className="size-4 animate-spin" /> : null}
                {t("createProject")}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t("target")}</Label>
            <Select value={target} onValueChange={(v) => v != null && setTarget(v)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="products">{t("products")}</SelectItem>
                <SelectItem value="reviews">{t("reviews")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>{t("file")}</Label>
            <Input
              type="file"
              accept=".csv,.json,.xlsx,.xlsm"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>

          <div className="flex gap-2">
            <Button variant="outline" onClick={runPreview} disabled={!projectId || !file || isPending}>
              {isPending ? <LoaderIcon className="size-4 animate-spin" /> : null}
              {t("previewBtn")}
            </Button>
            <Button onClick={runImport} disabled={!projectId || !file || isPending}>
              <FileUpIcon className="size-4" />
              {t("importBtn")}
            </Button>
          </div>

          {error ? <p className="text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("report")}</CardTitle>
        </CardHeader>
        <CardContent>
          {report ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge variant={report.status === "completed" ? "secondary" : "destructive"}>
                  {report.status === "completed" ? t("completed") : t("failed")}
                </Badge>
              </div>
              {report.report ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("reportImported")}</TableHead>
                      <TableHead>{t("reportSkipped")}</TableHead>
                      <TableHead>{t("reportInvalid")}</TableHead>
                      <TableHead>{t("reportErrors")}</TableHead>
                      <TableHead>{t("reportWarnings")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell>{report.report.imported}</TableCell>
                      <TableCell>{report.report.skipped_duplicates}</TableCell>
                      <TableCell>{report.report.rows_invalid}</TableCell>
                      <TableCell>{report.report.errors.length}</TableCell>
                      <TableCell>{report.report.warnings.length}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              ) : null}
            </div>
          ) : preview ? (
            <div className="space-y-3 text-sm">
              <p>
                {preview.row_count} {t("rowCount")}
              </p>
              <ul className="divide-y">
                {mappedColumns.map((c) => (
                  <li key={c.source_field} className="py-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate font-medium">{c.source_field}</span>
                      <Badge variant="outline">{c.detected_target}</Badge>
                    </div>
                  </li>
                ))}
                {preview.columns
                  .filter((c) => !c.detected_target)
                  .map((c) => (
                    <li key={c.source_field} className="py-2 text-muted-foreground">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate">{c.source_field}</span>
                        <Badge variant="outline">{t("unmapped")}</Badge>
                      </div>
                    </li>
                  ))}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
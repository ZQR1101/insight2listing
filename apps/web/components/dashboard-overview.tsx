"use client";

import { useTranslations } from "next-intl";
import { RefreshCwIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SectionCards } from "@/components/section-cards";
import { WorkflowStatus } from "@/components/workflow-status";
import { ProductsTable, type ProductRow } from "@/components/products-table";
import { useWorkspaceData } from "@/hooks/use-workspace-data";
import type { Product, Project } from "@/lib/api";

function buildRows(
  projects: Project[],
  productsByProject: Record<string, Product[]>
): ProductRow[] {
  const rows: ProductRow[] = [];
  for (const project of projects) {
    for (const p of productsByProject[project.id] ?? []) {
      rows.push({ ...p, project_name: project.name });
    }
  }
  return rows;
}

export function DashboardOverview() {
  const data = useWorkspaceData();
  const t = useTranslations("common");

  if (data.loading) {
    return <p className="px-6 py-8 text-sm text-muted-foreground">{t("loading")}</p>;
  }

  if (data.error) {
    return (
      <div className="px-4 lg:px-6">
        <p className="text-sm text-destructive">{data.error}</p>
        <Button variant="outline" size="sm" className="mt-2" onClick={data.reload}>
          {t("retry")}
        </Button>
      </div>
    );
  }

  const rows = buildRows(data.projects, data.productsByProject);

  return (
    <>
      <div className="flex items-center justify-end px-4 lg:px-6">
        <Button variant="ghost" size="sm" onClick={data.reload}>
          <RefreshCwIcon className="size-4" />
          {t("refresh")}
        </Button>
      </div>
      <SectionCards data={data.totals} />
      <div className="mt-4 px-4 lg:px-6">
        <WorkflowStatus
          projects={data.projects}
          counts={Object.fromEntries(
            data.projects.map((p) => [
              p.id,
              {
                products: data.productsByProject[p.id]?.length ?? 0,
                reviews: data.reviewCounts[p.id] ?? 0,
              },
            ])
          )}
        />
      </div>
      <div className="mt-4 px-4 lg:px-6">
        <ProductsTable rows={rows} />
      </div>
    </>
  );
}
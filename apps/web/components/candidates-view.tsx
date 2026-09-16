"use client";

import { useTranslations } from "next-intl";
import { RefreshCwIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ProductsTable, type ProductRow } from "@/components/products-table";
import { useWorkspaceData } from "@/hooks/use-workspace-data";
import type { Product, Project } from "@/lib/api";

export function CandidatesView() {
  const data = useWorkspaceData();
  const t = useTranslations("candidates");
  const tCommon = useTranslations("common");

  if (data.loading) {
    return <p className="px-6 text-sm text-muted-foreground">{tCommon("loading")}</p>;
  }

  if (data.error) {
    return (
      <div className="px-4 lg:px-6">
        <p className="text-sm text-destructive">{data.error}</p>
        <Button variant="outline" size="sm" className="mt-2" onClick={data.reload}>
          {tCommon("retry")}
        </Button>
      </div>
    );
  }

  const rows: ProductRow[] = data.projects.flatMap((project: Project) =>
    (data.productsByProject[project.id] ?? []).map((p: Product) => ({
      ...p,
      project_name: project.name,
    }))
  );

  return (
    <div className="px-4 lg:px-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>{t("title")}</CardTitle>
            <CardDescription>{t("desc")}</CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={data.reload}>
            <RefreshCwIcon className="size-4" />
            {tCommon("refresh")}
          </Button>
        </CardHeader>
        <CardContent>
          <ProductsTable rows={rows} />
        </CardContent>
      </Card>
    </div>
  );
}
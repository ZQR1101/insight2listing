"use client";

import { useTranslations } from "next-intl";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Project } from "@/lib/api";

export function WorkflowStatus({
  projects,
  counts,
}: {
  projects: Project[];
  counts: { [id: string]: { products: number; reviews: number } };
}) {
  const t = useTranslations("dashboard");
  const tCommon = useTranslations("common");

  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>{t("workflow")}</CardTitle>
        <CardDescription>{t("workflowDesc")}</CardDescription>
      </CardHeader>
      <CardContent>
        {projects.length === 0 ? (
          <p className="py-6 text-sm text-muted-foreground">{t("noProjects")}</p>
        ) : (
          <ul className="divide-y">
            {projects.map((p) => {
              const c = counts[p.id] ?? { products: 0, reviews: 0 };
              return (
                <li key={p.id} className="flex items-center justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{p.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {c.products} {tCommon("products")} · {c.reviews}{" "}
                      {tCommon("reviews")}
                    </p>
                  </div>
                  <Badge variant={p.status === "DRAFT" ? "outline" : "secondary"}>
                    {p.status === "DATA_IMPORTED" ? t("dataImported") : t("draft")}
                  </Badge>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
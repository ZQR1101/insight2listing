"use client";

import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Product } from "@/lib/api";

export interface ProductRow extends Product {
  project_name: string;
}

function freshnessLabel(status?: string) {
  switch (status) {
    case "fresh":
      return "fresh";
    case "aging":
      return "aging";
    case "stale":
      return "stale";
    default:
      return "unknown";
  }
}

export function ProductsTable({ rows }: { rows: ProductRow[] }) {
  const t = useTranslations("candidates.table");
  const cand = useTranslations("candidates");

  if (rows.length === 0) {
    return <p className="px-6 py-8 text-sm text-muted-foreground">{cand("empty")}</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t("title")}</TableHead>
          <TableHead className="hidden md:table-cell">{t("project")}</TableHead>
          <TableHead className="hidden md:table-cell">{t("brand")}</TableHead>
          <TableHead className="hidden lg:table-cell">{t("rating")}</TableHead>
          <TableHead className="hidden lg:table-cell">{t("reviews")}</TableHead>
          <TableHead>{t("freshness")}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((p) => (
          <TableRow key={p.id}>
            <TableCell className="max-w-72 truncate font-medium">{p.title}</TableCell>
            <TableCell className="hidden md:table-cell">{p.project_name}</TableCell>
            <TableCell className="hidden md:table-cell">{p.brand ?? "—"}</TableCell>
            <TableCell className="hidden lg:table-cell">{p.rating ?? "—"}</TableCell>
            <TableCell className="hidden lg:table-cell">{p.review_count ?? "—"}</TableCell>
            <TableCell>
              <Badge variant={p.freshness?.freshness_status === "stale" ? "destructive" : "outline"}>
                {freshnessLabel(p.freshness?.freshness_status)}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
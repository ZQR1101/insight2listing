"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ConstructionIcon } from "lucide-react";

export function PlaceholderPanel() {
  const t = useTranslations("common");

  return (
    <div className="px-4 lg:px-6">
      <Card>
        <CardHeader className="flex items-start gap-3">
          <ConstructionIcon className="size-5 text-muted-foreground" />
          <div>
            <CardTitle>{t("comingSoon")}</CardTitle>
            <CardDescription>{t("empty")}</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground" />
      </Card>
    </div>
  );
}
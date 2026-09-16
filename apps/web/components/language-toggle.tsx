"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { LanguagesIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LanguageToggle() {
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const next = locale === "zh-CN" ? "en" : "zh-CN";
  const label = locale === "zh-CN" ? "EN" : "中文";

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => router.replace(pathname, { locale: next })}
      className="gap-1.5 text-muted-foreground"
    >
      <LanguagesIcon className="size-4" />
      {label}
    </Button>
  );
}
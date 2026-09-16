import { getTranslations } from "next-intl/server";
import { SiteShell } from "@/components/site-shell";
import { ImportPanel } from "@/components/import-panel";

export default async function ImportPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "header" });

  return (
    <SiteShell title={t("import")}>
      <ImportPanel />
    </SiteShell>
  );
}
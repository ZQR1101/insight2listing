import { getTranslations } from "next-intl/server";
import { SiteShell } from "@/components/site-shell";
import { EvidenceView } from "@/components/evidence-view";

export default async function EvidencePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "header" });

  return (
    <SiteShell title={t("evidence")}>
      <EvidenceView />
    </SiteShell>
  );
}
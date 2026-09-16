import { getTranslations } from "next-intl/server";
import { SiteShell } from "@/components/site-shell";
import { CandidatesView } from "@/components/candidates-view";

export default async function CandidatesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "header" });

  return (
    <SiteShell title={t("candidates")}>
      <CandidatesView />
    </SiteShell>
  );
}
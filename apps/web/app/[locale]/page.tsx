import { getTranslations } from "next-intl/server";
import { SiteShell } from "@/components/site-shell";
import { DashboardOverview } from "@/components/dashboard-overview";

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "header" });

  return (
    <SiteShell title={t("overview")}>
      <DashboardOverview />
    </SiteShell>
  );
}
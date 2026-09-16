import { getTranslations } from "next-intl/server";
import { SiteShell } from "@/components/site-shell";
import { PlaceholderPanel } from "@/components/placeholder-panel";

export default async function SettingsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "header" });

  return (
    <SiteShell title={t("settings")}>
      <PlaceholderPanel />
    </SiteShell>
  );
}
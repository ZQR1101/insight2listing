import { getTranslations } from "next-intl/server";
import { SiteShell } from "@/components/site-shell";
import { CreativeStudio } from "@/components/creative-studio";

export default async function CreativesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "header" });

  return (
    <SiteShell title={t("creatives")}>
      <CreativeStudio />
    </SiteShell>
  );
}

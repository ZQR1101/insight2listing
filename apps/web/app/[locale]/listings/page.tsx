import { getTranslations } from "next-intl/server";
import { SiteShell } from "@/components/site-shell";
import { ListingStudio } from "@/components/listing-studio";

export default async function ListingsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "header" });

  return (
    <SiteShell title={t("listings")}>
      <ListingStudio />
    </SiteShell>
  );
}
"use client";

import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { BoxesIcon, PackageIcon, MessageSquareMoreIcon, ListChecksIcon } from "lucide-react";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export interface SectionCardsData {
  projects: number;
  products: number;
  reviews: number;
  pending: number;
}

export function SectionCards({ data }: { data: SectionCardsData }) {
  const t = useTranslations("dashboard");

  const items: {
    key: string;
    labelKey: "projects" | "products" | "reviews" | "pendingReview";
    icon: ReactNode;
    value: number;
    desc: string;
  }[] = [
    {
      key: "projects",
      labelKey: "projects",
      icon: <BoxesIcon className="size-4" />,
      value: data.projects,
      desc: t("projectsDesc"),
    },
    {
      key: "products",
      labelKey: "products",
      icon: <PackageIcon className="size-4" />,
      value: data.products,
      desc: t("productsDesc"),
    },
    {
      key: "reviews",
      labelKey: "reviews",
      icon: <MessageSquareMoreIcon className="size-4" />,
      value: data.reviews,
      desc: t("reviewsDesc"),
    },
    {
      key: "pending",
      labelKey: "pendingReview",
      icon: <ListChecksIcon className="size-4" />,
      value: data.pending,
      desc: t("pendingReviewDesc"),
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-linear-to-t *:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4 dark:*:data-[slot=card]:bg-card">
      {items.map((item) => (
        <Card key={item.key} className="@container/card">
          <CardHeader>
            <CardDescription>{t(item.labelKey)}</CardDescription>
            <CardTitle className="flex items-center gap-2 text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              {item.value}
            </CardTitle>
          </CardHeader>
          <CardFooter className="flex-col items-start gap-1.5 text-sm">
            <div className="line-clamp-1 flex gap-2 font-medium">{item.icon}</div>
            <div className="text-muted-foreground">{item.desc}</div>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
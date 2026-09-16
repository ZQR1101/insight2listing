"use client";

import * as React from "react";
import { useLocale, useTranslations } from "next-intl";
import {
  LayoutDashboardIcon,
  FolderIcon,
  DatabaseIcon,
  UsersIcon,
  FileTextIcon,
  SettingsIcon,
  CircleHelpIcon,
} from "lucide-react";

import { NavMain } from "@/components/nav-main";
import { NavSecondary } from "@/components/nav-secondary";
import { NavUser } from "@/components/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
} from "@/components/ui/sidebar";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const t = useTranslations("nav");
  const locale = useLocale();
  const href = (path: string) => `/${locale}${path}`;

  const navMain = [
    { title: t("overview"), url: href(""), icon: <LayoutDashboardIcon /> },
    { title: t("dataImport"), url: href("/import"), icon: <DatabaseIcon /> },
    { title: t("candidates"), url: href("/candidates"), icon: <FolderIcon /> },
    { title: t("evidence"), url: href("/evidence"), icon: <UsersIcon /> },
    { title: t("listings"), url: href("/listings"), icon: <FileTextIcon /> },
  ];

  const navSecondary = [
    { title: t("settings"), url: href("/settings"), icon: <SettingsIcon /> },
    { title: t("help"), url: "#", icon: <CircleHelpIcon /> },
  ];

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarContent>
        <NavMain items={navMain} />
        <NavSecondary items={navSecondary} className="mt-auto" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={{ name: "ZQR1101", email: "Project owner" }} />
      </SidebarFooter>
    </Sidebar>
  );
}
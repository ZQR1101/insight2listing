import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Navigation helpers bound to our configured locales. `usePathname`/`useRouter`
// here are locale-aware (unlike plain next/navigation).
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
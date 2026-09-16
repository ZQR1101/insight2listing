import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";
import { routing } from "./routing";
import zhMessages from "../messages/zh.json";
import enMessages from "../messages/en.json";

// Static imports keep message loading build-time resolvable (works in
// Turbopack) instead of relying on a runtime dynamic import.
const messages = { "zh-CN": zhMessages, en: enMessages } as const;

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  return {
    locale,
    messages: messages[locale as keyof typeof messages],
  };
});
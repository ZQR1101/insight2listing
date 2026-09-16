import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Match all locale-prefixed paths and the root, but never the API proxy,
  // Next internals or files with a dot (e.g. favicon.ico).
  matcher: [
    "/",
    "/(zh-CN|en)/:path*",
    "/((?!api|_next|_vercel|.*\\..*).*)",
  ],
};